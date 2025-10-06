#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Grok Token Manager
Simplified async token pool management for Grok provider
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from app.utils.logger import get_logger

logger = get_logger()


class GrokTokenManager:
    """Manages Grok authentication tokens with rotation and health tracking"""
    
    def __init__(self, auth_manager):
        """
        Initialize token manager
        
        Args:
            auth_manager: GrokAuthManager instance for authentication
        """
        self.auth_manager = auth_manager
        self._lock = asyncio.Lock()
        self._credentials: Optional[Dict[str, Any]] = None
        self._last_auth_time: Optional[int] = None
        self._auth_duration = 3600  # 1 hour
        self._request_count = 0
        self._failure_count = 0
        
    async def get_credentials(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get valid credentials (with automatic refresh if needed)
        
        Args:
            force_refresh: Force re-authentication
            
        Returns:
            Dict containing cookies and statsig_id
        """
        async with self._lock:
            current_time = int(time.time())
            
            # Check if we need to refresh
            needs_refresh = (
                force_refresh or
                self._credentials is None or
                self._last_auth_time is None or
                (current_time - self._last_auth_time) >= self._auth_duration or
                self._failure_count >= 3
            )
            
            if needs_refresh:
                logger.info("🔄 Refreshing Grok credentials")
                try:
                    self._credentials = await self.auth_manager.get_credentials()
                    self._last_auth_time = current_time
                    self._failure_count = 0
                    logger.info("✅ Credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to refresh credentials: {e}")
                    if self._credentials is None:
                        raise
            
            self._request_count += 1
            return self._credentials
    
    def record_success(self):
        """Record successful API call"""
        self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self, error: Exception):
        """Record failed API call"""
        self._failure_count += 1
        logger.warning(f"⚠️ Token failure recorded (count: {self._failure_count}): {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get token manager statistics"""
        return {
            "request_count": self._request_count,
            "failure_count": self._failure_count,
            "last_auth_time": self._last_auth_time,
            "has_credentials": self._credentials is not None
        }

