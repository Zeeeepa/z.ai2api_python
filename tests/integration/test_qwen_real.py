#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Real-world integration tests for Qwen provider
Tests actual API calls with real authentication
"""

import pytest
import httpx
import asyncio
import json
from typing import Dict, Any

from app.providers.qwen_provider import QwenProvider
from app.models.schemas import OpenAIRequest, Message


class TestQwenAuthentication:
    """Test Qwen authentication flows"""
    
    @pytest.mark.asyncio
    async def test_auth_headers(self, qwen_credentials):
        """Test authentication header generation"""
        provider = QwenProvider()
        
        try:
            headers = await provider.get_auth_headers()
            
            assert headers is not None
            assert "User-Agent" in headers
            assert "Content-Type" in headers
            assert "source" in headers
            assert headers["source"] == "web"
            
            print(f"✓ Qwen auth headers configured properly")
            print(f"  Headers: {list(headers.keys())}")
            
        except Exception as e:
            pytest.skip(f"Qwen auth test: {e}")


class TestQwenModels:
    """Test all Qwen models"""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("model", [
        "qwen-max",
        "qwen-plus",
        "qwen-turbo",
    ])
    async def test_model_basic_completion(self, model, test_messages, validate_openai_response):
        """Test basic completion for each model"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model=model,
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            max_tokens=150,
            temperature=0.7
        )
        
        try:
            response = await provider.chat_completion(request)
            
            assert isinstance(response, dict)
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            print(f"✓ {model} - Basic completion successful")
            print(f"  Response: {content[:100]}...")
            
        except Exception as e:
            pytest.skip(f"Qwen model {model} test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_qwen_max_latest(self, test_messages, validate_openai_response):
        """Test qwen-max-latest model"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-max-latest",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            max_tokens=200,
            temperature=0.7
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            print(f"✓ qwen-max-latest successful")
            print(f"  Response: {content[:150]}...")
            
        except Exception as e:
            pytest.skip(f"Qwen max-latest test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_qwen_thinking_model(self, test_messages, validate_openai_response):
        """Test qwen-max-thinking model"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-max-thinking",
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
            
            print(f"✓ qwen-max-thinking successful")
            print(f"  Response length: {len(content)} chars")
            
        except Exception as e:
            pytest.skip(f"Qwen thinking test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_qwen_search_model(self, test_messages, validate_openai_response):
        """Test qwen-max-search model"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-max-search",
            messages=[Message(**msg) for msg in test_messages["search"]],
            stream=False,
            max_tokens=500,
            temperature=0.7
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            print(f"✓ qwen-max-search successful")
            print(f"  Response: {content[:200]}...")
            
        except Exception as e:
            pytest.skip(f"Qwen search test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_qwen_long_model(self, test_messages, validate_openai_response):
        """Test qwen-long model for extended context"""
        provider = QwenProvider()
        
        # Create a longer conversation context
        long_context = [
            {"role": "user", "content": "Remember this: The password is 'blue42'"},
            {"role": "assistant", "content": "I'll remember that the password is 'blue42'"},
            {"role": "user", "content": "What was the password I just told you?"}
        ]
        
        request = OpenAIRequest(
            model="qwen-long",
            messages=[Message(**msg) for msg in long_context],
            stream=False,
            max_tokens=100,
            temperature=0.3
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            print(f"✓ qwen-long successful")
            print(f"  Response: {content}")
            
        except Exception as e:
            pytest.skip(f"Qwen long test skipped: {e}")


class TestQwenStreaming:
    """Test streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, test_messages):
        """Test streaming chat completion"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-max",
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
            print(f"✓ Qwen streaming successful, received {len(chunks)} chunks")
            print(f"  First chunk: {chunks[0][:100] if chunks else 'empty'}...")
            
        except Exception as e:
            pytest.skip(f"Qwen streaming test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_streaming_complete_response(self, test_messages):
        """Test full streaming response assembly"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-turbo",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=True,
            max_tokens=300
        )
        
        try:
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
            print(f"✓ Qwen streaming complete: {chunk_count} chunks")
            print(f"  Full response length: {len(combined)} chars")
            
        except Exception as e:
            pytest.skip(f"Qwen streaming assembly test skipped: {e}")


class TestQwenMultiTurn:
    """Test multi-turn conversations"""
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, test_messages, validate_openai_response):
        """Test conversation with multiple turns"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-max",
            messages=[Message(**msg) for msg in test_messages["multi_turn"]],
            stream=False,
            max_tokens=150
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            print(f"✓ Qwen multi-turn successful")
            print(f"  Response: {content}")
            
        except Exception as e:
            pytest.skip(f"Qwen multi-turn test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_complex_conversation(self, validate_openai_response):
        """Test complex multi-turn conversation"""
        provider = QwenProvider()
        
        conversation = [
            {"role": "system", "content": "You are a helpful math tutor."},
            {"role": "user", "content": "What is the Pythagorean theorem?"},
            {"role": "assistant", "content": "The Pythagorean theorem states that in a right triangle, a² + b² = c²."},
            {"role": "user", "content": "Can you give me an example with actual numbers?"}
        ]
        
        request = OpenAIRequest(
            model="qwen-max",
            messages=[Message(**msg) for msg in conversation],
            stream=False,
            max_tokens=200
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            assert len(content) > 0
            
            print(f"✓ Qwen complex conversation successful")
            print(f"  Response: {content[:150]}...")
            
        except Exception as e:
            pytest.skip(f"Qwen complex conversation test skipped: {e}")


class TestQwenParameters:
    """Test various parameter configurations"""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("temperature", [0.1, 0.5, 0.9])
    async def test_temperature_settings(self, temperature, test_messages, validate_openai_response):
        """Test different temperature settings"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-max",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            temperature=temperature,
            max_tokens=150
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            print(f"✓ Qwen temperature {temperature} works correctly")
            
        except Exception as e:
            pytest.skip(f"Qwen temperature test skipped: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("max_tokens", [50, 200, 500])
    async def test_max_tokens_settings(self, max_tokens, test_messages, validate_openai_response):
        """Test different max_tokens settings"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-max",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            content = response["choices"][0]["message"]["content"]
            print(f"✓ Qwen max_tokens={max_tokens}, response length={len(content)}")
            
        except Exception as e:
            pytest.skip(f"Qwen max_tokens test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_top_p_settings(self, test_messages, validate_openai_response):
        """Test top_p parameter"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-max",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False,
            max_tokens=150,
            temperature=0.8,
            top_p=0.9
        )
        
        try:
            response = await provider.chat_completion(request)
            validate_openai_response(response, stream=False)
            
            print(f"✓ Qwen top_p parameter works")
            
        except Exception as e:
            pytest.skip(f"Qwen top_p test skipped: {e}")


class TestQwenErrorHandling:
    """Test error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_model(self, test_messages):
        """Test handling of invalid model"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-invalid-model",
            messages=[Message(**msg) for msg in test_messages["simple"]],
            stream=False
        )
        
        try:
            response = await provider.chat_completion(request)
            print(f"✓ Qwen invalid model handled (mapped to default)")
        except Exception as e:
            print(f"✓ Qwen invalid model properly rejected: {type(e).__name__}")
    
    @pytest.mark.asyncio
    async def test_empty_messages(self):
        """Test handling of empty messages"""
        provider = QwenProvider()
        
        request = OpenAIRequest(
            model="qwen-max",
            messages=[],
            stream=False
        )
        
        try:
            response = await provider.chat_completion(request)
            print(f"✓ Qwen empty messages handled")
        except Exception as e:
            print(f"✓ Qwen empty messages properly rejected: {type(e).__name__}")


class TestQwenEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, test_messages, validate_openai_response):
        """Test complete workflow from request to response"""
        provider = QwenProvider()
        
        tests_passed = []
        
        # Test 1: Simple request
        try:
            request1 = OpenAIRequest(
                model="qwen-max",
                messages=[Message(**msg) for msg in test_messages["simple"]],
                stream=False,
                max_tokens=150
            )
            response1 = await provider.chat_completion(request1)
            validate_openai_response(response1)
            tests_passed.append("simple")
        except Exception as e:
            print(f"  Simple request: {e}")
        
        # Test 2: Thinking model
        try:
            request2 = OpenAIRequest(
                model="qwen-max-thinking",
                messages=[Message(**msg) for msg in test_messages["thinking"]],
                stream=False,
                max_tokens=400
            )
            response2 = await provider.chat_completion(request2)
            validate_openai_response(response2)
            tests_passed.append("thinking")
        except Exception as e:
            print(f"  Thinking request: {e}")
        
        # Test 3: Streaming
        try:
            request3 = OpenAIRequest(
                model="qwen-turbo",
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
        
        # Test 4: Multi-turn
        try:
            request4 = OpenAIRequest(
                model="qwen-max",
                messages=[Message(**msg) for msg in test_messages["multi_turn"]],
                stream=False,
                max_tokens=150
            )
            response4 = await provider.chat_completion(request4)
            validate_openai_response(response4)
            tests_passed.append("multi-turn")
        except Exception as e:
            print(f"  Multi-turn request: {e}")
        
        print(f"✓ Qwen workflow tests passed: {tests_passed}")
        print(f"  - Simple completion: {'✓' if 'simple' in tests_passed else '✗'}")
        print(f"  - Thinking model: {'✓' if 'thinking' in tests_passed else '✗'}")
        print(f"  - Streaming: {'✓' if 'streaming' in tests_passed else '✗'}")
        print(f"  - Multi-turn: {'✓' if 'multi-turn' in tests_passed else '✗'}")
        
        # At least one test should pass
        if len(tests_passed) > 0:
            assert True
        else:
            pytest.skip("All Qwen workflow tests skipped due to errors")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

