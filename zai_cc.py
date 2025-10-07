#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Z.AI Claude Code Integration - WORKING VERSION
==============================================

Two-step chat creation flow implemented correctly.
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
import time

import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://chat.z.ai"
X_FE_VERSION = "prod-fe-1.0.76"

class ZAIClaudeCodeBridge:
    """Bridge with TWO-STEP chat creation flow."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.client = httpx.AsyncClient(timeout=120.0)
        logger.info(f"🔧 Initialized (anonymous={not token})")
    
    async def get_token(self) -> str:
        """Get authentication token."""
        if self.token:
            return self.token
        
        try:
            response = await self.client.get(f"{BASE_URL}/api/v1/auths/")
            token = response.json().get("token")
            logger.debug(f"✅ Got token: {token[:20]}...")
            return token
        except Exception as e:
            logger.error(f"❌ Token error: {e}")
            raise HTTPException(status_code=500, detail=f"Auth failed: {e}")
    
    def generate_uuid(self) -> str:
        return str(uuid.uuid4())
    
    def get_headers(self, token: str, chat_id: Optional[str] = None) -> Dict[str, str]:
        """Generate request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "X-FE-Version": X_FE_VERSION,
            "Authorization": f"Bearer {token}",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/c/{chat_id}" if chat_id else BASE_URL,
        }
        return headers
    
    async def create_chat_session(
        self, 
        token: str, 
        chat_id: str,
        message_id: str,
        message: str,
        model: str
    ) -> str:
        """
        STEP 1: Create chat session to get signature.
        Returns the actual chat_id with embedded signature.
        """
        timestamp = int(time.time())
        
        payload = {
            "chat": {
                "id": "",
                "title": "Claude Code Chat",
                "models": [model],
                "params": {},
                "history": {
                    "messages": {
                        message_id: {
                            "id": message_id,
                            "parentId": None,
                            "childrenIds": [],
                            "role": "user",
                            "content": message,
                            "timestamp": timestamp,
                            "models": [model]
                        }
                    },
                    "currentId": message_id
                },
                "createdAt": timestamp,
                "updatedAt": timestamp
            }
        }
        
        headers = self.get_headers(token, chat_id)
        
        logger.info(f"📝 Creating chat session with model: {model}")
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/v1/chats/new",
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"❌ Chat creation failed ({response.status_code}): {error_text[:200]}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Chat creation failed: {error_text}"
                )
            
            data = response.json()
            actual_chat_id = data.get("id")
            
            if not actual_chat_id:
                raise HTTPException(
                    status_code=500,
                    detail="No chat ID returned from session creation"
                )
            
            logger.info(f"✅ Chat session created: {actual_chat_id}")
            return actual_chat_id
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Chat creation error: {e}")
            raise HTTPException(status_code=500, detail=f"Chat creation failed: {e}")
    
    async def chat_completion(self, request: Dict[str, Any]) -> Response:
        """
        Handle chat completion with TWO-STEP flow:
        1. Create chat session
        2. Send completion request
        """
        try:
            # Extract parameters
            model = request.get("model", "glm-4.5v")
            messages = request.get("messages", [])
            stream = request.get("stream", True)
            
            # Get token
            token = await self.get_token()
            
            # Generate IDs
            chat_id = self.generate_uuid()
            message_id = self.generate_uuid()
            
            # Get last user message
            user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        user_message = content
                    elif isinstance(content, list):
                        for item in content:
                            if item.get("type") == "text":
                                user_message = item.get("text", "")
                                break
                    if user_message:
                        break
            
            if not user_message:
                user_message = "Hello"
            
            # STEP 1: Create chat session
            actual_chat_id = await self.create_chat_session(
                token, chat_id, message_id, user_message, model
            )
            
            # STEP 2: Send completion request with the chat session
            body = {
                "stream": stream,
                "model": model,
                "messages": messages,
                "params": {},
                "features": {
                    "image_generation": False,
                    "web_search": "search" in model.lower(),
                    "auto_web_search": False,
                    "preview_mode": False,
                    "flags": [],
                    "features": [],
                    "enable_thinking": "thinking" in model.lower(),
                },
                "variables": {
                    "{{USER_NAME}}": "Guest",
                    "{{CURRENT_DATETIME}}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
                "chat_id": actual_chat_id,  # Use the actual chat_id from step 1
                "id": self.generate_uuid(),
            }
            
            headers = self.get_headers(token, actual_chat_id)
            
            logger.info(f"📡 Sending completion request with chat_id: {actual_chat_id}")
            
            response = await self.client.post(
                f"{BASE_URL}/api/chat/completions",
                json=body,
                headers=headers,
                timeout=120.0
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"❌ Completion failed ({response.status_code}): {error_text[:200]}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Completion failed: {error_text}"
                )
            
            # Handle streaming response
            if stream:
                async def stream_response():
                    try:
                        content = ""
                        async for line in response.aiter_lines():
                            if not line or not line.startswith("data:"):
                                continue
                            
                            chunk_str = line[5:].strip()
                            if not chunk_str or chunk_str == "[DONE]":
                                # Send final chunk
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
                            
                            try:
                                chunk = json.loads(chunk_str)
                                
                                if chunk.get("type") == "chat:completion":
                                    data = chunk.get("data", {})
                                    delta_content = data.get("delta_content", "")
                                    
                                    if delta_content:
                                        content += delta_content
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
                            
                            except json.JSONDecodeError:
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
                                    "content": f"\n\n[Error: {str(e)}]"
                                },
                                "finish_reason": "stop"
                            }]
                        }
                        yield f"data: {json.dumps(error_chunk)}\n\n"
                        yield "data: [DONE]\n\n"
                
                return StreamingResponse(
                    stream_response(),
                    media_type="text/event-stream"
                )
            else:
                # Non-streaming
                content = ""
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        chunk_str = line[5:].strip()
                        if chunk_str and chunk_str != "[DONE]":
                            try:
                                chunk = json.loads(chunk_str)
                                if chunk.get("type") == "chat:completion":
                                    delta = chunk.get("data", {}).get("delta_content", "")
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


app = FastAPI(title="Z.AI Claude Code Bridge", version="2.0.0")
bridge = None

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """OpenAI-compatible chat completions endpoint."""
    try:
        body = await request.json()
        logger.info(f"📥 Request: model={body.get('model')}")
        return await bridge.chat_completion(body)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "object": "list",
        "data": [
            {"id": "glm-4.5v", "object": "model", "owned_by": "z.ai"},
            {"id": "GLM-4.5", "object": "model", "owned_by": "z.ai"},
            {"id": "GLM-4.6", "object": "model", "owned_by": "z.ai"},
        ]
    }

@app.get("/health")
async def health_check():
    """Health check."""
    return {"status": "ok", "service": "zai-claude-code-bridge", "version": "2.0.0"}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Z.AI Claude Code Bridge")
    parser.add_argument("--port", type=int, default=int(os.getenv("ZAIMCP_PORT", "3456")),
                        help="Server port (default: 3456)")
    parser.add_argument("--host", default=os.getenv("ZAIMCP_HOST", "127.0.0.1"),
                        help="Server host (default: 127.0.0.1)")
    parser.add_argument("--token", default=os.getenv("ZAIMCP_TOKEN"),
                        help="Z.AI token (optional)")
    
    args = parser.parse_args()
    
    global bridge
    bridge = ZAIClaudeCodeBridge(token=args.token)
    
    logger.info("=" * 60)
    logger.info("🚀 Z.AI Claude Code Bridge v2.0 - WORKING VERSION")
    logger.info(f"📡 Listening: http://{args.host}:{args.port}")
    logger.info(f"🔐 Auth: {'Token' if args.token else 'Anonymous'}")
    logger.info(f"📌 Version: {X_FE_VERSION}")
    logger.info("✅ Two-step chat creation implemented")
    logger.info("=" * 60)
    
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()

