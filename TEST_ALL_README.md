# 🧪 Z.AI Model Validation Test Suite

Comprehensive test suite for validating all Z.AI models through OpenAI-compatible API endpoints.

## 📋 Overview

`test_all.py` validates **7 Z.AI models** through automated testing:

| Model | Type | Context | Features |
|-------|------|---------|----------|
| **GLM-4.5** | Standard | 128K | General purpose |
| **GLM-4.5-Air** | Fast | 128K | Lightweight & efficient |
| **GLM-4.5-Thinking** | Reasoning | 128K | Extended thinking process |
| **GLM-4.5-Search** | Web Search | 128K | Internet search enhanced |
| **GLM-4.6** | Extended | 200K | Long context support |
| **GLM-4.6-Thinking** | Extended + Reasoning | 200K | Long context + thinking |
| **GLM-4.5V** | Multimodal | 128K | Vision/image support |

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install openai

# Start the API server (in another terminal)
python main.py --port 8080
```

### Run All Tests

```bash
# Test all models
python test_all.py

# Verbose output (show full responses)
python test_all.py --verbose

# Export results to JSON
python test_all.py --export
```

## 📖 Usage Examples

### Test All Models (Default)

```bash
python test_all.py
```

**Output:**
```
🧪 Z.AI Model Validation Test Suite
====================================

Testing: GLM-4.5 (Standard)
✅ Response received in 2.34s
Response: I am GLM-4.5, a large language model...
Tokens: 156 (45+111)

Testing: GLM-4.5V (Vision/Multimodal)
✅ Response received in 1.89s
Response: I am GLM-4.5V...
Tokens: 142 (38+104)

📊 Test Summary
==============
Total Tests: 7
✅ Passed: 7
Failed: 0
Pass Rate: 100.0%
Average Response Time: 2.15s

✅ All tests passed!
```

### Test Specific Model

```bash
# Test only GLM-4.5-Thinking
python test_all.py --model GLM-4.5-Thinking

# Test only vision model
python test_all.py --model GLM-4.5V
```

### Verbose Mode (Full Responses)

```bash
python test_all.py --verbose
```

**Shows:**
- Complete response text (not truncated)
- Thinking process (for Thinking models)
- Detailed token usage breakdown

### Custom Server Configuration

```bash
# Custom base URL
python test_all.py --base-url http://192.168.1.100:8080/v1

# Custom API key
python test_all.py --api-key sk-your-actual-key

# Both
python test_all.py --base-url http://api.example.com/v1 --api-key sk-abc123
```

### Export Results to JSON

```bash
python test_all.py --export
```

**Generates `test_results.json`:**
```json
{
  "summary": {
    "total": 7,
    "passed": 7,
    "failed": 0,
    "pass_rate": 100.0
  },
  "results": [
    {
      "model": "GLM-4.5",
      "success": true,
      "response_time": 2.34,
      "response_text": "I am GLM-4.5...",
      "thinking": null,
      "usage": {
        "prompt_tokens": 45,
        "completion_tokens": 111,
        "total_tokens": 156
      }
    }
  ]
}
```

### Skip Health Check

```bash
# Skip initial server health check
python test_all.py --no-health-check
```

Useful when server is slow to respond or you're debugging.

## 🔍 What Gets Tested

### For Each Model:

1. **✅ Connectivity** - Can reach the API endpoint
2. **✅ Authentication** - API key accepted
3. **✅ Model Availability** - Model exists and responds
4. **✅ Response Validity** - Response is non-empty and well-formed
5. **✅ Performance** - Response time tracking
6. **✅ Token Usage** - Proper usage statistics
7. **✅ Special Features** - Thinking process (for Thinking models)

### Validation Checks:

- ✅ Server responds within timeout (60s)
- ✅ Response contains valid text
- ✅ Token usage is reported correctly
- ✅ No API errors or exceptions
- ✅ Response time is reasonable
- ✅ Thinking models include reasoning process

## 📊 Test Output Explained

### Success Output

```
Testing: GLM-4.5-Thinking (Reasoning)
Model: GLM-4.5-Thinking
Capabilities: text, thinking
Description: Reasoning-optimized model with extended thinking
Sending request: 'Solve this step by step: What is 15 * 23?'
✅ Response received in 3.12s
Response: Let me solve this step by step...
Tokens: 234 (28+206)
```

**Breakdown:**
- **Model info**: Name, capabilities, description
- **Request**: Prompt sent to model
- **Response time**: How long it took (seconds)
- **Response**: Truncated response text (full text in verbose mode)
- **Tokens**: `total (prompt+completion)`

### Failure Output

```
Testing: GLM-4.5-Search (Web Search)
Model: GLM-4.5-Search
❌ Test failed after 5.00s
❌ Error: Connection timeout after 60s
```

**Common Errors:**
- `Connection refused` - Server not running
- `Connection timeout` - Server slow or unresponsive
- `401 Unauthorized` - Invalid API key
- `404 Not Found` - Model not available
- `Empty response` - Model returned no text

## 🎯 Advanced Usage

### Programmatic Usage

```python
from test_all import test_model, MODELS, TestStats
from openai import OpenAI

# Initialize client
client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="sk-dummy"
)

# Test a specific model
model = MODELS[0]  # GLM-4.5
result = test_model(client, model, verbose=True)

if result.success:
    print(f"✅ {model.name}: {result.response_text}")
    print(f"Time: {result.response_time:.2f}s")
    print(f"Tokens: {result.usage['total_tokens']}")
else:
    print(f"❌ {model.name} failed: {result.error}")

# Test all models
stats = TestStats()
for model in MODELS:
    result = test_model(client, model)
    stats.add_result(result)

print(f"Pass rate: {stats.pass_rate:.1f}%")
```

### Integration with CI/CD

```bash
#!/bin/bash
# ci_test.sh - Run in CI pipeline

# Start server in background
python main.py --port 8080 &
SERVER_PID=$!

# Wait for server to start
sleep 10

# Run tests
python test_all.py --export --no-health-check

# Capture exit code
EXIT_CODE=$?

# Stop server
kill $SERVER_PID

# Exit with test result
exit $EXIT_CODE
```

**Usage in GitHub Actions:**

```yaml
- name: Test Z.AI Models
  run: |
    python main.py --port 8080 &
    sleep 10
    python test_all.py --export
    
- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: test_results.json
```

## 🔧 Troubleshooting

### Error: Server Not Running

```
❌ Server health check failed: Connection refused
⚠️  Make sure the API server is running:
    python main.py --port 8080
```

**Solution:**
```bash
# Terminal 1: Start server
python main.py --port 8080

# Terminal 2: Run tests
python test_all.py
```

### Error: openai Library Not Found

```
❌ Error: openai library not installed!
Install with: pip install openai
```

**Solution:**
```bash
pip install openai
# or with uv
uv pip install openai
```

### Error: Connection Timeout

```
❌ Test failed after 60.00s
❌ Error: Connection timeout
```

**Possible causes:**
1. Server overloaded (too many requests)
2. Model not responding
3. Network issues

**Solution:**
```bash
# Restart server
pkill -f "python main.py"
python main.py --port 8080

# Run tests with longer timeout
# (Edit REQUEST_TIMEOUT in test_all.py)
```

### Error: Model Not Found

```
❌ Model not found: GLM-4.5-Custom
ℹ️  Available models:
  • GLM-4.5
  • GLM-4.5-Air
  • GLM-4.5-Thinking
  ...
```

**Solution:**
```bash
# Check available models
python test_all.py --model GLM-4.5
```

## 📈 Performance Benchmarks

### Expected Response Times

| Model | Typical | Fast | Slow |
|-------|---------|------|------|
| GLM-4.5-Air | 1-2s | <1s | >3s |
| GLM-4.5 | 2-3s | <2s | >5s |
| GLM-4.5V | 2-4s | <2s | >6s |
| GLM-4.5-Thinking | 3-5s | <3s | >8s |
| GLM-4.6 | 2-4s | <2s | >6s |

**Note:** Times vary based on:
- Prompt complexity
- Server load
- Network latency
- Model busy state

## 🎓 Understanding Results

### What "100% Pass Rate" Means

✅ **All models:**
1. Are reachable and responding
2. Accept authentication correctly
3. Return valid, non-empty responses
4. Complete within timeout (60s)
5. Report proper token usage

### What It Doesn't Test

❌ **Not validated:**
- Response accuracy/quality
- Reasoning correctness
- Search result relevance
- Vision understanding (images not tested)
- Function calling capabilities
- Long context handling (>10K tokens)

### When to Use This Test

**✅ Good for:**
- Validating server is running correctly
- Checking all models are accessible
- Verifying API compatibility
- Quick smoke testing
- CI/CD health checks

**❌ Not suitable for:**
- Evaluating model quality
- Testing complex scenarios
- Benchmarking accuracy
- Load testing

## 🔍 Example Test Session

```bash
$ python test_all.py --verbose

🧪 Z.AI Model Validation Test Suite
====================================
Base URL: http://localhost:8080/v1
API Key: ********

ℹ️  Testing server connection: http://localhost:8080/v1
✅ Server is reachable and responding

🚀 Running Tests (7 models)
===========================

[1/7]
Testing: GLM-4.5 (Standard)
Model: GLM-4.5
Capabilities: text
Description: General purpose model with 128K context
Sending request: 'What is your model name and version?...'
✅ Response received in 2.34s

Response:
I am GLM-4.5, a large language model developed by Zhipu AI.

Token Usage:
  Prompt: 12
  Completion: 18
  Total: 30

[2/7]
Testing: GLM-4.5-Thinking (Reasoning)
Model: GLM-4.5-Thinking
Capabilities: text, thinking
Description: Reasoning-optimized model with extended thinking
Sending request: 'Solve this step by step: What is 15 * 23?'
✅ Response received in 4.56s

Response:
Let me solve 15 × 23 step by step:
15 × 20 = 300
15 × 3 = 45
300 + 45 = 345

Thinking Process:
I'll break this down using the distributive property...

Token Usage:
  Prompt: 15
  Completion: 89
  Total: 104

... [5 more models] ...

📊 Test Summary
==============
Total Tests: 7
✅ Passed: 7
Failed: 0

Pass Rate: 100.0%
Average Response Time: 2.78s

📋 Detailed Results
==================

✅ Successful Tests (7):
  • GLM-4.5 (Standard)
    Time: 2.34s
    Tokens: 30
  • GLM-4.5-Air (Fast)
    Time: 1.89s
    Tokens: 25
  • GLM-4.5-Thinking (Reasoning)
    Time: 4.56s
    Tokens: 104
    ⚡ Has thinking process
  ... [4 more] ...

✅ All tests passed!
```

## 🤝 Contributing

Found a bug or want to add a test? PRs welcome!

**Common additions:**
- Add new model configurations
- Add vision/image testing
- Add function calling tests
- Add streaming response tests
- Add load testing capabilities

## 📝 License

MIT - See main repository LICENSE file

---

**Questions?** Open an issue or check the main [README.md](README.md)

