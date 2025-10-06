# Z.AI2API - OpenAI-Compatible Multi-Provider API Gateway

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

**Unified OpenAI-compatible API gateway supporting multiple AI providers with unlimited scalability via FlareProx**

[Features](#features) • [Quick Start](#quick-start) • [Docker Deploy](#docker-deployment) • [FlareProx](#flareprox-integration) • [API Docs](#api-documentation)

</div>

---

## 🎯 Features

- ✅ **OpenAI-Compatible API** - Drop-in replacement for OpenAI API
- 🔄 **Multi-Provider Support** - Z.AI, K2Think, Qwen (45+ models total)
- 🚀 **Unlimited Scalability** - FlareProx integration for IP rotation via Cloudflare Workers
- 🐳 **Docker Ready** - One-command deployment with docker-compose
- ⚡ **High Performance** - Async/await, streaming support
- 🔐 **Secure** - Environment-based configuration
- 📊 **Comprehensive** - Tool calling, thinking mode, search, multimodal

---

## 📦 Supported Providers & Models

| Provider | Models | Features |
|----------|--------|----------|
| **Z.AI** | 7 | GLM-4.5, GLM-4.6 (standard, thinking, search, air) |
| **K2Think** | 1 | MBZUAI-IFM/K2-Think (advanced reasoning) |
| **Qwen** | 35+ | qwen-max/plus/turbo/long + variants (thinking, search, image, video, deep-research) |

**Total**: 45+ models across 3 providers

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Provider credentials (Z.AI, K2Think, Qwen)
- (Optional) Cloudflare account for FlareProx unlimited scalability

### Installation

```bash
# Clone repository
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env and add your credentials

# Start server (that's it!)
python main.py
```

**✅ FlareProx auto-initializes on startup if credentials are configured!**

Server starts at `http://localhost:8080` with automatic:
- ✅ Provider initialization
- ✅ FlareProx proxy creation (if enabled)
- ✅ Intelligent load balancing
- ✅ Auto-scaling based on traffic

### Configuration

Edit `.env` file with your credentials:

```env
# Provider Credentials
ZAI_EMAIL=your_email@example.com
ZAI_PASSWORD=your_password

K2THINK_EMAIL=your_email@example.com
K2THINK_PASSWORD=your_password

QWEN_EMAIL=your_email@example.com
QWEN_PASSWORD=your_password

# Optional: FlareProx for unlimited scalability
FLAREPROX_ENABLED=true
CLOUDFLARE_API_TOKEN=your_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
FLAREPROX_PROXY_COUNT=3
```

---

## 🐳 Docker Deployment

### Quick Deploy

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Deploy with Docker
cd docker
./deploy.sh
```

### Manual Docker Commands

```bash
# Build and start
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop
docker-compose -f docker/docker-compose.yml down
```

---

## 🔥 FlareProx Integration

FlareProx enables **unlimited scalability** by routing requests through Cloudflare Workers, providing:

- ✅ **IP Rotation** - Automatic IP address rotation
- ✅ **Rate Limit Bypass** - Distribute requests across multiple endpoints
- ✅ **Free Tier** - 100,000 requests/day per worker
- ✅ **Global CDN** - Cloudflare's edge network

### Setup FlareProx

**FlareProx is now AUTOMATIC! Just configure and start!**

1. **Get Cloudflare Credentials**:
   - Sign up at [cloudflare.com](https://cloudflare.com)
   - Create API token: [https://dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
   - Use "Edit Cloudflare Workers" template
   - Copy token and Account ID

2. **Configure .env**:
```env
FLAREPROX_ENABLED=true
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id
FLAREPROX_PROXY_COUNT=3  # Number of proxy endpoints
FLAREPROX_AUTO_ROTATE=true
```

3. **Start Server** (FlareProx auto-initializes!):
```bash
python main.py
```

That's it! FlareProx will:
- ✅ Auto-create proxy workers on startup
- ✅ Load balance across all proxies
- ✅ Auto-rotate every 100 requests
- ✅ Scale automatically with traffic

**Optional Manual Management**:
```bash
# View active proxies
python flareprox.py list

# Create additional proxies
python flareprox.py create --count 5

# Cleanup all proxies
python flareprox.py cleanup
```

### How FlareProx Works

```
Client Request → Z.AI2API Router → FlareProx Pool (3+ endpoints)
                                    ↓ (auto-rotate)
                                 Cloudflare Worker #1 → Provider API
                                 Cloudflare Worker #2 → Provider API  
                                 Cloudflare Worker #3 → Provider API
```

Each worker gets **100,000 requests/day**, so 3 workers = **300,000 requests/day** for free!

---

## 📖 API Documentation

### Base URL
```
http://localhost:8080
```

### Endpoints

#### Chat Completions
```bash
POST /v1/chat/completions

curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

#### List Models
```bash
GET /v1/models

curl http://localhost:8080/v1/models
```

#### Health Check
```bash
GET /health

curl http://localhost:8080/health
```

### Supported Features

- ✅ **Streaming** - `"stream": true`
- ✅ **Thinking Mode** - Use models with `-thinking` suffix
- ✅ **Search** - Use models with `-search` suffix
- ✅ **Tool Calling** - `"tools": [...]`
- ✅ **Multimodal** - Images, video (model-dependent)
- ✅ **Temperature & Parameters** - `temperature`, `max_tokens`, `top_p`

### Example: Using Thinking Mode

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-4.5-Thinking",
    "messages": [
      {"role": "user", "content": "Explain quantum computing"}
    ],
    "stream": false
  }'
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific provider tests
pytest tests/test_zai.py -v -s
pytest tests/test_k2.py -v -s
pytest tests/test_qwen.py -v -s

# Test with actual API calls
pytest tests/test_zai.py::TestZAIAuthentication::test_token_retrieval -v -s
```

---

## 📁 Project Structure

```
z.ai2api_python/
├── app/                    # Application code
│   ├── api/               # API endpoints
│   ├── providers/         # Provider implementations
│   ├── models/            # Data models
│   ├── core/              # Core configuration
│   └── utils/             # Utilities
├── docker/                # Docker deployment
│   ├── Dockerfile         # Container image
│   ├── docker-compose.yml # Service orchestration
│   └── deploy.sh          # Deployment script
├── tests/                 # Test suite
│   ├── test_zai.py       # Z.AI tests
│   ├── test_k2.py        # K2Think tests
│   └── test_qwen.py      # Qwen tests
├── .env.example          # Environment template
├── flareprox.py          # FlareProx manager
├── main.py               # Entry point
└── README.md             # This file
```

---

## 🛠️ Development

### Local Development

```bash
# Install in development mode
pip install -e .

# Run with auto-reload
python main.py --reload

# Run with debug logging
python main.py --debug
```

### CLI Commands

```bash
# List available models
python main.py --list-models

# Health check
python main.py --check

# Version info
python main.py --version
```

---

## 📊 Performance & Scalability

### Without FlareProx
- Single IP address
- Provider rate limits apply
- ~100-1000 requests/hour (provider dependent)

### With FlareProx (3 workers)
- 3 rotating IP addresses
- 300,000 requests/day total
- ~12,500 requests/hour sustained
- Automatic failover

### Scaling to 100M+ Requests/Month

```bash
# Create 10 FlareProx endpoints
python flareprox.py create --count 10

# Result: 10 workers × 100K/day = 1M requests/day = 30M/month
```

**Cost**: $0 (Cloudflare Workers free tier)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🔗 Links

- **GitHub**: [Zeeeepa/z.ai2api_python](https://github.com/Zeeeepa/z.ai2api_python)
- **Issues**: [Report a bug](https://github.com/Zeeeepa/z.ai2api_python/issues)
- **Cloudflare Workers**: [Get Started](https://workers.cloudflare.com/)

---

## ⚠️ Disclaimer

This project is for educational and research purposes. Ensure you comply with provider terms of service and API usage policies.

---

<div align="center">

**Made with ❤️ by the Z.AI2API Team**

⭐ Star this repo if you find it useful!

</div>
