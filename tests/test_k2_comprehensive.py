#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive K2Think Provider Tests
Tests advanced reasoning, tool use, and concurrent operations
"""

import os
import sys
import pytest
import asyncio
import httpx
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.k2think import K2ThinkProvider


# ========================================
# Test Configuration
# ========================================

BASE_URL = "http://localhost:8080/v1"
CONCURRENT_REQUESTS = 10
TIMEOUT = 90.0  # K2Think may need more time for reasoning

K2THINK_MODEL = "MBZUAI-IFM/K2-Think"


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def http_client():
    """HTTP client for API requests"""
    return httpx.AsyncClient(timeout=TIMEOUT)


# ========================================
# Test 1: Concurrent Reasoning Requests
# ========================================

@pytest.mark.asyncio
async def test_concurrent_reasoning_requests(http_client):
    """Test 10 concurrent reasoning requests"""
    
    reasoning_prompts = [
        "If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?",
        "A farmer has chickens and cows. Together they have 50 heads and 140 legs. How many of each?",
        "If the day after tomorrow is Sunday, what day is today?",
        "Three friends are standing in a line. Alice is taller than Bob. Bob is taller than Carol. Who is shortest?",
        "A clock shows 3:15. What is the angle between hour and minute hands?",
        "If 5 cats catch 5 mice in 5 minutes, how long for 100 cats to catch 100 mice?",
        "A bat and ball cost $1.10 total. The bat costs $1 more than the ball. What does the ball cost?",
        "If you're running a race and pass the person in 2nd place, what place are you in?",
        "A store has a 20% off sale. If an item originally cost $50, what's the sale price?",
        "How many months have 28 days?"
    ]
    
    async def make_reasoning_request(prompt: str, index: int) -> Dict[str, Any]:
        """Make a reasoning request"""
        request = {
            "model": K2THINK_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "max_tokens": 500
        }
        
        try:
            response = await http_client.post(
                f"{BASE_URL}/chat/completions",
                json=request
            )
            
            return {
                "index": index,
                "prompt": prompt[:50],
                "success": response.status_code == 200,
                "content": response.json()["choices"][0]["message"]["content"] if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                "index": index,
                "prompt": prompt[:50],
                "success": False,
                "error": str(e)
            }
    
    # Run 10 concurrent reasoning requests
    tasks = [make_reasoning_request(prompt, i) for i, prompt in enumerate(reasoning_prompts)]
    results = await asyncio.gather(*tasks)
    
    successful = [r for r in results if r["success"]]
    
    print(f"\n✅ Concurrent Reasoning: {len(successful)}/{CONCURRENT_REQUESTS} successful")
    for result in successful[:3]:
        print(f"   Q: {result['prompt']}...")
        print(f"   A: {result['content'][:100]}...\n")
    
    assert len(successful) >= CONCURRENT_REQUESTS * 0.7, "At least 70% should succeed"


# ========================================
# Test 2: Complex Logic Problem
# ========================================

@pytest.mark.asyncio
async def test_complex_logic_problem(http_client):
    """Test K2Think with complex logical reasoning"""
    
    request = {
        "model": K2THINK_MODEL,
        "messages": [
            {
                "role": "user",
                "content": """
You have 12 balls, one of which weighs differently (either heavier or lighter).
You have a balance scale and can use it exactly 3 times.
How would you identify the different ball and determine if it's heavier or lighter?
Provide step-by-step reasoning.
                """.strip()
            }
        ],
        "stream": False,
        "max_tokens": 1000
    }
    
    response = await http_client.post(
        f"{BASE_URL}/chat/completions",
        json=request
    )
    
    assert response.status_code == 200
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    print(f"\n✅ Complex Logic Problem:")
    print(f"   {content[:500]}...")
    
    # Should provide detailed step-by-step reasoning
    assert len(content) > 300, "Should provide detailed reasoning"
    assert "step" in content.lower() or "weighing" in content.lower(), "Should contain step-by-step analysis"


# ========================================
# Test 3: Mathematical Reasoning
# ========================================

@pytest.mark.asyncio
async def test_mathematical_reasoning(http_client):
    """Test mathematical problem solving with reasoning"""
    
    request = {
        "model": K2THINK_MODEL,
        "messages": [
            {
                "role": "user",
                "content": """
Solve this problem step by step:
A train leaves Station A at 2 PM traveling at 60 mph toward Station B.
Another train leaves Station B at 3 PM traveling at 80 mph toward Station A.
If the stations are 320 miles apart, at what time will they meet?
Show your complete reasoning process.
                """.strip()
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
    
    print(f"\n✅ Mathematical Reasoning:")
    print(f"   {content}")
    
    assert len(content) > 200, "Should show complete reasoning"


# ========================================
# Test 4: Code Analysis and Debugging
# ========================================

@pytest.mark.asyncio
async def test_code_analysis(http_client):
    """Test code analysis and bug finding"""
    
    buggy_code = """
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers)):
        total += numbers[i]
    return total / len(numbers)

# Test
result = calculate_average([])
print(result)
    """.strip()
    
    request = {
        "model": K2THINK_MODEL,
        "messages": [
            {
                "role": "user",
                "content": f"""
Analyze this Python code and identify any bugs or issues:

```python
{buggy_code}
```

Explain the problem and suggest a fix with reasoning.
                """.strip()
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
    
    print(f"\n✅ Code Analysis:")
    print(f"   {content[:400]}...")
    
    # Should identify the division by zero issue
    assert "empty" in content.lower() or "zero" in content.lower(), "Should identify empty list issue"


# ========================================
# Test 5: Multi-Step Problem Solving
# ========================================

@pytest.mark.asyncio
async def test_multi_step_problem(http_client):
    """Test multi-step problem solving"""
    
    request = {
        "model": K2THINK_MODEL,
        "messages": [
            {
                "role": "user",
                "content": """
A company has 3 products: A, B, and C.
- Product A costs $10 to make and sells for $25
- Product B costs $15 to make and sells for $35
- Product C costs $20 to make and sells for $45

If they make 100 units of A, 80 units of B, and 60 units of C:
1. What's the total manufacturing cost?
2. What's the total revenue?
3. What's the profit margin percentage?
4. Which product has the best profit margin?

Solve step by step.
                """.strip()
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
    
    print(f"\n✅ Multi-Step Problem:")
    print(f"   {content[:500]}...")
    
    assert len(content) > 400, "Should show detailed multi-step solution"


# ========================================
# Test 6: Tool Calling - Data Analysis
# ========================================

@pytest.mark.asyncio
async def test_tool_data_analysis(http_client):
    """Test tool calling for data analysis"""
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "analyze_data",
                "description": "Analyze a dataset and return statistics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Array of numbers to analyze"
                        },
                        "metrics": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["mean", "median", "std", "min", "max"]
                            },
                            "description": "Metrics to calculate"
                        }
                    },
                    "required": ["data", "metrics"]
                }
            }
        }
    ]
    
    request = {
        "model": K2THINK_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Analyze this data: [12, 15, 18, 20, 22, 25, 28, 30, 35, 40]. Calculate mean, median, and standard deviation."
            }
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
    
    print(f"\n✅ Tool Data Analysis:")
    print(f"   {data}")


# ========================================
# Test 7: Streaming with Reasoning
# ========================================

@pytest.mark.asyncio
async def test_streaming_reasoning(http_client):
    """Test streaming response with reasoning"""
    
    request = {
        "model": K2THINK_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Explain the concept of recursion in programming with a simple example. Think step by step."
            }
        ],
        "stream": True
    }
    
    chunks = []
    
    async with http_client.stream(
        "POST",
        f"{BASE_URL}/chat/completions",
        json=request
    ) as response:
        assert response.status_code == 200
        
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str != "[DONE]":
                    chunks.append(data_str)
    
    print(f"\n✅ Streaming Reasoning: Received {len(chunks)} chunks")
    
    assert len(chunks) > 5, "Should receive multiple chunks"


# ========================================
# Test 8: Chain of Thought Reasoning
# ========================================

@pytest.mark.asyncio
async def test_chain_of_thought(http_client):
    """Test chain of thought reasoning"""
    
    request = {
        "model": K2THINK_MODEL,
        "messages": [
            {
                "role": "user",
                "content": """
Question: A bakery sells cupcakes in boxes of 6 and 8. 
What's the smallest number of cupcakes you can buy to get exactly 100 cupcakes?
You can buy any combination of boxes.

Think through this step by step, showing your reasoning process.
                """.strip()
            }
        ],
        "stream": False,
        "max_tokens": 800
    }
    
    response = await http_client.post(
        f"{BASE_URL}/chat/completions",
        json=request
    )
    
    assert response.status_code == 200
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    print(f"\n✅ Chain of Thought:")
    print(f"   {content}")
    
    assert len(content) > 200, "Should show chain of thought"


# ========================================
# Test 9: Concurrent Different Tasks
# ========================================

@pytest.mark.asyncio
async def test_concurrent_mixed_tasks(http_client):
    """Test concurrent requests with different task types"""
    
    tasks_prompts = [
        "Solve: 2x + 5 = 17",
        "Explain binary search algorithm briefly",
        "What's the capital of France?",
        "Calculate: 15% of 200",
        "Define 'machine learning' in one sentence",
        "What is 2^10?",
        "List 3 prime numbers between 20 and 40",
        "What's the square root of 144?",
        "Explain what an API is briefly",
        "Calculate the area of a circle with radius 5"
    ]
    
    async def make_task_request(prompt: str, index: int):
        request = {
            "model": K2THINK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "max_tokens": 100
        }
        
        try:
            response = await http_client.post(
                f"{BASE_URL}/chat/completions",
                json=request
            )
            
            return {
                "index": index,
                "success": response.status_code == 200,
                "prompt": prompt[:40],
                "answer": response.json()["choices"][0]["message"]["content"][:80] if response.status_code == 200 else None
            }
        except Exception as e:
            return {"index": index, "success": False, "error": str(e)}
    
    tasks = [make_task_request(prompt, i) for i, prompt in enumerate(tasks_prompts)]
    results = await asyncio.gather(*tasks)
    
    successful = [r for r in results if r["success"]]
    
    print(f"\n✅ Concurrent Mixed Tasks: {len(successful)}/{len(tasks_prompts)} successful")
    for result in successful[:5]:
        print(f"   Q: {result['prompt']}...")
        print(f"   A: {result['answer']}...\n")
    
    assert len(successful) >= len(tasks_prompts) * 0.7


# ========================================
# Test 10: Temperature Variation
# ========================================

@pytest.mark.asyncio
async def test_temperature_creativity(http_client):
    """Test how temperature affects reasoning"""
    
    temperatures = [0.1, 0.5, 1.0, 1.5]
    results = []
    
    for temp in temperatures:
        request = {
            "model": K2THINK_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": "Come up with a creative solution to reduce plastic waste in oceans."
                }
            ],
            "temperature": temp,
            "max_tokens": 200,
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
                "temp": temp,
                "response": content
            })
    
    print(f"\n✅ Temperature Creativity Test:")
    for result in results:
        print(f"   Temperature {result['temp']}:")
        print(f"   {result['response'][:150]}...\n")
    
    assert len(results) >= 3, "Most temperature tests should succeed"


# ========================================
# Test 11: System Prompt Reasoning
# ========================================

@pytest.mark.asyncio
async def test_system_prompt_expert(http_client):
    """Test system prompt for expert reasoning"""
    
    request = {
        "model": K2THINK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert mathematician. Always show your work step by step and verify your answers."
            },
            {
                "role": "user",
                "content": "If f(x) = 2x² + 3x - 5, what is f(3)?"
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
    
    print(f"\n✅ System Prompt Expert:")
    print(f"   {content}")
    
    assert "step" in content.lower() or "=" in content, "Should show mathematical working"


# ========================================
# Test 12: Long-Form Reasoning
# ========================================

@pytest.mark.asyncio
async def test_long_form_reasoning(http_client):
    """Test long-form detailed reasoning"""
    
    request = {
        "model": K2THINK_MODEL,
        "messages": [
            {
                "role": "user",
                "content": """
Write a detailed analysis of the following algorithm's time complexity:

```python
def find_duplicates(arr):
    result = []
    for i in range(len(arr)):
        for j in range(i+1, len(arr)):
            if arr[i] == arr[j] and arr[i] not in result:
                result.append(arr[i])
    return result
```

Explain Big O notation, best/worst cases, and suggest improvements.
                """.strip()
            }
        ],
        "stream": False,
        "max_tokens": 1000
    }
    
    response = await http_client.post(
        f"{BASE_URL}/chat/completions",
        json=request
    )
    
    assert response.status_code == 200
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    
    print(f"\n✅ Long-Form Reasoning:")
    print(f"   Length: {len(content)} characters")
    print(f"   Preview: {content[:300]}...")
    
    assert len(content) > 500, "Should provide detailed analysis"
    assert "O(" in content, "Should mention Big O notation"


# ========================================
# Run Tests
# ========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

