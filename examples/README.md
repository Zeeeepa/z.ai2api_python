# Qwen API Examples

This directory contains comprehensive examples demonstrating all features of the Qwen Chat API through the OpenAI-compatible interface.

## Prerequisites

1. **Server Running**: Start the API server
   ```bash
   python main.py
   ```

2. **Configuration**: Set up Qwen credentials in `config/providers.json`:
   ```json
   {
       "providers": [
           {
               "name": "qwen",
               "base Url": "https://chat.qwen.ai",
               "loginUrl": "https://chat.qwen.ai/login",
               "chatUrl": "https://chat.qwen.ai/chat",
               "email": "your-email@example.com",
               "password": "your-password",
               "enabled": true
           }
       ]
   }
   ```

3. **Authentication Token**: Set your API token
   ```bash
   export AUTH_TOKEN="sk-your-api-key"
   ```

## Running Examples

### Run All Examples
```bash
python examples/qwen_examples.py
```

### Run Specific Example
```bash
python examples/qwen_examples.py --example 1   # Basic chat
python examples/qwen_examples.py --example 2   # Streaming
python examples/qwen_examples.py --example 3   # Thinking mode
python examples/qwen_examples.py --example 4   # Web search
python examples/qwen_examples.py --example 5   # Vision/multimodal
python examples/qwen_examples.py --example 6   # List models
python examples/qwen_examples.py --example 7   # Error handling
python examples/qwen_examples.py --example 8   # Multi-turn conversation
```

### Custom Configuration
```bash
python examples/qwen_examples.py --base-url http://localhost:8080/v1 --token sk-custom-token
```

## Examples Overview

### 1. Basic Chat Completion
Demonstrates the fixed request structure with all required fields:
- ✅ session_id (UUID)
- ✅ chat_id (UUID)
- ✅ Messages with chat_type and extra
- ✅ Proper feature_config

**What it tests**:
- Simple text-to-text conversation
- Correct request payload structure
- Response parsing

**Expected output**:
```
✅ Response: Quantum computing uses quantum-mechanical phenomena...
📊 Model: qwen-max
🆔 ID: chatcmpl-...
```

### 2. Streaming Chat
Real-time streaming responses using Server-Sent Events (SSE).

**What it tests**:
- Streaming API endpoint
- Incremental response chunks
- Stream completion handling

**Expected output**:
```
📝 Streaming response:
Once upon a time, there was a curious robot named Circuit...

✅ Received 487 characters
```

### 3. Thinking Mode (Reasoning)
Enables deep reasoning with the `-thinking` model suffix.

**What it tests**:
- feature_config.thinking_enabled = true
- Reasoning mode activation
- Extended processing for complex problems

**Expected output**:
```
💭 Response: You have 6 apples. (3 + 5 - 2 = 6)
🧠 Reasoning: First I add 3 + 5 = 8, then subtract 2...
✅ Thinking mode response received
```

### 4. Web Search Mode
Real-time web search integration with the `-search` suffix.

**What it tests**:
- Web search capability
- Current information retrieval
- Citation handling

**Expected output**:
```
🔍 Response with web search: Based on recent developments...
✅ Search-augmented response received
```

### 5. Multimodal Vision
Image understanding and analysis.

**What it tests**:
- Image URL handling in messages
- Vision capabilities
- Multimodal content processing

**Expected output**:
```
👁️ Vision analysis: This image shows a wooden boardwalk...
✅ Multimodal response received
```

### 6. List Available Models
Enumerate all supported Qwen models.

**What it tests**:
- Models endpoint
- Provider discovery
- Model listing

**Expected output**:
```
📋 Available Qwen models:
  - qwen-max
  - qwen-max-thinking
  - qwen-max-search
  - qwen-plus
  - qwen-turbo
  - qwen-long
✅ Found 6 Qwen models
```

### 7. Error Handling
Demonstrates graceful error handling for invalid requests.

**What it tests**:
- Invalid model names
- Error response parsing
- Exception handling

**Expected output**:
```
✅ Correctly caught NotFoundError: Model 'invalid-model-name' not found
```

### 8. Multi-turn Conversation
Conversation with context and history.

**What it tests**:
- Conversation continuity
- Context maintenance across turns
- Session management

**Expected output**:
```
👤 User: My name is Alice.
🤖 Assistant: Hello Alice! Nice to meet you...

👤 User: What's my name?
🤖 Assistant: Your name is Alice!

✅ Conversation context maintained!
```

## Troubleshooting

### Common Issues

1. **Connection Error**: 
   ```
   ❌ Error: Connection refused
   ```
   **Solution**: Ensure the server is running on the correct port.

2. **Authentication Failed**:
   ```
   ❌ Error: 401 Unauthorized
   ```
   **Solution**: Check your AUTH_TOKEN and Qwen credentials in config/providers.json.

3. **Model Not Found**:
   ```
   ❌ Error: Model 'qwen-max' not found
   ```
   **Solution**: Verify Qwen provider is enabled in configuration.

4. **Timeout**:
   ```
   ❌ Error: Request timeout
   ```
   **Solution**: Increase timeout or check network connectivity.

## Request Structure Examples

### Text Chat (Fixed Structure)
```python
{
    "model": "qwen-max",
    "messages": [
        {
            "role": "user",
            "content": "Hello",
            "chat_type": "text",    # ✅ FIXED: Now included
            "extra": {}              # ✅ FIXED: Now included
        }
    ],
    "stream": true,
    "incremental_output": true,
    "chat_type": "normal",
    "session_id": "uuid-here",      # ✅ FIXED: Now included
    "chat_id": "uuid-here",         # ✅ FIXED: Now included
    "feature_config": {
        "output_schema": "phase",
        "thinking_enabled": false
    }
}
```

### Thinking Mode
```python
{
    "model": "qwen-max",
    # ... same as above but with:
    "feature_config": {
        "output_schema": "phase",
        "thinking_enabled": true    # ✅ FIXED: Correct structure
    }
}
```

## Performance Tips

1. **Use Streaming**: For better UX, enable streaming for long responses
   ```python
   stream=True
   ```

2. **Set Appropriate Tokens**: Control response length
   ```python
   max_tokens=500
   ```

3. **Temperature Control**: Adjust creativity
   ```python
   temperature=0.7  # Higher = more creative
   ```

4. **Model Selection**:
   - `qwen-max`: Best quality, slower
   - `qwen-turbo`: Faster, good quality
   - `qwen-max-thinking`: For complex reasoning
   - `qwen-max-search`: For current information

## Integration with Other Clients

### cURL
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-max",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### JavaScript/TypeScript
```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-your-api-key',
  baseURL: 'http://localhost:8080/v1'
});

const response = await client.chat.completions.create({
  model: 'qwen-max',
  messages: [{role: 'user', content: 'Hello'}]
});
```

### Python (requests)
```python
import requests

response = requests.post(
    'http://localhost:8080/v1/chat/completions',
    headers={'Authorization': 'Bearer sk-your-api-key'},
    json={
        'model': 'qwen-max',
        'messages': [{'role': 'user', 'content': 'Hello'}]
    }
)
```

## What Was Fixed

These examples demonstrate the corrected implementation that fixes all 9 critical issues:

1. ✅ **session_id (UUID)** - Now generated for every request
2. ✅ **chat_id (UUID)** - Now generated for every request
3. ✅ **parent_id: null** - Included in appropriate requests
4. ✅ **chat_mode: "normal"** - Set correctly
5. ✅ **timestamp** - Added to all requests
6. ✅ **Message chat_type** - Every message has chat_type field
7. ✅ **Message extra: {}** - Every message has extra field
8. ✅ **thinking_budget** - Correct structure in feature_config
9. ✅ **feature_config** - Complete structure with output_schema

## Further Reading

- [Qwen API Documentation](docs/providers/QWEN.md)
- [API Structure Reference](docs/QWEN_API_STRUCTURE.md)
- [Main README](../README.md)

## Support

If you encounter issues:
1. Check the server logs for detailed error messages
2. Verify your configuration matches the examples
3. Ensure you're using the latest version
4. Review the [troubleshooting guide](docs/TROUBLESHOOTING.md)

