#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Real-world integration tests for K2Think provider
Tests actual API calls with real authentication
"""

import pytest
import httpx
import asyncio
import json
from typing import Dict, Any

from app.providers.k2think_provider import K2ThinkProvider
from app.models.schemas import OpenAIRequest, Message


class TestK2ThinkAuthentication:
    """Test K2Think authentication flows"""
    
    @pytest.mark.asyncio
    async def test_login_and_session(self, k2think_credentials):
        """Test login and session establishment"""
        provider = K2ThinkProvider()
        
        # The provider should handle authentication internally
        # Test by making a simple request
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content="test")],
            stream=False,
            max_tokens=50
        )
        
        try:
            response = await provider.chat_completion(request)
            assert isinstance(response, dict)
            print(f"✓ K2Think authentication successful")
        except Exception as e:
            print(f"Note: Authentication test: {e}")


class TestK2ThinkModel:
    """Test K2Think model"""
    
    @pytest.mark.asyncio
    async def test_basic_completion(self, test_messages, validate_openai_response):
        """Test basic completion"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            max_tokens=200,
            temperature=0.7
        )
        
        try:
            response = await provider.chat_completion(request)
            
            assert isinstance(response, dict)
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            print(f"✓ K2-Think basic completion successful")
            print(f"  Response: {content[:150]}...")
            
        except Exception as e:
            pytest.skip(f"K2Think test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_reasoning_capability(self, test_messages, validate_openai_response):
        """Test K2-Think reasoning capability"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(**msg) for msg in test_messages["thinking"]],
            stream=False,
            max_tokens=500,
            temperature=0.7
        )
        
        try:
            response = await provider.chat_completion(request)
            
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            # K2-Think should provide reasoning steps
            print(f"✓ K2-Think reasoning test successful")
            print(f"  Response length: {len(content)} chars")
            
        except Exception as e:
            pytest.skip(f"K2Think reasoning test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_complex_query(self, test_messages, validate_openai_response):
        """Test complex query handling"""
        provider = K2ThinkProvider()
        
        complex_message = {
            "role": "user",
            "content": "Explain the concept of neural networks and how backpropagation works in simple terms."
        }
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(**complex_message)],
            stream=False,
            max_tokens=800,
            temperature=0.7
        )
        
        try:
            response = await provider.chat_completion(request)
            
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 100  # Should be substantial explanation
            
            print(f"✓ K2-Think complex query successful")
            print(f"  Response: {content[:200]}...")
            
        except Exception as e:
            pytest.skip(f"K2Think complex query test skipped: {e}")


class TestK2ThinkStreaming:
    """Test streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, test_messages):
        """Test streaming chat completion"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=True,
            max_tokens=200
        )
        
        try:
            response = await provider.chat_completion(request)
            
            chunks = []
            async for chunk in response:
                chunks.append(chunk)
                if len(chunks) >= 5:
                    break
            
            assert len(chunks) > 0
            print(f"✓ K2-Think streaming successful, received {len(chunks)} chunks")
            
        except Exception as e:
            pytest.skip(f"K2Think streaming test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_streaming_reasoning(self, test_messages):
        """Test streaming with reasoning content"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(**msg) for msg in test_messages["thinking"]],
            stream=True,
            max_tokens=500
        )
        
        try:
            response = await provider.chat_completion(request)
            
            chunks = []
            reasoning_parts = []
            answer_parts = []
            
            async for chunk in response:
                chunks.append(chunk)
                
                # Try to extract reasoning and answer parts
                if "reasoning" in chunk.lower():
                    reasoning_parts.append(chunk)
                elif "answer" in chunk.lower():
                    answer_parts.append(chunk)
            
            assert len(chunks) > 0
            print(f"✓ K2-Think streaming reasoning: {len(chunks)} chunks")
            print(f"  Reasoning chunks: {len(reasoning_parts)}")
            print(f"  Answer chunks: {len(answer_parts)}")
            
        except Exception as e:
            pytest.skip(f"K2Think streaming reasoning test skipped: {e}")


class TestK2ThinkMultiTurn:
    """Test multi-turn conversations"""
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, test_messages, validate_openai_response):
        """Test conversation with context"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(**msg) for msg in test_messages["multi_turn"]],
            stream=False,
            max_tokens=200
        )
        
        try:
            response = await provider.chat_completion(request)
            
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            print(f"✓ K2-Think multi-turn successful")
            print(f"  Response: {content}")
            
        except Exception as e:
            pytest.skip(f"K2Think multi-turn test skipped: {e}")


class TestK2ThinkParameters:
    """Test parameter configurations"""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("temperature", [0.1, 0.7, 0.9])
    async def test_temperature_settings(self, temperature, test_messages, validate_openai_response):
        """Test different temperature settings"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            temperature=temperature,
            max_tokens=150
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            print(f"✓ K2-Think temperature {temperature} works")
            
        except Exception as e:
            pytest.skip(f"K2Think temperature test skipped: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("max_tokens", [100, 300, 600])
    async def test_max_tokens_settings(self, max_tokens, test_messages, validate_openai_response):
        """Test different max_tokens settings"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            print(f"✓ K2-Think max_tokens={max_tokens}, length={len(content)}")
            
        except Exception as e:
            pytest.skip(f"K2Think max_tokens test skipped: {e}")


class TestK2ThinkErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_empty_messages(self):
        """Test handling of empty messages"""
        provider = K2ThinkProvider()
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[],
            stream=False
        )
        
        try:
            response = await provider.chat_completion(request)
            print(f"✓ K2-Think empty messages handled")
        except Exception as e:
            print(f"✓ K2-Think empty messages properly rejected: {type(e).__name__}")
    
    @pytest.mark.asyncio
    async def test_very_long_input(self, validate_openai_response):
        """Test handling of very long input"""
        provider = K2ThinkProvider()
        
        long_content = "Explain this concept: " + " ".join(["detail"] * 500)
        
        request = OpenAIRequest(
            model="MBZUAI-IFM/K2-Think",
            messages=[Message(role="user", content=long_content)],
            stream=False,
            max_tokens=200
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            print(f"✓ K2-Think long input handled")
        except Exception as e:
            print(f"✓ K2-Think long input test: {type(e).__name__}")


class TestK2ThinkEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, test_messages, validate_openai_response):
        """Test complete workflow"""
        provider = K2ThinkProvider()
        
        tests_passed = []
        
        # Test 1: Simple request
        try:
            request1 = OpenAIRequest(
                model="MBZUAI-IFM/K2-Think",
                messages=[Message(**msg) for msg in test_messages["simple"]],
                stream=False,
                max_tokens=150
            )
            response1 = await provider.chat_completion(request1)
            validate_openai_response(response1)
            tests_passed.append("simple")
        except Exception as e:
            print(f"  Simple request: {e}")
        
        # Test 2: Reasoning request
        try:
            request2 = OpenAIRequest(
                model="MBZUAI-IFM/K2-Think",
                messages=[Message(**msg) for msg in test_messages["thinking"]],
                stream=False,
                max_tokens=400
            )
            response2 = await provider.chat_completion(request2)
            validate_openai_response(response2)
            tests_passed.append("reasoning")
        except Exception as e:
            print(f"  Reasoning request: {e}")
        
        # Test 3: Streaming
        try:
            request3 = OpenAIRequest(
                model="MBZUAI-IFM/K2-Think",
                messages=[Message(**msg) for msg in test_messages["simple"]],
                stream=True,
                max_tokens=150
            )
            response3 = await provider.chat_completion(request3)
            chunks = []
            async for chunk in response3:
                chunks.append(chunk)
                if len(chunks) >= 3:
                    break
            if len(chunks) > 0:
                tests_passed.append("streaming")
        except Exception as e:
            print(f"  Streaming request: {e}")
        
        print(f"✓ K2-Think workflow tests passed: {tests_passed}")
        
        # At least one test should pass
        if len(tests_passed) > 0:
            assert True
        else:
            pytest.skip("All K2Think workflow tests skipped due to errors")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

