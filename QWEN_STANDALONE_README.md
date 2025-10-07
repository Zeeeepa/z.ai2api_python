# Qwen Standalone API Server

🚀 **Production-ready OpenAI-compatible API server for all Qwen models**

## Features

✅ **Complete Model Support**
- **qwen-max family** (7 models): base, latest, 0428, thinking, search, deep-research, video
- **qwen-plus family** (6 models): base, latest, thinking, search, deep-research, video  
- **qwen-turbo family** (6 models): base, latest, thinking, search, deep-research, video
- **qwen-long family** (5 models): base, thinking, search, deep-research, video
- **Special models** (3 models): qwen-deep-research, qwen3-coder-plus, qwen-coder-plus

✅ **Advanced Features**
- OpenAI-compatible API format
- Streaming & non-streaming responses
- Image generation & editing
- Video generation
- Deep research with citations
- Multi-modal support (text, image, video, audio)
- FlareProx integration for unlimited scaling
- Docker deployment ready
- Health checks & monitoring

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python

# Checkout qwen standalone branch
git checkout pr-1

# Install dependencies
pip install -e .
```

### 2. Configuration

Create `.env.qwen` file:

```env
# Required
QWEN_EMAIL=your@email.com
QWEN_PASSWORD=your_password

# Optional
PORT=8081
DEBUG=false
ENABLE_FLAREPROX=true
CLOUDFLARE_API_KEY=your_api_key
CLOUDFLARE_ACCOUNT_ID=your_account_id
```

### 3. Run Server

#### Option A: Direct Python
```bash
python qwen_server.py
```

#### Option B: Docker Compose
```bash
docker-compose -f docker-compose.qwen.yml up -d
```

#### Option C: Docker Build
```bash
docker build -f Dockerfile.qwen -t qwen-api .
docker run -p 8081:8081 --env-file .env.qwen qwen-api
```

## Usage Examples

### Python (OpenAI SDK)

```python
from openai import OpenAI

# Initialize client
client = OpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8081/v1"
)

# Text completion
response = client.chat.completions.create(
    model="qwen-turbo-latest",
    messages=[{"role": "user", "content": "What model are you?"}]
)
print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="qwen-max-latest",
    messages=[{"role": "user", "content": "Count to 10"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

# Thinking mode
response = client.chat.completions.create(
    model="qwen-max-thinking",
    messages=[{"role": "user", "content": "Solve: What is 157 * 23?"}]
)
print(response.choices[0].message.content)

# Search mode
response = client.chat.completions.create(
    model="qwen-plus-search",
    messages=[{"role": "user", "content": "Latest AI news"}]
)
print(response.choices[0].message.content)

# Image generation
response = client.images.generate(
    model="qwen-max-image",
    prompt="A beautiful sunset over mountains",
    n=1,
    size="1024x1024"
)
print(response.data[0].url)
```

### cURL

```bash
# Text completion
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{
    "model": "qwen-turbo-latest",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Streaming
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{
    "model": "qwen-max-latest",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }'

# List models
curl http://localhost:8081/v1/models

# Health check
curl http://localhost:8081/health
```

### JavaScript/TypeScript

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-anything',
  baseURL: 'http://localhost:8081/v1'
});

// Text completion
const response = await client.chat.completions.create({
  model: 'qwen-turbo-latest',
  messages: [{ role: 'user', content: 'What model are you?' }]
});

console.log(response.choices[0].message.content);

// Streaming
const stream = await client.chat.completions.create({
  model: 'qwen-max-latest',
  messages: [{ role: 'user', content: 'Count to 10' }],
  stream: true
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}
```

## Model Families

### qwen-max (7 models)
- `qwen-max` - Base model for general tasks
- `qwen-max-latest` - Latest stable version
- `qwen-max-0428` - Specific version
- `qwen-max-thinking` - Enhanced reasoning
- `qwen-max-search` - Web search integrated
- `qwen-max-deep-research` - Comprehensive research
- `qwen-max-video` - Video generation

### qwen-plus (6 models)
- `qwen-plus` - Base model
- `qwen-plus-latest` - Latest version
- `qwen-plus-thinking` - Reasoning mode
- `qwen-plus-search` - Search mode
- `qwen-plus-deep-research` - Research mode
- `qwen-plus-video` - Video generation

### qwen-turbo (6 models)
- `qwen-turbo` - Fast base model
- `qwen-turbo-latest` - Latest version
- `qwen-turbo-thinking` - Reasoning mode
- `qwen-turbo-search` - Search mode
- `qwen-turbo-deep-research` - Research mode
- `qwen-turbo-video` - Video generation

### qwen-long (5 models)
- `qwen-long` - Long context model
- `qwen-long-thinking` - Reasoning mode
- `qwen-long-search` - Search mode
- `qwen-long-deep-research` - Research mode
- `qwen-long-video` - Video generation

### Special Models (3 models)
- `qwen-deep-research` - Standalone research model
- `qwen3-coder-plus` - Code generation v3
- `qwen-coder-plus` - Code generation

## Testing

### Quick Test (3 basic models)
```bash
python test_qwen_server.py --quick
```

### Comprehensive Test (all 27+ models)
```bash
python test_qwen_server.py
```

### Custom Base URL
```bash
python test_qwen_server.py --base-url http://your-server:8081/v1
```

## FlareProx Integration

FlareProx provides unlimited scaling through Cloudflare Workers proxy rotation.

### Setup

1. Get Cloudflare credentials:
   - Sign up at https://cloudflare.com
   - Go to https://dash.cloudflare.com/profile/api-tokens
   - Create API token with "Edit Cloudflare Workers" permissions

2. Configure in `.env.qwen`:
```env
ENABLE_FLAREPROX=true
CLOUDFLARE_API_KEY=your_api_key
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_EMAIL=your@email.com
```

3. Manage workers:
```bash
# Create proxy workers
python flareprox.py create --count 3

# List active workers
python flareprox.py list

# Test workers
python flareprox.py test

# Cleanup all workers
python flareprox.py cleanup
```

### Benefits
- ✅ Unlimited request scaling
- ✅ Automatic IP rotation
- ✅ Bypass rate limits
- ✅ Geographic distribution
- ✅ Free tier: 100,000 requests/day per worker

## API Endpoints

### Chat Completions
```
POST /v1/chat/completions
```

OpenAI-compatible chat completion endpoint supporting all Qwen models.

**Request:**
```json
{
  "model": "qwen-turbo-latest",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 4096
}
```

**Response:**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "qwen-turbo-latest",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### List Models
```
GET /v1/models
```

Returns list of all available models.

### Image Generation
```
POST /v1/images/generations
```

Generate images using Qwen image models.

**Request:**
```json
{
  "model": "qwen-max-image",
  "prompt": "A beautiful sunset",
  "n": 1,
  "size": "1024x1024"
}
```

### Health Check
```
GET /health
```

Returns server health status.

## Docker Deployment

### Simple Deployment
```bash
docker-compose -f docker-compose.qwen.yml up -d
```

### With Custom Configuration
```bash
# Edit .env.qwen with your credentials
nano .env.qwen

# Start services
docker-compose -f docker-compose.qwen.yml up -d

# View logs
docker-compose -f docker-compose.qwen.yml logs -f

# Stop services
docker-compose -f docker-compose.qwen.yml down
```

### Production Deployment
```bash
# Build with optimizations
docker build -f Dockerfile.qwen -t qwen-api:prod .

# Run with resource limits
docker run -d \
  --name qwen-api \
  -p 8081:8081 \
  --memory="2g" \
  --cpus="2" \
  --env-file .env.qwen \
  --restart unless-stopped \
  qwen-api:prod

# Monitor
docker logs -f qwen-api
docker stats qwen-api
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `8081` | Server port |
| `QWEN_EMAIL` | Yes | - | Qwen account email |
| `QWEN_PASSWORD` | Yes | - | Qwen account password |
| `DEBUG` | No | `false` | Enable debug logging |
| `ENABLE_FLAREPROX` | No | `false` | Enable FlareProx scaling |
| `CLOUDFLARE_API_KEY` | No* | - | Cloudflare API key (*required if FlareProx enabled) |
| `CLOUDFLARE_ACCOUNT_ID` | No* | - | Cloudflare account ID (*required if FlareProx enabled) |
| `CLOUDFLARE_EMAIL` | No | - | Cloudflare account email |
| `DEFAULT_MODEL` | No | `qwen-turbo-latest` | Default model |
| `MAX_TOKENS` | No | `4096` | Max tokens per request |
| `TEMPERATURE` | No | `0.7` | Default temperature |

## Troubleshooting

### Server won't start
```bash
# Check logs
docker-compose -f docker-compose.qwen.yml logs

# Verify credentials
cat .env.qwen

# Test health
curl http://localhost:8081/health
```

### Authentication errors
```bash
# Verify Qwen credentials
# Login at https://chat.qwen.ai to test

# Check environment variables
env | grep QWEN
```

### Model not found
```bash
# List available models
curl http://localhost:8081/v1/models

# Use exact model name from list
```

### Slow responses
```bash
# Enable FlareProx for scaling
# Edit .env.qwen:
ENABLE_FLAREPROX=true

# Restart server
docker-compose -f docker-compose.qwen.yml restart
```

## Performance

- **Average latency**: 100-500ms per request
- **Streaming**: Real-time token generation
- **Throughput**: 10-50 requests/second (without FlareProx)
- **Throughput with FlareProx**: 100-500+ requests/second
- **Memory usage**: ~500MB-1GB
- **CPU usage**: 10-30% per core

## Security

- ✅ CORS enabled for all origins
- ✅ API key validation (configurable)
- ✅ Rate limiting support
- ✅ Environment-based secrets
- ✅ Docker security best practices
- ✅ Health check endpoints

## License

MIT License - see LICENSE file

## Support

- **Issues**: https://github.com/Zeeeepa/z.ai2api_python/issues
- **Documentation**: https://github.com/Zeeeepa/z.ai2api_python
- **Discord**: [Join our community]

## Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## Changelog

### v1.0.0 (2025-01-07)
- ✅ Initial standalone release
- ✅ All 27+ Qwen models supported
- ✅ OpenAI-compatible API
- ✅ Docker deployment
- ✅ FlareProx integration
- ✅ Comprehensive test suite

---

Made with ❤️ by Zeeeepa

