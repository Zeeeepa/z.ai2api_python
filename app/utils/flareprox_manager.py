#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FlareProx Manager - Automatic proxy management with load balancing
"""

import os
import asyncio
import time
from typing import List, Dict, Optional
from collections import deque
import threading

from app.utils.logger import get_logger

logger = get_logger()


class FlareProxManager:
    """
    Manages FlareProx proxies with automatic initialization and load balancing
    """
    
    def __init__(self):
        self.enabled = False
        self.proxies: deque = deque()  # Rotating queue of proxy URLs
        self.request_count = 0
        self.rotate_interval = 100  # Requests before rotation
        self.current_proxy_index = 0
        self._lock = threading.Lock()
        self._initialized = False
        
        # Configuration from environment
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
        self.proxy_count = int(os.getenv("FLAREPROX_PROXY_COUNT", "3"))
        self.auto_rotate = os.getenv("FLAREPROX_AUTO_ROTATE", "true").lower() == "true"
        self.enabled = os.getenv("FLAREPROX_ENABLED", "false").lower() == "true"
    
    async def initialize(self) -> bool:
        """Initialize FlareProx proxies"""
        if not self.enabled:
            logger.info("🔥 FlareProx: Disabled")
            return False
        
        if not self.api_token or not self.account_id:
            logger.warning("⚠️  FlareProx: Missing credentials (CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID)")
            self.enabled = False
            return False
        
        logger.info(f"🔥 FlareProx: Initializing with {self.proxy_count} proxies...")
        
        try:
            # Import FlareProx here to avoid circular imports
            import sys
            import importlib.util
            
            # Load flareprox module
            flareprox_path = os.path.join(os.getcwd(), "flareprox.py")
            spec = importlib.util.spec_from_file_location("flareprox", flareprox_path)
            if not spec or not spec.loader:
                logger.error("❌ FlareProx: Could not load flareprox.py")
                self.enabled = False
                return False
            
            flareprox_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(flareprox_module)
            
            # Create FlareProx instance
            flareprox = flareprox_module.FlareProx()
            
            if not flareprox.is_configured:
                logger.error("❌ FlareProx: Not configured properly")
                self.enabled = False
                return False
            
            # Load existing proxies or create new ones
            endpoints = flareprox.sync_endpoints()
            
            if len(endpoints) < self.proxy_count:
                logger.info(f"🔥 FlareProx: Creating {self.proxy_count - len(endpoints)} additional proxies...")
                result = flareprox.create_proxies(self.proxy_count - len(endpoints))
                endpoints = flareprox.sync_endpoints()
            
            if not endpoints:
                logger.error("❌ FlareProx: No proxies available")
                self.enabled = False
                return False
            
            # Store proxy URLs in rotating queue
            for endpoint in endpoints:
                self.proxies.append(endpoint["url"])
            
            logger.info(f"✅ FlareProx: Initialized with {len(self.proxies)} proxies")
            logger.info(f"🔄 FlareProx: Auto-rotate every {self.rotate_interval} requests")
            for i, proxy in enumerate(endpoints, 1):
                logger.info(f"   [{i}] {proxy['url']}")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ FlareProx initialization failed: {e}")
            self.enabled = False
            return False
    
    def get_proxy_url(self, target_url: str) -> str:
        """
        Get next proxy URL for load balancing
        
        Args:
            target_url: The target URL to proxy to
            
        Returns:
            Proxied URL or original URL if FlareProx is disabled
        """
        if not self.enabled or not self._initialized or not self.proxies:
            return target_url
        
        with self._lock:
            # Get current proxy
            if self.auto_rotate:
                # Auto-rotate based on request count
                self.request_count += 1
                if self.request_count >= self.rotate_interval:
                    self.proxies.rotate(-1)  # Move to next proxy
                    self.request_count = 0
                    logger.debug(f"🔄 FlareProx: Rotated to proxy {self.proxies[0]}")
            
            proxy_url = self.proxies[0]
            
            # Build proxied URL: proxy_url?url=target_url
            if "?" in proxy_url:
                proxied_url = f"{proxy_url}&url={target_url}"
            else:
                proxied_url = f"{proxy_url}?url={target_url}"
            
            return proxied_url
    
    def get_stats(self) -> Dict:
        """Get FlareProx statistics"""
        return {
            "enabled": self.enabled,
            "initialized": self._initialized,
            "proxy_count": len(self.proxies),
            "request_count": self.request_count,
            "auto_rotate": self.auto_rotate,
            "rotate_interval": self.rotate_interval
        }
    
    def add_proxy(self, proxy_url: str):
        """Add a new proxy to the rotation"""
        with self._lock:
            self.proxies.append(proxy_url)
            logger.info(f"✅ FlareProx: Added proxy {proxy_url}")
    
    def remove_proxy(self, proxy_url: str):
        """Remove a proxy from the rotation"""
        with self._lock:
            if proxy_url in self.proxies:
                self.proxies.remove(proxy_url)
                logger.info(f"🗑️  FlareProx: Removed proxy {proxy_url}")


# Global FlareProx manager instance
_flareprox_manager: Optional[FlareProxManager] = None


def get_flareprox_manager() -> FlareProxManager:
    """Get the global FlareProx manager instance"""
    global _flareprox_manager
    if _flareprox_manager is None:
        _flareprox_manager = FlareProxManager()
    return _flareprox_manager


async def initialize_flareprox() -> bool:
    """Initialize FlareProx manager"""
    manager = get_flareprox_manager()
    return await manager.initialize()

