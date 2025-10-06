# Test Suite for z.ai2api_python

Comprehensive testing for all AI provider integrations.

## Test Files

### `test_all_providers.py`
Comprehensive test suite that validates:
- All provider endpoints (ZAI, K2Think, Qwen)
- All model variants for each provider
- Concurrent request handling
- Response times and reliability

**Usage:**
```bash
# Make sure server is running first
SKIP_AUTH_TOKEN=true python main.py &

# Run tests
python tests/test_all_providers.py
```

**Output:**
- Console output with detailed test results
- JSON file: `tests/test_results.json` with full test data

### `parallelcalltest.py` 
Simple parallel request test demonstrating concurrent execution:
```bash
python tests/parallelcalltest.py
```

## Test Configuration

Tests use credentials from `auth_config.json` in the root directory:
```json
{
  "providers": {
    "zai": {
      "email": "your-email@example.com",
      "password": "your-password"
    },
    "qwen": {
      "email": "your-email@example.com",
      "password": "your-password"
    },
    "k2think": {
      "email": "your-email@example.com",
      "password": "your-password"
    }
  }
}
```

## Test Results

Recent test run (2025-10-06):
```
✅ Successful: 6/10 tests
❌ Failed: 4/10 tests

Success Rate by Provider:
  K2THINK: 100% (2/2)
  QWEN: 100% (4/4)
  ZAI: 0% (0/4) - Authentication issue

Performance:
  Concurrent execution: 8.80s
  Sequential would take: ~30s
  Speedup: 3.4x faster!
```

## Provider-Specific Notes

### ZAI (chat.z.ai)
- Models: GLM-4.5, GLM-4.6, GLM-4.5-Air, GLM-4.6-Search
- Status: Currently failing with 400 error (likely credential issue)
- Authentication: Playwright-based browser automation

### K2Think (k2think.ai)
- Models: MBZUAI-IFM/K2-Think
- Status: ✅ Working (100% success rate)
- Average response time: 2.91s

### Qwen (chat.qwen.ai)
- Models: qwen-turbo, qwen-plus, qwen-max, qwen-long
- Status: ✅ Working (100% success rate)  
- Average response time: 0.69s (blazing fast!)

## Adding New Tests

To add tests for a new provider:

1. Add provider configuration to `TEST_CONFIGS` in `test_all_providers.py`:
```python
"newprovider": {
    "models": ["model-1", "model-2"],
    "test_message": "Test message"
}
```

2. Ensure credentials are in `auth_config.json`

3. Run the test suite

## Debugging Failed Tests

If tests fail:

1. Check server logs: `tail -f server.log`
2. Verify credentials in `auth_config.json`
3. Test models endpoint: `curl http://localhost:8080/v1/models`
4. Check provider-specific authentication in Playwright browser

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Concurrent requests (3 providers) | 8.80s |
| Average response time (successful) | 1.43s |
| Qwen average | 0.69s |
| K2Think average | 2.91s |
| Concurrent speedup | 3.4x |

