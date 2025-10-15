#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    API_ENDPOINT: str = "https://chat.z.ai/api/chat/completions"
    
    # Authentication
    AUTH_TOKEN: Optional[str] = os.getenv("AUTH_TOKEN")

    # Token池配置
    TOKEN_FAILURE_THRESHOLD: int = int(os.getenv("TOKEN_FAILURE_THRESHOLD", "3"))  # 失败3次后标记为不可用
    TOKEN_RECOVERY_TIMEOUT: int = int(os.getenv("TOKEN_RECOVERY_TIMEOUT", "1800"))  # 30分钟后重试失败的token

    # Model Configuration
    GLM45_MODEL: str = os.getenv("GLM45_MODEL", "GLM-4.5")
    GLM45_THINKING_MODEL: str = os.getenv("GLM45_THINKING_MODEL", "GLM-4.5-Thinking")
    GLM45_SEARCH_MODEL: str = os.getenv("GLM45_SEARCH_MODEL", "GLM-4.5-Search")
    GLM45_AIR_MODEL: str = os.getenv("GLM45_AIR_MODEL", "GLM-4.5-Air")
    GLM45V_MODEL: str = os.getenv("GLM45V_MODEL", "GLM-4.5V")
    GLM46_MODEL: str = os.getenv("GLM46_MODEL", "GLM-4.6")
    GLM46_THINKING_MODEL: str = os.getenv("GLM46_THINKING_MODEL", "GLM-4.6-Thinking")
    GLM46_SEARCH_MODEL: str = os.getenv("GLM46_SEARCH_MODEL", "GLM-4.6-Search")
    GLM46_ADVANCED_SEARCH_MODEL: str = os.getenv("GLM46_ADVANCED_SEARCH_MODEL", "GLM-4.6-advanced-search")

    # Provider Model Mapping
    @property
    def provider_model_mapping(self) -> Dict[str, str]:
        """模型到提供商的映射"""
        return {
            # Z.AI models
            "GLM-4.5": "zai",
            "GLM-4.5-Thinking": "zai",
            "GLM-4.5-Search": "zai",
            "GLM-4.5-Air": "zai",
            "GLM-4.5V": "zai",
            "GLM-4.6": "zai",
            "GLM-4.6-Thinking": "zai",
            "GLM-4.6-Search": "zai",
            "GLM-4.6-advanced-search": "zai",
            # K2Think models
            "MBZUAI-IFM/K2-Think": "k2think",
            # LongCat models
            "LongCat-Flash": "longcat",
            "LongCat": "longcat",
            "LongCat-Search": "longcat",
        }

    # Server Configuration
    LISTEN_PORT: int = int(os.getenv("LISTEN_PORT", "8080"))
    DEBUG_LOGGING: bool = os.getenv("DEBUG_LOGGING", "true").lower() == "true"
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "z-ai2api-server")

    ANONYMOUS_MODE: bool = os.getenv("ANONYMOUS_MODE", "true").lower() == "true"
    TOOL_SUPPORT: bool = os.getenv("TOOL_SUPPORT", "true").lower() == "true"
    SCAN_LIMIT: int = int(os.getenv("SCAN_LIMIT", "200000"))
    SKIP_AUTH_TOKEN: bool = os.getenv("SKIP_AUTH_TOKEN", "false").lower() == "true"

    # LongCat Configuration
    LONGCAT_TOKEN: Optional[str] = os.getenv("LONGCAT_TOKEN")

    # Provider Configuration
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "zai")  # 默认提供商：zai/k2think/longcat

    # Admin Panel Authentication
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")  # 管理后台密码
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "your-secret-key-change-in-production")  # Session 密钥

    # Browser Headers
    CLIENT_HEADERS: Dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
        "Accept-Language": "zh-CN",
        "sec-ch-ua": '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "X-FE-Version": "prod-fe-1.0.98",
        "Origin": "https://chat.z.ai",
    }

    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略额外字段，防止环境变量中的未知字段导致验证错误


settings = Settings()
