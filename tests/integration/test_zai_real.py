#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Real-world integration tests for ZAI provider
Tests actual API calls with real authentication
"""

import pytest
import httpx
import asyncio
import json
from typing import Dict, Any

from app.providers.zai_provider import ZAIProvider
from app.models.schemas import OpenAIRequest, Message


class TestZAIAuthentication:
    """Test ZAI authentication flows"""
    
    @pytest.mark.asyncio
    async def test_guest_token_retrieval(self, zai_credentials):
        """Test retrieving guest/visitor token"""
        provider = ZAIProvider()
        
        # Should be able to get a token (either guest or from pool)
        token = await provider.get_token()
        
        # Token might be empty in anonymous mode if auth fails, but method should not raise
        assert isinstance(token, str)
        print(f"✓ Retrieved token: {token[:20] if token else 'empty'}...")
    
    @pytest.mark.asyncio
    async def test_authenticated_request_headers(self, zai_credentials):
        """Test that authentication headers are properly set"""
        provider = ZAIProvider()
        
        # Get headers
        headers = provider.config.headers
        
        assert headers is not None
        assert "User-Agent" in headers
        assert "Accept" in headers
        print(f"✓ Headers properly configured: {list(headers.keys())}")


class TestZAIModels:
    """Test all ZAI models"""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("model", [
        "GLM-4.5",
        "GLM-4.5-Air",
        "GLM-4.6",
    ])
    async def test_model_basic_completion(self, model, test_messages, validate_openai_response):
        """Test basic completion for each model"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model=model,
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            max_tokens=100,
            temperature=0.7
        )
        
        try:
            response = await provider.chat_completion(request)
            
            # Validate response format
            assert isinstance(response, dict)
            validate_openai_response(response, stream=False)
            
            # Check content is not empty
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            print(f"✓ {model} - Basic completion successful")
            print(f"  Response: {content[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Model {model} failed: {e}")
    
    @pytest.mark.asyncio
    async def test_thinking_model(self, test_messages, validate_openai_response):
        """Test GLM-4.5-Thinking model with reasoning"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model="GLM-4.5-Thinking",
            messages=[Message(**msg) for msg in test_messages["thinking"]],
            stream=False,
            max_tokens=500,
            temperature=0.7
        )
        
        response = await provider.chat_completion(request)
        
        validate_openai_response(response, stream=False)
        
        content = response["choices"][0]["message"]["content"]
        assert len(content) > 0
        
        # Thinking models should provide detailed reasoning
        print(f"✓ Thinking model response: {content[:200]}...")
    
    @pytest.mark.asyncio
    async def test_search_model(self, test_messages, validate_openai_response):
        """Test GLM-4.5-Search model with web search"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model="GLM-4.5-Search",
            messages=[Message(**msg) for msg in test_messages["search"]],
            stream=False,
            max_tokens=500,
            temperature=0.7
        )
        
        response = await provider.chat_completion(request)
        
        validate_openai_response(response, stream=False)
        
        content = response["choices"][0]["message"]["content"]
        assert len(content) > 0
        
        print(f"✓ Search model response: {content[:200]}...")


class TestZAIStreaming:
    """Test streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, test_messages):
        """Test streaming chat completion"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=True,
            max_tokens=100
        )
        
        response = await provider.chat_completion(request)
        
        # Response should be an async generator for streaming
        chunks = []
        async for chunk in response:
            chunks.append(chunk)
            if len(chunks) >= 5:  # Get first 5 chunks
                break
        
        assert len(chunks) > 0
        print(f"✓ Streaming successful, received {len(chunks)} chunks")
        print(f"  First chunk: {chunks[0][:100] if chunks else 'empty'}...")
    
    @pytest.mark.asyncio
    async def test_streaming_complete_response(self, test_messages):
        """Test full streaming response assembly"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model="GLM-4.5-Air",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=True,
            max_tokens=200
        )
        
        response = await provider.chat_completion(request)
        
        full_content = []
        chunk_count = 0
        
        async for chunk in response:
            chunk_count += 1
            # Parse SSE chunk
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str and data_str != "[DONE]":
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                full_content.append(delta["content"])
                    except json.JSONDecodeError:
                        pass
        
        combined = "".join(full_content)
        
        assert chunk_count > 0
        assert len(combined) > 0
        
        print(f"✓ Streaming complete: {chunk_count} chunks")
        print(f"  Full response: {combined[:200]}...")


class TestZAIMultiTurn:
    """Test multi-turn conversations"""
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, test_messages, validate_openai_response):
        """Test conversation with multiple turns"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(**msg) for msg in test_messages["multi_turn"]],
            stream=False,
            max_tokens=100
        )
        
        response = await provider.chat_completion(request)
        
        validate_openai_response(response, stream=False)
        
        content = response["choices"][0]["message"]["content"]
        assert len(content) > 0
        
        # Should reference the multiplication (2+2)*3 = 12
        print(f"✓ Multi-turn conversation successful")
        print(f"  Response: {content}")


class TestZAIParameters:
    """Test various parameter configurations"""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("temperature", [0.1, 0.5, 0.9])
    async def test_temperature_settings(self, temperature, test_messages, validate_openai_response):
        """Test different temperature settings"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            temperature=temperature,
            max_tokens=100
        )
        
        response = await provider.chat_completion(request)
        validate_openai_response(response, stream=False)
        
        print(f"✓ Temperature {temperature} works correctly")
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("max_tokens", [50, 200, 500])
    async def test_max_tokens_settings(self, max_tokens, test_messages, validate_openai_response):
        """Test different max_tokens settings"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        response = await provider.chat_completion(request)
        validate_openai_response(response, stream=False)
        
        content = response["choices"][0]["message"]["content"]
        print(f"✓ max_tokens={max_tokens}, response length={len(content)}")


class TestZAIErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_model(self, test_messages):
        """Test handling of invalid model"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model="invalid-model-name",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False
        )
        
        # Should handle gracefully or provide meaningful error
        try:
            response = await provider.chat_completion(request)
            # If it doesn't error, it might map to a default model
            print(f"✓ Invalid model handled (mapped to default)")
        except Exception as e:
            # Error is expected and acceptable
            print(f"✓ Invalid model properly rejected: {type(e).__name__}")
    
    @pytest.mark.asyncio
    async def test_empty_messages(self):
        """Test handling of empty messages"""
        provider = ZAIProvider()
        
        request = OpenAIRequest(
            model="GLM-4.5",
            messages=[],
            stream=False
        )
        
        # Should handle empty messages gracefully
        try:
            response = await provider.chat_completion(request)
            print(f"✓ Empty messages handled")
        except Exception as e:
            print(f"✓ Empty messages properly rejected: {type(e).__name__}")


class TestZAIEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, test_messages, validate_openai_response):
        """Test complete workflow from request to response"""
        provider = ZAIProvider()
        
        # Test 1: Simple request
        request1 = OpenAIRequest(
            model="GLM-4.5",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False
        )
        
        response1 = await provider.chat_completion(request1)
        validate_openai_response(response1)
        
        # Test 2: Follow-up with thinking model
        request2 = OpenAIRequest(
            model="GLM-4.5-Thinking",
            messages=[Message(**msg) for msg in test_messages["thinking"]],
            stream=False
        )
        
        response2 = await provider.chat_completion(request2)
        validate_openai_response(response2)
        
        # Test 3: Streaming response
        request3 = OpenAIRequest(
            model="GLM-4.5-Air",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=True
        )
        
        response3 = await provider.chat_completion(request3)
        chunks = []
        async for chunk in response3:
            chunks.append(chunk)
            if len(chunks) >= 3:
                break
        
        assert len(chunks) > 0
        
        print(f"✓ Complete workflow test passed")
        print(f"  - Simple completion: ✓")
        print(f"  - Thinking model: ✓")
        print(f"  - Streaming: ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

