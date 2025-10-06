#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Grok Provider
Implements Grok AI integration with automated authentication
"""

import json
import uuid
import httpx
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Union

from app.providers.base import BaseProvider, ProviderConfig
from app.providers.grok_auth import GrokAuthManager
from app.providers.grok_token_manager import GrokTokenManager
from app.models.schemas import OpenAIRequest, Message
from app.utils.logger import get_logger

logger = get_logger()


class GrokProvider(BaseProvider):
    """Grok AI Provider with automated authentication"""
    
    # Model mapping
    MODELS = {
        "grok-3": "grok-3",
        "grok-4": "grok-4",
        "grok-auto": "grok-auto",
        "grok-fast": "grok-fast",
        "grok-expert": "grok-expert",
        "grok-deepsearch": "grok-deepsearch",
        "grok-image": "grok-image",
    }
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize Grok provider
        
        Args:
            config_data: Configuration dictionary containing email, password, etc.
        """
        config = ProviderConfig(
            name="grok",
            api_endpoint="https://grok.com/rest/app-chat",
            timeout=120
        )
        super().__init__(config)
        
        # Initialize auth manager
        self.auth_manager = GrokAuthManager(
            login_url=config_data.get("loginUrl", "https://accounts.x.ai/sign-in?redirect=grok-com&email=true"),
            chat_url=config_data.get("chatUrl", "https://grok.com/chat"),
            email=config_data["email"],
            password=config_data["password"],
            proxy_url=config_data.get("proxy")
        )
        
        # Initialize token manager
        self.token_manager = GrokTokenManager(self.auth_manager)
        
        self.base_url = "https://grok.com"
        self.api_url = f"{self.base_url}/rest/app-chat/conversations/new"
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported models"""
        return list(self.MODELS.keys())
    
    async def _get_headers(self, credentials: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers with authentication"""
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "text/plain;charset=UTF-8",
            "Connection": "keep-alive",
            "Origin": "https://grok.com",
            "Referer": "https://grok.com/chat",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        
        # Add dynamic headers
        headers["x-statsig-id"] = credentials.get("statsig_id", "")
        headers["x-xai-request-id"] = str(uuid.uuid4())
        
        # Add cookies as Cookie header
        cookies = credentials.get("cookies", [])
        if cookies:
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            headers["Cookie"] = cookie_str
        
        return headers
    
    async def transform_request(self, request: OpenAIRequest) -> Dict[str, Any]:
        """Transform OpenAI request to Grok format"""
        # Build conversation data
        conversation_data = {
            "model": self.MODELS.get(request.model, "grok-3"),
            "messages": []
        }
        
        # Convert messages
        for msg in request.messages:
            if isinstance(msg.content, str):
                conversation_data["messages"].append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, list):
                # Handle multimodal content
                content_parts = []
                for part in msg.content:
                    if hasattr(part, 'type') and hasattr(part, 'text'):
                        content_parts.append(part.text)
                conversation_data["messages"].append({
                    "role": msg.role,
                    "content": " ".join(content_parts)
                })
        
        return conversation_data
    
    async def _parse_sse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse SSE data line"""
        if not line.startswith("data: "):
            return None
        
        data_str = line[6:].strip()
        if data_str == "[DONE]":
            return {"done": True}
        
        try:
            return json.loads(data_str)
        except json.JSONDecodeError:
            return None
    
    async def transform_response(
        self, 
        response: httpx.Response, 
        request: OpenAIRequest
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Transform Grok response to OpenAI format"""
        chat_id = self.create_chat_id()
        model = request.model
        
        if request.stream:
            return self._stream_response(response, chat_id, model)
        else:
            return await self._non_stream_response(response, chat_id, model)
    
    async def _stream_response(
        self,
        response: httpx.Response,
        chat_id: str,
        model: str
    ) -> AsyncGenerator[str, None]:
        """Process streaming response"""
        try:
            buffer = ""
            full_content = ""
            
            async for chunk in response.aiter_text():
                buffer += chunk
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    data = await self._parse_sse_line(line)
                    if not data:
                        continue
                    
                    if data.get("done"):
                        # Send final chunk
                        final_chunk = self.create_stream_chunk(chat_id, model, finish_reason="stop")
                        yield await self.format_sse_chunk(final_chunk)
                        break
                    
                    # Extract content
                    content = ""
                    if "choices" in data:
                        for choice in data["choices"]:
                            delta = choice.get("delta", {})
                            content += delta.get("content", "")
                    elif "content" in data:
                        content = data["content"]
                    
                    if content:
                        full_content += content
                        chunk_data = self.create_stream_chunk(chat_id, model, content)
                        yield await self.format_sse_chunk(chunk_data)
            
            # Send done marker
            yield await self.format_sse_done()
            
            # Record success
            self.token_manager.record_success()
            
        except Exception as e:
            logger.error(f"❌ Stream processing error: {e}")
            self.token_manager.record_failure(e)
            error_chunk = self.create_stream_chunk(chat_id, model, finish_reason="error")
            yield await self.format_sse_chunk(error_chunk)
            yield await self.format_sse_done()
    
    async def _non_stream_response(
        self,
        response: httpx.Response,
        chat_id: str,
        model: str
    ) -> Dict[str, Any]:
        """Process non-streaming response"""
        try:
            response_text = response.text
            
            # Try to parse as JSON
            try:
                data = json.loads(response_text)
                
                # Extract content
                content = ""
                if "choices" in data:
                    for choice in data["choices"]:
                        message = choice.get("message", {})
                        content += message.get("content", "")
                elif "content" in data:
                    content = data["content"]
                else:
                    content = str(data)
                
                # Record success
                self.token_manager.record_success()
                
                return self.create_openai_response(chat_id, model, content)
                
            except json.JSONDecodeError:
                # Treat as plain text
                self.token_manager.record_success()
                return self.create_openai_response(chat_id, model, response_text)
        
        except Exception as e:
            logger.error(f"❌ Response processing error: {e}")
            self.token_manager.record_failure(e)
            raise
    
    async def chat_completion(
        self, 
        request: OpenAIRequest,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """
        Main chat completion method
        
        Args:
            request: OpenAI format request
            **kwargs: Additional parameters
            
        Returns:
            OpenAI format response (streaming or non-streaming)
        """
        self.log_request(request)
        
        try:
            # Get credentials
            credentials = await self.token_manager.get_credentials()
            
            # Get headers
            headers = await self._get_headers(credentials)
            
            # Transform request
            grok_request = await self.transform_request(request)
            
            # Make API request
            async with httpx.AsyncClient(timeout=120.0) as client:
                if request.stream:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json=grok_request,
                        timeout=120.0
                    )
                    response.raise_for_status()
                    return await self.transform_response(response, request)
                else:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json=grok_request,
                        timeout=120.0
                    )
                    response.raise_for_status()
                    return await self.transform_response(response, request)
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"❌ Grok API error: {error_msg}")
            self.token_manager.record_failure(e)
            
            # If unauthorized, try to refresh credentials
            if e.response.status_code in [401, 403]:
                logger.info("🔄 Attempting to refresh credentials...")
                try:
                    await self.token_manager.get_credentials(force_refresh=True)
                    logger.info("✅ Credentials refreshed, please retry")
                except Exception as refresh_error:
                    logger.error(f"❌ Failed to refresh credentials: {refresh_error}")
            
            return self.handle_error(e, "API request")
        
        except Exception as e:
            logger.error(f"❌ Grok provider error: {e}")
            self.token_manager.record_failure(e)
            return self.handle_error(e, "chat completion")
