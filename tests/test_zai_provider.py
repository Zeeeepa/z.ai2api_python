#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive tests for Z.AI Provider
Tests all models, features, tools, and functions
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.providers.zai_provider import ZAIProvider
from app.providers.base import ProviderConfig
from app.models.schemas import OpenAIRequest, Message


class TestZAIProviderInitialization:
    """Test Z.AI provider initialization"""
    
    def test_provider_initialization(self):
        """Test provider can be initialized"""
        provider = ZAIProvider()
        assert provider.name == "zai"
        assert provider.base_url == "https://chat.z.ai"
    
    def test_supported_models(self):
        """Test all supported models are available"""
        provider = ZAIProvider()
        models = provider.get_supported_models()
        
        expected_models = [
            "GLM-4.5",
            "GLM-4.5-Thinking",
            "GLM-4.5-Search",
            "GLM-4.5-Air",
            "GLM-4.6",
            "GLM-4.6-Thinking",
            "GLM-4.6-Search",
        ]
        
        for model in expected_models:
            assert model in models, f"Model {model} not found in supported models"
    
    def test_model_mapping(self):
        """Test model mapping to upstream IDs"""
        provider = ZAIProvider()
        
        assert provider.model_mapping["GLM-4.5"] == "0727-360B-API"
        assert provider.model_mapping["GLM-4.5-Thinking"] == "0727-360B-API"
        assert provider.model_mapping["GLM-4.5-Search"] == "0727-360B-API"
        assert provider.model_mapping["GLM-4.5-Air"] == "0727-106B-API"
        assert provider.model_mapping["GLM-4.6"] == "GLM-4-6-API-V1"
        assert provider.model_mapping["GLM-4.6-Thinking"] == "GLM-4-6-API-V1"
        assert provider.model_mapping["GLM-4.6-Search"] == "GLM-4-6-API-V1"


class TestZAIProviderModels:
    """Test individual Z.AI models"""
    
    @pytest.mark.asyncio
    async def test_glm45_standard_model(self):
        """Test GLM-4.5 standard model request transformation"""
        provider = ZAIProvider()
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Hello")],
            stream=False
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            
            assert transformed["model"] == "0727-360B-API"
            assert transformed["stream"] is True  # Always streams internally
            assert "features" in transformed
            assert transformed["features"]["enable_thinking"] is False
            assert transformed["features"]["web_search"] is False
    
    @pytest.mark.asyncio
    async def test_glm45_thinking_model(self):
        """Test GLM-4.5-Thinking model enables thinking mode"""
        provider = ZAIProvider()
        request = OpenAIRequest(
            model="GLM-4.5-Thinking",
            messages=[Message(role="user", content="Solve 2+2")],
            stream=False
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            
            assert transformed["features"]["enable_thinking"] is True
            assert transformed["features"]["web_search"] is False
    
    @pytest.mark.asyncio
    async def test_glm45_search_model(self):
        """Test GLM-4.5-Search model enables search"""
        provider = ZAIProvider()
        request = OpenAIRequest(
            model="GLM-4.5-Search",
            messages=[Message(role="user", content="What's the weather?")],
            stream=False
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            
            assert transformed["features"]["web_search"] is True
            assert transformed["features"]["auto_web_search"] is True
            # Should include deep-web-search MCP server for 4.5 search
            assert any(
                feature.get("server") == "deep-web-search" 
                for feature in transformed["features"].get("features", [])
            )
    
    @pytest.mark.asyncio
    async def test_glm45_air_model(self):
        """Test GLM-4.5-Air lightweight model"""
        provider = ZAIProvider()
        request = OpenAIRequest(
            model="GLM-4.5-Air",
            messages=[Message(role="user", content="Quick question")],
            stream=False
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            
            assert transformed["model"] == "0727-106B-API"  # Different upstream ID
    
    @pytest.mark.asyncio
    async def test_glm46_models(self):
        """Test GLM-4.6 models use correct upstream ID"""
        provider = ZAIProvider()
        
        for model_name in ["GLM-4.6", "GLM-4.6-Thinking", "GLM-4.6-Search"]:
            request = OpenAIRequest(
                model=model_name,
                messages=[Message(role="user", content="Test")],
                stream=False
            )
            
            with patch.object(provider, 'get_token', return_value="test-token"):
                transformed = await provider.transform_request(request)
                assert transformed["model"] == "GLM-4-6-API-V1"


class TestZAIProviderFeatures:
    """Test Z.AI provider features"""
    
    @pytest.mark.asyncio
    async def test_streaming_support(self):
        """Test streaming mode transformation"""
        provider = ZAIProvider()
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Stream test")],
            stream=True
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            assert transformed["stream"] is True
    
    @pytest.mark.asyncio
    async def test_mcp_servers_integration(self):
        """Test MCP servers are included in features"""
        provider = ZAIProvider()
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Test")],
            stream=False
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            
            features = transformed["features"]["features"]
            mcp_servers = [f["server"] for f in features if f.get("type") == "mcp"]
            
            expected_servers = [
                "vibe-coding",
                "ppt-maker",
                "image-search",
                "deep-research",
                "advanced-search"
            ]
            
            for server in expected_servers:
                assert server in mcp_servers, f"MCP server {server} not found"
    
    @pytest.mark.asyncio
    async def test_tool_calling_support(self):
        """Test tool calling / function calling support"""
        provider = ZAIProvider()
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Use tools")],
            stream=False,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get weather info",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string"}
                            }
                        }
                    }
                }
            ]
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            # Tools should be transformed and included
            assert "tools" in transformed or "functions" in transformed
    
    @pytest.mark.asyncio
    async def test_multimodal_content(self):
        """Test multimodal content handling"""
        provider = ZAIProvider()
        
        # Create message with multimodal content
        class ContentPart:
            def __init__(self, type, text):
                self.type = type
                self.text = text
        
        message = Message(
            role="user",
            content=[
                ContentPart("text", "Describe this image"),
                ContentPart("image_url", "https://example.com/image.jpg")
            ]
        )
        
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[message],
            stream=False
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            # Should handle multimodal content
            assert "messages" in transformed


class TestZAIProviderAuthentication:
    """Test Z.AI authentication mechanisms"""
    
    @pytest.mark.asyncio
    async def test_token_pool_usage(self):
        """Test token pool integration"""
        provider = ZAIProvider()
        
        with patch('app.providers.zai_provider.get_token_pool') as mock_pool:
            mock_pool_instance = Mock()
            mock_pool_instance.get_next_token.return_value = "pool-token-123"
            mock_pool.return_value = mock_pool_instance
            
            token = await provider.get_token()
            assert token == "pool-token-123"
    
    @pytest.mark.asyncio
    async def test_anonymous_mode(self):
        """Test anonymous mode visitor token acquisition"""
        provider = ZAIProvider()
        
        with patch('app.providers.zai_provider.settings') as mock_settings:
            mock_settings.ANONYMOUS_MODE = True
            mock_settings.AUTH_TOKEN = None
            
            with patch('app.providers.zai_provider.httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"token": "visitor-token-456"}
                
                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )
                
                token = await provider.get_token()
                assert token == "visitor-token-456"
    
    def test_token_failure_marking(self):
        """Test marking token failures"""
        provider = ZAIProvider()
        
        with patch('app.providers.zai_provider.get_token_pool') as mock_pool:
            mock_pool_instance = Mock()
            mock_pool.return_value = mock_pool_instance
            
            provider.mark_token_failure("failed-token", Exception("Test error"))
            mock_pool_instance.mark_token_failure.assert_called_once()


class TestZAIProviderErrorHandling:
    """Test Z.AI error handling"""
    
    def test_handle_error(self):
        """Test error handling produces proper error response"""
        provider = ZAIProvider()
        error = Exception("Test error")
        
        error_response = provider.handle_error(error, "test context")
        
        assert "error" in error_response
        assert "message" in error_response["error"]
        assert "type" in error_response["error"]
        assert error_response["error"]["type"] == "provider_error"
    
    @pytest.mark.asyncio
    async def test_invalid_model_handling(self):
        """Test handling of invalid model names"""
        provider = ZAIProvider()
        request = OpenAIRequest(
            model="INVALID-MODEL",
            messages=[Message(role="user", content="Test")],
            stream=False
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            # Should fallback to default model
            assert transformed["model"] == "0727-360B-API"


class TestZAIProviderResponseTransformation:
    """Test Z.AI response transformation"""
    
    def test_create_openai_response(self):
        """Test OpenAI response creation"""
        provider = ZAIProvider()
        chat_id = "chatcmpl-123"
        model = "GLM-4.5"
        content = "Test response"
        usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        
        response = provider.create_openai_response(chat_id, model, content, usage)
        
        assert response["id"] == chat_id
        assert response["model"] == model
        assert response["choices"][0]["message"]["content"] == content
        assert response["usage"] == usage
    
    def test_create_openai_response_with_reasoning(self):
        """Test OpenAI response with reasoning content"""
        provider = ZAIProvider()
        chat_id = "chatcmpl-456"
        model = "GLM-4.5-Thinking"
        content = "Final answer"
        reasoning = "Let me think... step by step"
        
        response = provider.create_openai_response_with_reasoning(
            chat_id, model, content, reasoning
        )
        
        assert response["choices"][0]["message"]["content"] == content
        assert response["choices"][0]["message"]["reasoning_content"] == reasoning
    
    def test_create_openai_chunk(self):
        """Test streaming chunk creation"""
        provider = ZAIProvider()
        chat_id = "chatcmpl-789"
        model = "GLM-4.5"
        delta = {"content": "Hello"}
        
        chunk = provider.create_openai_chunk(chat_id, model, delta, None)
        
        assert chunk["id"] == chat_id
        assert chunk["object"] == "chat.completion.chunk"
        assert chunk["choices"][0]["delta"] == delta
        assert chunk["choices"][0]["finish_reason"] is None


class TestZAIProviderIntegration:
    """Integration tests for Z.AI provider"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_request_flow(self):
        """Test complete request-response flow"""
        provider = ZAIProvider()
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Hello, world!")],
            stream=False,
            temperature=0.7,
            max_tokens=100
        )
        
        with patch.object(provider, 'get_token', return_value="test-token"):
            # Test transformation
            transformed = await provider.transform_request(request)
            
            assert transformed is not None
            assert "model" in transformed
            assert "messages" in transformed
            assert "features" in transformed
    
    def test_chat_id_generation(self):
        """Test unique chat ID generation"""
        provider = ZAIProvider()
        
        chat_id_1 = provider.create_chat_id()
        chat_id_2 = provider.create_chat_id()
        
        assert chat_id_1.startswith("chatcmpl-")
        assert chat_id_2.startswith("chatcmpl-")
        assert chat_id_1 != chat_id_2  # Should be unique


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

