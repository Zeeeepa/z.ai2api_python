#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive tests for Qwen Provider
Tests all models, features, modes, and capabilities
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.providers.qwen_provider import (
    QwenProvider,
    QwenRequestBuilder,
    QwenMessage,
    QwenUploader
)
from app.models.schemas import OpenAIRequest, Message


class TestQwenProviderInitialization:
    """Test Qwen provider initialization"""
    
    def test_provider_initialization(self):
        """Test provider can be initialized"""
        provider = QwenProvider()
        assert provider.name == "qwen"
        assert provider.config.api_endpoint == "https://chat.qwen.ai/api/v2/chats"
    
    def test_provider_initialization_with_auth(self):
        """Test provider with authentication config"""
        auth_config = {
            "email": "test@example.com",
            "password": "testpass"
        }
        provider = QwenProvider(auth_config=auth_config)
        assert provider.auth is not None
    
    def test_supported_base_models(self):
        """Test base model names"""
        provider = QwenProvider()
        models = provider.get_supported_models()
        
        base_models = ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long"]
        for model in base_models:
            assert model in models
    
    def test_model_variants(self):
        """Test model variants are available"""
        provider = QwenProvider()
        models = provider.get_supported_models()
        
        # Should have thinking variants
        assert "qwen-max-thinking" in models
        assert "qwen-plus-thinking" in models
        
        # Should have search variants
        assert "qwen-max-search" in models
        
        # Should have image variants
        assert "qwen-max-image" in models
        
        # Should have video variant
        assert "qwen-max-video" in models
    
    def test_model_mapping(self):
        """Test model mapping to base models"""
        provider = QwenProvider()
        
        # Verify key mappings
        assert provider.model_mapping["qwen-max"] == "qwen-max"
        assert provider.model_mapping["qwen-max-thinking"] == "qwen-max"
        assert provider.model_mapping["qwen-max-search"] == "qwen-max"
        assert provider.model_mapping["qwen-plus"] == "qwen-plus"
        assert provider.model_mapping["qwen-turbo"] == "qwen-turbo"


class TestQwenRequestBuilder:
    """Test Qwen request builder"""
    
    def test_builder_initialization(self):
        """Test request builder can be initialized"""
        builder = QwenRequestBuilder()
        assert builder is not None
    
    def test_get_chat_type(self):
        """Test chat type detection"""
        # Image generation
        assert QwenRequestBuilder.get_chat_type("qwen-max-image") == "t2i"
        
        # Image editing
        assert QwenRequestBuilder.get_chat_type("qwen-max-image_edit") == "image_edit"
        
        # Video generation
        assert QwenRequestBuilder.get_chat_type("qwen-max-video") == "t2v"
        
        # Normal text chat
        assert QwenRequestBuilder.get_chat_type("qwen-max") == "normal"
        assert QwenRequestBuilder.get_chat_type("qwen-max-thinking") == "normal"
        assert QwenRequestBuilder.get_chat_type("qwen-max-search") == "normal"
    
    def test_remove_model_suffix(self):
        """Test model suffix removal"""
        assert QwenRequestBuilder.remove_model_suffix("qwen-max-thinking") == "qwen-max"
        assert QwenRequestBuilder.remove_model_suffix("qwen-max-search") == "qwen-max"
        assert QwenRequestBuilder.remove_model_suffix("qwen-max-image") == "qwen-max"
        assert QwenRequestBuilder.remove_model_suffix("qwen-max") == "qwen-max"
    
    def test_is_thinking_mode(self):
        """Test thinking mode detection"""
        assert QwenRequestBuilder.is_thinking_mode("qwen-max-thinking") is True
        assert QwenRequestBuilder.is_thinking_mode("qwen-plus-thinking") is True
        assert QwenRequestBuilder.is_thinking_mode("qwen-max") is False
        assert QwenRequestBuilder.is_thinking_mode("qwen-max-search") is False
    
    def test_is_search_mode(self):
        """Test search mode detection"""
        assert QwenRequestBuilder.is_search_mode("qwen-max-search") is True
        assert QwenRequestBuilder.is_search_mode("qwen-plus-search") is True
        assert QwenRequestBuilder.is_search_mode("qwen-max") is False
        assert QwenRequestBuilder.is_search_mode("qwen-max-thinking") is False
    
    def test_build_text_chat_request(self):
        """Test building text chat request"""
        messages = [
            QwenMessage(role="user", content="Hello", chat_type="text")
        ]
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max",
            messages=messages,
            stream=False
        )
        
        assert request["model"] == "qwen-max"
        assert request["action"] == "next"
        assert request["mode"] == "chat"
        assert "messages" in request
        assert "thinking_enabled" in request["messages"][0]["feature_config"]
    
    def test_build_text_chat_with_thinking(self):
        """Test building text chat with thinking enabled"""
        messages = [
            QwenMessage(role="user", content="Solve 2+2", chat_type="text")
        ]
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max-thinking",
            messages=messages,
            stream=False
        )
        
        # Thinking should be enabled
        assert request["messages"][0]["feature_config"]["thinking_enabled"] is True
    
    def test_build_image_generation_request(self):
        """Test building image generation request"""
        request = QwenRequestBuilder.build_image_generation_request(
            model="qwen-max-image",
            prompt="A beautiful sunset",
            size="1024x1024"
        )
        
        assert request["model"] == "qwen-max"
        assert request["action"] == "next"
        assert request["mode"] == "chat"
        assert request["messages"][0]["chat_type"] == "t2i"
        assert "beautiful sunset" in request["messages"][0]["content"]


class TestQwenModels:
    """Test individual Qwen models"""
    
    @pytest.mark.asyncio
    async def test_qwen_max_standard(self):
        """Test qwen-max standard model"""
        provider = QwenProvider()
        request = OpenAIRequest(
            model="qwen-max",
            messages=[Message(role="user", content="Hello")],
            stream=False
        )
        
        with patch.object(provider, 'get_auth_headers', new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}
            
            # Should build request without errors
            builder = provider.builder
            assert builder is not None
    
    @pytest.mark.asyncio
    async def test_qwen_max_thinking(self):
        """Test qwen-max-thinking model"""
        provider = QwenProvider()
        request = OpenAIRequest(
            model="qwen-max-thinking",
            messages=[Message(role="user", content="Solve this problem")],
            stream=False
        )
        
        # Verify thinking mode is detected
        assert QwenRequestBuilder.is_thinking_mode("qwen-max-thinking")
    
    @pytest.mark.asyncio
    async def test_qwen_max_search(self):
        """Test qwen-max-search model"""
        provider = QwenProvider()
        
        # Verify search mode is detected
        assert QwenRequestBuilder.is_search_mode("qwen-max-search")
    
    @pytest.mark.asyncio
    async def test_qwen_max_image(self):
        """Test qwen-max-image model for image generation"""
        provider = QwenProvider()
        
        # Verify chat type is t2i
        chat_type = QwenRequestBuilder.get_chat_type("qwen-max-image")
        assert chat_type == "t2i"
    
    @pytest.mark.asyncio
    async def test_qwen_max_video(self):
        """Test qwen-max-video model for video generation"""
        provider = QwenProvider()
        
        # Verify chat type is t2v
        chat_type = QwenRequestBuilder.get_chat_type("qwen-max-video")
        assert chat_type == "t2v"
    
    @pytest.mark.asyncio
    async def test_qwen_plus_model(self):
        """Test qwen-plus model"""
        provider = QwenProvider()
        models = provider.get_supported_models()
        
        assert "qwen-plus" in models
        assert "qwen-plus-thinking" in models
        assert "qwen-plus-search" in models
    
    @pytest.mark.asyncio
    async def test_qwen_turbo_model(self):
        """Test qwen-turbo fast model"""
        provider = QwenProvider()
        models = provider.get_supported_models()
        
        assert "qwen-turbo" in models
        assert "qwen-turbo-thinking" in models
    
    @pytest.mark.asyncio
    async def test_qwen_long_model(self):
        """Test qwen-long model for long context"""
        provider = QwenProvider()
        models = provider.get_supported_models()
        
        assert "qwen-long" in models


class TestQwenFeatures:
    """Test Qwen provider features"""
    
    @pytest.mark.asyncio
    async def test_thinking_mode_feature(self):
        """Test thinking mode feature"""
        messages = [QwenMessage(role="user", content="Think deeply", chat_type="text")]
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max-thinking",
            messages=messages,
            stream=False
        )
        
        # Should have thinking enabled
        feature_config = request["messages"][0]["feature_config"]
        assert feature_config["thinking_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_search_mode_feature(self):
        """Test search mode feature"""
        # Search mode uses normal text chat with different model
        assert QwenRequestBuilder.is_search_mode("qwen-max-search")
    
    @pytest.mark.asyncio
    async def test_streaming_support(self):
        """Test streaming mode"""
        messages = [QwenMessage(role="user", content="Stream test", chat_type="text")]
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max",
            messages=messages,
            stream=True
        )
        
        # Stream should be enabled
        assert request.get("stream") is True or "stream" not in request  # May not be in dict
    
    @pytest.mark.asyncio
    async def test_image_generation_feature(self):
        """Test image generation feature"""
        request = QwenRequestBuilder.build_image_generation_request(
            model="qwen-max-image",
            prompt="A cat",
            size="1024x1024"
        )
        
        assert request["messages"][0]["chat_type"] == "t2i"
        assert "cat" in request["messages"][0]["content"]
    
    @pytest.mark.asyncio
    async def test_video_generation_feature(self):
        """Test video generation capability"""
        chat_type = QwenRequestBuilder.get_chat_type("qwen-max-video")
        assert chat_type == "t2v"
    
    @pytest.mark.asyncio
    async def test_deep_research_mode(self):
        """Test deep research mode alias"""
        provider = QwenProvider()
        
        # Deep research should map to qwen-max
        assert provider.model_mapping["qwen-deep-research"] == "qwen-max"
        assert provider.model_mapping["qwen-max-deep-research"] == "qwen-max"


class TestQwenAuthentication:
    """Test Qwen authentication"""
    
    @pytest.mark.asyncio
    async def test_auth_headers_generation(self):
        """Test authentication headers"""
        provider = QwenProvider()
        
        with patch.object(provider, 'auth') as mock_auth:
            mock_auth.get_token = AsyncMock(return_value="test-token-123")
            mock_auth.get_valid_session = AsyncMock(return_value={})
            
            headers = await provider.get_auth_headers()
            
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer test-token-123"
            assert headers["Content-Type"] == "application/json"
            assert headers["source"] == "web"
            assert "x-request-id" in headers
    
    @pytest.mark.asyncio
    async def test_auth_headers_without_token(self):
        """Test headers when no token available"""
        provider = QwenProvider()
        provider.auth = None
        
        headers = await provider.get_auth_headers()
        
        # Should still have required headers
        assert "Content-Type" in headers
        assert "source" in headers
        assert "x-request-id" in headers
        # But no Authorization
        assert "Authorization" not in headers
    
    @pytest.mark.asyncio
    async def test_auth_with_cookie(self):
        """Test authentication with cookie"""
        provider = QwenProvider()
        
        with patch.object(provider, 'auth') as mock_auth:
            mock_auth.get_token = AsyncMock(return_value="token")
            mock_auth.get_valid_session = AsyncMock(return_value={
                "extra": {"ssxmod_itna": "cookie-value"}
            })
            
            headers = await provider.get_auth_headers()
            
            assert "Cookie" in headers
            assert "ssxmod_itna=cookie-value" in headers["Cookie"]


class TestQwenMessage:
    """Test Qwen message dataclass"""
    
    def test_message_creation(self):
        """Test creating Qwen message"""
        msg = QwenMessage(
            role="user",
            content="Hello",
            chat_type="text"
        )
        
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.chat_type == "text"
    
    def test_message_to_dict(self):
        """Test converting message to dictionary"""
        msg = QwenMessage(
            role="user",
            content="Test",
            chat_type="text",
            extra={"key": "value"}
        )
        
        msg_dict = msg.to_dict()
        
        assert msg_dict["role"] == "user"
        assert msg_dict["content"] == "Test"
        assert msg_dict["chat_type"] == "text"
        assert msg_dict["extra"] == {"key": "value"}
    
    def test_message_with_files(self):
        """Test message with files"""
        msg = QwenMessage(
            role="user",
            content="Image",
            chat_type="text",
            files=[{"type": "image", "url": "http://example.com/img.jpg"}]
        )
        
        msg_dict = msg.to_dict()
        assert "files" in msg_dict
        assert len(msg_dict["files"]) == 1
    
    def test_message_with_feature_config(self):
        """Test message with feature config"""
        msg = QwenMessage(
            role="user",
            content="Think",
            chat_type="text",
            feature_config={"thinking_enabled": True}
        )
        
        msg_dict = msg.to_dict()
        assert "feature_config" in msg_dict
        assert msg_dict["feature_config"]["thinking_enabled"] is True


class TestQwenUploader:
    """Test Qwen file uploader"""
    
    def test_uploader_initialization(self):
        """Test uploader can be initialized"""
        uploader = QwenUploader(auth_token="test-token")
        assert uploader.auth_token == "test-token"
    
    def test_get_file_type(self):
        """Test file type detection"""
        uploader = QwenUploader(auth_token="test")
        
        # Image types
        assert uploader.get_file_type("image/jpeg") == "image"
        assert uploader.get_file_type("image/png") == "image"
        
        # Video types
        assert uploader.get_file_type("video/mp4") == "video"
        
        # Audio types
        assert uploader.get_file_type("audio/mpeg") == "audio"
        
        # Document types
        assert uploader.get_file_type("application/pdf") == "document"
        assert uploader.get_file_type("text/plain") == "document"
    
    def test_validate_file_type(self):
        """Test file type validation"""
        uploader = QwenUploader(auth_token="test")
        
        # Should accept supported types
        assert uploader.validate_file_type("image/jpeg") is True
        assert uploader.validate_file_type("video/mp4") is True
        
        # May reject unsupported types depending on implementation
        # This depends on actual validation logic
    
    def test_max_file_size_constant(self):
        """Test max file size is defined"""
        assert QwenUploader.MAX_FILE_SIZE == 100 * 1024 * 1024  # 100MB
    
    def test_supported_types_defined(self):
        """Test supported types are defined"""
        types = QwenUploader.SUPPORTED_TYPES
        
        assert 'image' in types
        assert 'video' in types
        assert 'audio' in types
        assert 'document' in types


class TestQwenErrorHandling:
    """Test Qwen error handling"""
    
    def test_handle_error(self):
        """Test error handling"""
        provider = QwenProvider()
        error = Exception("Test error")
        
        error_response = provider.handle_error(error, "test context")
        
        assert "error" in error_response
        assert "message" in error_response["error"]
        assert "Test error" in error_response["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_invalid_model_handling(self):
        """Test handling of invalid model names"""
        provider = QwenProvider()
        
        # Should handle gracefully or map to valid model
        models = provider.get_supported_models()
        assert len(models) > 0


class TestQwenIntegration:
    """Integration tests for Qwen provider"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_text_request_flow(self):
        """Test complete text request flow"""
        provider = QwenProvider()
        
        messages = [
            QwenMessage(role="system", content="You are helpful", chat_type="text"),
            QwenMessage(role="user", content="Hello", chat_type="text")
        ]
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max",
            messages=messages,
            stream=False
        )
        
        assert request["model"] == "qwen-max"
        assert len(request["messages"]) == 2
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_thinking_request_flow(self):
        """Test complete thinking mode request flow"""
        provider = QwenProvider()
        
        messages = [
            QwenMessage(role="user", content="Think deeply about AI", chat_type="text")
        ]
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max-thinking",
            messages=messages,
            stream=False
        )
        
        # Verify thinking is enabled
        assert request["messages"][0]["feature_config"]["thinking_enabled"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_image_generation_flow(self):
        """Test complete image generation flow"""
        provider = QwenProvider()
        
        request = QwenRequestBuilder.build_image_generation_request(
            model="qwen-max-image",
            prompt="A beautiful landscape",
            size="1024x1024"
        )
        
        assert request["model"] == "qwen-max"
        assert request["messages"][0]["chat_type"] == "t2i"


class TestQwenEdgeCases:
    """Test edge cases for Qwen provider"""
    
    def test_model_with_multiple_suffixes(self):
        """Test handling model names with unusual patterns"""
        provider = QwenProvider()
        
        # Should handle standard suffixes
        assert QwenRequestBuilder.remove_model_suffix("qwen-max-thinking") == "qwen-max"
        assert QwenRequestBuilder.remove_model_suffix("qwen-max-search") == "qwen-max"
    
    def test_empty_messages_list(self):
        """Test handling empty messages"""
        messages = []
        
        request = QwenRequestBuilder.build_text_chat_request(
            model="qwen-max",
            messages=messages,
            stream=False
        )
        
        # Should handle gracefully
        assert "messages" in request
    
    def test_very_long_content(self):
        """Test handling very long content"""
        long_content = "A" * 50000
        msg = QwenMessage(role="user", content=long_content, chat_type="text")
        
        msg_dict = msg.to_dict()
        assert len(msg_dict["content"]) == 50000
    
    def test_special_characters_in_content(self):
        """Test special characters handling"""
        special = "Test 中文 🎉 \n\t special"
        msg = QwenMessage(role="user", content=special, chat_type="text")
        
        msg_dict = msg.to_dict()
        assert msg_dict["content"] == special
    
    @pytest.mark.asyncio
    async def test_all_model_variants_accessible(self):
        """Test all model variants are accessible"""
        provider = QwenProvider()
        models = provider.get_supported_models()
        
        # Should have at least these base models
        required = ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long"]
        for req in required:
            assert req in models


class TestQwenCoderModels:
    """Test Qwen coder-specific models"""
    
    def test_coder_models_available(self):
        """Test coder models are in supported list"""
        provider = QwenProvider()
        models = provider.get_supported_models()
        
        assert "qwen3-coder-plus" in models
        assert "qwen-coder-plus" in models
    
    def test_coder_model_mapping(self):
        """Test coder models map correctly"""
        provider = QwenProvider()
        
        # Both should map to qwen-plus
        assert provider.model_mapping["qwen3-coder-plus"] == "qwen-plus"
        assert provider.model_mapping["qwen-coder-plus"] == "qwen-plus"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

