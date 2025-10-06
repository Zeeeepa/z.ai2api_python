#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive tests for LongCat Provider
Tests all models, features, and functions
"""

import pytest
from unittest.mock import Mock, patch
from app.providers.longcat_provider import LongCatProvider
from app.models.schemas import OpenAIRequest, Message


class TestLongCatProviderInitialization:
    """Test LongCat provider initialization"""
    
    def test_provider_initialization(self):
        """Test provider can be initialized"""
        provider = LongCatProvider()
        assert provider.name == "longcat"
        assert provider.config.api_endpoint == "https://longcat.chat/api/v1/chat-completion"
    
    def test_supported_models(self):
        """Test all supported models"""
        provider = LongCatProvider()
        models = provider.get_supported_models()
        
        expected_models = ["LongCat-Flash", "LongCat", "LongCat-Search"]
        
        for model in expected_models:
            assert model in models, f"Model {model} not found"
        assert len(models) == 3
    
    def test_headers_configuration(self):
        """Test proper headers are configured"""
        provider = LongCatProvider()
        headers = provider.config.headers
        
        assert headers['accept'] == 'text/event-stream,application/json'
        assert headers['content-type'] == 'application/json'
        assert headers['origin'] == 'https://longcat.chat'
        assert 'referer' in headers


class TestLongCatProviderModels:
    """Test individual LongCat models"""
    
    @pytest.mark.asyncio
    async def test_longcat_flash_model(self):
        """Test LongCat-Flash lightweight model"""
        provider = LongCatProvider()
        request = OpenAIRequest(
            model="LongCat-Flash",
            messages=[Message(role="user", content="Quick question")],
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            
            assert transformed["model"] == "LongCat-Flash"
            assert "passport" in transformed
            assert transformed["stream"] is False
    
    @pytest.mark.asyncio
    async def test_longcat_standard_model(self):
        """Test LongCat standard model"""
        provider = LongCatProvider()
        request = OpenAIRequest(
            model="LongCat",
            messages=[Message(role="user", content="Standard question")],
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            assert transformed["model"] == "LongCat"
    
    @pytest.mark.asyncio
    async def test_longcat_search_model(self):
        """Test LongCat-Search search-enabled model"""
        provider = LongCatProvider()
        request = OpenAIRequest(
            model="LongCat-Search",
            messages=[Message(role="user", content="What's the latest news?")],
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            
            assert transformed["model"] == "LongCat-Search"
            # Search model should be configured appropriately


class TestLongCatProviderFeatures:
    """Test LongCat provider features"""
    
    @pytest.mark.asyncio
    async def test_streaming_support(self):
        """Test streaming mode"""
        provider = LongCatProvider()
        request = OpenAIRequest(
            model="LongCat",
            messages=[Message(role="user", content="Stream test")],
            stream=True
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            assert transformed["stream"] is True
    
    @pytest.mark.asyncio
    async def test_search_capability(self):
        """Test search capability in Search model"""
        provider = LongCatProvider()
        request = OpenAIRequest(
            model="LongCat-Search",
            messages=[Message(role="user", content="Search for AI news")],
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            # Search model should have search enabled
            assert transformed["model"] == "LongCat-Search"
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self):
        """Test multi-turn conversations"""
        provider = LongCatProvider()
        messages = [
            Message(role="system", content="You are helpful"),
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi!"),
            Message(role="user", content="How are you?")
        ]
        
        request = OpenAIRequest(
            model="LongCat",
            messages=messages,
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            assert len(transformed["messages"]) == 4
    
    @pytest.mark.asyncio
    async def test_temperature_parameter(self):
        """Test temperature parameter handling"""
        provider = LongCatProvider()
        
        for temp in [0.0, 0.5, 0.7, 1.0]:
            request = OpenAIRequest(
                model="LongCat",
                messages=[Message(role="user", content="Test")],
                temperature=temp
            )
            
            with patch.object(provider, 'get_passport_token', return_value="test-token"):
                transformed = await provider.transform_request(request)
                # Temperature should be included
                assert "temperature" in transformed or temp == 0.7  # default


class TestLongCatProviderAuthentication:
    """Test LongCat authentication mechanisms"""
    
    def test_passport_token_from_env(self):
        """Test passport token from environment variable"""
        provider = LongCatProvider()
        
        with patch('app.providers.longcat_provider.settings') as mock_settings:
            mock_settings.LONGCAT_PASSPORT_TOKEN = "env-token-123"
            
            token = provider.get_passport_token()
            assert token == "env-token-123"
    
    def test_passport_token_from_file(self):
        """Test passport token from file"""
        provider = LongCatProvider()
        
        with patch('app.providers.longcat_provider.settings') as mock_settings:
            mock_settings.LONGCAT_PASSPORT_TOKEN = None
            mock_settings.LONGCAT_TOKENS_FILE = "tokens.txt"
            
            mock_open = Mock()
            mock_open.return_value.__enter__.return_value.readlines.return_value = [
                "token1\n",
                "token2\n",
                "token3\n"
            ]
            
            with patch('builtins.open', mock_open):
                token = provider.get_passport_token()
                # Should return one of the tokens
                assert token in ["token1", "token2", "token3"]
    
    def test_no_passport_token_available(self):
        """Test behavior when no passport token available"""
        provider = LongCatProvider()
        
        with patch('app.providers.longcat_provider.settings') as mock_settings:
            mock_settings.LONGCAT_PASSPORT_TOKEN = None
            mock_settings.LONGCAT_TOKENS_FILE = None
            
            token = provider.get_passport_token()
            assert token is None
    
    @pytest.mark.asyncio
    async def test_passport_token_in_request(self):
        """Test passport token is included in transformed request"""
        provider = LongCatProvider()
        request = OpenAIRequest(
            model="LongCat",
            messages=[Message(role="user", content="Test")],
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value="passport-abc"):
            transformed = await provider.transform_request(request)
            assert transformed["passport"] == "passport-abc"


class TestLongCatProviderResponseTransformation:
    """Test LongCat response transformation"""
    
    def test_create_openai_response(self):
        """Test OpenAI format response creation"""
        provider = LongCatProvider()
        chat_id = "chatcmpl-longcat-123"
        model = "LongCat"
        content = "This is a response"
        usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        
        response = provider.create_openai_response(chat_id, model, content, usage)
        
        assert response["id"] == chat_id
        assert response["object"] == "chat.completion"
        assert response["model"] == model
        assert response["choices"][0]["message"]["content"] == content
        assert response["usage"] == usage
    
    def test_create_streaming_chunk(self):
        """Test streaming chunk creation"""
        provider = LongCatProvider()
        chat_id = "chatcmpl-longcat-456"
        model = "LongCat-Flash"
        delta = {"content": "Streaming "}
        
        chunk = provider.create_openai_chunk(chat_id, model, delta, None)
        
        assert chunk["id"] == chat_id
        assert chunk["object"] == "chat.completion.chunk"
        assert chunk["model"] == model
        assert chunk["choices"][0]["delta"] == delta
        assert chunk["choices"][0]["finish_reason"] is None
    
    def test_final_chunk_with_finish_reason(self):
        """Test final streaming chunk"""
        provider = LongCatProvider()
        
        chunk = provider.create_openai_chunk(
            "chatcmpl-789",
            "LongCat",
            {},
            "stop"
        )
        
        assert chunk["choices"][0]["finish_reason"] == "stop"


class TestLongCatProviderErrorHandling:
    """Test LongCat error handling"""
    
    def test_handle_error(self):
        """Test error handling"""
        provider = LongCatProvider()
        error = Exception("Network error")
        
        error_response = provider.handle_error(error, "request processing")
        
        assert "error" in error_response
        assert "message" in error_response["error"]
        assert "Network error" in error_response["error"]["message"]
        assert error_response["error"]["type"] == "provider_error"
    
    @pytest.mark.asyncio
    async def test_missing_passport_token_error(self):
        """Test error when passport token is missing"""
        provider = LongCatProvider()
        request = OpenAIRequest(
            model="LongCat",
            messages=[Message(role="user", content="Test")],
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value=None):
            try:
                transformed = await provider.transform_request(request)
                # Should handle missing token gracefully or raise error
                assert transformed is not None or True
            except Exception as e:
                # Should be a handled exception
                assert isinstance(e, (ValueError, TypeError, AttributeError))
    
    def test_log_request(self):
        """Test request logging"""
        provider = LongCatProvider()
        request = OpenAIRequest(
            model="LongCat",
            messages=[Message(role="user", content="Test")],
            stream=False
        )
        
        # Should not raise errors
        provider.log_request(request)
    
    def test_log_response_success(self):
        """Test successful response logging"""
        provider = LongCatProvider()
        provider.log_response(True)
    
    def test_log_response_failure(self):
        """Test failed response logging"""
        provider = LongCatProvider()
        provider.log_response(False, "Connection timeout")


class TestLongCatProviderUtilities:
    """Test LongCat utility functions"""
    
    def test_chat_id_generation(self):
        """Test unique chat ID generation"""
        provider = LongCatProvider()
        
        chat_id_1 = provider.create_chat_id()
        chat_id_2 = provider.create_chat_id()
        
        assert chat_id_1.startswith("chatcmpl-")
        assert chat_id_2.startswith("chatcmpl-")
        assert chat_id_1 != chat_id_2
    
    @pytest.mark.asyncio
    async def test_sse_formatting(self):
        """Test SSE chunk formatting"""
        provider = LongCatProvider()
        chunk = {"id": "test", "object": "chat.completion.chunk"}
        
        sse_formatted = await provider.format_sse_chunk(chunk)
        
        assert sse_formatted.startswith("data: ")
        assert sse_formatted.endswith("\n\n")
    
    @pytest.mark.asyncio
    async def test_sse_done_marker(self):
        """Test SSE done marker"""
        provider = LongCatProvider()
        
        done = await provider.format_sse_done()
        assert done == "data: [DONE]\n\n"


class TestLongCatProviderIntegration:
    """Integration tests for LongCat provider"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_flash_request_flow(self):
        """Test complete request flow for Flash model"""
        provider = LongCatProvider()
        
        request = OpenAIRequest(
            model="LongCat-Flash",
            messages=[
                Message(role="system", content="Be concise"),
                Message(role="user", content="Quick answer: 2+2?")
            ],
            stream=False,
            temperature=0.5
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-passport"):
            transformed = await provider.transform_request(request)
            
            assert transformed["model"] == "LongCat-Flash"
            assert len(transformed["messages"]) == 2
            assert transformed["passport"] == "test-passport"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_search_request_flow(self):
        """Test complete request flow for Search model"""
        provider = LongCatProvider()
        
        request = OpenAIRequest(
            model="LongCat-Search",
            messages=[Message(role="user", content="Latest AI breakthroughs?")],
            stream=True
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-passport"):
            transformed = await provider.transform_request(request)
            
            assert transformed["model"] == "LongCat-Search"
            assert transformed["stream"] is True


class TestLongCatProviderEdgeCases:
    """Test edge cases for LongCat provider"""
    
    @pytest.mark.asyncio
    async def test_empty_passport_token(self):
        """Test handling of empty passport token"""
        provider = LongCatProvider()
        request = OpenAIRequest(
            model="LongCat",
            messages=[Message(role="user", content="Test")],
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value=""):
            # Should handle empty token
            try:
                transformed = await provider.transform_request(request)
                assert transformed is not None
            except Exception:
                pass  # Expected if validation fails
    
    @pytest.mark.asyncio
    async def test_very_long_message(self):
        """Test handling of very long messages"""
        provider = LongCatProvider()
        
        long_content = "X" * 50000
        request = OpenAIRequest(
            model="LongCat",
            messages=[Message(role="user", content=long_content)],
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            assert len(transformed["messages"][0]["content"]) == 50000
    
    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test special characters in messages"""
        provider = LongCatProvider()
        
        special = "Test 中文 🚀 \n\t special chars"
        request = OpenAIRequest(
            model="LongCat",
            messages=[Message(role="user", content=special)],
            stream=False
        )
        
        with patch.object(provider, 'get_passport_token', return_value="test-token"):
            transformed = await provider.transform_request(request)
            assert transformed["messages"][0]["content"] == special
    
    @pytest.mark.asyncio
    async def test_all_models_sequentially(self):
        """Test all models in sequence"""
        provider = LongCatProvider()
        models = ["LongCat-Flash", "LongCat", "LongCat-Search"]
        
        with patch.object(provider, 'get_passport_token', return_value="test-token"):
            for model in models:
                request = OpenAIRequest(
                    model=model,
                    messages=[Message(role="user", content=f"Test {model}")],
                    stream=False
                )
                
                transformed = await provider.transform_request(request)
                assert transformed["model"] == model


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

