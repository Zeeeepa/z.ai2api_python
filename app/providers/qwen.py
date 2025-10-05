"""
Qwen Provider - Complete OpenAI-compatible implementation
Supports: text chat, thinking mode, search, image generation, image editing
"""

import hashlib
import json
from typing import Any, AsyncIterator, Dict, Optional

import httpx
from loguru import logger

from app.utils.token_utils import decompress_token, parse_credentials


class QwenProvider:
    """
    Qwen provider with full feature support
    """
    
    def __init__(self):
        self.name = "qwen"
        self.base_url = "https://chat.qwen.ai"
        self.api_base = f"{self.base_url}/api/v2"
        self.chat_url = f"{self.api_base}/chat/completions"
        self.new_chat_url = f"{self.api_base}/chats/new"
        self.models_url = f"{self.base_url}/api/models"
        
        # Supported models
        self.models = [
            'qwen-max',
            'qwen-max-latest', 
            'qwen-plus',
            'qwen-turbo',
            'qwen-long',
            'qwen3-coder-plus',
            'qwen-deep-research'
        ]
        
        logger.info("🔧 Initialized Qwen Provider")
    
    def parse_model_name(self, model: str) -> Dict[str, Any]:
        """
        Parse model name to extract base model and mode
        
        Examples:
            qwen-max -> {base: qwen-max, chat_type: t2t, thinking: False}
            qwen-max-thinking -> {base: qwen-max, chat_type: t2t, thinking: True}
            qwen-max-search -> {base: qwen-max, chat_type: search, thinking: False}
            qwen-max-image -> {base: qwen-max, chat_type: t2i, thinking: False}
        """
        thinking = '-thinking' in model
        search = '-search' in model
        image_edit = '-image_edit' in model
        image = '-image' in model and not image_edit
        video = '-video' in model
        
        # Determine chat type
        if video:
            chat_type = 't2v'
        elif image_edit:
            chat_type = 'image_edit'
        elif image:
            chat_type = 't2i'
        elif search:
            chat_type = 'search'
        elif 'deep-research' in model:
            chat_type = 'deep_research'
        else:
            chat_type = 't2t'
        
        # Remove suffixes for base model
        base_model = model
        for suffix in ['-thinking', '-search', '-image_edit', '-image', '-video']:
            base_model = base_model.replace(suffix, '')
        
        return {
            'base_model': base_model,
            'thinking': thinking,
            'search': search,
            'image': image,
            'image_edit': image_edit,
            'video': video,
            'chat_type': chat_type
        }
    
    async def get_auth_headers(
        self, 
        compressed_token: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get authentication headers from compressed token or session
        
        Args:
            compressed_token: Optional compressed Qwen token
            
        Returns:
            Dict with Authorization and Cookie headers
        """
        # If compressed token provided, decompress it
        if compressed_token:
            try:
                credentials = decompress_token(compressed_token)
                parsed = parse_credentials(credentials)
                
                if not parsed:
                    raise ValueError("Invalid token format")
                
                headers = {
                    'Authorization': f'Bearer {parsed["qwen_token"]}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                    'source': 'web'
                }
                
                if parsed.get('ssxmod_itna'):
                    headers['Cookie'] = f'ssxmod_itna={parsed["ssxmod_itna"]}'
                
                return headers
                
            except Exception as e:
                logger.error(f"❌ Token decompression error: {e}")
                raise
        
        # Otherwise, try to get from session store
        from app.auth.session_store import SessionStore
        session_store = SessionStore('qwen')
        session = session_store.load_session()
        
        if not session:
            raise ValueError(
                "No valid session found. Please provide compressed token."
            )
        
        headers = {
            'Authorization': f'Bearer {session.get("token", "")}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'source': 'web'
        }
        
        # Add cookies if available
        if session.get('cookies'):
            cookie_str = '; '.join(
                f'{k}={v}' for k, v in session['cookies'].items()
            )
            headers['Cookie'] = cookie_str
        
        return headers
    
    async def create_chat_session(
        self,
        model: str,
        chat_type: str,
        headers: Dict[str, str]
    ) -> Optional[str]:
        """
        Create new chat session for image/video generation
        
        Returns:
            Chat ID or None if failed
        """
        try:
            logger.info(f"📝 Creating chat session: {chat_type}")
            
            payload = {
                "title": "New Chat",
                "models": [model],
                "chat_mode": "normal",
                "chat_type": chat_type,
                "timestamp": 0
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.new_chat_url,
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    chat_id = data.get('data', {}).get('id')
                    if chat_id:
                        logger.success(f"✅ Chat session: {chat_id}")
                        return chat_id
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Chat session error: {e}")
            return None
    
    def calculate_aspect_ratio(self, size: str) -> str:
        """Calculate aspect ratio from size string like 1024x1024"""
        try:
            width, height = map(int, size.split('x'))
            
            def gcd(a, b):
                while b:
                    a, b = b, a % b
                return a
            
            divisor = gcd(width, height)
            return f"{width//divisor}:{height//divisor}"
            
        except Exception:
            return "1:1"
    
    async def transform_image_gen_request(
        self,
        request: Dict[str, Any],
        model_info: Dict[str, str],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Transform OpenAI image generation to Qwen format"""
        
        # Create chat session
        chat_id = await self.create_chat_session(
            model_info['base_model'],
            't2i',
            headers
        )
        
        if not chat_id:
            raise Exception("Failed to create chat session")
        
        # Size mapping
        size = request.get('size', '1024x1024')
        size_map = {
            "256x256": "1:1",
            "512x512": "1:1",
            "1024x1024": "1:1",
            "1792x1024": "16:9",
            "1024x1792": "9:16",
            "2048x2048": "1:1",
            "1152x768": "3:2",
            "768x1152": "2:3"
        }
        qwen_size = size_map.get(size, self.calculate_aspect_ratio(size))
        
        # Extract prompt
        messages = request.get('messages', [])
        prompt = ""
        
        if messages:
            last_user = next(
                (m for m in reversed(messages) if m.get('role') == 'user'),
                None
            )
            if last_user:
                content = last_user.get('content')
                if isinstance(content, str):
                    prompt = content
                elif isinstance(content, list):
                    for item in content:
                        if item.get('type') == 'text':
                            prompt += item.get('text', '')
        
        return {
            "stream": True,
            "chat_id": chat_id,
            "model": model_info['base_model'],
            "size": qwen_size,
            "messages": [{
                "role": "user",
                "content": prompt or "Generate an image",
                "files": [],
                "chat_type": "t2i",
                "feature_config": {
                    "output_schema": "phase"
                }
            }]
        }
    
    async def transform_request(
        self,
        request: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Transform OpenAI format to Qwen format
        """
        model = request.get('model', 'qwen-max')
        model_info = self.parse_model_name(model)
        
        logger.info(
            f"🔄 Transform: {model} -> {model_info['chat_type']}"
        )
        
        # Image generation
        if model_info['image']:
            return await self.transform_image_gen_request(
                request, model_info, headers
            )
        
        # Text chat (default)
        messages = request.get('messages', [])
        
        # Build thinking config
        thinking_config = {
            "output_schema": "phase",
            "thinking_enabled": model_info['thinking'],
            "thinking_budget": 81920
        }
        
        if request.get('thinking_budget'):
            thinking_config['thinking_budget'] = min(
                int(request['thinking_budget']), 38912
            )
        
        # Generate IDs
        import time
        timestamp = str(time.time()).encode()
        session_id = hashlib.sha256(timestamp).hexdigest()[:32]
        chat_id = hashlib.sha256(timestamp + b'chat').hexdigest()[:32]
        
        return {
            "model": model_info['base_model'],
            "messages": messages,
            "stream": True,
            "incremental_output": True,
            "chat_type": model_info['chat_type'],
            "session_id": session_id,
            "chat_id": chat_id,
            "feature_config": thinking_config
        }
    
    async def stream_response(
        self,
        request: Dict[str, Any],
        headers: Dict[str, str]
    ) -> AsyncIterator[str]:
        """
        Stream chat response in OpenAI format
        """
        try:
            # Transform request
            qwen_request = await self.transform_request(request, headers)
            
            logger.info("📡 Streaming from Qwen API")
            logger.debug(f"Request: {json.dumps(qwen_request, indent=2)}")
            
            sent_image_urls = set()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    'POST',
                    self.chat_url,
                    headers=headers,
                    json=qwen_request
                ) as response:
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"❌ Qwen API error: {response.status_code}")
                        raise Exception(f"API error: {error_text.decode()}")
                    
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        
                        # Process complete lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            
                            if not line or line == 'data: [DONE]':
                                continue
                            
                            if line.startswith('data: '):
                                line = line[6:]
                            
                            try:
                                data = json.loads(line)
                                
                                # Extract content
                                content = ""
                                finish_reason = None
                                
                                if 'choices' in data and data['choices']:
                                    choice = data['choices'][0]
                                    delta = choice.get('delta') or choice.get(
                                        'message'
                                    )
                                    
                                    if delta:
                                        content = delta.get('content', '')
                                        
                                        # Handle image URLs
                                        if delta.get('phase') == 'image_gen':
                                            if (content and 
                                                content.startswith('https://')):
                                                if content not in sent_image_urls:
                                                    sent_image_urls.add(content)
                                                    content = f"![Image]({content})"
                                                else:
                                                    content = ""
                                        
                                        finish_reason = choice.get('finish_reason')
                                
                                # Send chunk if there's content
                                if content or finish_reason:
                                    chunk_id = hashlib.md5(
                                        str(id(chunk)).encode()
                                    ).hexdigest()[:8]
                                    
                                    chunk_data = {
                                        "id": f"chatcmpl-{chunk_id}",
                                        "object": "chat.completion.chunk",
                                        "created": 0,
                                        "model": request.get('model', 'qwen-max'),
                                        "choices": [{
                                            "index": 0,
                                            "delta": {
                                                "content": content
                                            } if content else {},
                                            "finish_reason": finish_reason
                                        }]
                                    }
                                    
                                    yield f"data: {json.dumps(chunk_data)}\n\n"
                                
                            except json.JSONDecodeError:
                                continue
                    
                    yield "data: [DONE]\n\n"
                    
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
            error_chunk = {
                "id": "error",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": request.get('model', 'qwen-max'),
                "choices": [{
                    "index": 0,
                    "delta": {"content": f"Error: {str(e)}"},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
    
    async def chat_completion(
        self,
        request: Dict[str, Any],
        compressed_token: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Main chat completion endpoint
        
        Args:
            request: OpenAI format request
            compressed_token: Optional compressed Qwen token
            
        Yields:
            SSE formatted response chunks
        """
        # Get auth headers
        headers = await self.get_auth_headers(compressed_token)
        
        # Stream response
        async for chunk in self.stream_response(request, headers):
            yield chunk
