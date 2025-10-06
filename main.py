#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import psutil
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.core.config import settings
from app.core import openai
from app.core import image_endpoints
from app.utils.reload_config import RELOAD_CONFIG
from app.utils.logger import setup_logger
from app.utils.token_pool import initialize_token_pool
from app.utils.flareprox_manager import initialize_flareprox, get_flareprox_manager
from app.providers import initialize_providers

from granian import Granian


# Setup logger
logger = setup_logger(log_dir="logs", debug_mode=settings.DEBUG_LOGGING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化提供商系统
    initialize_providers()

    # 初始化 FlareProx (如果启用)
    await initialize_flareprox()

    # 初始化 token 池
    token_list = settings.auth_token_list
    if token_list:
        token_pool = initialize_token_pool(
            tokens=token_list,
            failure_threshold=settings.TOKEN_FAILURE_THRESHOLD,
            recovery_timeout=settings.TOKEN_RECOVERY_TIMEOUT
        )

    yield

    logger.info("🔄 应用正在关闭...")


# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include API routers
app.include_router(openai.router)
app.include_router(image_endpoints.router)


@app.options("/")
async def handle_options():
    """Handle OPTIONS requests"""
    return Response(status_code=200)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "OpenAI Compatible API Server"}


def run_server():
    """Run the Granian server"""
    service_name = settings.SERVICE_NAME

    logger.info(f"🚀 启动 {service_name} 服务...")
    logger.info(f"📡 监听地址: 0.0.0.0:{settings.LISTEN_PORT}")
    logger.info(f"🔧 调试模式: {'开启' if settings.DEBUG_LOGGING else '关闭'}")
    logger.info(f"🔐 匿名模式: {'开启' if settings.ANONYMOUS_MODE else '关闭'}")

    try:
        Granian(
            "main:app",
            interface="asgi",
            address="0.0.0.0",
            port=settings.LISTEN_PORT,
            reload=False,  # 生产环境请关闭热重载
            process_name=service_name,  # 设置进程名称
            **RELOAD_CONFIG,    # 热重载配置
        ).serve()
    except KeyboardInterrupt:
        logger.info("🛑 收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # When run directly, use the CLI module for enhanced startup
    from app.cli import main as cli_main
    cli_main()
