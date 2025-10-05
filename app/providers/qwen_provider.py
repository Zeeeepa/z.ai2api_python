#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Qwen Provider - FIXED Implementation
=====================================

This provider now uses the correct request structure based on the qwenchat2api
TypeScript reference implementation.

ALL 9 CRITICAL ISSUES FIXED:
1. ✅ session_id (UUID) - now included
2. ✅ chat_id (UUID) - now included
3. ✅ parent_id: null - now included
4. ✅ chat_mode: "normal" - now included
5. ✅ timestamp - now included
6. ✅ Message chat_type - now included
7. ✅ Message extra: {} - now included
8. ✅ thinking_budget - correct structure in feature_config
9. ✅ feature_config - proper structure with output_schema
"""

import json
import time
import httpx
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from datetime import datetime

from app.providers.base import BaseProvider, ProviderConfig
from app.providers.qwen_builder import QwenRequestBuilder, build_qwen_request
from app.models.schemas import OpenAIRequest, Message
from app.auth.provider_auth import QwenAuth
from app.utils.logger import get_logger

logger = get_logger()


class QwenProvider(BaseProvider):
    """
    Qwen Provider with automatic authentication and CORRECT request structure.
    
    Now uses QwenRequestBuilder to ensure all required fields are present.
    """
    
    # Correct API endpoints (from reference implementation)
    BASE_URL = "https://chat.qwen.ai"
    CHAT_COMPLETIONS_URL = f"{BASE_URL}/api/v2/chat/completions"
    NEW_CHAT_URL = f"{BASE_URL}/api/v2/chats/new"
    MODELS_URL = f"{BASE_URL}/api/models"
    
    def __init__(self, auth_config: Optional[Dict[str, str]] = None):
        """
        Initialize Qwen provider
        
        Args:
            auth_config: Optional authentication configuration with email/password
        """
        config = ProviderConfig(
            name="qwen",
            api_endpoint=self.CHAT_COMPLETIONS_URL,  # Correct v2 endpoint
            timeout=60,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
                'Origin': self.BASE_URL,
                'Referer': f'{self.BASE_URL}/chat'
            }
        )
        super().__init__(config)
        
        # Authentication
        if auth_config:
            self.auth = QwenAuth(auth_config)
        else:
            self.auth = None
        
        # Request builder
        self.builder = QwenRequestBuilder()
        
        # Model mapping for backward compatibility
        self.model_mapping = {
            "qwen-max": "qwen-max",
            "qwen-max-latest": "qwen-max",
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
        """
        Get authentication headers with cookies and token.
        
        Returns:
            Headers dictionary with Authorization and Cookie
        """
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
                logger.debug("Added Bearer token to headers")
        
        return headers
    
    async def create_chat_session(
        self,
        model: str,
        chat_type: str = "t2i"
    ) -> Optional[str]:
        """
        Create a new chat session (required for image generation/editing).
        
        Args:
            model: Model name (will be cleaned of suffixes)
            chat_type: "t2i", "image_edit", "t2v", or "normal"
            
        Returns:
            Chat ID if successful, None otherwise
        """
        try:
            headers = await self.get_auth_headers()
            
            # Build session payload using builder
            payload = self.builder.build_chat_session_payload(model, chat_type)
            
            logger.info(f"Creating Qwen chat session: model={model}, chat_type={chat_type}")
            logger.debug(f"Session payload: {json.dumps(payload, indent=2)}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.NEW_CHAT_URL,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    chat_id = data.get("data", {}).get("id")
                    
                    if chat_id:
                        logger.info(f"✅ Created Qwen chat session: {chat_id}")
                        return chat_id
                    else:
                        logger.error(f"No chat ID in response: {data}")
                        return None
                else:
                    error_text = response.text
                    logger.error(
                        f"Failed to create chat session: "
                        f"status={response.status_code}, error={error_text}"
                    )
                    return None
                    
        except Exception as e:
            logger.error(f"Exception creating chat session: {e}", exc_info=True)
            return None
    
    async def transform_request(self, request: OpenAIRequest) -> Dict[str, Any]:
        """
        Transform OpenAI request to Qwen format using the builder.
        
        This method now uses QwenRequestBuilder which includes ALL required fields:
        - session_id (UUID)
        - chat_id (UUID)
        - Messages with chat_type and extra
        - Proper feature_config structure
        - And more...
        
        Args:
            request: OpenAI format request
            
        Returns:
            Dictionary with url, headers, body, and metadata
        """
        logger.info(f"🔄 Transforming request for model: {request.model}")
        
        # Determine request type from model
        chat_type = self.builder.determine_chat_type(request.model)
        logger.debug(f"Detected chat type: {chat_type}")
        
        # Convert OpenAI messages to list of dicts
        messages_list = []
        for msg in request.messages:
            msg_dict = {"role": msg.role}
            
            if isinstance(msg.content, str):
                msg_dict["content"] = msg.content
            elif isinstance(msg.content, list):
                # Handle multimodal content
                # For now, extract text and images
                text_parts = []
                image_urls = []
                
                for part in msg.content:
                    if hasattr(part, 'type'):
                        if part.type == 'text':
                            text_parts.append(part.text or "")
                        elif part.type == 'image_url':
                            if hasattr(part, 'image_url'):
                                url = (part.image_url.get("url") 
                                      if isinstance(part.image_url, dict) 
                                      else part.image_url)
                                if url:
                                    image_urls.append(url)
                
                msg_dict["content"] = " ".join(text_parts)
                if image_urls:
                    msg_dict["_image_urls"] = image_urls  # Store for later
            
            messages_list.append(msg_dict)
        
        # Handle different request types
        if chat_type in ["t2i", "image_edit"]:
            # Image generation/editing requires chat session
            logger.info(f"Creating chat session for {chat_type}")
            chat_id = await self.create_chat_session(request.model, chat_type)
            
            if not chat_id:
                raise ValueError(f"Failed to create chat session for {chat_type}")
            
            if chat_type == "t2i":
                # Build image generation request
                prompt = messages_list[-1].get("content", "") if messages_list else ""
                size = getattr(request, 'size', '1024x1024')  # OpenAI format
                
                body = self.builder.build_image_generation_request(
                    chat_id=chat_id,
                    model=request.model,
                    prompt=prompt,
                    size=size
                )
            else:
                # Build image edit request
                prompt = messages_list[-1].get("content", "") if messages_list else ""
                
                # Extract image URL from messages
                image_url = None
                for msg in messages_list:
                    if "_image_urls" in msg and msg["_image_urls"]:
                        image_url = msg["_image_urls"][0]
                        break
                
                if not image_url:
                    raise ValueError("No image URL found for image editing")
                
                body = self.builder.build_image_edit_request(
                    chat_id=chat_id,
                    model=request.model,
                    prompt=prompt,
                    image_url=image_url
                )
        else:
            # Standard text-to-text chat
            body = self.builder.build_text_chat_request(
                model=request.model,
                messages=messages_list,
                stream=request.stream if request.stream is not None else True
            )
            
            # Add optional OpenAI parameters if provided
            if request.temperature is not None:
                body["temperature"] = request.temperature
            if request.max_tokens is not None:
                body["max_tokens"] = request.max_tokens
            if request.top_p is not None:
                body["top_p"] = request.top_p
        
        # Log the complete request body for debugging
        logger.debug(f"📦 Complete Qwen request body:\n{json.dumps(body, indent=2)}")
        
        # Verify all critical fields are present
        if chat_type == "normal":
            assert "session_id" in body, "❌ Missing session_id"
            assert "chat_id" in body, "❌ Missing chat_id"
            assert "feature_config" in body, "❌ Missing feature_config"
            
            for msg in body["messages"]:
                assert "chat_type" in msg, "❌ Missing chat_type in message"
                assert "extra" in msg, "❌ Missing extra in message"
            
            logger.info("✅ All critical fields present in request")
        
        # Get auth headers
        headers = await self.get_auth_headers()
        
        return {
            "url": self.CHAT_COMPLETIONS_URL,
            "headers": headers,
            "body": body,
            "model": request.model,
            "chat_type": chat_type
        }
    
    async def transform_response(
        self,
        response: Any,
        request: OpenAIRequest,
        transformed: Optional[Dict[str, Any]] = None
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """
        Transform Qwen response to OpenAI format.
        
        Args:
            response: Qwen API response
            request: Original OpenAI request
            transformed: Transformed request data
            
        Returns:
            OpenAI formatted response or async generator for streaming
        """
        
        if isinstance(response, httpx.Response):
            try:
                data = response.json()
                
                # Extract content from various possible locations
                content = ""
                reasoning_content = ""
                
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    message = choice.get("message", {})
                    content = message.get("content", "")
                    reasoning_content = message.get("reasoning_content", "")
                elif "content" in data:
                    content = data["content"]
                elif "text" in data:
                    content = data["text"]
                elif "data" in data:
                    # Check for image URL in data
                    if isinstance(data["data"], dict):
                        content = data["data"].get("url") or data["data"].get("content", "")
                
                # Create OpenAI compatible response
                chat_id = self.create_chat_id()
                openai_response = self.create_openai_response(
                    chat_id=chat_id,
                    model=request.model,
                    content=content,
                    finish_reason="stop"
                )
                
                # Add reasoning content if present (thinking mode)
                if reasoning_content:
                    openai_response["choices"][0]["message"]["reasoning_content"] = reasoning_content
                
                return openai_response
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                raise
            except Exception as e:
                logger.error(f"Error transforming response: {e}", exc_info=True)
                raise
        
        # If response is a stream, return as-is (handled by base class)
        return response
    
    async def stream_response(
        self,
        response: httpx.Response,
        request: OpenAIRequest,
        transformed: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream Qwen SSE response and convert to OpenAI format.
        
        Handles Qwen's streaming response format and converts to OpenAI SSE format.
        
        Args:
            response: Streaming HTTP response
            request: Original request
            transformed: Transformed request metadata
            
        Yields:
            OpenAI formatted SSE chunks
        """
        chat_id = self.create_chat_id()
        buffer = ""
        
        try:
            async for chunk in response.aiter_text():
                buffer += chunk
                
                # Process complete lines
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    # Skip non-data lines
                    if not line.startswith("data:"):
                        continue
                    
                    # Extract data
                    data_str = line[5:].strip()
                    
                    # Check for [DONE]
                    if data_str == "[DONE]":
                        # Send final done chunk
                        yield "data: [DONE]\n\n"
                        break
                    
                    try:
                        data = json.loads(data_str)
                        
                        # Check for errors
                        if data.get("success") is False:
                            error_msg = data.get("data", {}).get("details", "Unknown error")
                            logger.error(f"Qwen API error: {error_msg}")
                            
                            # Send error as content
                            error_chunk = self.create_stream_chunk(
                                chat_id=chat_id,
                                model=request.model,
                                content=f"Error: {error_msg}",
                                finish_reason="stop"
                            )
                            yield f"data: {json.dumps(error_chunk)}\n\n"
                            yield "data: [DONE]\n\n"
                            break
                        
                        # Extract delta content
                        delta_content = None
                        finish_reason = None
                        
                        if "choices" in data:
                            choices = data["choices"]
                            if choices and len(choices) > 0:
                                delta = choices[0].get("delta", {})
                                delta_content = delta.get("content")
                                finish_reason = choices[0].get("finish_reason")
                        
                        # Send chunk if there's content
                        if delta_content is not None:
                            chunk_data = self.create_stream_chunk(
                                chat_id=chat_id,
                                model=request.model,
                                content=delta_content,
                                finish_reason=finish_reason
                            )
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                        
                        # Check if done
                        if finish_reason:
                            yield "data: [DONE]\n\n"
                            break
                            
                    except json.JSONDecodeError:
                        # Skip malformed JSON
                        logger.warning(f"Skipping malformed JSON: {data_str[:100]}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing chunk: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error in stream_response: {e}", exc_info=True)
            # Send error chunk
            error_chunk = self.create_stream_chunk(
                chat_id=chat_id,
                model=request.model,
                content=f"Stream error: {str(e)}",
                finish_reason="stop"
            )
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"

