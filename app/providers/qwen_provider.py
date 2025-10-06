#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Qwen Provider - CONSOLIDATED IMPLEMENTATION
============================================

This is the unified Qwen provider consolidating features from:
- qwen.py: Basic chat completion, model parsing
- qwen_builder.py: Request building, UUID generation
- qwen_provider.py: Main provider, authentication
- qwen_upload.py: File upload via STS tokens

Features:
✅ Text chat (normal, thinking, search modes)
✅ Image generation & editing
✅ Video generation
✅ Deep research
✅ File uploads (image, video, audio, documents)
✅ Multi-modal support
✅ Streaming & non-streaming
✅ Automatic authentication
"""

import json
import time
import httpx
import asyncio
import hashlib
import mimetypes
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
from io import BytesIO

from app.providers.base import BaseProvider, ProviderConfig
from app.models.schemas import OpenAIRequest, Message
from app.auth.provider_auth import QwenAuth
from app.utils.logger import get_logger

logger = get_logger()

@dataclass
class QwenMessage:
    """Qwen-formatted message"""
    role: str
    content: str
    chat_type: str = "text"
    extra: dict = None
    files: list = None
    feature_config: dict = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "role": self.role,
            "content": self.content,
            "chat_type": self.chat_type,
            "extra": self.extra or {}
        }
        
        if self.files is not None:
            result["files"] = self.files
            
        if self.feature_config is not None:
            result["feature_config"] = self.feature_config
            
        return result


class QwenUploader:
    """
    Qwen file upload handler with STS token authentication
    
    Supports:
    - Image files (JPEG, PNG, GIF, WebP, BMP)
    - Video files (MP4, AVI, MOV, WMV, FLV)
    - Audio files (MP3, WAV, AAC, OGG)
    - Documents (PDF, TXT, DOC)
    """
    
    # Configuration constants
    STS_TOKEN_URL = "https://chat.qwen.ai/api/v1/files/getstsToken"
    MAX_RETRIES = 3
    TIMEOUT = 30.0
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    RETRY_DELAY = 1.0  # seconds
    
    # Supported file types (using main types for detection)
    SUPPORTED_TYPES = {
        'image': ['image'],
        'video': ['video'],
        'audio': ['audio'],
        'document': ['application', 'text']
    }
    
    def __init__(self, auth_token: str):
        """
        Initialize uploader with auth token
        
        Args:
            auth_token: Bearer token for Qwen authentication
        """
        self.auth_token = auth_token if auth_token.startswith('Bearer ') else f'Bearer {auth_token}'
        self._upload_cache: Dict[str, Dict[str, str]] = {}  # SHA256 -> file_info cache
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """
        Validate file size is within limits
        
        Args:
            file_size: File size in bytes
            
        Returns:
            True if valid, False otherwise
        """
        return 0 < file_size <= QwenUploader.MAX_FILE_SIZE
    
    @staticmethod
    def get_simple_file_type(mime_type: str) -> str:
        """
        Get simplified file type from MIME type
        
        Args:
            mime_type: Full MIME type (e.g., "image/jpeg")
            
        Returns:
            Simplified type: "image", "video", "audio", "document", or "file"
        """
        if not mime_type:
            return 'file'
        
        main_type = mime_type.split('/')[0].lower()
        
        # Check each category
        for category, types in QwenUploader.SUPPORTED_TYPES.items():
            if main_type in types:
                return category
        
        return 'file'
    
    @staticmethod
    def calculate_file_hash(file_buffer: bytes) -> str:
        """
        Calculate SHA256 hash of file for caching
        
        Args:
            file_buffer: File content bytes
            
        Returns:
            Hex string of SHA256 hash
        """
        return hashlib.sha256(file_buffer).hexdigest()
    
    async def request_sts_token(
        self,
        filename: str,
        filesize: int,
        filetype_simple: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Request STS token from Qwen API with retry mechanism
        
        Args:
            filename: Original filename
            filesize: File size in bytes
            filetype_simple: Simplified file type
            retry_count: Current retry attempt
            
        Returns:
            Dict with 'credentials' and 'file_info'
            
        Raises:
            Exception: If request fails after retries
        """
        try:
            # Validation
            if not filename:
                raise ValueError("Filename cannot be empty")
            
            if not self.validate_file_size(filesize):
                raise ValueError(f"File size exceeds limit of {self.MAX_FILE_SIZE / 1024 / 1024}MB")
            
            # Generate request ID
            import uuid
            request_id = str(uuid.uuid4())
            
            # Build headers
            headers = {
                'Authorization': self.auth_token,
                'Content-Type': 'application/json',
                'x-request-id': request_id,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Build payload
            payload = {
                'filename': filename,
                'filesize': filesize,
                'filetype': filetype_simple
            }
            
            logger.info(f"🎫 Requesting STS token: {filename} ({filesize} bytes, {filetype_simple})")
            
            # Make request
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.post(
                    self.STS_TOKEN_URL,
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    sts_data = response.json()
                    
                    # Extract credentials
                    credentials = {
                        'access_key_id': sts_data.get('access_key_id'),
                        'access_key_secret': sts_data.get('access_key_secret'),
                        'security_token': sts_data.get('security_token')
                    }
                    
                    # Extract file info
                    file_info = {
                        'url': sts_data.get('file_url'),
                        'path': sts_data.get('file_path'),
                        'bucket': sts_data.get('bucketname'),
                        'endpoint': f"{sts_data.get('region')}.aliyuncs.com",
                        'id': sts_data.get('file_id')
                    }
                    
                    # Validate completeness
                    required_creds = ['access_key_id', 'access_key_secret', 'security_token']
                    required_info = ['url', 'path', 'bucket', 'endpoint', 'id']
                    
                    missing_creds = [k for k in required_creds if not credentials.get(k)]
                    missing_info = [k for k in required_info if not file_info.get(k)]
                    
                    if missing_creds or missing_info:
                        missing = missing_creds + missing_info
                        raise ValueError(f"STS response incomplete, missing: {', '.join(missing)}")
                    
                    logger.info("✅ STS token acquired successfully")
                    return {
                        'credentials': credentials,
                        'file_info': file_info
                    }
                else:
                    raise Exception(f"STS token request failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"❌ STS token request failed (retry: {retry_count}): {e}")
            
            # Handle 403 specially
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 403:
                logger.error("403 Forbidden - Token permission issue")
                raise Exception("Authentication failed, check token permissions")
            
            # Retry logic
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (2 ** retry_count)  # Exponential backoff
                logger.warning(f"⏳ Retrying in {delay}s...")
                await asyncio.sleep(delay)
                return await self.request_sts_token(filename, filesize, filetype_simple, retry_count + 1)
            
            raise
    
    async def upload_to_oss(
        self,
        file_buffer: bytes,
        sts_credentials: Dict[str, str],
        oss_info: Dict[str, str],
        content_type: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Upload file to Aliyun OSS using STS credentials
        
        Args:
            file_buffer: File content bytes
            sts_credentials: STS credentials from request_sts_token
            oss_info: OSS information from request_sts_token
            content_type: MIME type
            retry_count: Current retry attempt
            
        Returns:
            Upload result dict
            
        Raises:
            Exception: If upload fails after retries
        """
        try:
            # Validation
            if not file_buffer or not sts_credentials or not oss_info:
                raise ValueError("Missing required upload parameters")
            
            logger.info(f"📤 Uploading to OSS: {oss_info['path']} ({len(file_buffer)} bytes)")
            
            # Build OSS URL
            oss_url = f"https://{oss_info['bucket']}.{oss_info['endpoint']}/{oss_info['path']}"
            
            # Build headers for OSS
            headers = {
                'Content-Type': content_type or 'application/octet-stream',
                'x-oss-security-token': sts_credentials['security_token']
            }
            
            # Build auth header (OSS uses different format)
            from datetime import datetime
            date_str = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # Simple PUT request with STS token
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.put(
                    oss_url,
                    content=file_buffer,
                    headers={
                        **headers,
                        'Date': date_str,
                        'Authorization': f"OSS {sts_credentials['access_key_id']}:{sts_credentials['access_key_secret']}"
                    }
                )
                
                if response.status_code == 200:
                    logger.info("✅ File uploaded to OSS successfully")
                    return {'success': True, 'status': 200}
                else:
                    raise Exception(f"OSS upload failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"❌ OSS upload failed (retry: {retry_count}): {e}")
            
            # Retry logic
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (2 ** retry_count)
                logger.warning(f"⏳ Retrying OSS upload in {delay}s...")
                await asyncio.sleep(delay)
                return await self.upload_to_oss(
                    file_buffer, sts_credentials, oss_info, content_type, retry_count + 1
                )
            
            raise
    
    async def upload_file(
        self,
        file_buffer: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Complete file upload workflow: STS token -> OSS upload
        
        Args:
            file_buffer: File content bytes
            filename: Original filename (e.g., "image.png")
            
        Returns:
            Dict with file_url, file_id, and message
            
        Raises:
            Exception: If any step fails
        """
        try:
            # Validation
            if not file_buffer or not filename:
                raise ValueError("Missing required upload parameters")
            
            # Calculate hash for caching
            file_hash = self.calculate_file_hash(file_buffer)
            
            # Check cache
            if file_hash in self._upload_cache:
                logger.info(f"✨ Using cached upload for {filename}")
                return self._upload_cache[file_hash]
            
            filesize = len(file_buffer)
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            filetype_simple = self.get_simple_file_type(mime_type)
            
            # File size validation
            if not self.validate_file_size(filesize):
                raise ValueError(f"File size exceeds limit of {self.MAX_FILE_SIZE / 1024 / 1024}MB")
            
            logger.info(f"📤 Starting upload: {filename} ({filesize} bytes, {mime_type})")
            
            # Step 1: Get STS token
            sts_result = await self.request_sts_token(filename, filesize, filetype_simple)
            credentials = sts_result['credentials']
            file_info = sts_result['file_info']
            
            # Step 2: Upload to OSS
            await self.upload_to_oss(file_buffer, credentials, file_info, mime_type)
            
            logger.info("✅ File upload workflow complete")
            
            result = {
                'status': 200,
                'file_url': file_info['url'],
                'file_id': file_info['id'],
                'message': 'File uploaded successfully'
            }
            
            # Cache result
            self._upload_cache[file_hash] = result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ File upload workflow failed: {e}")
            raise


async def upload_file_to_qwen_oss(
    file_buffer: bytes,
    filename: str,
    auth_token: str
) -> Dict[str, Any]:
    """
    Convenience function for file upload
    
    Args:
        file_buffer: File content bytes
        filename: Original filename
        auth_token: Qwen authentication token
        
    Returns:
        Dict with file_url, file_id, and message
    """
    uploader = QwenUploader(auth_token)
    return await uploader.upload_file(file_buffer, filename)


class QwenRequestBuilder:
    """
    Builds properly structured Qwen API requests.
    
    Based on qwenchat2api/main.ts reference implementation.
    """
    
    # Size mappings from OpenAI format to Qwen aspect ratios
    SIZE_MAP = {
        "256x256": "1:1",
        "512x512": "1:1",
        "1024x1024": "1:1",
        "1792x1024": "16:9",
        "1024x1792": "9:16",
        "2048x2048": "1:1",
        "1152x768": "3:2",
        "768x1152": "2:3",
    }
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate UUID for session_id or chat_id"""
        return str(uuid.uuid4())
    
    @staticmethod
    def get_timestamp() -> int:
        """Get current timestamp in milliseconds"""
        return int(time.time() * 1000)
    
    @staticmethod
    def determine_chat_type(model: str) -> str:
        """
        Determine chat type from model name.
        
        Args:
            model: Model name (e.g., "qwen-max-image", "qwen-max-thinking")
            
        Returns:
            Chat type: "t2i", "image_edit", "t2v", or "normal"
        """
        if model.endswith('-image'):
            return 't2i'
        elif model.endswith('-image_edit'):
            return 'image_edit'
        elif model.endswith('-video'):
            return 't2v'
        else:
            return 'normal'
    
    @staticmethod
    def clean_model_name(model: str) -> str:
        """
        Remove known suffixes from model name.
        
        Args:
            model: Model with suffix (e.g., "qwen-max-thinking")
            
        Returns:
            Base model name (e.g., "qwen-max")
        """
        # Remove known suffixes
        suffixes = ['-search', '-thinking', '-image', '-image_edit', '-video']
        for suffix in suffixes:
            if model.endswith(suffix):
                return model[:-len(suffix)]
        return model
    
    @staticmethod
    def is_thinking_mode(model: str) -> bool:
        """Check if model is in thinking mode"""
        return '-thinking' in model
    
    @staticmethod
    def is_search_mode(model: str) -> bool:
        """Check if model is in search mode"""
        return '-search' in model
    
    @staticmethod
    def transform_openai_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform OpenAI format messages to Qwen format.
        
        Adds required chat_type and extra fields to each message.
        
        Args:
            messages: OpenAI format messages
            
        Returns:
            Qwen format messages with chat_type and extra
        """
        qwen_messages = []
        
        for msg in messages:
            qwen_msg = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "chat_type": "text",
                "extra": {}
            }
            qwen_messages.append(qwen_msg)
        
        return qwen_messages
    
    @staticmethod
    def map_size_to_aspect_ratio(size: str) -> str:
        """
        Map OpenAI size format to Qwen aspect ratio.
        
        Args:
            size: OpenAI size (e.g., "1024x1024")
            
        Returns:
            Qwen aspect ratio (e.g., "1:1")
        """
        # Check predefined mappings
        if size in QwenRequestBuilder.SIZE_MAP:
            return QwenRequestBuilder.SIZE_MAP[size]
        
        # Calculate aspect ratio for custom sizes
        try:
            width, height = map(int, size.split('x'))
            
            # Calculate GCD for simplification
            def gcd(a: int, b: int) -> int:
                while b:
                    a, b = b, a % b
                return a
            
            divisor = gcd(width, height)
            aspect_ratio = f"{width // divisor}:{height // divisor}"
            
            logger.info(f"Calculated aspect ratio for {size}: {aspect_ratio}")
            return aspect_ratio
        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Invalid size format: {size}, defaulting to 1:1. Error: {e}")
            return "1:1"
    
    @classmethod
    def build_text_chat_request(
        cls,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        Build standard text-to-text chat request.
        
        This is the default request type for normal conversations.
        Includes all required fields: session_id, chat_id, feature_config.
        
        Args:
            model: Model name (e.g., "qwen-max", "qwen-max-thinking")
            messages: OpenAI format messages
            stream: Enable streaming response
            
        Returns:
            Properly structured Qwen API request
        """
        # Clean model name and detect features
        clean_model = cls.clean_model_name(model)
        thinking_enabled = cls.is_thinking_mode(model)
        
        # Transform messages to Qwen format
        qwen_messages = cls.transform_openai_messages(messages)
        
        # Build request with ALL required fields
        request = {
            "model": clean_model,
            "messages": qwen_messages,
            "stream": stream,
            "incremental_output": True,
            "chat_type": "normal",
            "session_id": cls.generate_uuid(),  # CRITICAL: Required UUID
            "chat_id": cls.generate_uuid(),     # CRITICAL: Required UUID
            "feature_config": {
                "output_schema": "phase",
                "thinking_enabled": thinking_enabled
            }
        }
        
        logger.info(
            f"Built text chat request: model={clean_model}, "
            f"thinking={thinking_enabled}, messages={len(qwen_messages)}"
        )
        
        return request
    
    @classmethod
    def build_image_generation_request(
        cls,
        chat_id: str,
        model: str,
        prompt: str,
        size: str = "1024x1024"
    ) -> Dict[str, Any]:
        """
        Build text-to-image generation request.
        
        Note: Requires pre-created chat session. Use create_chat_session() first.
        
        Args:
            chat_id: Chat ID from session creation
            model: Model name
            prompt: Image generation prompt
            size: Image size in OpenAI format (e.g., "1024x1024")
            
        Returns:
            Properly structured image generation request
        """
        clean_model = cls.clean_model_name(model)
        aspect_ratio = cls.map_size_to_aspect_ratio(size)
        
        request = {
            "stream": True,
            "chat_id": chat_id,
            "model": clean_model,
            "size": aspect_ratio,
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
        
        logger.info(
            f"Built image generation request: chat_id={chat_id}, "
            f"model={clean_model}, size={aspect_ratio}"
        )
        
        return request
    
    @classmethod
    def build_image_edit_request(
        cls,
        chat_id: str,
        model: str,
        prompt: str,
        image_url: str
    ) -> Dict[str, Any]:
        """
        Build image editing request.
        
        Note: Requires pre-created chat session with chat_type="image_edit".
        
        Args:
            chat_id: Chat ID from session creation
            model: Model name
            prompt: Editing instructions
            image_url: URL of image to edit
            
        Returns:
            Properly structured image editing request
        """
        clean_model = cls.clean_model_name(model)
        
        request = {
            "stream": True,
            "chat_id": chat_id,
            "model": clean_model,
            "messages": [{
                "role": "user",
                "content": prompt,
                "files": [{
                    "type": "image",
                    "url": image_url
                }],
                "chat_type": "image_edit",
                "feature_config": {
                    "output_schema": "phase"
                }
            }]
        }
        
        logger.info(
            f"Built image edit request: chat_id={chat_id}, "
            f"model={clean_model}, image={image_url[:50]}..."
        )
        
        return request
    
    @classmethod
    def build_chat_session_payload(
        cls,
        model: str,
        chat_type: str = "normal"
    ) -> Dict[str, Any]:
        """
        Build payload for creating new chat session.
        
        Required for image generation and editing workflows.
        
        Args:
            model: Model name
            chat_type: "normal", "t2i", "image_edit", or "t2v"
            
        Returns:
            Chat session creation payload
        """
        clean_model = cls.clean_model_name(model)
        
        payload = {
            "title": "New Chat",
            "models": [clean_model],
            "chat_mode": "normal",
            "chat_type": chat_type,
            "timestamp": cls.get_timestamp()
        }
        
        logger.info(
            f"Built chat session payload: model={clean_model}, "
            f"chat_type={chat_type}"
        )
        
        return payload
    
    @classmethod
    def extract_images_from_messages(
        cls,
        messages: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Extract image URLs from message history.
        
        Looks for:
        - Markdown images in assistant messages: ![alt](url)
        - image_url objects in user messages
        - Direct image fields
        
        Args:
            messages: Conversation messages
            
        Returns:
            List of image URLs (most recent first, max 3)
        """
        import re
        
        images = []
        markdown_regex = re.compile(r'!\[.*?\]\((.*?)\)')
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            # Extract from assistant markdown
            if role == "assistant" and isinstance(content, str):
                matches = markdown_regex.findall(content)
                images.extend(matches)
            
            # Extract from user messages
            elif role == "user":
                if isinstance(content, str):
                    matches = markdown_regex.findall(content)
                    images.extend(matches)
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "image_url":
                                url = item.get("image_url", {}).get("url")
                                if url:
                                    images.append(url)
                            elif item.get("type") == "image" and item.get("image"):
                                images.append(item["image"])
        
        # Return last 3 images (most recent)
        return images[-3:] if images else []


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
            "qwen-plus-latest": "qwen-plus",
            "qwen-turbo": "qwen-turbo",
            "qwen-turbo-latest": "qwen-turbo",
            "qwen-long": "qwen-long",
            # Deep research aliases
            "qwen-deep-research": "qwen-max",
            "qwen-max-deep-research": "qwen-max",
            # Code generation models (qwen3-coder series)
            "qwen3-coder-plus": "qwen-plus",
            "qwen-coder-plus": "qwen-plus",
        }
    
    def get_supported_models(self) -> List[str]:
        """Get supported models list"""
        return list(self.model_mapping.keys())
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers with Bearer token and required headers.
        
        Based on qwenchat2api TypeScript implementation, requires:
        - Authorization: Bearer token (compressed localStorage + cookie)
        - source: web
        - x-request-id: UUID  
        - User-Agent: Chrome
        - Content-Type: application/json
        
        Returns:
            Headers dictionary with all required fields
        """
        import uuid
        
        # Start with base headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Origin": "https://chat.qwen.ai",
            "Referer": "https://chat.qwen.ai/chat",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "source": "web",
            "x-request-id": str(uuid.uuid4())
        }
        
        if self.auth:
            # Get Bearer token (most important!)
            token = await self.auth.get_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
                logger.debug(f"✅ Added Bearer token to headers (length: {len(token)})")
            else:
                logger.warning("⚠️ No Bearer token available - API calls may fail")
            
            # Also add ssxmod_itna cookie if available (from session extra)
            session = await self.auth.get_valid_session()
            if session and "extra" in session:
                ssxmod_itna = session["extra"].get("ssxmod_itna")
                if ssxmod_itna:
                    headers["Cookie"] = f"ssxmod_itna={ssxmod_itna}"
                    logger.debug("✅ Added ssxmod_itna cookie to headers")
        
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
    
    async def chat_completion(
        self,
        request: OpenAIRequest,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """
        Main chat completion endpoint.
        
        Handles both streaming and non-streaming requests.
        
        Args:
            request: OpenAI format request
            **kwargs: Additional parameters
            
        Returns:
            OpenAI formatted response or async generator for streaming
        """
        import httpx
        
        # Transform request
        transformed = await self.transform_request(request)
        
        # Make HTTP request
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            http_response = await client.post(
                transformed["url"],
                json=transformed["body"],
                headers=transformed["headers"]
            )
            
            # Handle streaming
            if request.stream:
                async def stream_generator():
                    async for chunk in self.stream_response(
                        http_response,
                        request,
                        transformed
                    ):
                        yield chunk
                
                return stream_generator()
            
            # Handle non-streaming
            else:
                return await self.transform_response(
                    http_response,
                    request,
                    transformed
                )
    
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
                    content=content
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
    
    def calculate_aspect_ratio(self, size: str) -> str:
        """
        Calculate aspect ratio from size string (e.g., "1024x768" -> "4:3")
        
        Args:
            size: Size string in format "WIDTHxHEIGHT"
            
        Returns:
            Aspect ratio string like "16:9" or "1:1"
        """
        try:
            width, height = map(int, size.split('x'))
            
            # Calculate GCD for simplification
            def gcd(a: int, b: int) -> int:
                while b:
                    a, b = b, a % b
                return a
            
            divisor = gcd(width, height)
            ratio = f"{width//divisor}:{height//divisor}"
            
            logger.debug(f"Calculated aspect ratio for {size}: {ratio}")
            return ratio
            
        except Exception as e:
            logger.error(f"Failed to calculate aspect ratio for '{size}': {e}")
            return "1:1"  # Default fallback
    
    async def generate_image(
        self,
        prompt: str,
        model: str = "qwen-max",
        size: str = "1024x1024",
        n: int = 1
    ) -> Dict[str, Any]:
        """
        Generate image from text prompt (text-to-image)
        
        Args:
            prompt: Text description of desired image
            model: Model name (will strip -image suffix)
            size: Image size like "1024x1024"
            n: Number of images (currently only 1 supported)
            
        Returns:
            OpenAI-compatible response with image URL
        """
        import uuid
        
        try:
            # Clean model name
            base_model = model.replace('-image', '')
            
            # Create chat session for image generation
            chat_id = await self.create_chat_session(base_model, chat_type="t2i")
            if not chat_id:
                raise Exception("Failed to create chat session for image generation")
            
            # Calculate aspect ratio
            aspect_ratio = self.calculate_aspect_ratio(size)
            
            # Build request
            request_body = {
                "model": base_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "chat_type": "t2i",
                        "extra": {},
                        "feature_config": {
                            "output_schema": "phase",
                            "thinking_enabled": False
                        }
                    }
                ],
                "stream": True,
                "incremental_output": True,
                "chat_type": "t2i",
                "session_id": str(uuid.uuid4()),
                "chat_id": chat_id,
                "parent_id": None,
                "chat_mode": "normal",
                "timestamp": int(time.time() * 1000),
                "feature_config": {
                    "output_schema": "phase",
                    "thinking_enabled": False
                },
                "image_gen_config": {
                    "aspect_ratio": aspect_ratio,
                    "size": size
                }
            }
            
            # Get headers
            headers = await self.get_auth_headers()
            
            logger.info(f"Generating image: prompt='{prompt[:50]}...', size={size}")
            
            # Make request
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                    json=request_body,
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise Exception(f"Image generation failed: {response.status_code} - {response.text}")
                
                # Parse streaming response to extract image URL
                image_urls = []
                sent_urls = set()  # Track to prevent duplicates
                
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        
                        if not line or not line.startswith("data:"):
                            continue
                        
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Check for image_gen phase
                            if data.get("type") == "image_gen" or "image_gen" in str(data):
                                # Extract URL from various possible locations
                                url = None
                                
                                if "data" in data:
                                    url = data["data"].get("url") or data["data"].get("content")
                                
                                # Also check markdown format
                                content = data.get("data", {}).get("content", "")
                                if "![" in content and "](" in content:
                                    import re
                                    matches = re.findall(r'!\[.*?\]\((.*?)\)', content)
                                    if matches:
                                        url = matches[0]
                                
                                if url and url not in sent_urls:
                                    image_urls.append(url)
                                    sent_urls.add(url)
                                    logger.info(f"✅ Found image URL: {url}")
                                    
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.debug(f"Error parsing chunk: {e}")
                            continue
                
                if not image_urls:
                    raise Exception("No image URLs found in response")
                
                # Return OpenAI-compatible response
                return {
                    "created": int(time.time()),
                    "data": [
                        {
                            "url": url,
                            "revised_prompt": prompt
                        }
                        for url in image_urls[:n]
                    ]
                }
                
        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise
    
    async def edit_image(
        self,
        image: str,
        prompt: str,
        mask: Optional[str] = None,
        model: str = "qwen-max",
        size: str = "1024x1024",
        n: int = 1
    ) -> Dict[str, Any]:
        """
        Edit image based on text instructions
        
        Args:
            image: Base64 encoded image or URL
            prompt: Edit instructions
            mask: Optional base64 encoded mask
            model: Model name
            size: Image size
            n: Number of images
            
        Returns:
            OpenAI-compatible response with edited image URL
        """
        import uuid
        import base64
        import re
        
        try:
            # Clean model name
            base_model = model.replace('-image_edit', '').replace('-image', '')
            
            # Create chat session for image editing
            chat_id = await self.create_chat_session(base_model, chat_type="image_edit")
            if not chat_id:
                raise Exception("Failed to create chat session for image editing")
            
            # Process image input
            image_url = None
            if image.startswith('http://') or image.startswith('https://'):
                # Direct URL
                image_url = image
            elif image.startswith('data:image'):
                # Data URL - extract base64
                match = re.search(r'data:image/[^;]+;base64,(.+)', image)
                if match:
                    image_data = base64.b64decode(match.group(1))
                    # Upload to OSS
                    from app.providers.qwen_upload import upload_file_to_qwen_oss
                    headers = await self.get_auth_headers()
                    token = headers.get('Authorization', '').replace('Bearer ', '')
                    upload_result = await upload_file_to_qwen_oss(image_data, 'edit_image.png', token)
                    image_url = upload_result['file_url']
                else:
                    raise ValueError("Invalid data URL format")
            else:
                # Assume base64 encoded
                try:
                    image_data = base64.b64decode(image)
                    # Upload to OSS
                    from app.providers.qwen_upload import upload_file_to_qwen_oss
                    headers = await self.get_auth_headers()
                    token = headers.get('Authorization', '').replace('Bearer ', '')
                    upload_result = await upload_file_to_qwen_oss(image_data, 'edit_image.png', token)
                    image_url = upload_result['file_url']
                except Exception as e:
                    raise ValueError(f"Invalid base64 image: {e}")
            
            # Calculate aspect ratio
            aspect_ratio = self.calculate_aspect_ratio(size)
            
            # Build request with image context
            messages = [
                {
                    "role": "user",
                    "content": f"![image]({image_url})\n\n{prompt}",
                    "chat_type": "image_edit",
                    "extra": {},
                    "feature_config": {
                        "output_schema": "phase",
                        "thinking_enabled": False
                    }
                }
            ]
            
            request_body = {
                "model": base_model,
                "messages": messages,
                "stream": True,
                "incremental_output": True,
                "chat_type": "image_edit",
                "session_id": str(uuid.uuid4()),
                "chat_id": chat_id,
                "parent_id": None,
                "chat_mode": "normal",
                "timestamp": int(time.time() * 1000),
                "feature_config": {
                    "output_schema": "phase",
                    "thinking_enabled": False
                },
                "image_gen_config": {
                    "aspect_ratio": aspect_ratio,
                    "size": size
                }
            }
            
            # Get headers
            headers = await self.get_auth_headers()
            
            logger.info(f"Editing image: prompt='{prompt[:50]}...', size={size}")
            
            # Make request
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                    json=request_body,
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise Exception(f"Image editing failed: {response.status_code} - {response.text}")
                
                # Parse streaming response
                image_urls = []
                sent_urls = set()
                
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        
                        if not line or not line.startswith("data:"):
                            continue
                        
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Extract image URL
                            if data.get("type") == "image_gen" or "image_gen" in str(data):
                                url = None
                                
                                if "data" in data:
                                    url = data["data"].get("url") or data["data"].get("content")
                                
                                # Check markdown format
                                content = data.get("data", {}).get("content", "")
                                if "![" in content and "](" in content:
                                    matches = re.findall(r'!\[.*?\]\((.*?)\)', content)
                                    if matches:
                                        url = matches[0]
                                
                                if url and url not in sent_urls:
                                    image_urls.append(url)
                                    sent_urls.add(url)
                                    logger.info(f"✅ Found edited image URL: {url}")
                                    
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.debug(f"Error parsing chunk: {e}")
                            continue
                
                if not image_urls:
                    raise Exception("No image URLs found in response")
                
                # Return OpenAI-compatible response
                return {
                    "created": int(time.time()),
                    "data": [
                        {
                            "url": url,
                            "revised_prompt": prompt
                        }
                        for url in image_urls[:n]
                    ]
                }
                
        except Exception as e:
            logger.error(f"Image editing failed: {e}", exc_info=True)
            raise
    
    async def generate_video(
        self,
        prompt: str,
        model: str = "qwen-max",
        duration: int = 5,
        size: str = "1920x1080"
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt (text-to-video)
        
        Args:
            prompt: Text description of desired video
            model: Model name
            duration: Video duration in seconds
            size: Video resolution
            
        Returns:
            Response with video URL
        """
        import uuid
        
        try:
            # Clean model name
            base_model = model.replace('-video', '')
            
            # Create chat session for video generation
            chat_id = await self.create_chat_session(base_model, chat_type="t2v")
            if not chat_id:
                raise Exception("Failed to create chat session for video generation")
            
            # Calculate aspect ratio
            aspect_ratio = self.calculate_aspect_ratio(size)
            
            # Build request
            request_body = {
                "model": base_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                        "chat_type": "t2v",
                        "extra": {},
                        "feature_config": {
                            "output_schema": "phase",
                            "thinking_enabled": False
                        }
                    }
                ],
                "stream": True,
                "incremental_output": True,
                "chat_type": "t2v",
                "session_id": str(uuid.uuid4()),
                "chat_id": chat_id,
                "parent_id": None,
                "chat_mode": "normal",
                "timestamp": int(time.time() * 1000),
                "feature_config": {
                    "output_schema": "phase",
                    "thinking_enabled": False
                },
                "video_gen_config": {
                    "aspect_ratio": aspect_ratio,
                    "size": size,
                    "duration": duration
                }
            }
            
            # Get headers
            headers = await self.get_auth_headers()
            
            logger.info(f"Generating video: prompt='{prompt[:50]}...', duration={duration}s, size={size}")
            
            # Make request with longer timeout for video
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{self.CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                    json=request_body,
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise Exception(f"Video generation failed: {response.status_code} - {response.text}")
                
                # Parse streaming response
                video_urls = []
                sent_urls = set()
                
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        
                        if not line or not line.startswith("data:"):
                            continue
                        
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Extract video URL
                            if data.get("type") == "video_gen" or "video_gen" in str(data):
                                url = None
                                
                                if "data" in data:
                                    url = data["data"].get("url") or data["data"].get("content")
                                
                                # Check markdown format
                                content = data.get("data", {}).get("content", "")
                                if "[video](" in content or "![" in content:
                                    import re
                                    matches = re.findall(r'!\[.*?\]\((.*?)\)|\[video\]\((.*?)\)', content)
                                    for match in matches:
                                        url = match[0] or match[1]
                                        if url:
                                            break
                                
                                if url and url not in sent_urls:
                                    video_urls.append(url)
                                    sent_urls.add(url)
                                    logger.info(f"✅ Found video URL: {url}")
                                    
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.debug(f"Error parsing chunk: {e}")
                            continue
                
                if not video_urls:
                    raise Exception("No video URLs found in response")
                
                # Return response
                return {
                    "created": int(time.time()),
                    "data": [
                        {
                            "url": url,
                            "prompt": prompt,
                            "duration": duration,
                            "size": size
                        }
                        for url in video_urls
                    ]
                }
                
        except Exception as e:
            logger.error(f"Video generation failed: {e}", exc_info=True)
            raise
    
    def get_supported_models(self) -> list[str]:
        """
        Get expanded list of supported model variants
        
        Returns all base models with their feature suffixes:
        - base model (text chat)
        - -thinking (reasoning mode)
        - -search (web search)
        - -image (text-to-image)
        - -image_edit (image editing)
        - -video (text-to-video)
        - -deep-research (comprehensive research)
        
        Returns:
            List of all model variant names
        """
        base_models = [
            "qwen-max",
            "qwen-plus",
            "qwen-turbo",
            "qwen-long"
        ]
        
        suffixes = [
            "",  # Base model
            "-thinking",
            "-search",
            "-image",
            "-image_edit",
            "-video",
            "-deep-research"
        ]
        
        models = []
        for base in base_models:
            for suffix in suffixes:
                models.append(f"{base}{suffix}")
        
        # Add aliases
        models.extend([
            "qwen-max-latest",
            "qwen-max-0428",
            "qwen-plus-latest",
            "qwen-turbo-latest",
            # Deep research aliases (without base prefix)
            "qwen-deep-research",
            # Code models
            "qwen3-coder-plus",
            "qwen-coder-plus"
        ])
        
        logger.debug(f"Generated {len(models)} model variants")
        return models
    
    async def deep_research(
        self,
        query: str,
        model: str = "qwen-max",
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Perform deep research on a query with citations
        
        Args:
            query: Research question
            model: Model to use
            max_iterations: Maximum research iterations
            
        Returns:
            Research results with citations and sources
        """
        import uuid
        
        try:
            # Clean model name
            base_model = model.replace('-deep-research', '')
            
            # Create chat session for deep research
            chat_id = await self.create_chat_session(base_model, chat_type="deep_research")
            if not chat_id:
                raise Exception("Failed to create chat session for deep research")
            
            # Build request
            request_body = {
                "model": base_model,
                "messages": [
                    {
                        "role": "user",
                        "content": query,
                        "chat_type": "deep_research",
                        "extra": {},
                        "feature_config": {
                            "output_schema": "phase",
                            "thinking_enabled": True,
                            "thinking_budget": 10000
                        }
                    }
                ],
                "stream": True,
                "incremental_output": True,
                "chat_type": "deep_research",
                "session_id": str(uuid.uuid4()),
                "chat_id": chat_id,
                "parent_id": None,
                "chat_mode": "normal",
                "timestamp": int(time.time() * 1000),
                "feature_config": {
                    "output_schema": "phase",
                    "thinking_enabled": True,
                    "thinking_budget": 10000
                },
                "research_config": {
                    "max_iterations": max_iterations,
                    "include_citations": True
                }
            }
            
            # Get headers
            headers = await self.get_auth_headers()
            
            logger.info(f"Starting deep research: '{query[:50]}...' max_iterations={max_iterations}")
            
            # Make request with extended timeout
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{self.CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                    json=request_body,
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise Exception(f"Deep research failed: {response.status_code} - {response.text}")
                
                # Parse streaming response
                research_content = []
                citations = []
                thinking_content = []
                
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        
                        if not line or not line.startswith("data:"):
                            continue
                        
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Extract different content types
                            phase_type = data.get("type", "")
                            content = data.get("data", {}).get("content", "")
                            
                            if phase_type == "thinking":
                                # Thinking/reasoning phase
                                if content:
                                    thinking_content.append(content)
                            elif phase_type == "research" or phase_type == "answer":
                                # Main research content
                                if content:
                                    research_content.append(content)
                            
                            # Extract citations
                            if "citation" in data or "[citation:" in content:
                                import re
                                citation_matches = re.findall(r'\[citation:([^\]]+)\]', content)
                                for citation in citation_matches:
                                    if citation not in citations:
                                        citations.append(citation)
                                        logger.debug(f"Found citation: {citation}")
                            
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.debug(f"Error parsing chunk: {e}")
                            continue
                
                if not research_content:
                    raise Exception("No research content found in response")
                
                # Return structured research results
                return {
                    "created": int(time.time()),
                    "query": query,
                    "answer": "".join(research_content),
                    "thinking": "".join(thinking_content) if thinking_content else None,
                    "citations": citations,
                    "iterations": max_iterations,
                    "chat_id": chat_id
                }
                
        except Exception as e:
            logger.error(f"Deep research failed: {e}", exc_info=True)
            raise
