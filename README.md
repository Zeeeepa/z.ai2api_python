# OpenAI-Compatible Multi-Provider API Server

> A unified OpenAI-compatible API server that aggregates multiple AI chat providers (Z.AI, K2Think, Qwen, LongCat) with automatic authentication, session management, and intelligent request routing.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🌟 Features

- **🔌 OpenAI-Compatible API** - Drop-in replacement for OpenAI API
- **🎯 Multi-Provider Support** - Unified access to 4+ AI providers
- **🔐 Automatic Authentication** - Manages sessions and cookies automatically
- **🔄 Intelligent Routing** - Routes requests to appropriate provider by model name
- **💾 Session Encryption** - Secure storage of authentication sessions
- **📡 Streaming Support** - Real-time streaming responses
- **🛡️ Error Handling** - Automatic retry and fallback mechanisms
- **📊 Model Discovery** - Lists all available models from all providers

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python

# Install dependencies
pip install -r requirements.txt
# or with uv
uv pip install -r requirements.txt

# Create configuration
cp .env.example .env
cp config/providers.json.example config/providers.json

# Edit configuration with your credentials
nano .env
nano config/providers.json
```

### Configuration

#### 1. API Authentication (`.env`)

```bash
# Single API key
AUTH_TOKEN=sk-your-secret-api-key

# Or skip auth for development (NOT recommended for production)
SKIP_AUTH_TOKEN=true

# Optional: Multiple API keys
AUTH_TOKENS_FILE=tokens.txt

# LongCat provider token
LONGCAT_PASSPORT_TOKEN=your-longcat-token
```

#### 2. Provider Credentials (`config/providers.json`)

```json
{
    "providers": [
        {
            "name": "zai",
            "baseUrl": "https://chat.z.ai",
            "loginUrl": "https://chat.z.ai/login",
            "chatUrl": "https://chat.z.ai/chat",
            "email": "your-email@example.com",
            "password": "your-password",
            "enabled": true
        },
        {
            "name": "k2think",
            "baseUrl": "https://www.k2think.ai",
            "loginUrl": "https://www.k2think.ai/login",
            "chatUrl": "https://www.k2think.ai/chat",
            "email": "your-email@example.com",
            "password": "your-password",
            "enabled": true
        },
        {
            "name": "qwen",
            "baseUrl": "https://chat.qwen.ai",
            "loginUrl": "https://chat.qwen.ai/login",
            "chatUrl": "https://chat.qwen.ai/chat",
            "email": "your-email@example.com",
            "password": "your-password",
            "enabled": true
        }
    ]
}
```

### Running the Server

```bash
# Start the server
python main.py

# Server will start on http://localhost:8080
# API endpoint: http://localhost:8080/v1
```

## 📖 Usage

### Python (OpenAI SDK)

```python
import openai

client = openai.OpenAI(
    api_key="sk-your-api-key",
    base_url="http://localhost:8080/v1"
)

# Use any supported model
response = client.chat.completions.create(
    model="GLM-4.5",  # or "K2-Think", "qwen-max", etc.
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is quantum computing?"}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)
```

### cURL

```bash
# Chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'

# List available models
curl http://localhost:8080/v1/models \
  -H "Authorization: Bearer sk-your-api-key"

# Streaming response
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": true
  }'
```

### JavaScript/TypeScript

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-your-api-key',
  baseURL: 'http://localhost:8080/v1'
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'GLM-4.5',
    messages: [
      { role: 'user', content: 'What is machine learning?' }
    ]
  });
  
  console.log(response.choices[0].message.content);
}

chat();
```

## 🎯 Supported Models

### Z.AI Provider
- `GLM-4.5` - Standard chat model
- `GLM-4.5-Thinking` - Reasoning-focused model
- `GLM-4.5-Search` - Web search-enabled model
- `GLM-4.5-Air` - Lightweight model
- `GLM-4.6` - Latest version
- `GLM-4.6-Thinking` - Latest reasoning model
- `GLM-4.6-Search` - Latest search model

### K2Think Provider
- `MBZUAI-IFM/K2-Think` - Advanced reasoning model

### Qwen Provider
- `qwen-max` - Most capable model
- `qwen-max-thinking` - Reasoning mode
- `qwen-max-search` - Web search capability
- `qwen-max-image` - Image generation
- `qwen-plus` - Balanced performance
- `qwen-turbo` - Fast responses
- `qwen-long` - Extended context

### LongCat Provider
- `LongCat-Flash` - Fast responses
- `LongCat` - Standard model
- `LongCat-Search` - Search-enabled

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Client Application                │
│              (OpenAI SDK, cURL, etc.)              │
└───────────────────────┬─────────────────────────────┘
                        │
                        │ HTTP Request (OpenAI Format)
                        │
        ┌───────────────▼────────────────┐
        │      API Server (FastAPI)      │
        │   - Authentication Middleware   │
        │   - Request Validation         │
        └───────────────┬────────────────┘
                        │
                        │
        ┌───────────────▼────────────────┐
        │      Provider Router           │
        │   - Model → Provider Mapping   │
        │   - Load Balancing             │
        └───────────────┬────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼───┐    ┌────▼───┐    ┌────▼───┐
    │  Z.AI  │    │K2Think │    │  Qwen  │
    │Provider│    │Provider│    │Provider│
    │        │    │        │    │        │
    │- Auth  │    │- Auth  │    │- Auth  │
    │- Trans │    │- Trans │    │- Trans │
    │- Stream│    │- Stream│    │- Stream│
    └────┬───┘    └────┬───┘    └────┬───┘
         │             │              │
         │    External Provider APIs  │
         └──────────────┴──────────────┘
```

## 📂 Project Structure

```
z.ai2api_python/
├── app/
│   ├── auth/                    # Authentication modules
│   │   ├── __init__.py
│   │   ├── provider_auth.py     # Provider login/session
│   │   └── session_store.py     # Encrypted session storage
│   ├── core/                    # Core application
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration management
│   │   └── openai.py            # OpenAI-compatible endpoints
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic models
│   └── providers/               # Provider implementations
│       ├── __init__.py
│       ├── base.py              # Base provider class
│       ├── provider_factory.py  # Provider routing
│       ├── zai_provider.py      # Z.AI implementation
│       ├── k2think_provider.py  # K2Think implementation
│       ├── qwen_provider.py     # Qwen implementation
│       └── longcat_provider.py  # LongCat implementation
├── config/
│   ├── providers.json           # Provider credentials
│   └── providers.json.example   # Example configuration
├── docs/
│   └── AUTHENTICATION.md        # Authentication guide
├── .sessions/                   # Encrypted session files
├── .env                         # Environment variables
├── .env.example                 # Example environment
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔐 Security

### Authentication Flow

1. **API Request** → Client sends request with Bearer token
2. **Token Validation** → Server validates against `AUTH_TOKEN` or token file
3. **Provider Selection** → Router selects provider based on model
4. **Session Check** → Provider checks for valid cached session
5. **Auto Login** → If session invalid, auto-login with credentials
6. **Request Transform** → Convert OpenAI format to provider format
7. **Provider API Call** → Make authenticated request to provider
8. **Response Transform** → Convert provider response to OpenAI format

### Session Management

- Sessions stored encrypted in `.sessions/` directory
- Encryption: PBKDF2-HMAC-SHA256 with random salt
- Auto-refresh on expiration
- Secure deletion of expired sessions

### Best Practices

✅ **DO:**
- Use strong API tokens (`openssl rand -hex 32`)
- Set `SKIP_AUTH_TOKEN=false` in production
- Rotate provider credentials regularly
- Keep `.env` and `config/providers.json` private
- Use environment variables in deployment

❌ **DON'T:**
- Commit credentials to version control
- Use `SKIP_AUTH_TOKEN=true` in production
- Share API tokens
- Store sessions in public locations

## 🧪 Testing

### Run Validation Tests

```bash
# Install test dependencies
pip install pytest openai

# Run tests
python tests/test_providers.py
```

### Manual Testing

```bash
# Test models endpoint
curl http://localhost:8080/v1/models \
  -H "Authorization: Bearer sk-test-key"

# Test chat completion
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-test-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5",
    "messages": [{"role": "user", "content": "Test message"}],
    "max_tokens": 50
  }'
```

## 📊 Monitoring

### Logs

Server logs include:
- Request routing information
- Provider selection
- Authentication status
- Error details
- Response timing

Example log output:
```
2025-10-05 15:39:36 | INFO | 😶‍🌫️ 收到客户端请求 - 模型: GLM-4.5
2025-10-05 15:39:36 | INFO | 🚦 路由请求: 模型=GLM-4.5
2025-10-05 15:39:36 | DEBUG | 🎯 模型 GLM-4.5 找到提供商 zai
2025-10-05 15:39:36 | INFO | ✅ 使用提供商: zai
2025-10-05 15:39:37 | INFO | 🎉 请求处理完成: zai
```

### Health Check

```bash
# Check if server is running
curl http://localhost:8080/v1/models

# Expected response
{
  "object": "list",
  "data": [
    {"id": "GLM-4.5", "object": "model", "owned_by": "zai"},
    ...
  ]
}
```

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
```

```bash
# Build
docker build -t openai-multi-provider .

# Run
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/.sessions:/app/.sessions \
  -e AUTH_TOKEN=sk-your-api-key \
  --name openai-api \
  openai-multi-provider
```

### Systemd Service

```ini
[Unit]
Description=OpenAI Multi-Provider API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/openai-api
Environment="PATH=/opt/openai-api/venv/bin"
ExecStart=/opt/openai-api/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Environment Variables for Production

```bash
# .env
AUTH_TOKEN=sk-$(openssl rand -hex 32)
SKIP_AUTH_TOKEN=false
LOG_LEVEL=INFO

# Optional
AUTH_TOKENS_FILE=/secure/path/tokens.txt
LONGCAT_PASSPORT_TOKEN=your-token
SESSION_ENCRYPTION_KEY=$(openssl rand -hex 32)
```

## 🐛 Troubleshooting

### Common Issues

**Issue: "Invalid API key"**
- Check `AUTH_TOKEN` in `.env`
- Verify Authorization header format: `Bearer <token>`
- Ensure `SKIP_AUTH_TOKEN` setting matches your intent

**Issue: "Model not found"**
- Verify model name is correct
- Check provider is enabled in `config/providers.json`
- Ensure provider credentials are valid

**Issue: Provider authentication fails**
- Clear sessions: `rm -rf .sessions/`
- Verify credentials in `config/providers.json`
- Check provider website for account status

**Issue: LongCat "Missing passport token"**
- Set `LONGCAT_PASSPORT_TOKEN` environment variable
- Or configure `LONGCAT_TOKENS_FILE`

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone and install
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python
pip install -r requirements.txt

# Install dev dependencies
pip install pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black app/

# Lint
flake8 app/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) - API specification
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- Provider APIs: Z.AI, K2Think, Qwen, LongCat

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/Zeeeepa/z.ai2api_python/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Zeeeepa/z.ai2api_python/discussions)
- 📧 **Email**: support@example.com

## 📈 Roadmap

- [ ] Add more provider integrations
- [ ] Implement request caching
- [ ] Add rate limiting
- [ ] Create web dashboard
- [ ] Add usage analytics
- [ ] Support for function calling
- [ ] Image generation endpoints
- [ ] Audio transcription support

---

**Made with ❤️ by the community**

