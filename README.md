# Z.AI Browser Automation - OpenAI Compatible API

[![Status](https://img.shields.io/badge/status-working-brightgreen)](https://github.com/Zeeeepa/z.ai2api_python)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![API](https://img.shields.io/badge/API-OpenAI%20Compatible-orange)](https://platform.openai.com/docs/api-reference)

> **One-command deployment** of Z.AI guest mode with OpenAI-compatible API using browser automation.

---

## 🚀 Quick Start

### One Command Installation

```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/z.ai2api_python/main/install_and_run.sh | bash
```

**That's it!** The script will:
- Clone the repository
- Install all dependencies (Python, Playwright, browsers)
- Deploy the server with browser automation
- Validate with actual OpenAI API call
- Print formatted response
- Keep server running

---

## ✨ Features

- 🆓 **Guest Mode** - No API keys required
- 🔓 **Bypasses Signature Validation** - Uses browser automation
- 🔌 **OpenAI Compatible** - Drop-in replacement for OpenAI API
- 🚀 **Auto-Install** - Zero manual configuration
- 🧪 **Self-Testing** - Validates deployment automatically
- 📊 **Built-in Stats** - `/stats` endpoint for monitoring
- 📖 **API Documentation** - Auto-generated Swagger docs at `/docs`
- 💪 **Production Ready** - Error handling, logging, CORS support

---

## 📖 Usage

### After Deployment

```bash
# Set environment variables
export OPENAI_API_KEY='sk-test'
export OPENAI_BASE_URL='http://127.0.0.1:9000/v1'

# Use with OpenAI Python client
python3 << 'EOF'
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model='GLM-4.5',
    messages=[{'role': 'user', 'content': 'Hello, how are you?'}]
)
print(response.choices[0].message.content)
EOF
```

### Alternative Languages

**cURL:**
```bash
curl http://127.0.0.1:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-test" \
  -d '{
    "model": "GLM-4.5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**JavaScript:**
```javascript
const OpenAI = require('openai');

const client = new OpenAI({
  apiKey: 'sk-test',
  baseURL: 'http://127.0.0.1:9000/v1'
});

const response = await client.chat.completions.create({
  model: 'GLM-4.5',
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(response.choices[0].message.content);
```

---

## 🎯 Deployment Options

### Option 1: One-Command (Recommended)
```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/z.ai2api_python/main/install_and_run.sh | bash
```

### Option 2: Clone First
```bash
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python
bash install_and_run.sh
```

### Option 3: Manual Deployment
```bash
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python
bash deploy_browser_automation.sh 9000
```

### Option 4: Custom Port
```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/z.ai2api_python/main/install_and_run.sh | bash -s -- main 8080
```

---

## 🛠️ Management

### Health Check
```bash
curl http://127.0.0.1:9000/health
```

### Statistics
```bash
curl http://127.0.0.1:9000/stats
```

### API Documentation
```bash
# Open in browser
open http://127.0.0.1:9000/docs
```

### View Logs
```bash
tail -f /tmp/zai_server_9000.log
```

### Stop Server
```bash
# Get PID from deployment output
kill <PID>
```

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/stats` | GET | Statistics |
| `/docs` | GET | API documentation (Swagger) |
| `/v1/chat/completions` | POST | OpenAI-compatible chat |

---

## 🔧 Technical Details

### Architecture

```
┌─────────────────────┐
│   OpenAI Client     │
│  (Python/JS/cURL)   │
└──────────┬──────────┘
           │ HTTP POST
           ↓
┌─────────────────────┐
│   FastAPI Server    │
│    + Uvicorn        │ Port 9000
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   Playwright        │
│  Browser Automation │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   Z.AI Website      │
│   (chat.z.ai)       │
│   Guest Mode        │
└─────────────────────┘
```

### Technology Stack

- **FastAPI** - Modern async Python web framework
- **Uvicorn** - ASGI server
- **Playwright** - Browser automation
- **Chromium** - Headless browser
- **Python 3.8+** - Runtime

### How It Works

1. Launches headless Chromium browser
2. Navigates to chat.z.ai in guest mode
3. Receives requests via OpenAI-compatible API
4. Types messages into Z.AI chat interface
5. Extracts responses from DOM
6. Returns formatted OpenAI-compatible responses

---

## 🐛 Troubleshooting

### Browser Initialization Fails

```bash
# Manually install Playwright browsers
playwright install chromium
playwright install-deps chromium
```

### Port Already in Use

```bash
# Use different port
curl -fsSL <url> | bash -s -- main 8080
```

### Slow Responses

Browser automation takes 5-10 seconds per request. This is normal behavior.

### No Response Extracted

Check server logs for DOM selector issues:
```bash
tail -f /tmp/zai_server_9000.log
```

---

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[install_and_run.sh](install_and_run.sh)** - Main installation script
- **[deploy_browser_automation.sh](deploy_browser_automation.sh)** - Standalone deployment

---

## 🧪 Testing

The installation script automatically runs validation tests. You can also test manually:

```bash
export OPENAI_API_KEY='sk-test'
export OPENAI_BASE_URL='http://127.0.0.1:9000/v1'

python3 << 'EOF'
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model='GLM-4.5',
    messages=[{'role': 'user', 'content': 'Test message'}]
)
print(response.choices[0].message.content)
EOF
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Faster response extraction
- Better DOM selectors
- Enhanced error handling
- Alternative deployment methods
- Performance optimizations
- Additional model support

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🎉 Credits

Created by the Codegen team as a working solution for Z.AI guest mode access.

**Tested and verified:** January 9, 2025

---

## 🔗 Links

- **GitHub Repository:** https://github.com/Zeeeepa/z.ai2api_python
- **Pull Request:** https://github.com/Zeeeepa/z.ai2api_python/pull/7
- **Z.AI Website:** https://chat.z.ai
- **OpenAI API Docs:** https://platform.openai.com/docs/api-reference

---

## ⚠️ Disclaimer

This project is for educational and research purposes. It uses browser automation to access Z.AI in guest mode. For production use, consider:

- Z.AI Official API (https://z.ai/manage-apikey)
- Rate limiting implementation
- Error recovery mechanisms
- Proper authentication if available

---

## 🌟 Star History

If you find this useful, please consider starring the repository!

---

**Happy Coding!** 🚀

