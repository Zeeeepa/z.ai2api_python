#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Z.AI Claude Code Integration
============================

This module provides Claude Code integration for the Z.AI API service.
It acts as a bridge between Claude Code Router and the Z.AI backend,
handling authentication, request transformation, and response streaming.

Usage:
    python zai_cc.py --port 3456 --host 127.0.0.1

Environment Variables:
    ZAIMCP_TOKEN: Z.AI authentication token (optional, uses anonymous if not set)
    ZAIMCP_PORT: Server port (default: 3456)
    ZAIMCP_HOST: Server host (default: 127.0.0.1)
    
Compatible with Claude Code Router plugin system.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator
import argparse

import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://chat.z.ai"
X_FE_VERSION = "prod-fe-1.0.76"  # Verified working version from Z.ai2api

class ZAIClaudeCodeBridge:
    """
    Bridge between Claude Code Router and Z.AI API.
    
    Handles:
    - Anonymous/authenticated token management
    - Request transformation (OpenAI → Z.AI format)
    - Response transformation (Z.AI → OpenAI format)
    - Streaming support
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the bridge.
        
        Args:
            token: Z.AI authentication token. If None, uses anonymous mode.
        """
        self.token = token
        self.client = httpx.AsyncClient(timeout=120.0)
        logger.info(f"🔧 Initialized Z.AI bridge (anonymous={not token})")
    
    async def get_token(self) -> str:
        """
        Get authentication token (anonymous or provided).
        
        Returns:
            str: Authentication token for Z.AI API
        """
        if self.token:
            return self.token
        
        try:
            response = await self.client.get(f"{BASE_URL}/api/v1/auths/")
            data = response.json()
            token = data.get("token")
            logger.debug(f"✅ Got anonymous token: {token[:20]}...")
            return token
        except Exception as e:
            logger.error(f"❌ Failed to get anonymous token: {e}")
            raise HTTPException(status_code=500, detail="Failed to authenticate with Z.AI")
    
    def generate_uuid(self) -> str:
        """Generate a UUID for chat/message IDs."""
        return str(uuid.uuid4())
    
    def get_headers(self, token: str, chat_id: Optional[str] = None) -> Dict[str, str]:
        """
        Generate request headers for Z.AI API.
        
        Args:
            token: Authentication token
            chat_id: Optional chat ID for Referer header
            
        Returns:
            Dict of HTTP headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "X-FE-Version": X_FE_VERSION,
            "Authorization": f"Bearer {token}",
            "Origin": BASE_URL,
        }
        
        if chat_id:
            headers["Referer"] = f"{BASE_URL}/c/{chat_id}"
        else:
            headers["Referer"] = BASE_URL
        
        return headers
    
    async def transform_request(self, openai_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform OpenAI-format request to Z.AI format.
        
        Args:
            openai_request: Request in OpenAI API format
            
        Returns:
            Dict containing:
                - body: Z.AI request body
                - token: Authentication token
                - chat_id: Generated chat ID
        """
        # Extract OpenAI parameters
        model = openai_request.get("model", "glm-4.5v")
        messages = openai_request.get("messages", [])
        stream = openai_request.get("stream", True)
        temperature = openai_request.get("temperature")
        max_tokens = openai_request.get("max_tokens")
        
        # Detect model capabilities
        model_lower = model.lower()
        is_thinking = "thinking" in model_lower
        is_search = "search" in model_lower
        
        # Get authentication token
        token = await self.get_token()
        
        # Generate IDs
        chat_id = self.generate_uuid()
        message_id = self.generate_uuid()
        
        # Build Z.AI request body
        body = {
            "stream": stream,
            "model": model,
            "messages": messages,
            "params": {},
            "features": {
                "image_generation": False,
                "web_search": is_search,
                "auto_web_search": is_search,
                "preview_mode": False,
                "flags": [],
                "features": [],
                "enable_thinking": is_thinking,
            },
            "variables": {
                "{{USER_NAME}}": "Guest",
                "{{USER_LOCATION}}": "Unknown",
                "{{CURRENT_DATETIME}}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "{{CURRENT_DATE}}": datetime.now().strftime("%Y-%m-%d"),
                "{{CURRENT_TIME}}": datetime.now().strftime("%H:%M:%S"),
                "{{CURRENT_WEEKDAY}}": datetime.now().strftime("%A"),
                "{{CURRENT_TIMEZONE}}": "UTC",
                "{{USER_LANGUAGE}}": "en-US",
            },
            "model_item": {
                "id": model,
                "name": model,
                "owned_by": "z.ai"
            },
            "chat_id": chat_id,
            "id": message_id,
        }
        
        # Add optional parameters
        if temperature is not None:
            body["params"]["temperature"] = temperature
        if max_tokens is not None:
            body["params"]["max_tokens"] = max_tokens
        
        logger.info(f"🔄 Transformed request: model={model}, stream={stream}, chat_id={chat_id}")
        
        return {
            "body": body,
            "token": token,
            "chat_id": chat_id
        }
    
    async def stream_response(
        self,
        response: httpx.Response,
        model: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream Z.AI response and transform to OpenAI format.
        
        Args:
            response: httpx streaming response from Z.AI
            model: Model name for response
            
        Yields:
            str: SSE-formatted chunks in OpenAI format
        """
        try:
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                
                chunk_str = line[5:].strip()
                if not chunk_str or chunk_str == "[DONE]":
                    yield "data: [DONE]\n\n"
                    break
                
                try:
                    chunk = json.loads(chunk_str)
                    
                    # Check if this is a Z.AI completion chunk
                    if chunk.get("type") == "chat:completion":
                        data = chunk.get("data", {})
                        phase = data.get("phase", "other")
                        delta_content = data.get("delta_content", "")
                        
                        if delta_content:
                            # Transform to OpenAI format
                            openai_chunk = {
                                "id": f"chatcmpl-{self.generate_uuid()}",
                                "object": "chat.completion.chunk",
                                "created": int(datetime.now().timestamp()),
                                "model": model,
                                "choices": [{
                                    "index": 0,
                                    "delta": {
                                        "role": "assistant",
                                        "content": delta_content
                                    },
                                    "finish_reason": None
                                }]
                            }
                            
                            yield f"data: {json.dumps(openai_chunk)}\n\n"
                        
                        # Check for completion
                        if data.get("done", False):
                            finish_chunk = {
                                "id": f"chatcmpl-{self.generate_uuid()}",
                                "object": "chat.completion.chunk",
                                "created": int(datetime.now().timestamp()),
                                "model": model,
                                "choices": [{
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": "stop"
                                }]
                            }
                            yield f"data: {json.dumps(finish_chunk)}\n\n"
                            yield "data: [DONE]\n\n"
                            break
                
                except json.JSONDecodeError:
                    logger.warning(f"⚠️  Failed to parse chunk: {chunk_str[:100]}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Stream error: {e}")
            error_chunk = {
                "id": f"chatcmpl-{self.generate_uuid()}",
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "content": f"\n\n[Error: {str(e)}]"
                    },
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
    
    async def chat_completion(self, request: Dict[str, Any]) -> Response:
        """
        Handle chat completion request.
        
        Args:
            request: OpenAI-format request
            
        Returns:
            FastAPI Response (streaming or non-streaming)
        """
        try:
            # Transform request
            transformed = await self.transform_request(request)
            body = transformed["body"]
            token = transformed["token"]
            chat_id = transformed["chat_id"]
            model = request.get("model", "glm-4.5v")
            
            # Build headers
            headers = self.get_headers(token, chat_id)
            
            # Make request to Z.AI
            logger.info(f"📡 Sending request to Z.AI: {BASE_URL}/api/chat/completions")
            
            response = await self.client.post(
                f"{BASE_URL}/api/chat/completions",
                json=body,
                headers=headers,
                timeout=120.0
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"❌ Z.AI error ({response.status_code}): {error_text[:200]}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Z.AI API error: {error_text}"
                )
            
            # Return streaming response
            if body["stream"]:
                return StreamingResponse(
                    self.stream_response(response, model),
                    media_type="text/event-stream"
                )
            else:
                # Non-streaming not fully implemented yet
                # For now, convert stream to complete response
                content = ""
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        chunk_str = line[5:].strip()
                        if chunk_str and chunk_str != "[DONE]":
                            try:
                                chunk = json.loads(chunk_str)
                                if chunk.get("type") == "chat:completion":
                                    data = chunk.get("data", {})
                                    delta = data.get("delta_content", "")
                                    if delta:
                                        content += delta
                            except:
                                pass
                
                result = {
                    "id": f"chatcmpl-{self.generate_uuid()}",
                    "object": "chat.completion",
                    "created": int(datetime.now().timestamp()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
                
                return Response(
                    content=json.dumps(result),
                    media_type="application/json"
                )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Chat completion error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


# FastAPI app
app = FastAPI(title="Z.AI Claude Code Bridge", version="1.0.0")
bridge = None  # Will be initialized in main()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible chat completions endpoint.
    
    Receives requests from Claude Code Router and forwards to Z.AI.
    """
    try:
        body = await request.json()
        logger.info(f"📥 Received request: model={body.get('model')}")
        return await bridge.chat_completion(body)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Request handling error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """List available models (for Claude Code Router compatibility)."""
    return {
        "object": "list",
        "data": [
            {
                "id": "glm-4.5v",
                "object": "model",
                "created": 1704067200,
                "owned_by": "z.ai"
            },
            {
                "id": "0727-360B-API",
                "object": "model",
                "created": 1704067200,
                "owned_by": "z.ai"
            },
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "zai-claude-code-bridge"}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Z.AI Claude Code Bridge")
    parser.add_argument("--port", type=int, default=int(os.getenv("ZAIMCP_PORT", "3456")),
                        help="Server port (default: 3456)")
    parser.add_argument("--host", default=os.getenv("ZAIMCP_HOST", "127.0.0.1"),
                        help="Server host (default: 127.0.0.1)")
    parser.add_argument("--token", default=os.getenv("ZAIMCP_TOKEN"),
                        help="Z.AI authentication token (optional)")
    
    args = parser.parse_args()
    
    # Initialize bridge
    global bridge
    bridge = ZAIClaudeCodeBridge(token=args.token)
    
    # Start server
    logger.info("=" * 60)
    logger.info("🚀 Z.AI Claude Code Bridge Starting...")
    logger.info(f"📡 Listening on: http://{args.host}:{args.port}")
    logger.info(f"🔐 Authentication: {'Token' if args.token else 'Anonymous'}")
    logger.info(f"🌐 Z.AI Backend: {BASE_URL}")
    logger.info(f"📌 API Version: {X_FE_VERSION}")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

