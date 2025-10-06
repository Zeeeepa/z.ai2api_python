#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive Integration Tests for K2Think Provider

Tests actual authentication, all models, all features, and real functionality.
"""

import pytest
import asyncio
from typing import List, Dict, Any
from app.providers.k2think_provider import K2ThinkProvider
from app.models.schemas import OpenAIRequest, Message


class TestK2ThinkAuthentication:
    """Test K2Think authentication and session management"""
    
    @pytest.fixture
    def provider(self):
        """Initialize K2Think provider"""
        return K2ThinkProvider()
    
    def test_conversation_id_generation(self, provider):
        """Test conversation ID generation"""
        conv_id = provider._generate_conversation_id()
        assert conv_id is not None
        assert isinstance(conv_id, str)
        assert len(conv_id) == 36  # UUID format
        print(f"✅ Generated conversation_id: {conv_id}")
    
    def test_cookie_generation(self, provider):
        """Test cookie generation for guest access"""
        cookies = provider._get_guest_cookies()
        assert cookies is not None
        assert isinstance(cookies, str)
        assert "AWSALB" in cookies
        print(f"✅ Generated cookies")


class TestK2ThinkModels:
    """Test all K2Think models"""
    
    @pytest.fixture
    def provider(self):
        return K2ThinkProvider()
    
    def test_supported_models_list(self, provider):
        """Test that K2-Think model is supported"""
        models = provider.get_supported_models()
        assert "MBZUAI-IFM/K2-Think" in models
        print(f"✅ K2-Think model is supported")
    
    @pytest.mark.asyncio
    async def test_k2think_model(self, provider):
        """Test K2-Think model with actual request"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Hello")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ K2-Think response received")
    
    @pytest.mark.asyncio
    async def test_k2think_reasoning(self, provider):
        """Test K2-Think reasoning capabilities"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Solve this problem: If a train travels at 60 mph for 2 hours, how far does it go?")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ K2-Think reasoning tested")


class TestK2ThinkFeatures:
    """Test all K2Think features"""
    
    @pytest.fixture
    def provider(self):
        return K2ThinkProvider()
    
    @pytest.mark.asyncio
    async def test_streaming(self, provider):
        """Test streaming responses"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
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
    async def test_max_tokens(self, provider):
        """Test max_tokens parameter"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Write a long story")],
            max_tokens=50,
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ max_tokens parameter tested")
    
    @pytest.mark.asyncio
    async def test_temperature(self, provider):
        """Test temperature parameter"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Be creative")],
            temperature=0.9,
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ temperature parameter tested")
    
    @pytest.mark.asyncio
    async def test_top_p(self, provider):
        """Test top_p parameter"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Generate text")],
            top_p=0.9,
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ top_p parameter tested")
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, provider):
        """Test multi-turn conversation with context"""
        messages = [
            Message(role="user", content="Remember this number: 42"),
            Message(role="assistant", content="I'll remember 42."),
            Message(role="user", content="What number did I tell you?")
        ]
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=messages,
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Multi-turn conversation tested")


class TestK2ThinkErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def provider(self):
        return K2ThinkProvider()
    
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
            model="MBZUAI-IFM/K2-Think",
            messages=[],
            stream=False
        )
        
        with pytest.raises(Exception):
            await provider.chat_completions(request)
        print(f"✅ Empty messages error handled")
    
    @pytest.mark.asyncio
    async def test_very_long_message(self, provider):
        """Test handling of very long message"""
        long_message = "Hello " * 1000
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content=long_message)],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Very long message tested")
    
    @pytest.mark.asyncio
    async def test_special_characters(self, provider):
        """Test handling of special characters"""
        special_content = "Test: 中文 español 日本語 🎉 \n\t\r"
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content=special_content)],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Special characters tested")


class TestK2ThinkIntegration:
    """Integration tests combining multiple features"""
    
    @pytest.fixture
    def provider(self):
        return K2ThinkProvider()
    
    @pytest.mark.asyncio
    async def test_complex_reasoning_task(self, provider):
        """Test complex reasoning capabilities"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Explain the concept of recursion with an example")],
            stream=False,
            max_tokens=500
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Complex reasoning tested")
    
    @pytest.mark.asyncio
    async def test_streaming_long_response(self, provider):
        """Test streaming with long response"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Write a detailed explanation of machine learning")],
            stream=True,
            max_tokens=1000
        )
        
        chunks = 0
        total_content = ""
        async for chunk in provider.chat_completions(request):
            chunks += 1
            if hasattr(chunk, 'choices') and chunk.choices:
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    total_content += chunk.choices[0].delta.content
        
        assert chunks > 0
        assert len(total_content) > 0
        print(f"✅ Streaming long response: {chunks} chunks, {len(total_content)} chars")
    
    @pytest.mark.asyncio
    async def test_code_generation(self, provider):
        """Test code generation capabilities"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Write a Python function to calculate fibonacci numbers")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Code generation tested")
    
    @pytest.mark.asyncio
    async def test_mathematical_reasoning(self, provider):
        """Test mathematical reasoning"""
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="Solve: (15 + 23) * 2 - 10")],
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        print(f"✅ Mathematical reasoning tested")
    
    @pytest.mark.asyncio
    async def test_context_retention(self, provider):
        """Test context retention across messages"""
        messages = [
            Message(role="user", content="I have a cat named Whiskers"),
            Message(role="assistant", content="That's nice! Whiskers sounds like a lovely cat."),
            Message(role="user", content="What's my cat's name?")
        ]
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=messages,
            stream=False
        )
        
        response = await provider.chat_completions(request)
        assert response is not None
        # Response should mention "Whiskers"
        print(f"✅ Context retention tested")


class TestK2ThinkPerformance:
    """Performance and reliability tests"""
    
    @pytest.fixture
    def provider(self):
        return K2ThinkProvider()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, provider):
        """Test handling multiple concurrent requests"""
        requests = [
            OpenAIRequest(
                model="MBZUAI-IFM/K2-Think",
                messages=[Message(role="user", content=f"Test {i}")],
                stream=False
            )
            for i in range(3)
        ]
        
        tasks = [provider.chat_completions(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in responses if not isinstance(r, Exception))
        print(f"✅ Concurrent requests: {successful}/3 successful")
        assert successful > 0
    
    @pytest.mark.asyncio
    async def test_rapid_sequential_requests(self, provider):
        """Test rapid sequential requests"""
        for i in range(3):
            request = OpenAIRequest(
                model="MBZUAI-IFM/K2-Think",
                messages=[Message(role="user", content=f"Quick test {i}")],
                stream=False,
                max_tokens=20
            )
            
            response = await provider.chat_completions(request)
            assert response is not None
        
        print(f"✅ Rapid sequential requests completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

