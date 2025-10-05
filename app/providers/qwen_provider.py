#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Qwen Provider Adapter with Auto-Authentication
"""

import json
import time
import uuid
import httpx
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from datetime import datetime

from app.providers.base import BaseProvider, ProviderConfig
from app.models.schemas import OpenAIRequest, Message
from app.auth.provider_auth import QwenAuth
from app.utils.logger import get_logger

logger = get_logger()


class QwenProvider(BaseProvider):
    """Qwen Provider with automatic authentication"""
    
    def __init__(self, auth_config: Optional[Dict[str, str]] = None):
        """
        Initialize Qwen provider
        
        Args:
            auth_config: Optional authentication configuration
        """
        config = ProviderConfig(
            name="qwen",
            api_endpoint="https://chat.qwen.ai/api/v1/chat",
            timeout=60,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
                'Origin': 'https://chat.qwen.ai',
                'Referer': 'https://chat.qwen.ai/chat'
            }
        )
        super().__init__(config)
        
        # Authentication
        if auth_config:
            self.auth = QwenAuth(auth_config)
        else:
            self.auth = None
        
        # Base URL
        self.base_url = "https://chat.qwen.ai"
        self.create_chat_url = f"{self.base_url}/api/v1/chat/create"
        
        # Model mapping
        self.model_mapping = {
            "qwen-max": "qwen-max",
            "qwen-max-thinking": "qwen-max",
            "qwen-max-search": "qwen-max",
            "qwen-max-image": "qwen-max",
            "qwen-plus": "qwen-plus",
            "qwen-turbo": "qwen-turbo",
            "qwen-long": "qwen-long",
        }
    
    def get_supported_models(self) -> List[str]:
        """Get supported models list"""
        return list(self.model_mapping.keys())
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with cookies"""
        headers = self.config.headers.copy()
        
        if self.auth:
            # Get fresh cookies
            cookies = await self.auth.get_cookies()
            if cookies:
                # Convert cookies dict to Cookie header string
                cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
                headers["Cookie"] = cookie_str
                logger.debug(f"Added {len(cookies)} cookies to headers")
            
            # Get token if available
            token = await self.auth.get_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    async def create_new_chat(self, model: str, chat_type: str = "t2t") -> Optional[str]:
        """
        Create a new chat session
        
        Args:
            model: Model name
            chat_type: Chat type (t2t, t2i, image_edit, t2v)
            
        Returns:
            Chat ID if successful
        """
        try:
            headers = await self.get_auth_headers()
            
            payload = {
                "model": model,
                "chat_type": chat_type,
                "timestamp": int(time.time() * 1000)
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.create_chat_url,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    chat_id = data.get("chat_id") or data.get("id")
                    logger.debug(f"Created Qwen chat: {chat_id}")
                    return chat_id
                else:
                    logger.error(f"Failed to create chat: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            return None
    
    async def transform_request(self, request: OpenAIRequest) -> Dict[str, Any]:
        """Transform OpenAI request to Qwen format"""
        logger.info(f"🔄 Transforming OpenAI request to Qwen format: {request.model}")
        
        # Determine model and features
        requested_model = request.model or "qwen-max"
        is_thinking = "-thinking" in requested_model.lower()
        is_search = "-search" in requested_model.lower()
        is_image = "-image" in requested_model.lower()
        
        # Get base model
        base_model = self.model_mapping.get(requested_model, "qwen-max")
        
        # Determine chat type
        chat_type = "t2t"  # default
        if is_image:
            chat_type = "t2i"
        
        # Create chat session if needed
        chat_id = await self.create_new_chat(base_model, chat_type)
        
        # Transform messages
        messages = []
        for msg in request.messages:
            if isinstance(msg.content, str):
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, list):
                # Handle multimodal content
                content_text = ""
                files = []
                for part in msg.content:
                    if hasattr(part, 'type') and part.type == 'text':
                        content_text += (part.text or "")
                    elif hasattr(part, 'type') and part.type == 'image_url':
                        if hasattr(part, 'image_url') and part.image_url:
                            files.append({
                                "type": "image",
                                "url": part.image_url.get("url") if isinstance(part.image_url, dict) else part.image_url
                            })
                
                msg_obj = {
                    "role": msg.role,
                    "content": content_text
                }
                if files:
                    msg_obj["files"] = files
                messages.append(msg_obj)
        
        # Build request body
        body = {
            "model": base_model,
            "messages": messages,
            "stream": request.stream if request.stream is not None else True,
            "chat_type": chat_type,
            "timestamp": int(time.time() * 1000)
        }
        
        # Add chat_id if created
        if chat_id:
            body["chat_id"] = chat_id
        
        # Add feature flags
        body["feature_config"] = {
            "thinking_enabled": is_thinking,
            "search_enabled": is_search,
        }
        
        # Add optional parameters
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            body["top_p"] = request.top_p
        
        # Get headers
        headers = await self.get_auth_headers()
        
        return {
            "url": self.config.api_endpoint,
            "headers": headers,
            "body": body,
            "chat_id": chat_id,
            "model": requested_model
        }
    
    async def transform_response(
        self,
        response: Any,
        request: OpenAIRequest,
        transformed: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Transform Qwen response to OpenAI format"""
        
        # For streaming responses, this method won't be called directly
        # Instead, the stream handler will process SSE events
        
        if isinstance(response, httpx.Response):
            try:
                data = response.json()
                
                # Extract content
                content = ""
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                elif "content" in data:
                    content = data["content"]
                elif "text" in data:
                    content = data["text"]
                
                # Create OpenAI response
                chat_id = self.create_chat_id()
                return self.create_openai_response(
                    chat_id=chat_id,
                    model=request.model,
                    content=content,
                    usage={
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                )
                
            except Exception as e:
                logger.error(f"Error transforming response: {e}")
                return self.handle_error(e, "响应转换")
        
        return self.handle_error(Exception("Invalid response type"))
    
    async def chat_completion(
        self,
        request: OpenAIRequest,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Chat completion interface"""
        self.log_request(request)
        
        try:
            # Transform request
            transformed = await self.transform_request(request)
            
            # Handle based on stream mode
            if request.stream:
                return self._create_stream_response(request, transformed)
            else:
                # Non-streaming response
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        transformed["url"],
                        headers=transformed["headers"],
                        json=transformed["body"]
                    )
                    
                    if not response.is_success:
                        error_msg = f"Qwen API error: {response.status_code}"
                        self.log_response(False, error_msg)
                        
                        # Try to re-authenticate if 401/403
                        if response.status_code in [401, 403] and self.auth:
                            logger.info("🔄 Re-authenticating...")
                            await self.auth.get_valid_session(force_refresh=True)
                            # Retry once
                            transformed = await self.transform_request(request)
                            response = await client.post(
                                transformed["url"],
                                headers=transformed["headers"],
                                json=transformed["body"]
                            )
                        
                        if not response.is_success:
                            return self.handle_error(Exception(error_msg))
                    
                    return await self.transform_response(response, request, transformed)
        
        except Exception as e:
            self.log_response(False, str(e))
            return self.handle_error(e, "请求处理")
    
    async def _create_stream_response(
        self,
        request: OpenAIRequest,
        transformed: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Create streaming response"""
        chat_id = self.create_chat_id()
        content_buffer = ""
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    transformed["url"],
                    headers=transformed["headers"],
                    json=transformed["body"]
                ) as response:
                    
                    if response.status_code not in [200, 201]:
                        # Try to re-authenticate if 401/403
                        if response.status_code in [401, 403] and self.auth:
                            logger.info("🔄 Re-authenticating during stream...")
                            await self.auth.get_valid_session(force_refresh=True)
                            transformed = await self.transform_request(request)
                            
                            # Retry stream
                            async with client.stream(
                                "POST",
                                transformed["url"],
                                headers=transformed["headers"],
                                json=transformed["body"]
                            ) as retry_response:
                                async for line in retry_response.aiter_lines():
                                    chunk = await self._process_stream_line(line, chat_id, request.model, content_buffer)
                                    if chunk:
                                        content_buffer += chunk.get("delta", "")
                                        yield await self.format_sse_chunk(chunk)
                        else:
                            error_chunk = self.create_openai_chunk(
                                chat_id, request.model,
                                {"content": f"Error: {response.status_code}"},
                                "stop"
                            )
                            yield await self.format_sse_chunk(error_chunk)
                            yield await self.format_sse_done()
                            return
                    
                    # Process stream
                    async for line in response.aiter_lines():
                        chunk = await self._process_stream_line(line, chat_id, request.model, content_buffer)
                        if chunk:
                            content_buffer += chunk.get("delta", "")
                            yield await self.format_sse_chunk(chunk)
            
            # Send final chunk
            final_chunk = self.create_openai_chunk(chat_id, request.model, {}, "stop")
            yield await self.format_sse_chunk(final_chunk)
            yield await self.format_sse_done()
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_chunk = self.create_openai_chunk(
                chat_id, request.model,
                {"content": f"Error: {str(e)}"},
                "stop"
            )
            yield await self.format_sse_chunk(error_chunk)
            yield await self.format_sse_done()
    
    async def _process_stream_line(
        self,
        line: str,
        chat_id: str,
        model: str,
        content_buffer: str
    ) -> Optional[Dict[str, Any]]:
        """Process a single SSE line"""
        if not line or not line.strip():
            return None
        
        # Remove 'data: ' prefix if present
        if line.startswith("data: "):
            line = line[6:]
        
        # Skip [DONE] marker
        if line.strip() == "[DONE]":
            return None
        
        try:
            data = json.loads(line)
            
            # Extract content delta
            delta_content = ""
            
            # Try different response formats
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "delta" in choice:
                    delta_content = choice["delta"].get("content", "")
                elif "message" in choice:
                    delta_content = choice["message"].get("content", "")
            elif "content" in data:
                delta_content = data["content"]
            elif "text" in data:
                delta_content = data["text"]
            
            if delta_content:
                return self.create_openai_chunk(
                    chat_id, model,
                    {"content": delta_content},
                    None
                )
        
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.debug(f"Error processing stream line: {e}")
        
        return None

