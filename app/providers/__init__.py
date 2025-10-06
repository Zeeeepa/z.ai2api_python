#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多提供商架构包
提供统一的提供商接口和路由机制
"""

from app.providers.base import BaseProvider, ProviderConfig, provider_registry
from app.providers.zai_provider import ZAIProvider
from app.providers.k2think_provider import K2ThinkProvider
from app.providers.qwen_provider import QwenProvider
from app.providers.provider_factory import ProviderFactory, ProviderRouter, get_provider_router, initialize_providers

__all__ = [
    "BaseProvider",
    "ProviderConfig", 
    "provider_registry",
    "ZAIProvider",
    "K2ThinkProvider", 
    "QwenProvider",
    "ProviderFactory",
    "ProviderRouter",
    "get_provider_router",
    "initialize_providers"
]
