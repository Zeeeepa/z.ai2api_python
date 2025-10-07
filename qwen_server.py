#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Qwen Standalone Server
=======================

A standalone OpenAI-compatible API server for Qwen models.

Usage:
    python qwen_server.py

Or with environment variables:
    PORT=8081 QWEN_EMAIL=your@email.com QWEN_PASSWORD=yourpass python qwen_server.py

Docker:
    docker-compose up -d

Test:
    from openai import OpenAI
    client = OpenAI(
        api_key="sk-anything",
        base_url="http://localhost:8081/v1"
    )
    response = client.chat.completions.create(
        model="qwen-turbo-latest",
        messages=[{"role": "user", "content": "What model are you?"}]
    )
    print(response.choices[0].message.content)
"""

import os
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import logging
from typing import AsyncGenerator, Optional, Dict, Any
import time
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Qwen provider
try:
    from app.providers.qwen_provider import QwenProvider
    from app.providers.base import ProviderConfig
    from app.models.schemas import OpenAIRequest, Message
except ImportError:
    logger.error("Failed to import required modules. Please install with: pip install -e .")
    sys.exit(1)

# Configuration from environment
PORT = int(os.getenv("PORT", "8081"))
QWEN_EMAIL = os.getenv("QWEN_EMAIL", "")
QWEN_PASSWORD = os.getenv("QWEN_PASSWORD", "")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENABLE_FLAREPROX = os.getenv("ENABLE_FLAREPROX", "false").lower() == "true"

# Global Qwen provider instance
qwen_provider: Optional[QwenProvider] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global qwen_provider
    
    logger.info("🚀 Starting Qwen Standalone Server...")
    logger.info(f"📡 Port: {PORT}")
    logger.info(f"🔐 Authentication: {'Enabled' if QWEN_EMAIL and QWEN_PASSWORD else 'Disabled'}")
    logger.info(f"🔧 Debug Mode: {DEBUG}")
    logger.info(f"🌐 FlareProx: {'Enabled' if ENABLE_FLAREPROX else 'Disabled'}")
    
    # Initialize Qwen provider
    config = ProviderConfig(
        name="qwen",
        base_url="https://chat.qwen.ai",
        api_key="",
        auth_required=bool(QWEN_EMAIL and QWEN_PASSWORD),
        timeout=60.0
    )
    
    qwen_provider = QwenProvider(config)
    
    # Set credentials if provided
    if QWEN_EMAIL and QWEN_PASSWORD:
        logger.info("🔑 Configuring Qwen credentials...")
        try:
            # Set credentials (authentication will happen on first request)
            qwen_provider.auth_manager.email = QWEN_EMAIL
            qwen_provider.auth_manager.password = QWEN_PASSWORD
            logger.info("✅ Credentials configured")
        except Exception as e:
            logger.error(f"❌ Failed to configure credentials: {e}")
    else:
        logger.warning("⚠️ No credentials provided. Some features may not work.")
    
    logger.info("✅ Qwen provider initialized")
    
    yield
    
    logger.info("🔄 Shutting down Qwen Standalone Server...")


# Create FastAPI app
app = FastAPI(
    title="Qwen API Server",
    description="OpenAI-compatible API server for Qwen models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Qwen API Server",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "provider": "qwen",
        "authenticated": bool(QWEN_EMAIL and QWEN_PASSWORD)
    }


@app.get("/v1/models")
async def list_models():
    """List available models"""
    global qwen_provider
    
    if not qwen_provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")
    
    models = qwen_provider.get_supported_models()
    
    return {
        "object": "list",
        "data": [
            {
                "id": model,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "qwen",
                "permission": [],
                "root": model,
                "parent": None
            }
            for model in models
        ]
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Chat completions endpoint (OpenAI-compatible)
    
    Supports all Qwen model families:
    - qwen-max, qwen-max-latest, qwen-max-0428
    - qwen-max-thinking, qwen-max-search
    - qwen-max-deep-research
    - qwen-max-video
    - qwen-plus (all variants)
    - qwen-turbo (all variants)
    - qwen-long (all variants)
    - qwen-deep-research
    - qwen3-coder-plus
    - qwen-coder-plus
    """
    global qwen_provider
    
    if not qwen_provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")
    
    try:
        # Parse request
        body = await request.json()
        
        model = body.get("model", "qwen-turbo-latest")
        messages = body.get("messages", [])
        stream = body.get("stream", False)
        temperature = body.get("temperature", 0.7)
        max_tokens = body.get("max_tokens")
        top_p = body.get("top_p", 1.0)
        
        # Validate request
        if not messages:
            raise HTTPException(status_code=400, detail="Messages are required")
        
        # Convert to OpenAIRequest
        openai_request = OpenAIRequest(
            model=model,
            messages=[Message(**msg) for msg in messages],
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        
        # Handle streaming
        if stream:
            async def generate_stream() -> AsyncGenerator[bytes, None]:
                """Generate streaming response"""
                try:
                    async for chunk in qwen_provider.chat_completion_stream(openai_request):
                        # Format as SSE
                        yield f"data: {json.dumps(chunk)}\n\n".encode('utf-8')
                    
                    # Send done signal
                    yield b"data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}", exc_info=True)
                    error_chunk = {
                        "error": {
                            "message": str(e),
                            "type": "server_error",
                            "code": "internal_error"
                        }
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n".encode('utf-8')
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        
        # Non-streaming response
        else:
            response = await qwen_provider.chat_completion(openai_request)
            return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/images/generations")
async def image_generation(request: Request):
    """Image generation endpoint (OpenAI-compatible)"""
    global qwen_provider
    
    if not qwen_provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")
    
    try:
        body = await request.json()
        
        prompt = body.get("prompt", "")
        model = body.get("model", "qwen-max-image")
        n = body.get("n", 1)
        size = body.get("size", "1024x1024")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Generate image
        result = await qwen_provider.generate_image(
            prompt=prompt,
            model=model,
            size=size,
            n=n
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.options("/{path:path}")
async def handle_options(path: str):
    """Handle OPTIONS requests for CORS"""
    return Response(status_code=200)


def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("  Qwen Standalone Server")
    logger.info("="*60)
    logger.info(f"  Port: {PORT}")
    logger.info(f"  Base URL: http://localhost:{PORT}/v1")
    logger.info(f"  Docs: http://localhost:{PORT}/docs")
    logger.info("="*60)
    
    # Run server
    uvicorn.run(
        "qwen_server:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info" if DEBUG else "warning",
        reload=DEBUG,
        access_log=DEBUG
    )


if __name__ == "__main__":
    main()

