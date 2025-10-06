#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shared pytest fixtures for all tests
"""

import os
import sys
import pytest
import asyncio
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Provider credentials
PROVIDER_CREDENTIALS = {
    "zai": {
        "name": "zai",
        "baseUrl": "https://chat.z.ai",
        "loginUrl": "https://chat.z.ai/login",
        "chatUrl": "https://chat.z.ai/chat",
        "email": "developer@pixelium.uk",
        "password": "developer123?",
    },
    "k2think": {
        "name": "k2think",
        "baseUrl": "https://www.k2think.ai",
        "loginUrl": "https://www.k2think.ai/login",
        "chatUrl": "https://www.k2think.ai/chat",
        "email": "developer@pixelium.uk",
        "password": "developer123?",
    },
    "qwen": {
        "name": "qwen",
        "baseUrl": "https://chat.qwen.ai",
        "loginUrl": "https://chat.qwen.ai/login",
        "chatUrl": "https://chat.qwen.ai/chat",
        "email": "developer@pixelium.uk",
        "password": "developer1?",
    }
}


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def provider_credentials():
    """Provide authentication credentials for all providers"""
    return PROVIDER_CREDENTIALS


@pytest.fixture
def zai_credentials():
    """ZAI provider credentials"""
    return PROVIDER_CREDENTIALS["zai"]


@pytest.fixture
def k2think_credentials():
    """K2Think provider credentials"""
    return PROVIDER_CREDENTIALS["k2think"]


@pytest.fixture
def qwen_credentials():
    """Qwen provider credentials"""
    return PROVIDER_CREDENTIALS["qwen"]


@pytest.fixture
def test_messages():
    """Standard test messages for chat completions"""
    return {
        "simple": [
            {"role": "user", "content": "Hello! Please respond with 'test successful'"}
        ],
        "multi_turn": [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4."},
            {"role": "user", "content": "Now multiply that by 3"}
        ],
        "complex": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain quantum computing in one sentence."}
        ],
        "search": [
            {"role": "user", "content": "What are the latest developments in AI? Please search the web."}
        ],
        "thinking": [
            {"role": "user", "content": "Solve this logic puzzle: If all roses are flowers and some flowers fade quickly, can we conclude all roses fade quickly?"}
        ]
    }


@pytest.fixture
def zai_models():
    """ZAI supported models"""
    return [
        "GLM-4.5",
        "GLM-4.5-Thinking",
        "GLM-4.5-Search",
        "GLM-4.5-Air",
        "GLM-4.6",
        "GLM-4.6-Thinking",
        "GLM-4.6-Search"
    ]


@pytest.fixture
def k2think_models():
    """K2Think supported models"""
    return ["MBZUAI-IFM/K2-Think"]


@pytest.fixture
def qwen_models():
    """Qwen supported models"""
    return [
        "qwen-max",
        "qwen-max-latest",
        "qwen-max-thinking",
        "qwen-max-search",
        "qwen-max-image",
        "qwen-plus",
        "qwen-turbo",
        "qwen-long"
    ]


@pytest.fixture
def openai_request_factory():
    """Factory for creating OpenAI-compatible requests"""
    def create_request(
        model: str,
        messages: list,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
    return create_request


@pytest.fixture
def validate_openai_response():
    """Validator for OpenAI-compatible responses"""
    def validate(response: Dict[str, Any], stream: bool = False):
        if stream:
            # For streaming responses, check SSE format
            assert "data:" in str(response) or "choices" in response
        else:
            # Non-streaming response validation
            assert "id" in response
            assert "object" in response
            assert response["object"] in ["chat.completion", "text_completion"]
            assert "created" in response
            assert "model" in response
            assert "choices" in response
            assert len(response["choices"]) > 0
            
            choice = response["choices"][0]
            assert "message" in choice
            assert "role" in choice["message"]
            assert "content" in choice["message"]
            assert "finish_reason" in choice
            
            # Optional usage field
            if "usage" in response:
                assert "prompt_tokens" in response["usage"]
                assert "completion_tokens" in response["usage"]
                assert "total_tokens" in response["usage"]
        
        return True
    
    return validate

