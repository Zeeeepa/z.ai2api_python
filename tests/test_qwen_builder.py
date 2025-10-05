"""
Unit tests for Qwen Request Builder
====================================

Tests all critical fields and structures required by Qwen API.
"""

import pytest
import uuid
from app.providers.qwen_builder import (
    QwenRequestBuilder,
    build_qwen_request,
    QwenMessage
)


class TestQwenMessage:
    """Test QwenMessage dataclass"""
    
    def test_basic_message_structure(self):
        """Test basic message has all required fields"""
        msg = QwenMessage(
            role="user",
            content="Hello"
        )
        
        result = msg.to_dict()
        
        assert result["role"] == "user"
        assert result["content"] == "Hello"
        assert result["chat_type"] == "text"
        assert result["extra"] == {}
    
    def test_message_with_files(self):
        """Test message with files array"""
        msg = QwenMessage(
            role="user",
            content="Edit this image",
            chat_type="image_edit",
            files=[{"type": "image", "url": "https://example.com/img.jpg"}]
        )
        
        result = msg.to_dict()
        
        assert "files" in result
        assert len(result["files"]) == 1
        assert result["files"][0]["url"] == "https://example.com/img.jpg"


class TestQwenRequestBuilder:
    """Test QwenRequestBuilder class"""
    
    def test_generate_uuid(self):
        """Test UUID generation"""
        uuid1 = QwenRequestBuilder.generate_uuid()
        uuid2 = QwenRequestBuilder.generate_uuid()
        
        # Should be valid UUIDs
        assert isinstance(uuid.UUID(uuid1), uuid.UUID)
        assert isinstance(uuid.UUID(uuid2), uuid.UUID)
        
        # Should be unique
        assert uuid1 != uuid2
    
    def test_get_timestamp(self):
        """Test timestamp generation"""
        ts = QwenRequestBuilder.get_timestamp()
        
        assert isinstance(ts, int)
        assert ts > 1700000000000  # After 2023
    
    def test_determine_chat_type(self):
        """Test chat type detection from model name"""
        assert QwenRequestBuilder.determine_chat_type("qwen-max") == "normal"
        assert QwenRequestBuilder.determine_chat_type("qwen-max-thinking") == "normal"
        assert QwenRequestBuilder.determine_chat_type("qwen-max-search") == "normal"
        assert QwenRequestBuilder.determine_chat_type("qwen-max-image") == "t2i"
        assert QwenRequestBuilder.determine_chat_type("qwen-max-image_edit") == "image_edit"
        assert QwenRequestBuilder.determine_chat_type("qwen-max-video") == "t2v"
    
    def test_clean_model_name(self):
        """Test model name cleaning"""
        assert QwenRequestBuilder.clean_model_name("qwen-max") == "qwen-max"
        assert QwenRequestBuilder.clean_model_name("qwen-max-thinking") == "qwen-max"
        assert QwenRequestBuilder.clean_model_name("qwen-max-search") == "qwen-max"
        assert QwenRequestBuilder.clean_model_name("qwen-max-image") == "qwen-max"
    
    def test_is_thinking_mode(self):
        """Test thinking mode detection"""
        assert QwenRequestBuilder.is_thinking_mode("qwen-max-thinking") is True
        assert QwenRequestBuilder.is_thinking_mode("qwen-max") is False
        assert QwenRequestBuilder.is_thinking_mode("qwen-max-search") is False
    
    def test_is_search_mode(self):
        """Test search mode detection"""
        assert QwenRequestBuilder.is_search_mode("qwen-max-search") is True
        assert QwenRequestBuilder.is_search_mode("qwen-max") is False
        assert QwenRequestBuilder.is_search_mode("qwen-max-thinking") is False
    
    def test_transform_openai_messages(self):
        """Test message transformation from OpenAI to Qwen format"""
        openai_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        qwen_messages = QwenRequestBuilder.transform_openai_messages(openai_messages)
        
        assert len(qwen_messages) == 2
        
        # First message
        assert qwen_messages[0]["role"] == "user"
        assert qwen_messages[0]["content"] == "Hello"
        assert qwen_messages[0]["chat_type"] == "text"
        assert qwen_messages[0]["extra"] == {}
        
        # Second message
        assert qwen_messages[1]["role"] == "assistant"
        assert qwen_messages[1]["content"] == "Hi there"
        assert qwen_messages[1]["chat_type"] == "text"
        assert qwen_messages[1]["extra"] == {}
    
    def test_map_size_to_aspect_ratio_predefined(self):
        """Test size mapping for predefined sizes"""
        assert QwenRequestBuilder.map_size_to_aspect_ratio("1024x1024") == "1:1"
        assert QwenRequestBuilder.map_size_to_aspect_ratio("1792x1024") == "16:9"
        assert QwenRequestBuilder.map_size_to_aspect_ratio("1024x1792") == "9:16"
        assert QwenRequestBuilder.map_size_to_aspect_ratio("1152x768") == "3:2"
    
    def test_map_size_to_aspect_ratio_custom(self):
        """Test size mapping for custom sizes"""
        # Should calculate GCD and simplify
        assert QwenRequestBuilder.map_size_to_aspect_ratio("1600x900") == "16:9"
        assert QwenRequestBuilder.map_size_to_aspect_ratio("2560x1440") == "16:9"
    
    def test_map_size_to_aspect_ratio_invalid(self):
        """Test size mapping with invalid input"""
        # Should default to 1:1
        result = QwenRequestBuilder.map_size_to_aspect_ratio("invalid")
        assert result == "1:1"


class TestTextChatRequest:
    """Test text-to-text chat request building"""
    
    def test_basic_text_chat_request(self):
        """Test basic text chat has all critical fields"""
        messages = [{"role": "user", "content": "Hello"}]
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max",
            messages=messages
        )
        
        # Critical fields that were missing
        assert "session_id" in request
        assert "chat_id" in request
        assert "chat_type" in request
        assert "feature_config" in request
        
        # Verify UUIDs are valid
        assert isinstance(uuid.UUID(request["session_id"]), uuid.UUID)
        assert isinstance(uuid.UUID(request["chat_id"]), uuid.UUID)
        
        # Verify values
        assert request["model"] == "qwen-max"
        assert request["stream"] is True
        assert request["incremental_output"] is True
        assert request["chat_type"] == "normal"
        
        # Verify feature_config structure
        assert request["feature_config"]["output_schema"] == "phase"
        assert request["feature_config"]["thinking_enabled"] is False
        
        # Verify messages have required fields
        assert len(request["messages"]) == 1
        assert request["messages"][0]["chat_type"] == "text"
        assert request["messages"][0]["extra"] == {}
    
    def test_thinking_mode_request(self):
        """Test thinking mode sets correct feature_config"""
        messages = [{"role": "user", "content": "Solve this problem"}]
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max-thinking",
            messages=messages
        )
        
        # Model should be cleaned
        assert request["model"] == "qwen-max"
        
        # Thinking should be enabled
        assert request["feature_config"]["thinking_enabled"] is True
    
    def test_message_transformation_in_request(self):
        """Test messages are properly transformed"""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max",
            messages=messages
        )
        
        assert len(request["messages"]) == 4
        
        # All messages should have chat_type and extra
        for msg in request["messages"]:
            assert "chat_type" in msg
            assert msg["chat_type"] == "text"
            assert "extra" in msg
            assert msg["extra"] == {}


class TestImageGenerationRequest:
    """Test image generation request building"""
    
    def test_image_generation_request(self):
        """Test image generation request structure"""
        request = QwenRequestBuilder.build_image_generation_request(
            chat_id="test-chat-id",
            model="qwen-max",
            prompt="A beautiful sunset",
            size="1024x1024"
        )
        
        assert request["stream"] is True
        assert request["chat_id"] == "test-chat-id"
        assert request["model"] == "qwen-max"
        assert request["size"] == "1:1"
        
        # Check message structure
        assert len(request["messages"]) == 1
        msg = request["messages"][0]
        
        assert msg["role"] == "user"
        assert msg["content"] == "A beautiful sunset"
        assert msg["chat_type"] == "t2i"
        assert msg["files"] == []
        assert "feature_config" in msg
        assert msg["feature_config"]["output_schema"] == "phase"
    
    def test_image_generation_custom_size(self):
        """Test custom size aspect ratio calculation"""
        request = QwenRequestBuilder.build_image_generation_request(
            chat_id="test-chat-id",
            model="qwen-max",
            prompt="Test",
            size="1792x1024"
        )
        
        assert request["size"] == "16:9"


class TestImageEditRequest:
    """Test image editing request building"""
    
    def test_image_edit_request(self):
        """Test image edit request structure"""
        request = QwenRequestBuilder.build_image_edit_request(
            chat_id="test-chat-id",
            model="qwen-max",
            prompt="Add a rainbow",
            image_url="https://example.com/image.jpg"
        )
        
        assert request["stream"] is True
        assert request["chat_id"] == "test-chat-id"
        assert request["model"] == "qwen-max"
        
        # Check message structure
        msg = request["messages"][0]
        assert msg["role"] == "user"
        assert msg["content"] == "Add a rainbow"
        assert msg["chat_type"] == "image_edit"
        
        # Check files array
        assert len(msg["files"]) == 1
        assert msg["files"][0]["type"] == "image"
        assert msg["files"][0]["url"] == "https://example.com/image.jpg"


class TestChatSessionPayload:
    """Test chat session creation payload"""
    
    def test_chat_session_payload(self):
        """Test chat session creation payload structure"""
        payload = QwenRequestBuilder.build_chat_session_payload(
            model="qwen-max",
            chat_type="t2i"
        )
        
        assert payload["title"] == "New Chat"
        assert payload["models"] == ["qwen-max"]
        assert payload["chat_mode"] == "normal"
        assert payload["chat_type"] == "t2i"
        assert "timestamp" in payload
        assert isinstance(payload["timestamp"], int)
    
    def test_chat_session_payload_different_types(self):
        """Test different chat types in session payload"""
        # Normal chat
        payload = QwenRequestBuilder.build_chat_session_payload("qwen-max", "normal")
        assert payload["chat_type"] == "normal"
        
        # Image generation
        payload = QwenRequestBuilder.build_chat_session_payload("qwen-max", "t2i")
        assert payload["chat_type"] == "t2i"
        
        # Image editing
        payload = QwenRequestBuilder.build_chat_session_payload("qwen-max", "image_edit")
        assert payload["chat_type"] == "image_edit"


class TestImageExtraction:
    """Test image URL extraction from messages"""
    
    def test_extract_markdown_images(self):
        """Test extracting images from markdown in assistant messages"""
        messages = [
            {
                "role": "assistant",
                "content": "Here's an image: ![alt](https://example.com/img1.jpg)"
            }
        ]
        
        images = QwenRequestBuilder.extract_images_from_messages(messages)
        
        assert len(images) == 1
        assert images[0] == "https://example.com/img1.jpg"
    
    def test_extract_image_url_objects(self):
        """Test extracting from OpenAI image_url format"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's this?"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/img.jpg"}}
                ]
            }
        ]
        
        images = QwenRequestBuilder.extract_images_from_messages(messages)
        
        assert len(images) == 1
        assert images[0] == "https://example.com/img.jpg"
    
    def test_extract_multiple_images(self):
        """Test extracting multiple images and limiting to 3"""
        messages = [
            {"role": "assistant", "content": "![img1](https://example.com/1.jpg)"},
            {"role": "assistant", "content": "![img2](https://example.com/2.jpg)"},
            {"role": "assistant", "content": "![img3](https://example.com/3.jpg)"},
            {"role": "assistant", "content": "![img4](https://example.com/4.jpg)"},
        ]
        
        images = QwenRequestBuilder.extract_images_from_messages(messages)
        
        # Should return last 3
        assert len(images) == 3
        assert images[0] == "https://example.com/2.jpg"
        assert images[1] == "https://example.com/3.jpg"
        assert images[2] == "https://example.com/4.jpg"


class TestBuildQwenRequest:
    """Test main build_qwen_request function"""
    
    def test_build_text_request(self):
        """Test building text request via main function"""
        messages = [{"role": "user", "content": "Hello"}]
        
        request, chat_id = build_qwen_request(
            model="qwen-max",
            messages=messages
        )
        
        # Should return request with no chat_id
        assert chat_id is None
        assert "session_id" in request
        assert "chat_id" in request
        assert request["model"] == "qwen-max"
    
    def test_build_thinking_request(self):
        """Test building thinking request via main function"""
        messages = [{"role": "user", "content": "Solve this"}]
        
        request, chat_id = build_qwen_request(
            model="qwen-max-thinking",
            messages=messages
        )
        
        assert chat_id is None
        assert request["model"] == "qwen-max"
        assert request["feature_config"]["thinking_enabled"] is True
    
    def test_build_image_generation_template(self):
        """Test image generation returns template requiring session"""
        messages = [{"role": "user", "content": "Generate a cat"}]
        
        request, chat_id = build_qwen_request(
            model="qwen-max-image",
            messages=messages,
            size="1024x1024"
        )
        
        # Should indicate session required
        assert chat_id == "REQUIRES_SESSION_CREATION"
        assert request["type"] == "t2i_template"
        assert request["prompt"] == "Generate a cat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

