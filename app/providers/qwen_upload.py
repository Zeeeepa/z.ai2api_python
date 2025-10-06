#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Qwen File Upload Module
Handles file uploads to Qwen's OSS (Object Storage Service) using STS tokens
"""

import asyncio
import hashlib
import mimetypes
from typing import Dict, Any, Optional, Tuple
import httpx
from io import BytesIO

from app.utils.logger import get_logger

logger = get_logger()


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
