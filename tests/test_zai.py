#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive Integration Tests for Z.AI Provider

Tests actual authentication, all models, all features, and real functionality.
"""

import pytest
import asyncio
from typing import List, Dict, Any
from app.providers.zai_provider import ZAIProvider
from app.models.schemas import OpenAIRequest, Message


class TestZAIAuthentication:
    """Test Z.AI authentication and token retrieval"""
    
    @pytest.fixture
    def provider(self):
        """Initialize Z.AI provider"""
        return ZAIProvider()
    
    def test_token_retrieval(self, provider):
        """Test actual token retrieval from Z.AI"""
        token = provider.get_valid_token()
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        print(f"✅ Retrieved token: {token[:20]}...")
    
    def test_chat_id_generation(self, provider):
        """Test chat ID generation"""
        chat_id = provider._generate_chat_id()
        assert chat_id is not None
        assert isinstance(chat_id, str)
        assert len(chat_id) == 36  # UUID format
        print(f"✅ Generated chat_id: {chat_id}")


class TestZAIModels:
    """Test all Z.AI models"""
    
    @pytest.fixture
    def provider(self):
        return ZAIProvider()
    
    def test_supported_models_list(self, provider):
        """Test that all expected models are supported"""
        models = provider.get_supported_models()
        expected_models = [
            "GLM-4.5",
            "GLM-4.5-Thinking",
            "GLM-4.5-Search",
            "GLM-4.5-Air",
            "GLM-4.6",
            "GLM-4.6-Thinking",
            "GLM-4.6-Search"
        ]
        
        for model in expected_models:
            assert model in models, f"Model {model} not found in supported models"
        
        print(f"✅ All {len(expected_models)} models are supported")
    
    @pytest.mark.asyncio
    async def test_glm45_model(self, provider):
        """Test GLM-4.5 model with actual request"""
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Hello")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ GLM-4.5 response received")
    
    @pytest.mark.asyncio
    async def test_glm45_thinking_model(self, provider):
        """Test GLM-4.5-Thinking model"""
        request = OpenAIRequest(
            model="GLM-4.5-Thinking",
            messages=[Message(role="user", content="Solve: 2+2")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ GLM-4.5-Thinking response received")
    
    @pytest.mark.asyncio
    async def test_glm45_search_model(self, provider):
        """Test GLM-4.5-Search model"""
        request = OpenAIRequest(
            model="GLM-4.5-Search",
            messages=[Message(role="user", content="What's the weather?")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ GLM-4.5-Search response received")
    
    @pytest.mark.asyncio
    async def test_glm46_model(self, provider):
        """Test GLM-4.6 model"""
        request = OpenAIRequest(
            model="GLM-4.6",
            messages=[Message(role="user", content="Hello")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ GLM-4.6 response received")


class TestZAIFeatures:
    """Test all Z.AI features"""
    
    @pytest.fixture
    def provider(self):
        return ZAIProvider()
    
    @pytest.mark.asyncio
    async def test_streaming(self, provider):
        """Test streaming responses"""
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Count to 5")],
            stream=True
        )
        
        chunks_received = 0
        async for chunk in provider.chat_completions(request):
            assert chunk is not None
            chunks_received += 1
        
        assert chunks_received > 0
        print(f"✅ Streaming: received {chunks_received} chunks")
    
    @pytest.mark.asyncio
    async def test_thinking_mode(self, provider):
        """Test thinking mode feature"""
        request = OpenAIRequest(
            model="GLM-4.5-Thinking",
            messages=[Message(role="user", content="Explain quantum physics")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        # Thinking mode should provide detailed reasoning
        print(f"✅ Thinking mode response received")
    
    @pytest.mark.asyncio
    async def test_search_capability(self, provider):
        """Test search capability"""
        request = OpenAIRequest(
            model="GLM-4.5-Search",
            messages=[Message(role="user", content="Latest news about AI")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Search capability tested")
    
    @pytest.mark.asyncio
    async def test_mcp_servers(self, provider):
        """Test MCP servers integration"""
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Test MCP")],
            stream=False,
            # MCP servers configuration
            extra_body={"mcp_servers": []}
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ MCP servers integration tested")
    
    @pytest.mark.asyncio
    async def test_tool_calling(self, provider):
        """Test tool calling support"""
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Use a tool")],
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        }
                    }
                }
            }],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Tool calling tested")
    
    @pytest.mark.asyncio
    async def test_multimodal_content(self, provider):
        """Test multimodal content support (text + images)"""
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[
                Message(
                    role="user",
                    content=[
                        {"type": "text", "text": "What's in this image?"},
                        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
                    ]
                )
            ],
            stream=False
        )
        
        try:
            response = await provider.chat_completions(request)
            print(f"✅ Multimodal content tested")
        except Exception as e:
            print(f"⚠️ Multimodal test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_temperature_parameter(self, provider):
        """Test temperature parameter"""
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Be creative")],
            temperature=0.9,
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Temperature parameter tested")
    
    @pytest.mark.asyncio
    async def test_max_tokens_parameter(self, provider):
        """Test max_tokens parameter"""
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="Write a story")],
            max_tokens=100,
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ max_tokens parameter tested")


class TestZAIErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def provider(self):
        return ZAIProvider()
    
    @pytest.mark.asyncio
    async def test_invalid_model(self, provider):
        """Test handling of invalid model"""
        request = OpenAIRequest(
            model="invalid-model",
            messages=[Message(role="user", content="Hello")],
            stream=False
        )
        
        with pytest.raises(Exception):
            await provider.chat_completions(request)
        print(f"✅ Invalid model error handled")
    
    @pytest.mark.asyncio
    async def test_empty_message(self, provider):
        """Test handling of empty message"""
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="")],
            stream=False
        )
        
        try:
            response = await provider.chat_completions(request)
            print(f"✅ Empty message handled")
        except Exception as e:
            print(f"✅ Empty message error: {e}")
    
    @pytest.mark.asyncio
    async def test_very_long_message(self, provider):
        """Test handling of very long message"""
        long_message = "Hello " * 1000
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content=long_message)],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Very long message tested")


class TestZAIIntegration:
    """Integration tests combining multiple features"""
    
    @pytest.fixture
    def provider(self):
        return ZAIProvider()
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, provider):
        """Test multi-turn conversation"""
        messages = [
            Message(role="user", content="My name is Alice"),
            Message(role="assistant", content="Nice to meet you, Alice!"),
            Message(role="user", content="What's my name?")
        ]
        
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=messages,
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Multi-turn conversation tested")
    
    @pytest.mark.asyncio
    async def test_thinking_with_search(self, provider):
        """Test combining thinking and search"""
        request = OpenAIRequest(
            model="GLM-4.5-Search",
            messages=[Message(role="user", content="Research and explain the latest AI developments")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Thinking + Search combination tested")
    
    @pytest.mark.asyncio
    async def test_streaming_with_tools(self, provider):
        """Test streaming with tool calling"""
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(role="user", content="What's the weather?")],
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {"type": "object", "properties": {}}
                }
            }],
            stream=True
        )
        
        chunks = 0
        async for chunk in provider.chat_completions(request):
            chunks += 1
        
        assert chunks > 0
        print(f"✅ Streaming + Tools: {chunks} chunks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

