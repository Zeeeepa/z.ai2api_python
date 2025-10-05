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
    """Qwen provider authentication"""
    
    async def login(self) -> Dict[str, Any]:
        """Login to Qwen and extract cookies"""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            # Step 1: Get initial cookies
            logger.debug(f"Qwen: Getting initial cookies from {self.base_url}")
            init_response = await client.get(self.base_url)
            
            # Step 2: Perform login
            login_data = {
                "email": self.email,
                "password": self.password
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': self.base_url,
                'Referer': self.base_url
            }
            
            logger.debug(f"Qwen: Posting login to {self.login_url}")
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
            
            # Extract token if in response
            token = None
            try:
                response_data = login_response.json()
                token = response_data.get("token") or response_data.get("access_token")
            except:
                pass
            
            # Also check for ssxmod_itna cookie specifically
            ssxmod_itna = cookies.get("ssxmod_itna")
            
            logger.info(f"Qwen: Extracted {len(cookies)} cookies, token: {bool(token)}, ssxmod_itna: {bool(ssxmod_itna)}")
            
            return {
                "cookies": cookies,
                "token": token,
                "extra": {
                    "ssxmod_itna": ssxmod_itna
                }
            }


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

