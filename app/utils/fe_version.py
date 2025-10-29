#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility helpers for resolving the latest X-FE-Version value from chat.z.ai.

The upstream service embeds the current front-end release identifier inside
its landing page static asset URLs (e.g. `prod-fe-1.0.107`). The helpers in
this module fetch the landing page, extract the version string, and cache it
with a configurable TTL so the expensive network fetch only happens when
necessary.
"""

from __future__ import annotations

import re
import time
from typing import Optional

import httpx

from app.utils.logger import get_logger
from app.utils.user_agent import get_random_user_agent

# Base URL to probe for the version string.
FE_VERSION_SOURCE_URL = "https://chat.z.ai"

# Cache TTL in seconds (default: 30 minutes).
CACHE_TTL_SECONDS = 1800

_logger = get_logger()
_version_pattern = re.compile(r"prod-fe-\d+\.\d+\.\d+")

_cached_version: str = ""
_cached_at: float = 0.0


def _extract_version(page_content: str) -> Optional[str]:
    """Extract the version string from the page content."""
    if not page_content:
        return None

    matches = _version_pattern.findall(page_content)
    if not matches:
        return None

    # Choose the highest lexical value to guard against mixed versions.
    return max(matches)




def _should_use_cache(force_refresh: bool) -> bool:
    """Determine whether the cached value can be reused."""
    if force_refresh:
        return False
    if not _cached_version:
        return False
    if _cached_at <= 0:
        return False
    return (time.time() - _cached_at) < CACHE_TTL_SECONDS


def get_latest_fe_version(force_refresh: bool = False) -> str:
    """
    Resolve the latest X-FE-Version value from chat.z.ai.

    The lookup order is:
        1. Cached value within TTL.
        2. Remote fetch from chat.z.ai.
    
    Raises:
        Exception: If unable to fetch the version from the remote source.
    """
    global _cached_version, _cached_at

    if _should_use_cache(force_refresh):
        return _cached_version

    try:
        headers = {"User-Agent": get_random_user_agent("chrome")}
    except Exception:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(FE_VERSION_SOURCE_URL, headers=headers)
            response.raise_for_status()
            version = _extract_version(response.text)
            if version:
                if version != _cached_version:
                    _logger.info(f"[Z.AI] Detected X-FE-Version update: {version}")
                _cached_version = version
                _cached_at = time.time()
                return version

            _logger.error("[Z.AI] Unable to locate X-FE-Version in landing page")
            raise Exception("Unable to locate X-FE-Version in landing page")
    except Exception as exc:
        _logger.error(f"[Z.AI] Failed to fetch X-FE-Version from {FE_VERSION_SOURCE_URL}: {exc}")
        raise Exception(f"Failed to fetch X-FE-Version: {exc}")


def refresh_fe_version() -> str:
    """Force refresh the cached version by bypassing the TTL."""
    return get_latest_fe_version(force_refresh=True)
