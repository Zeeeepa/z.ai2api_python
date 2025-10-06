#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Grok Authentication Module
Handles automated login and token retrieval using Playwright
"""

import json
import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.utils.logger import get_logger

logger = get_logger()


class GrokAuthManager:
    """Manages Grok authentication using Playwright for automated login"""
    
    def __init__(
        self, 
        login_url: str,
        chat_url: str,
        email: str,
        password: str,
        proxy_url: Optional[str] = None,
        token_cache_path: str = "data/grok_tokens.json"
    ):
        """
        Initialize Grok authentication manager
        
        Args:
            login_url: URL for X.AI login page
            chat_url: URL for Grok chat page
            email: Account email
            password: Account password
            proxy_url: Optional proxy URL
            token_cache_path: Path to store cached tokens
        """
        self.login_url = login_url
        self.chat_url = chat_url
        self.email = email
        self.password = password
        self.proxy_url = proxy_url
        self.token_cache_path = Path(token_cache_path)
        
        # Ensure data directory exists
        self.token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._lock = asyncio.Lock()
        
        # Cached credentials
        self._cached_cookies: Optional[list] = None
        self._cached_statsig_id: Optional[str] = None
        self._cache_timestamp: Optional[int] = None
        self._cache_duration = 3600  # 1 hour
    
    async def _ensure_browser(self) -> BrowserContext:
        """Ensure browser context is available"""
        if self._context:
            return self._context
        
        logger.info("🌐 Initializing Playwright browser for Grok authentication")
        
        self._playwright = await async_playwright().start()
        
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }
        
        if self.proxy_url:
            context_options["proxy"] = {"server": self.proxy_url}
        
        # Use persistent context to maintain session
        user_data_dir = Path("data/grok_browser_data")
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        self._context = await self._playwright.chromium.launch_persistent_context(
            str(user_data_dir),
            headless=True,
            # channel="chrome",  # Use default chromium instead of chrome channel
            args=[
                "--no-first-run",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
            ],
            **context_options,
        )
        
        logger.info("✅ Browser context initialized")
        return self._context
    
    async def _perform_login(self, page: Page) -> bool:
        """
        Perform login flow on X.AI
        
        Args:
            page: Playwright page object
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info(f"🔐 Navigating to login page: {self.login_url}")
            await page.goto(self.login_url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for email input field
            logger.info("⏳ Waiting for email input field")
            await page.wait_for_selector('input[type="email"]', timeout=10000)
            
            # Fill email
            logger.info(f"📧 Filling email: {self.email}")
            await page.fill('input[type="email"]', self.email)
            
            # Wait a bit for UI to update
            await asyncio.sleep(0.5)
            
            # Look for password field
            logger.info("🔑 Waiting for password input field")
            await page.wait_for_selector('input[type="password"]', timeout=10000)
            
            # Fill password
            logger.info("🔐 Filling password")
            await page.fill('input[type="password"]', self.password)
            
            # Wait a bit
            await asyncio.sleep(0.5)
            
            # Find and click submit button
            logger.info("🖱️ Looking for submit button")
            submit_button = await page.query_selector('button[type="submit"]')
            if not submit_button:
                # Try other common selectors
                submit_button = await page.query_selector('button:has-text("Sign in")')
            
            if submit_button:
                logger.info("✅ Clicking submit button")
                await submit_button.click()
            else:
                # Fallback: press Enter on password field
                logger.info("⚠️ Submit button not found, pressing Enter")
                await page.press('input[type="password"]', "Enter")
            
            # Wait for navigation or chat page
            logger.info("⏳ Waiting for login to complete")
            try:
                await page.wait_for_url(f"{self.chat_url}*", timeout=15000)
                logger.info("✅ Successfully redirected to chat page")
                return True
            except:
                # Check if we're already on chat page or a valid authenticated page
                current_url = page.url
                if "grok.com" in current_url and "sign-in" not in current_url:
                    logger.info(f"✅ Login successful - current URL: {current_url}")
                    return True
                
                # Check for error messages
                error_elements = await page.query_selector_all('[role="alert"], .error, [class*="error"]')
                if error_elements:
                    error_text = await error_elements[0].text_content()
                    logger.error(f"❌ Login error detected: {error_text}")
                    return False
                
                logger.warning(f"⚠️ Unexpected state after login - URL: {current_url}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False
    
    async def _patch_fetch_for_statsig(self, page: Page):
        """Patch window.fetch to intercept x-statsig-id headers"""
        await page.evaluate("""
            (() => {
                if (window.__fetchPatched) {
                    return "fetch already patched";
                }

                window.__fetchPatched = false;
                const originalFetch = window.fetch;
                window.__xStatsigId = null;

                window.fetch = async function(...args) {
                    const response = await originalFetch.apply(this, args);

                    try {
                        const req = args[0];
                        const opts = args[1] || {};
                        const url = typeof req === 'string' ? req : req.url;
                        const headers = opts.headers || {};

                        if (url.includes("grok.com/rest/app-chat")) {
                            let id = null;
                            if (headers["x-statsig-id"]) {
                                id = headers["x-statsig-id"];
                            } else if (typeof opts.headers?.get === "function") {
                                id = opts.headers.get("x-statsig-id");
                            }

                            if (id) {
                                window.__xStatsigId = id;
                                console.log("Captured x-statsig-id:", id);
                            }
                        }
                    } catch (e) {
                        console.warn("Error capturing x-statsig-id:", e);
                    }

                    return response;
                };

                window.__fetchPatched = true;
                return "fetch successfully patched";
            })()
        """)
        logger.info("✅ Fetch patching completed")
    
    async def _capture_statsig_id(self, page: Page) -> Optional[str]:
        """
        Capture x-statsig-id by triggering a chat request
        
        Args:
            page: Authenticated Playwright page
            
        Returns:
            Optional[str]: Captured x-statsig-id or None
        """
        try:
            logger.info("🎯 Capturing x-statsig-id header")
            
            # Patch fetch to intercept headers
            await self._patch_fetch_for_statsig(page)
            
            # Wait for textarea to be ready
            await page.wait_for_selector("textarea", timeout=10000)
            
            # Type a simple message to trigger API call
            import random
            import string
            random_char = random.choice(string.ascii_lowercase)
            
            logger.info(f"📝 Typing test message: {random_char}")
            await page.fill("textarea", random_char)
            await asyncio.sleep(0.5)
            await page.press("textarea", "Enter")
            
            # Wait for the API call to be made
            await asyncio.sleep(2)
            
            # Extract captured statsig ID
            statsig_id = await page.evaluate("window.__xStatsigId")
            
            if statsig_id:
                logger.info(f"✅ Successfully captured x-statsig-id: {statsig_id[:30]}...")
                return statsig_id
            else:
                logger.warning("⚠️ No x-statsig-id was captured")
                return None
        
        except Exception as e:
            logger.error(f"❌ Failed to capture x-statsig-id: {e}")
            return None
    
    async def _extract_cookies(self, context: BrowserContext) -> list:
        """Extract cookies from browser context"""
        cookies = await context.cookies()
        logger.info(f"🍪 Extracted {len(cookies)} cookies")
        return cookies
    
    def _save_credentials(self, cookies: list, statsig_id: str):
        """Save credentials to cache file"""
        try:
            credentials = {
                "cookies": cookies,
                "statsig_id": statsig_id,
                "timestamp": int(time.time()),
                "email": self.email
            }
            
            with open(self.token_cache_path, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            logger.info(f"💾 Credentials saved to {self.token_cache_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save credentials: {e}")
    
    def _load_credentials(self) -> Optional[Dict[str, Any]]:
        """Load credentials from cache file"""
        try:
            if not self.token_cache_path.exists():
                logger.info("📂 No cached credentials found")
                return None
            
            with open(self.token_cache_path, 'r') as f:
                credentials = json.load(f)
            
            # Check if credentials are expired (older than cache_duration)
            timestamp = credentials.get("timestamp", 0)
            age = int(time.time()) - timestamp
            
            if age > self._cache_duration:
                logger.info(f"⏰ Cached credentials expired (age: {age}s)")
                return None
            
            logger.info(f"✅ Loaded cached credentials (age: {age}s)")
            return credentials
        
        except Exception as e:
            logger.error(f"❌ Failed to load credentials: {e}")
            return None
    
    async def authenticate(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Authenticate and get credentials
        
        Args:
            force_refresh: Force re-authentication even if cache is valid
            
        Returns:
            Dict containing cookies and statsig_id
        """
        async with self._lock:
            # Try to use cached credentials if available and not forcing refresh
            if not force_refresh:
                cached = self._load_credentials()
                if cached:
                    self._cached_cookies = cached.get("cookies")
                    self._cached_statsig_id = cached.get("statsig_id")
                    self._cache_timestamp = cached.get("timestamp")
                    
                    return {
                        "cookies": self._cached_cookies,
                        "statsig_id": self._cached_statsig_id
                    }
            
            logger.info("🚀 Starting fresh authentication")
            
            # Ensure browser is ready
            context = await self._ensure_browser()
            
            # Create new page
            page = await context.new_page()
            
            try:
                # Perform login
                login_success = await self._perform_login(page)
                
                if not login_success:
                    raise Exception("Login failed")
                
                # Navigate to chat if not already there
                if self.chat_url not in page.url:
                    logger.info(f"🔄 Navigating to chat page: {self.chat_url}")
                    await page.goto(self.chat_url, wait_until="domcontentloaded", timeout=30000)
                
                # Capture statsig ID
                statsig_id = await self._capture_statsig_id(page)
                
                if not statsig_id:
                    # Use fallback statsig ID if capture fails
                    logger.warning("⚠️ Using fallback x-statsig-id")
                    statsig_id = "ZTpUeXBlRXJyb3I6IENhbm5vdCByZWFkIHByb3BlcnRpZXMgb2YgdW5kZWZpbmVkIChyZWFkaW5nICdjaGlsZE5vZGVzJyk="
                
                # Extract cookies
                cookies = await self._extract_cookies(context)
                
                # Save credentials
                self._save_credentials(cookies, statsig_id)
                
                # Update cache
                self._cached_cookies = cookies
                self._cached_statsig_id = statsig_id
                self._cache_timestamp = int(time.time())
                
                logger.info("✅ Authentication completed successfully")
                
                return {
                    "cookies": cookies,
                    "statsig_id": statsig_id
                }
            
            finally:
                await page.close()
    
    async def get_credentials(self) -> Dict[str, Any]:
        """
        Get current credentials (from cache or fresh authentication)
        
        Returns:
            Dict containing cookies and statsig_id
        """
        # Check if cache is still valid
        if (self._cached_cookies and self._cached_statsig_id and 
            self._cache_timestamp and 
            (int(time.time()) - self._cache_timestamp) < self._cache_duration):
            
            logger.info("✅ Using cached credentials")
            return {
                "cookies": self._cached_cookies,
                "statsig_id": self._cached_statsig_id
            }
        
        # Need fresh authentication
        return await self.authenticate()
    
    async def cleanup(self):
        """Clean up browser resources"""
        if self._context:
            await self._context.close()
            self._context = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("🧹 Browser resources cleaned up")
