"""
Qwen API Request Builder
=========================

This module builds properly structured requests for the Qwen Chat API.
All structures are based on the reference TypeScript implementation (qwenchat2api).

Critical Requirements:
- session_id (UUID) - required for all text requests
- chat_id (UUID) - required for all requests
- Messages must include chat_type and extra fields
- Feature config must use correct structure
- Image generation requires pre-created chat session
"""

import uuid
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


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


def build_qwen_request(
    model: str,
    messages: List[Dict[str, Any]],
    stream: bool = True,
    **kwargs
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Main entry point: Build appropriate Qwen request based on model type.
    
    This function automatically detects the request type from the model name
    and builds the appropriate request structure.
    
    Args:
        model: Model name (with or without suffixes)
        messages: OpenAI format messages
        stream: Enable streaming
        **kwargs: Additional parameters (size, image_url, etc.)
        
    Returns:
        Tuple of (request_dict, chat_id_or_none)
        - For text chat: (request, None)
        - For image generation: (request, chat_id) - chat_id needed externally
    """
    builder = QwenRequestBuilder()
    chat_type = builder.determine_chat_type(model)
    
    # Text-to-text (default)
    if chat_type == "normal":
        request = builder.build_text_chat_request(model, messages, stream)
        return request, None
    
    # Image generation
    elif chat_type == "t2i":
        # Note: Caller must create chat session first
        # This returns structure for use AFTER session creation
        prompt = messages[-1].get("content", "") if messages else ""
        size = kwargs.get("size", "1024x1024")
        
        # Return template - caller provides chat_id
        logger.warning(
            "Image generation requires chat session. "
            "Caller must create session and provide chat_id."
        )
        return {
            "type": "t2i_template",
            "prompt": prompt,
            "size": size,
            "model": model
        }, "REQUIRES_SESSION_CREATION"
    
    # Image editing
    elif chat_type == "image_edit":
        # Similar to t2i - requires session
        prompt = messages[-1].get("content", "") if messages else ""
        image_url = kwargs.get("image_url")
        
        logger.warning(
            "Image editing requires chat session. "
            "Caller must create session and provide chat_id."
        )
        return {
            "type": "image_edit_template",
            "prompt": prompt,
            "image_url": image_url,
            "model": model
        }, "REQUIRES_SESSION_CREATION"
    
    # Video generation (future)
    elif chat_type == "t2v":
        logger.error(f"Video generation not yet implemented for model: {model}")
        raise NotImplementedError("Video generation (t2v) not yet supported")
    
    else:
        logger.error(f"Unknown chat type: {chat_type} for model: {model}")
        raise ValueError(f"Unknown chat type: {chat_type}")

