# Complete Usage Guide

This guide shows you how to start the server and use all providers with OpenAI-compatible API format.

## 📋 Table of Contents

1. [Starting the Server](#starting-the-server)
2. [Using with OpenAI Python SDK](#using-with-openai-python-sdk)
3. [All Supported Models](#all-supported-models)
4. [Advanced Features](#advanced-features)
5. [Error Handling](#error-handling)

---

## 🚀 Starting the Server

### Step 1: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers for authentication
playwright install chromium
```

### Step 2: Configure Environment

Create `.env` file:

```bash
# Copy example
cp .env.example .env

# Edit configuration
nano .env
```

**Minimal `.env` configuration:**

```bash
# Server Configuration
PORT=8080
DEBUG_LOGGING=true

# Authentication (Optional - can disable for testing)
SKIP_AUTH_TOKEN=true

# Or use API key
# AUTH_TOKEN=sk-your-secret-api-key
```

### Step 3: Start the Server

```bash
# Start server
python main.py
```

**You'll see:**
```
🚀 启动 z.ai2api 服务...
📡 监听地址: 0.0.0.0:8080
🔧 调试模式: 开启
🔐 匿名模式: 关闭
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**Server is now running at:** `http://localhost:8080`

---

## 💻 Using with OpenAI Python SDK

### Installation

```bash
pip install openai
```

### Basic Usage

```python
from openai import OpenAI

# Initialize client
client = OpenAI(
    api_key="sk-anything",  # Can be anything if SKIP_AUTH_TOKEN=true
    base_url="http://localhost:8080/v1"
)

# Make a request
response = client.chat.completions.create(
    model="GLM-4.5",  # Choose any supported model
    messages=[
        {"role": "user", "content": "What is your model name?"}
    ]
)

print(response.choices[0].message.content)
```

### Example: Using Different Providers

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8080/v1"
)

# 1. Use ZAI (GLM models)
response = client.chat.completions.create(
    model="GLM-4.6",
    messages=[{"role": "user", "content": "Hello!"}]
)
print("ZAI:", response.choices[0].message.content)

# 2. Use K2Think
response = client.chat.completions.create(
    model="K2-Think",
    messages=[{"role": "user", "content": "Solve: 2+2=?"}]
)
print("K2Think:", response.choices[0].message.content)

# 3. Use Qwen
response = client.chat.completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "你好！"}]
)
print("Qwen:", response.choices[0].message.content)
```

### Streaming Responses

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8080/v1"
)

# Streaming request
stream = client.chat.completions.create(
    model="GLM-4.5",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

# Print streaming response
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='', flush=True)
```

---

## 🎯 All Supported Models

### ZAI Provider (GLM Models)

| Model | Description | Best For |
|-------|-------------|----------|
| `GLM-4.5` | Standard model | General chat |
| `GLM-4.5-Thinking` | Reasoning model | Complex problems |
| `GLM-4.5-Search` | Web search-enabled | Current information |
| `GLM-4.5-Air` | Lightweight model | Fast responses |
| `GLM-4.6` | Latest version | General chat (improved) |
| `GLM-4.6-Thinking` | Latest reasoning | Complex reasoning |
| `GLM-4.6-Search` | Latest search | Web-enabled queries |

**Example:**
```python
response = client.chat.completions.create(
    model="GLM-4.6-Thinking",  # Use reasoning model
    messages=[{"role": "user", "content": "Explain quantum entanglement"}],
    temperature=0.7,
    max_tokens=1000
)
```

### K2Think Provider

| Model | Description | Best For |
|-------|-------------|----------|
| `K2-Think` | MBZUAI-IFM reasoning model | Step-by-step reasoning |

**Example:**
```python
response = client.chat.completions.create(
    model="K2-Think",
    messages=[{"role": "user", "content": "Solve this step by step: If x+5=12, what is x?"}],
    temperature=0.3,  # Lower temperature for reasoning
    max_tokens=500
)
```

### Qwen Provider

| Model | Description | Best For |
|-------|-------------|----------|
| `qwen-max` | Flagship model | Complex tasks |
| `qwen-max-latest` | Latest version | Best performance |
| `qwen-max-thinking` | Reasoning model | Complex reasoning |
| `qwen-max-search` | Search-enabled | Web queries |
| `qwen-plus` | Balanced model | Good performance/speed |
| `qwen-turbo` | Fast model | Quick responses |
| `qwen-long` | Long context | Extended conversations |

**Example:**
```python
# Use Qwen for Chinese tasks
response = client.chat.completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "请写一首关于春天的诗"}],
    temperature=0.9,
    max_tokens=200
)
```

---

## 🔧 Advanced Features

### 1. List Available Models

```python
# Get all available models
models = client.models.list()

for model in models.data:
    print(f"- {model.id}: {model.owned_by}")
```

**Or with cURL:**
```bash
curl http://localhost:8080/v1/models
```

### 2. Multi-Turn Conversations

```python
# Maintain conversation context
messages = [
    {"role": "system", "content": "You are a helpful math tutor."},
    {"role": "user", "content": "What is the Pythagorean theorem?"},
]

# First response
response = client.chat.completions.create(
    model="GLM-4.5",
    messages=messages
)

# Add assistant response to history
messages.append({
    "role": "assistant",
    "content": response.choices[0].message.content
})

# Continue conversation
messages.append({
    "role": "user",
    "content": "Can you give me an example with actual numbers?"
})

response = client.chat.completions.create(
    model="GLM-4.5",
    messages=messages
)

print(response.choices[0].message.content)
```

### 3. Parameter Tuning

```python
response = client.chat.completions.create(
    model="GLM-4.5",
    messages=[{"role": "user", "content": "Write a creative story"}],
    
    # Temperature (0.0-1.0)
    # Lower = more focused, Higher = more creative
    temperature=0.9,
    
    # Max tokens (response length)
    max_tokens=1000,
    
    # Top P (nucleus sampling)
    top_p=0.95,
    
    # Presence penalty (-2.0 to 2.0)
    # Positive values encourage new topics
    presence_penalty=0.6,
    
    # Frequency penalty (-2.0 to 2.0)
    # Positive values reduce repetition
    frequency_penalty=0.5,
    
    # Streaming
    stream=False
)
```

### 4. Using Different Models for Different Tasks

```python
def ask_question(question, use_reasoning=False, use_search=False):
    """
    Smart model selection based on task
    """
    if use_reasoning:
        model = "GLM-4.6-Thinking"  # For complex reasoning
    elif use_search:
        model = "GLM-4.5-Search"    # For current information
    else:
        model = "GLM-4.6"           # For general chat
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}]
    )
    
    return response.choices[0].message.content

# Examples
print(ask_question("What's 2+2?"))
print(ask_question("Explain quantum mechanics", use_reasoning=True))
print(ask_question("What's the weather today?", use_search=True))
```

### 5. Async Usage

```python
import asyncio
from openai import AsyncOpenAI

async def async_example():
    client = AsyncOpenAI(
        api_key="sk-anything",
        base_url="http://localhost:8080/v1"
    )
    
    # Multiple concurrent requests
    tasks = [
        client.chat.completions.create(
            model="GLM-4.5",
            messages=[{"role": "user", "content": f"Count to {i}"}]
        )
        for i in range(1, 4)
    ]
    
    responses = await asyncio.gather(*tasks)
    
    for i, response in enumerate(responses, 1):
        print(f"Response {i}: {response.choices[0].message.content}")

# Run
asyncio.run(async_example())
```

---

## 🛡️ Error Handling

### Common Errors and Solutions

**1. Connection Error**
```python
from openai import OpenAI, OpenAIError

try:
    client = OpenAI(
        api_key="sk-anything",
        base_url="http://localhost:8080/v1"
    )
    
    response = client.chat.completions.create(
        model="GLM-4.5",
        messages=[{"role": "user", "content": "Hello"}]
    )
except OpenAIError as e:
    print(f"Error: {e}")
```

**Solutions:**
- Check if server is running: `curl http://localhost:8080`
- Verify correct port in `base_url`
- Ensure firewall allows connection

**2. Model Not Found**
```python
# List available models first
models = client.models.list()
available_models = [m.id for m in models.data]
print("Available:", available_models)

# Use a valid model
model = available_models[0]
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Hello"}]
)
```

**3. Authentication Error**
```python
# If you see authentication errors:
# 1. Check .env file has SKIP_AUTH_TOKEN=true
# 2. Or use correct API key from .env AUTH_TOKEN
```

---

## 📊 Complete Working Example

```python
#!/usr/bin/env python3
"""
Complete example showing all features
"""

from openai import OpenAI

# Initialize client
client = OpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8080/v1"
)

def main():
    # 1. List available models
    print("=" * 50)
    print("Available Models:")
    print("=" * 50)
    models = client.models.list()
    for model in models.data:
        print(f"  - {model.id} ({model.owned_by})")
    
    # 2. Simple request
    print("\n" + "=" * 50)
    print("Simple Request (GLM-4.5):")
    print("=" * 50)
    response = client.chat.completions.create(
        model="GLM-4.5",
        messages=[{"role": "user", "content": "What is AI?"}],
        max_tokens=150
    )
    print(response.choices[0].message.content)
    
    # 3. Reasoning task
    print("\n" + "=" * 50)
    print("Reasoning Task (GLM-4.5-Thinking):")
    print("=" * 50)
    response = client.chat.completions.create(
        model="GLM-4.5-Thinking",
        messages=[{"role": "user", "content": "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?"}],
        temperature=0.3
    )
    print(response.choices[0].message.content)
    
    # 4. Streaming response
    print("\n" + "=" * 50)
    print("Streaming Response (qwen-turbo):")
    print("=" * 50)
    stream = client.chat.completions.create(
        model="qwen-turbo",
        messages=[{"role": "user", "content": "Tell me a short joke"}],
        stream=True
    )
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end='', flush=True)
    print("\n")
    
    # 5. Multi-turn conversation
    print("\n" + "=" * 50)
    print("Multi-turn Conversation (K2-Think):")
    print("=" * 50)
    messages = [
        {"role": "user", "content": "What is 15% of 200?"}
    ]
    response = client.chat.completions.create(
        model="K2-Think",
        messages=messages
    )
    print(f"Assistant: {response.choices[0].message.content}")
    
    messages.append({"role": "assistant", "content": response.choices[0].message.content})
    messages.append({"role": "user", "content": "Now multiply that by 3"})
    
    response = client.chat.completions.create(
        model="K2-Think",
        messages=messages
    )
    print(f"Assistant: {response.choices[0].message.content}")

if __name__ == "__main__":
    main()
```

**Run it:**
```bash
python example.py
```

---

## 🔗 Additional Resources

- **Authentication Guide**: `docs/AUTHENTICATION_SETUP.md`
- **Testing Guide**: `docs/TESTING.md`
- **API Reference**: OpenAI API documentation (fully compatible)
- **Main README**: `README.md`

---

## 💡 Tips & Best Practices

1. **Model Selection**:
   - Use `*-Thinking` models for complex reasoning
   - Use `*-Search` models when current information needed
   - Use `turbo` or `Air` variants for speed

2. **Temperature Settings**:
   - 0.0-0.3: Factual, deterministic responses
   - 0.4-0.7: Balanced creativity and coherence
   - 0.8-1.0: Maximum creativity

3. **Max Tokens**:
   - Short answers: 50-200 tokens
   - Detailed explanations: 500-1000 tokens
   - Long content: 1000-2000 tokens

4. **Error Handling**:
   - Always wrap API calls in try-except
   - Implement retry logic for transient errors
   - Log errors for debugging

5. **Performance**:
   - Use streaming for long responses
   - Implement caching for repeated queries
   - Use async for concurrent requests

---

**Need help?** Check the logs in `logs/` directory or enable `DEBUG_LOGGING=true` in `.env`

