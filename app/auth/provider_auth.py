#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Provider Authentication Manager
Handles automatic login and session management for all providers
"""

import httpx
import json
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod

from app.auth.session_store import SessionStore
from app.utils.logger import get_logger

logger = get_logger()


class ProviderAuth(ABC):
    """Base class for provider authentication"""
    
    def __init__(self, config: Dict[str, str]):
        """
        Initialize provider authentication
        
        Args:
            config: Provider configuration (name, baseUrl, loginUrl, email, password)
        """
        self.config = config
        self.name = config["name"]
        self.base_url = config["baseUrl"]
        self.login_url = config["loginUrl"]
        self.email = config["email"]
        self.password = config["password"]
        
        # Session store
        self.session_store = SessionStore(self.name)
        
        # Cached session data
        self._cached_cookies: Optional[Dict[str, str]] = None
        self._cached_token: Optional[str] = None
    
    @abstractmethod
    async def login(self) -> Dict[str, Any]:
        """
        Perform login and extract authentication data
        
        Returns:
            Dict containing cookies, token, and any extra data
        """
        pass
    
    async def get_valid_session(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get valid session data, auto-login if needed
        
        Args:
            force_refresh: Force new login even if session exists
            
        Returns:
            Dict with cookies and token
        """
        # Check cached data first
        if not force_refresh and self._cached_cookies:
            return {
                "cookies": self._cached_cookies,
                "token": self._cached_token
            }
        
        # Try to load from storage
        if not force_refresh and self.session_store.is_valid(max_age=43200):  # 12 hours
            session = self.session_store.load_session()
            if session:
                self._cached_cookies = session.get("cookies")
                self._cached_token = session.get("token")
                logger.info(f"✅ Using cached {self.name} session")
                return {
                    "cookies": self._cached_cookies,
                    "token": self._cached_token
                }
        
        # Need to login
        logger.info(f"🔐 Logging in to {self.name}...")
        try:
            auth_data = await self.login()
            
            # Cache the data
            self._cached_cookies = auth_data.get("cookies", {})
            self._cached_token = auth_data.get("token")
            
            # Save to storage
            self.session_store.save_session(
                self._cached_cookies,
                self._cached_token,
                auth_data.get("extra")
            )
            
            logger.info(f"✅ {self.name} login successful")
            return {
                "cookies": self._cached_cookies,
                "token": self._cached_token
            }
            
        except Exception as e:
            logger.error(f"❌ {self.name} login failed: {e}")
            return None
    
    async def get_cookies(self, force_refresh: bool = False) -> Optional[Dict[str, str]]:
        """Get authentication cookies"""
        session = await self.get_valid_session(force_refresh)
        return session.get("cookies") if session else None
    
    async def get_token(self, force_refresh: bool = False) -> Optional[str]:
        """Get authentication token"""
        session = await self.get_valid_session(force_refresh)
        return session.get("token") if session else None
    
    def clear_session(self):
        """Clear cached session"""
        self._cached_cookies = None
        self._cached_token = None
        self.session_store.clear_session()


class QwenAuth(ProviderAuth):
    """Qwen provider authentication using Playwright to extract Bearer token"""
    
    async def login(self) -> Dict[str, Any]:
        """
        Login to Qwen using Playwright and extract Bearer token.
        
        The token is created by:
        1. Extracting web_api_auth_token from localStorage
        2. Extracting ssxmod_itna cookie
        3. Combining them: token|cookie
        4. Compressing with gzip
        5. Base64 encoding
        """
        from playwright.async_api import async_playwright
        import gzip
        import base64
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                logger.info(f"🌐 Qwen: Navigating to {self.base_url}")
                await page.goto(self.base_url, wait_until='networkidle', timeout=30000)
                
                # Click "Log in" button to go to login page
                try:
                    logger.debug("🔍 Qwen: Looking for 'Log in' button")
                    # Look for "Log in" button (English or Chinese)
                    login_link = await page.wait_for_selector('button:has-text("Log in"), button:has-text("登录"), a:has-text("Log in"), a:has-text("登录")', timeout=5000)
                    await login_link.click()
                    logger.info("👆 Qwen: Clicked 'Log in' button")
                    await page.wait_for_load_state('networkidle', timeout=10000)
                except Exception as e:
                    logger.debug(f"Qwen: Could not find/click login button: {e}, assuming already on login page")
                
                # Wait for login form
                logger.debug("🔐 Qwen: Waiting for login form")
                await page.wait_for_selector('input[type="email"], input[type="text"], input[name="email"]', timeout=10000)
                
                # Fill in credentials
                logger.debug("✏️ Qwen: Filling credentials")
                email_input = await page.query_selector('input[type="email"], input[type="text"], input[name="email"]')
                await email_input.fill(self.email)
                
                password_input = await page.query_selector('input[type="password"], input[name="password"]')
                await password_input.fill(self.password)
                
                # Click login button
                logger.debug("👆 Qwen: Clicking login button")
                submit_button = await page.query_selector('button[type="submit"], button:has-text("登录"), button:has-text("Login")')
                await submit_button.click()
                
                # Wait for successful login
                logger.debug("⏳ Qwen: Waiting for login to complete")
                try:
                    # Wait for URL change or specific element
                    await page.wait_for_url('**/chat**', timeout=20000)
                    logger.info("✅ Qwen: Login successful (URL changed)")
                except:
                    try:
                        # Alternative: wait for networkidle
                        await page.wait_for_load_state('networkidle', timeout=20000)
                        logger.info("✅ Qwen: Login successful (network idle)")
                    except:
                        # Last resort: check for localStorage token
                        logger.warning("⚠️ Qwen: Timeout waiting for login, checking token anyway")
                
                # Extract localStorage token with retries
                logger.debug("🔑 Qwen: Extracting localStorage token")
                web_api_token = None
                
                # Try multiple times - JavaScript may populate localStorage after page load
                for attempt in range(3):
                    web_api_token = await page.evaluate('''() => {
                        return localStorage.getItem('web_api_auth_token');
                    }''')
                    if web_api_token:
                        logger.info(f"✅ Qwen: Found web_api_token on attempt {attempt + 1}")
                        break
                    logger.debug(f"⏳ Qwen: Attempt {attempt + 1}/3 - waiting for token...")
                    await asyncio.sleep(1)
                
                # Extract all cookies
                logger.debug("🍪 Qwen: Extracting cookies")
                cookies = await context.cookies()
                
                # Find ssxmod_itna cookie
                ssxmod_itna = None
                cookie_dict = {}
                for cookie in cookies:
                    cookie_dict[cookie['name']] = cookie['value']
                    if cookie['name'] == 'ssxmod_itna':
                        ssxmod_itna = cookie['value']
                
                logger.info(f"📊 Qwen: web_api_token={bool(web_api_token)}, ssxmod_itna={bool(ssxmod_itna)}, total_cookies={len(cookie_dict)}")
                
                # Create Bearer token
                bearer_token = None
                if web_api_token and ssxmod_itna:
                    try:
                        # Combine: token|cookie
                        combined = f"{web_api_token}|{ssxmod_itna}"
                        logger.debug(f"🔗 Qwen: Combined length: {len(combined)}")
                        
                        # Compress with gzip
                        compressed = gzip.compress(combined.encode('utf-8'))
                        logger.debug(f"📦 Qwen: Compressed length: {len(compressed)}")
                        
                        # Base64 encode
                        bearer_token = base64.b64encode(compressed).decode('utf-8')
                        logger.info(f"🎟️ Qwen: Generated Bearer token (length: {len(bearer_token)})")
                    except Exception as e:
                        logger.error(f"❌ Qwen: Failed to generate Bearer token: {e}", exc_info=True)
                else:
                    # FALLBACK: Cookie-only auth (proven to work!)
                    if ssxmod_itna:
                        logger.warning("⚠️ Qwen: web_api_token not available, using cookie-only auth")
                        logger.info("💡 Qwen: Cookie-only auth is sufficient for most operations")
                    else:
                        logger.error("❌ Qwen: No authentication credentials found")
                
                await browser.close()
                
                # Success if we have either bearer token OR ssxmod_itna cookie
                if not bearer_token and not ssxmod_itna:
                    raise Exception("Failed to authenticate - no valid credentials found")
                
                return {
                    "cookies": cookie_dict,
                    "token": bearer_token,
                    "extra": {
                        "web_api_token": web_api_token,
                        "ssxmod_itna": ssxmod_itna
                    }
                }
                
            except Exception as e:
                logger.error(f"❌ Qwen Playwright login failed: {e}", exc_info=True)
                await browser.close()
                raise


class ZAIAuth(ProviderAuth):
    """Z.AI provider authentication"""
    
    async def login(self) -> Dict[str, Any]:
        """Login to Z.AI and extract token"""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            # Get initial page
            await client.get(self.base_url)
            
            # Login
            login_data = {
                "email": self.email,
                "password": self.password
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            login_response = await client.post(
                self.login_url,
                json=login_data,
                headers=headers
            )
            
            if login_response.status_code not in [200, 201]:
                raise Exception(f"Login failed with status {login_response.status_code}")
            
            # Extract token from response
            response_data = login_response.json()
            token = response_data.get("token") or response_data.get("access_token")
            
            # Extract cookies
            cookies = {}
            for cookie_name, cookie_value in client.cookies.items():
                cookies[cookie_name] = cookie_value
            
            logger.info(f"Z.AI: Extracted token and {len(cookies)} cookies")
            
            return {
                "cookies": cookies,
                "token": token,
                "extra": {}
            }


class K2ThinkAuth(ProviderAuth):
    """K2Think provider authentication"""
    
    async def login(self) -> Dict[str, Any]:
        """Login to K2Think and extract session"""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            # Get initial page
            await client.get(self.base_url)
            
            # Login
            login_data = {
                "email": self.email,
                "password": self.password
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            login_response = await client.post(
                self.login_url,
                json=login_data,
                headers=headers
            )
            
            if login_response.status_code not in [200, 201, 302]:
                raise Exception(f"Login failed with status {login_response.status_code}")
            
            # Extract cookies
            cookies = {}
            for cookie_name, cookie_value in client.cookies.items():
                cookies[cookie_name] = cookie_value
            
            # Extract token if available
            token = None
            try:
                response_data = login_response.json()
                token = response_data.get("token") or response_data.get("sessionId")
            except:
                pass
            
            logger.info(f"K2Think: Extracted {len(cookies)} cookies, token: {bool(token)}")
            
            return {
                "cookies": cookies,
                "token": token,
                "extra": {}
            }


# Factory for creating auth instances
def create_auth(config: Dict[str, str]) -> ProviderAuth:
    """
    Create authentication instance for provider
    
    Args:
        config: Provider configuration
        
    Returns:
        ProviderAuth instance
    """
    provider_name = config["name"].lower()
    
    if provider_name == "qwen":
        return QwenAuth(config)
    elif provider_name == "zai" or provider_name == "z.ai":
        return ZAIAuth(config)
    elif provider_name == "k2think":
        return K2ThinkAuth(config)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
