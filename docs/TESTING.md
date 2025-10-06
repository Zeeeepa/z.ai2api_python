# Testing Guide

This document describes the testing structure and how to run tests for the z.ai2api_python project.

## Test Organization

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests for individual components
│   ├── test_debug_api.py
│   ├── test_localStorage_debug.py
│   ├── test_qwen_page_debug.py
│   └── test_structure.py
├── integration/          # Integration tests with real API calls
│   ├── test_zai_real.py       # ZAI provider tests
│   ├── test_k2think_real.py   # K2Think provider tests
│   ├── test_qwen_real.py      # Qwen provider tests
│   ├── test_all_features.py
│   ├── test_all_providers.py
│   └── test_live_api.py
└── fixtures/             # Test data and helpers
```

## Test Categories

### Unit Tests
Located in `tests/unit/`, these test individual components without external dependencies.

### Integration Tests
Located in `tests/integration/`, these test real API interactions with actual service providers.

## Provider Test Credentials

Integration tests use the following credentials (configured in `conftest.py`):

**ZAI:**
- Base URL: https://chat.z.ai
- Email: developer@pixelium.uk
- Password: developer123?

**K2Think:**
- Base URL: https://www.k2think.ai
- Email: developer@pixelium.uk
- Password: developer123?

**Qwen:**
- Base URL: https://chat.qwen.ai
- Email: developer@pixelium.uk
- Password: developer1?

## Running Tests

### Install Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests for specific provider
pytest tests/integration/test_zai_real.py
pytest tests/integration/test_k2think_real.py
pytest tests/integration/test_qwen_real.py
```

### Run Tests with Markers

```bash
# Run only authentication tests
pytest -m auth

# Run only streaming tests
pytest -m streaming

# Run tests for specific provider
pytest -m zai
pytest -m k2think
pytest -m qwen

# Exclude slow tests
pytest -m "not slow"
```

### Run with Verbose Output

```bash
pytest -v -s
```

### Run Specific Test Function

```bash
pytest tests/integration/test_zai_real.py::TestZAIModels::test_model_basic_completion
```

## Test Coverage

### ZAI Provider Tests (`test_zai_real.py`)

- **Authentication**: Guest token retrieval, authenticated headers
- **Models**: All 7 models (GLM-4.5, GLM-4.5-Thinking, GLM-4.5-Search, GLM-4.5-Air, GLM-4.6, GLM-4.6-Thinking, GLM-4.6-Search)
- **Streaming**: Basic streaming, complete response assembly
- **Multi-turn**: Conversation context handling
- **Parameters**: Temperature, max_tokens variations
- **Error Handling**: Invalid models, empty messages
- **End-to-End**: Complete workflow validation

### K2Think Provider Tests (`test_k2think_real.py`)

- **Authentication**: Login and session management
- **Model**: MBZUAI-IFM/K2-Think with reasoning
- **Streaming**: Streaming responses with reasoning extraction
- **Multi-turn**: Context-aware conversations
- **Parameters**: Temperature, max_tokens variations
- **Error Handling**: Empty messages, long inputs
- **End-to-End**: Complete workflow validation

### Qwen Provider Tests (`test_qwen_real.py`)

- **Authentication**: Header generation and Bearer token
- **Models**: All 8 models (qwen-max, qwen-max-latest, qwen-max-thinking, qwen-max-search, qwen-max-image, qwen-plus, qwen-turbo, qwen-long)
- **Streaming**: Basic streaming, complete response assembly
- **Multi-turn**: Simple and complex conversations
- **Parameters**: Temperature, max_tokens, top_p variations
- **Error Handling**: Invalid models, empty messages
- **End-to-End**: Complete workflow validation

## Test Fixtures

Available fixtures from `conftest.py`:

- `provider_credentials`: All provider credentials
- `zai_credentials`: ZAI-specific credentials
- `k2think_credentials`: K2Think-specific credentials
- `qwen_credentials`: Qwen-specific credentials
- `test_messages`: Standard test message sets (simple, multi-turn, complex, search, thinking)
- `zai_models`: List of ZAI models
- `k2think_models`: List of K2Think models
- `qwen_models`: List of Qwen models
- `openai_request_factory`: Factory for creating OpenAI-compatible requests
- `validate_openai_response`: Validator for OpenAI response format

## Writing New Tests

### Example: Basic Integration Test

```python
import pytest
from app.providers.zai_provider import ZAIProvider
from app.models.schemas import OpenAIRequest, Message

@pytest.mark.asyncio
async def test_new_feature(test_messages, validate_openai_response):
    """Test new feature"""
    provider = ZAIProvider()
    
    request = OpenAIRequest(
        model="GLM-4.5",
        messages=[Message(**msg) for msg in test_messages["simple"]],
        stream=False
    )
    
    response = await provider.chat_completion(request)
    validate_openai_response(response)
    
    assert response["choices"][0]["message"]["content"] != ""
```

### Example: Parameterized Test

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("model", ["GLM-4.5", "GLM-4.6"])
async def test_multiple_models(model, test_messages):
    """Test multiple models"""
    provider = ZAIProvider()
    
    request = OpenAIRequest(
        model=model,
        messages=[Message(**msg) for msg in test_messages["simple"]],
        stream=False
    )
    
    response = await provider.chat_completion(request)
    assert isinstance(response, dict)
```

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-asyncio
    pytest tests/ -v
```

## Troubleshooting

### Authentication Failures

If tests fail due to authentication:
1. Verify credentials in `conftest.py`
2. Check if provider websites are accessible
3. Ensure no rate limiting is in effect

### Async Test Failures

If async tests fail:
1. Ensure `pytest-asyncio` is installed
2. Check that `@pytest.mark.asyncio` decorator is present
3. Verify `asyncio_mode = auto` in `pytest.ini`

### Timeout Issues

For slow network connections:
```bash
pytest --timeout=300  # 5 minute timeout per test
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures for setup/teardown
3. **Mocking**: Mock external dependencies in unit tests
4. **Real APIs**: Integration tests use real APIs
5. **Assertions**: Use specific assertions with clear messages
6. **Documentation**: Document complex test scenarios
7. **Skip Gracefully**: Use `pytest.skip()` for unavailable services

## Test Metrics

Target coverage by component:
- Providers: 90%+ (core functionality)
- Authentication: 85%+ (critical path)
- Transformers: 80%+ (data handling)
- Utilities: 70%+ (helper functions)

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

