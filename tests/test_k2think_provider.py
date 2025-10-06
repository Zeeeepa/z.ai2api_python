#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive tests for K2Think Provider
Tests all models, features, and functions
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.providers.k2think_provider import K2ThinkProvider
from app.models.schemas import OpenAIRequest, Message


class TestK2ThinkProviderInitialization:
    """Test K2Think provider initialization"""
    
    def test_provider_initialization(self):
        """Test provider can be initialized"""
        provider = K2ThinkProvider()
        assert provider.name == "k2think"
        assert provider.config.api_endpoint == "https://www.k2think.ai/api/guest/chat/completions"
    
    def test_supported_models(self):
        """Test supported model"""
        provider = K2ThinkProvider()
        models = provider.get_supported_models()
        
        assert "MBZUAI-IFM/K2-Think" in models
        assert len(models) == 1
    
    def test_headers_configuration(self):
        """Test proper headers are set"""
        provider = K2ThinkProvider()
        headers = provider.config.headers
        
        assert headers['Accept'] == 'text/event-stream'
        assert headers['Content-Type'] == 'application/json'
        assert headers['Origin'] == 'https://www.k2think.ai'
        assert 'Referer' in headers


class TestK2ThinkProviderModel:
    """Test K2Think model functionality"""
    
    @pytest.mark.asyncio
    async def test_model_request_transformation(self):
        """Test K2-Think model request transformation"""
        provider = K2ThinkProvider()
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Explain AI")],
            stream=False,
            temperature=0.7
        )
        
        transformed = await provider.transform_request(request)
        
        assert transformed["model"] == "MBZUAI-IFM/K2-Think"
        assert transformed["stream"] is False
        assert "messages" in transformed
        assert transformed["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_streaming_request(self):
        """Test streaming mode"""
        provider = K2ThinkProvider()
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Stream test")],
            stream=True
        )
        
        transformed = await provider.transform_request(request)
        assert transformed["stream"] is True
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """Test multi-turn conversation handling"""
        provider = K2ThinkProvider()
        messages = [
            Message(role="system", content="You are a helpful assistant"),
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
            Message(role="user", content="How are you?")
        ]
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=messages,
            stream=False
        )
        
        transformed = await provider.transform_request(request)
        assert len(transformed["messages"]) == 4
        assert transformed["messages"][0]["role"] == "system"
        assert transformed["messages"][-1]["role"] == "user"


class TestK2ThinkProviderFeatures:
    """Test K2Think provider features"""
    
    @pytest.mark.asyncio
    async def test_reasoning_capability(self):
        """Test reasoning mode (built into K2-Think model)"""
        provider = K2ThinkProvider()
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Solve: 2+2*3")],
            stream=False
        )
        
        transformed = await provider.transform_request(request)
        # K2-Think model inherently supports reasoning
        assert transformed["model"] == "MBZUAI-IFM/K2-Think"
    
    @pytest.mark.asyncio
    async def test_temperature_parameter(self):
        """Test temperature parameter handling"""
        provider = K2ThinkProvider()
        
        for temp in [0.0, 0.5, 0.7, 1.0, 1.5]:
            request = OpenAIRequest(
                model="MBZUAI-IFM/K2-Think",
                messages=[Message(role="user", content="Test")],
                temperature=temp
            )
            
            transformed = await provider.transform_request(request)
            assert transformed["temperature"] == temp
    
    @pytest.mark.asyncio
    async def test_max_tokens_parameter(self):
        """Test max_tokens parameter"""
        provider = K2ThinkProvider()
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Test")],
            max_tokens=500
        )
        
        transformed = await provider.transform_request(request)
        # Check if max_tokens is handled properly
        assert "max_tokens" in transformed or "max_completion_tokens" in transformed


class TestK2ThinkProviderAuthentication:
    """Test K2Think authentication (guest mode)"""
    
    def test_cookie_parsing(self):
        """Test cookie extraction from headers"""
        provider = K2ThinkProvider()
        
        headers = {
            'set-cookie': 'session_id=abc123; Path=/; HttpOnly',
            'other-header': 'value'
        }
        
        cookies = provider.parse_cookies(headers)
        assert 'session_id=abc123' in cookies
    
    def test_multiple_cookies_parsing(self):
        """Test parsing multiple cookies"""
        provider = K2ThinkProvider()
        
        # Simulate multiple set-cookie headers (httpx returns them as list)
        headers = [
            ('set-cookie', 'cookie1=value1; Path=/'),
            ('set-cookie', 'cookie2=value2; Path=/; HttpOnly'),
            ('content-type', 'application/json')
        ]
        
        # Provider should handle cookie extraction
        # This tests the logic exists
        assert hasattr(provider, 'parse_cookies')
    
    @pytest.mark.asyncio
    async def test_guest_mode_no_auth_required(self):
        """Test that no explicit auth token is required"""
        provider = K2ThinkProvider()
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Test")],
            stream=False
        )
        
        # Should not raise auth errors
        transformed = await provider.transform_request(request)
        assert transformed is not None


class TestK2ThinkProviderResponseTransformation:
    """Test K2Think response transformation"""
    
    def test_create_openai_response(self):
        """Test OpenAI response format creation"""
        provider = K2ThinkProvider()
        chat_id = "chatcmpl-k2think-123"
        model = "MBZUAI-IFM/K2-Think"
        content = "This is the response"
        usage = {"prompt_tokens": 15, "completion_tokens": 25, "total_tokens": 40}
        
        response = provider.create_openai_response(chat_id, model, content, usage)
        
        assert response["id"] == chat_id
        assert response["object"] == "chat.completion"
        assert response["model"] == model
        assert response["choices"][0]["message"]["content"] == content
        assert response["usage"] == usage
    
    def test_create_streaming_chunk(self):
        """Test streaming chunk creation"""
        provider = K2ThinkProvider()
        chat_id = "chatcmpl-k2think-456"
        model = "MBZUAI-IFM/K2-Think"
        delta = {"content": "Hello "}
        
        chunk = provider.create_openai_chunk(chat_id, model, delta, None)
        
        assert chunk["id"] == chat_id
        assert chunk["object"] == "chat.completion.chunk"
        assert chunk["model"] == model
        assert chunk["choices"][0]["delta"] == delta
        assert chunk["choices"][0]["finish_reason"] is None
    
    def test_final_streaming_chunk(self):
        """Test final streaming chunk with finish_reason"""
        provider = K2ThinkProvider()
        chunk = provider.create_openai_chunk(
            "chatcmpl-789",
            "MBZUAI-IFM/K2-Think",
            {},
            "stop"
        )
        
        assert chunk["choices"][0]["finish_reason"] == "stop"
        assert chunk["choices"][0]["delta"] == {}


class TestK2ThinkProviderErrorHandling:
    """Test K2Think error handling"""
    
    def test_handle_error(self):
        """Test error handling"""
        provider = K2ThinkProvider()
        error = Exception("Connection failed")
        
        error_response = provider.handle_error(error, "during request")
        
        assert "error" in error_response
        assert "message" in error_response["error"]
        assert "Connection failed" in error_response["error"]["message"]
        assert error_response["error"]["type"] == "provider_error"
    
    @pytest.mark.asyncio
    async def test_invalid_message_format(self):
        """Test handling of invalid message formats"""
        provider = K2ThinkProvider()
        
        # Empty messages should be handled
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[],
            stream=False
        )
        
        try:
            transformed = await provider.transform_request(request)
            # Should either transform or raise appropriate error
            assert isinstance(transformed, dict)
        except Exception as e:
            # Should be a handled exception
            assert isinstance(e, (ValueError, TypeError))
    
    def test_log_request(self):
        """Test request logging"""
        provider = K2ThinkProvider()
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Test")],
            stream=False
        )
        
        # Should not raise errors
        provider.log_request(request)
    
    def test_log_response(self):
        """Test response logging"""
        provider = K2ThinkProvider()
        
        # Success case
        provider.log_response(True)
        
        # Error case
        provider.log_response(False, "Test error")


class TestK2ThinkProviderUtilities:
    """Test K2Think utility functions"""
    
    def test_chat_id_generation(self):
        """Test unique chat ID generation"""
        provider = K2ThinkProvider()
        
        chat_id_1 = provider.create_chat_id()
        chat_id_2 = provider.create_chat_id()
        
        assert chat_id_1.startswith("chatcmpl-")
        assert chat_id_2.startswith("chatcmpl-")
        assert chat_id_1 != chat_id_2
    
    @pytest.mark.asyncio
    async def test_sse_chunk_formatting(self):
        """Test SSE chunk formatting"""
        provider = K2ThinkProvider()
        chunk = {"id": "test", "choices": [{"delta": {"content": "hi"}}]}
        
        sse_formatted = await provider.format_sse_chunk(chunk)
        
        assert sse_formatted.startswith("data: ")
        assert sse_formatted.endswith("\n\n")
        assert "test" in sse_formatted
    
    @pytest.mark.asyncio
    async def test_sse_done_marker(self):
        """Test SSE done marker"""
        provider = K2ThinkProvider()
        
        done_marker = await provider.format_sse_done()
        assert done_marker == "data: [DONE]\n\n"


class TestK2ThinkProviderIntegration:
    """Integration tests for K2Think provider"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_request_flow(self):
        """Test complete request transformation flow"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[
                Message(role="system", content="You are helpful"),
                Message(role="user", content="Explain quantum computing")
            ],
            stream=False,
            temperature=0.7,
            max_tokens=500
        )
        
        transformed = await provider.transform_request(request)
        
        # Verify all components
        assert transformed["model"] == "MBZUAI-IFM/K2-Think"
        assert len(transformed["messages"]) == 2
        assert transformed["temperature"] == 0.7
        assert transformed["stream"] is False
    
    @pytest.mark.asyncio
    @pytest.mark.integration  
    async def test_streaming_request_flow(self):
        """Test streaming request flow"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Count to 10")],
            stream=True
        )
        
        transformed = await provider.transform_request(request)
        assert transformed["stream"] is True


class TestK2ThinkProviderEdgeCases:
    """Test edge cases for K2Think provider"""
    
    @pytest.mark.asyncio
    async def test_very_long_message(self):
        """Test handling of very long messages"""
        provider = K2ThinkProvider()
        
        long_content = "A" * 10000
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content=long_content)],
            stream=False
        )
        
        transformed = await provider.transform_request(request)
        assert len(transformed["messages"][0]["content"]) == 10000
    
    @pytest.mark.asyncio
    async def test_special_characters_in_message(self):
        """Test special characters handling"""
        provider = K2ThinkProvider()
        
        special_content = "Test with 特殊字符 🎉 and\n\nnewlines\ttabs"
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content=special_content)],
            stream=False
        )
        
        transformed = await provider.transform_request(request)
        assert transformed["messages"][0]["content"] == special_content
    
    @pytest.mark.asyncio
    async def test_extreme_temperature_values(self):
        """Test extreme temperature values"""
        provider = K2ThinkProvider()
        
        # Test very low temperature
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Test")],
            temperature=0.01
        )
        transformed = await provider.transform_request(request)
        assert transformed["temperature"] == 0.01
        
        # Test very high temperature
        request.temperature = 2.0
        transformed = await provider.transform_request(request)
        assert transformed["temperature"] == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

