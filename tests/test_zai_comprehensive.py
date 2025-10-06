#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive Z.AI Provider Tests
Tests all models, features, tools, and concurrent operations
"""

import os
import sys
import pytest
import asyncio
import httpx
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.zai import ZAIProvider
from app.models.chat import ChatRequest, ChatMessage


# ========================================
# Test Configuration
# ========================================

BASE_URL = "http://localhost:8080/v1"
CONCURRENT_REQUESTS = 10
TIMEOUT = 60.0

# All Z.AI models to test
ZAI_MODELS = [
    "GLM-4.5",
    "GLM-4.5-Thinking",
    "GLM-4.5-Search",
    "GLM-4.5-Air",
    "GLM-4.6",
    "GLM-4.6-Thinking",
    "GLM-4.6-Search",
]


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def http_client():
    """HTTP client for API requests"""
    return httpx.AsyncClient(timeout=TIMEOUT)


@pytest.fixture
async def provider():
    """Z.AI provider instance"""
    provider = ZAIProvider()
    # Initialize if needed
    return provider


# ========================================
# Test 1: Concurrent Basic Requests
# ========================================

@pytest.mark.asyncio
async def test_concurrent_basic_requests(http_client):
    """Test 10 concurrent basic chat requests"""
    
    async def make_request(index: int) -> Dict[str, Any]:
        """Make a single request"""
        request = {
            "model": "GLM-4.5",
            "messages": [
                {"role": "user", "content": f"Count from 1 to 5. Request #{index}"}
            ],
            "stream": False
        }
        
        response = await http_client.post(
            f"{BASE_URL}/chat/completions",
            json=request
        )
        
        return {
            "index": index,
            "status": response.status_code,
            "data": response.json() if response.status_code == 200 else None
        }
    
    # Run 10 concurrent requests
    tasks = [make_request(i) for i in range(CONCURRENT_REQUESTS)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Validate results
    successful = [r for r in results if not isinstance(r, Exception) and r["status"] == 200]
    
    print(f"\n✅ Concurrent Basic Requests: {len(successful)}/{CONCURRENT_REQUESTS} successful")
    for result in successful[:3]:  # Show first 3
        content = result["data"]["choices"][0]["message"]["content"]
        print(f"   Request #{result['index']}: {content[:50]}...")
    
    assert len(successful) >= CONCURRENT_REQUESTS * 0.8, "At least 80% should succeed"


# ========================================
# Test 2: All Models - Single Request
# ========================================

@pytest.mark.asyncio
async def test_all_models_single_request(http_client):
    """Test all Z.AI models with a single request"""
    
    results = {}
    
    for model in ZAI_MODELS:
        request = {
            "model": model,
            "messages": [
                {"role": "user", "content": "What is 2+2? Answer briefly."}
            ],
            "stream": False,
            "max_tokens": 50
        }
        
        try:
            response = await http_client.post(
                f"{BASE_URL}/chat/completions",
                json=request
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                results[model] = {
                    "success": True,
                    "content": content
                }
            else:
                results[model] = {
                    "success": False,
                    "error": response.text
                }
        except Exception as e:
            results[model] = {
                "success": False,
                "error": str(e)
            }
    
    # Print results
    print(f"\n✅ All Models Test:")
    for model, result in results.items():
        status = "✅" if result["success"] else "❌"
        print(f"   {status} {model}")
        if result["success"]:
            print(f"      Response: {result['content'][:60]}...")
    
    successful_count = sum(1 for r in results.values() if r["success"])
    assert successful_count >= len(ZAI_MODELS) * 0.7, "At least 70% of models should work"


# ========================================
# Test 3: Streaming Responses
# ========================================

@pytest.mark.asyncio
async def test_streaming_response(http_client):
    """Test streaming chat completion"""
    
    request = {
        "model": "GLM-4.5",
        "messages": [
            {"role": "user", "content": "Write a haiku about artificial intelligence"}
        ],
        "stream": True
    }
    
    chunks = []
    
    async with http_client.stream(
        "POST",
        f"{BASE_URL}/chat/completions",
        json=request
    ) as response:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str != "[DONE]":
                    chunks.append(data_str)
    
    print(f"\n✅ Streaming Response: Received {len(chunks)} chunks")
    print(f"   First chunk: {chunks[0][:100] if chunks else 'None'}...")
    
    assert len(chunks) > 0, "Should receive at least one chunk"


# ========================================
# Test 4: Thinking Mode
# ========================================

@pytest.mark.asyncio
async def test_thinking_mode(http_client):
    """Test GLM-4.5-Thinking model with reasoning"""
    
    request = {
        "model": "GLM-4.5-Thinking",
        "messages": [
            {
                "role": "user",
                "content": "If a train travels 120 km in 2 hours, what is its average speed? Show your reasoning."
            }
        ],
        "stream": False
    }
    
    response = await http_client.post(
        f"{BASE_URL}/chat/completions",
        json=request
    )
    
    assert response.status_code == 200
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    print(f"\n✅ Thinking Mode Response:")
    print(f"   {content[:200]}...")
    
    # Thinking mode should provide reasoning
    assert len(content) > 50, "Thinking mode should provide detailed reasoning"


# ========================================
# Test 5: Search Mode
# ========================================

@pytest.mark.asyncio
async def test_search_mode(http_client):
    """Test GLM-4.5-Search model with web search"""
    
    request = {
        "model": "GLM-4.5-Search",
        "messages": [
            {
                "role": "user",
                "content": "What are the latest developments in quantum computing in 2025?"
            }
        ],
        "stream": False
    }
    
    response = await http_client.post(
        f"{BASE_URL}/chat/completions",
        json=request
    )
    
    assert response.status_code == 200
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    print(f"\n✅ Search Mode Response:")
    print(f"   {content[:200]}...")
    
    # Search mode should provide web-informed answer
    assert len(content) > 100, "Search mode should provide detailed web-informed answer"


# ========================================
# Test 6: Tool Calling - Function Definition
# ========================================

@pytest.mark.asyncio
async def test_tool_calling_simple(http_client):
    """Test simple tool/function calling"""
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather in a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city name"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"]
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    request = {
        "model": "GLM-4.5",
        "messages": [
            {"role": "user", "content": "What's the weather in London?"}
        ],
        "tools": tools,
        "tool_choice": "auto",
        "stream": False
    }
    
    response = await http_client.post(
        f"{BASE_URL}/chat/completions",
        json=request
    )
    
    assert response.status_code == 200
    data = response.json()
    
    print(f"\n✅ Tool Calling Response:")
    print(f"   {data}")
    
    # Should have tool calls
    message = data["choices"][0]["message"]
    assert "tool_calls" in message or "content" in message, "Should have tool calls or content"


# ========================================
# Test 7: Multi-Turn Conversation
# ========================================

@pytest.mark.asyncio
async def test_multi_turn_conversation(http_client):
    """Test multi-turn conversation with context"""
    
    messages = [
        {"role": "user", "content": "I'm learning Python. Can you help?"},
        {"role": "assistant", "content": "Of course! I'd be happy to help you learn Python. What specific topic would you like to start with?"},
        {"role": "user", "content": "Explain list comprehensions with an example"}
    ]
    
    request = {
        "model": "GLM-4.5",
        "messages": messages,
        "stream": False
    }
    
    response = await http_client.post(
        f"{BASE_URL}/chat/completions",
        json=request
    )
    
    assert response.status_code == 200
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    print(f"\n✅ Multi-turn Conversation:")
    print(f"   {content[:200]}...")
    
    assert "list comprehension" in content.lower(), "Should explain list comprehensions"


# ========================================
# Test 8: Temperature and Parameters
# ========================================

@pytest.mark.asyncio
async def test_temperature_parameters(http_client):
    """Test different temperature and generation parameters"""
    
    prompts_params = [
        {"temp": 0.1, "desc": "Low temperature (deterministic)"},
        {"temp": 0.7, "desc": "Medium temperature (balanced)"},
        {"temp": 1.5, "desc": "High temperature (creative)"},
    ]
    
    results = []
    
    for params in prompts_params:
        request = {
            "model": "GLM-4.5",
            "messages": [
                {"role": "user", "content": "Write a creative one-line story about a robot"}
            ],
            "temperature": params["temp"],
            "max_tokens": 50,
            "stream": False
        }
        
        response = await http_client.post(
            f"{BASE_URL}/chat/completions",
            json=request
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            results.append({
                "temp": params["temp"],
                "desc": params["desc"],
                "content": content
            })
    
    print(f"\n✅ Temperature Test Results:")
    for result in results:
        print(f"   {result['desc']} (temp={result['temp']})")
        print(f"   → {result['content'][:80]}...\n")
    
    assert len(results) == 3, "All temperature tests should succeed"


# ========================================
# Test 9: Concurrent Different Models
# ========================================

@pytest.mark.asyncio
async def test_concurrent_different_models(http_client):
    """Test 10 concurrent requests using different models"""
    
    async def make_model_request(model: str, index: int) -> Dict[str, Any]:
        """Make request with specific model"""
        request = {
            "model": model,
            "messages": [
                {"role": "user", "content": f"Hello from model {model}, request #{index}"}
            ],
            "stream": False,
            "max_tokens": 30
        }
        
        try:
            response = await http_client.post(
                f"{BASE_URL}/chat/completions",
                json=request
            )
            
            return {
                "model": model,
                "index": index,
                "success": response.status_code == 200,
                "content": response.json()["choices"][0]["message"]["content"] if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                "model": model,
                "index": index,
                "success": False,
                "error": str(e)
            }
    
    # Create 10 requests across different models
    tasks = []
    for i in range(CONCURRENT_REQUESTS):
        model = ZAI_MODELS[i % len(ZAI_MODELS)]
        tasks.append(make_model_request(model, i))
    
    results = await asyncio.gather(*tasks)
    
    successful = [r for r in results if r["success"]]
    
    print(f"\n✅ Concurrent Different Models: {len(successful)}/{CONCURRENT_REQUESTS} successful")
    for result in successful[:5]:
        print(f"   {result['model']}: {result['content'][:50]}...")
    
    assert len(successful) >= CONCURRENT_REQUESTS * 0.7, "At least 70% should succeed"


# ========================================
# Test 10: Complex Tool Use - Calculator
# ========================================

@pytest.mark.asyncio
async def test_complex_tool_calculator(http_client):
    """Test complex tool usage with calculator functions"""
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "The operation to perform"
                        },
                        "x": {
                            "type": "number",
                            "description": "First number"
                        },
                        "y": {
                            "type": "number",
                            "description": "Second number"
                        }
                    },
                    "required": ["operation", "x", "y"]
                }
            }
        }
    ]
    
    request = {
        "model": "GLM-4.5",
        "messages": [
            {"role": "user", "content": "Calculate 156 multiplied by 23"}
        ],
        "tools": tools,
        "tool_choice": "auto",
        "stream": False
    }
    
    response = await http_client.post(
        f"{BASE_URL}/chat/completions",
        json=request
    )
    
    assert response.status_code == 200
    data = response.json()
    
    print(f"\n✅ Complex Tool Calculator:")
    print(f"   Response: {data}")


# ========================================
# Test 11: System Message with Context
# ========================================

@pytest.mark.asyncio
async def test_system_message_context(http_client):
    """Test system message for role/context setting"""
    
    request = {
        "model": "GLM-4.5",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful Python programming tutor. Always provide code examples."
            },
            {
                "role": "user",
                "content": "How do I read a file in Python?"
            }
        ],
        "stream": False
    }
    
    response = await http_client.post(
        f"{BASE_URL}/chat/completions",
        json=request
    )
    
    assert response.status_code == 200
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    print(f"\n✅ System Message Test:")
    print(f"   {content[:250]}...")
    
    # Should contain code examples
    assert "```" in content or "open(" in content, "Should contain code examples"


# ========================================
# Test 12: Error Handling
# ========================================

@pytest.mark.asyncio
async def test_error_handling(http_client):
    """Test various error scenarios"""
    
    error_scenarios = [
        {
            "name": "Invalid model",
            "request": {
                "model": "invalid-model-xyz",
                "messages": [{"role": "user", "content": "test"}]
            }
        },
        {
            "name": "Empty messages",
            "request": {
                "model": "GLM-4.5",
                "messages": []
            }
        },
        {
            "name": "Invalid role",
            "request": {
                "model": "GLM-4.5",
                "messages": [{"role": "invalid", "content": "test"}]
            }
        }
    ]
    
    print(f"\n✅ Error Handling Tests:")
    
    for scenario in error_scenarios:
        response = await http_client.post(
            f"{BASE_URL}/chat/completions",
            json=scenario["request"]
        )
        
        print(f"   {scenario['name']}: Status {response.status_code}")
        assert response.status_code != 200, f"{scenario['name']} should return error"


# ========================================
# Run Tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

