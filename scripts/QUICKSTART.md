# 🚀 Quick Start Guide

Get the Z.AI to OpenAI API proxy running in 60 seconds!

## One-Command Setup

```bash
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python

# Optional: Set credentials
export ZAI_EMAIL="developer@pixelium.uk"
export ZAI_PASSWORD="developer123?"
export SERVER_PORT=7322

# Deploy, start, and test
bash scripts/all.sh
```

## What You Get

✅ **Server running** on http://localhost:7322 (or next available port)  
✅ **API endpoint** at http://localhost:7322/v1  
✅ **Automatic test** with working response  
✅ **Ready for production** or development use

## Test with cURL

```bash
curl -X POST "http://localhost:7322/v1/chat/completions" \
  -H "Authorization: Bearer sk-any" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## Test with Python

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-any",
    base_url="http://localhost:7322/v1"
)

response = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## Common Commands

```bash
# View logs
tail -f server.log

# Stop server
kill $(cat server.pid)

# Restart server
bash scripts/start.sh

# Run test
bash scripts/send_openai_request.sh
```

## File Locations

- **Logs:** `server.log`
- **PID:** `server.pid`
- **Port:** `server.port`
- **Scripts:** `scripts/`

## Need Help?

See [scripts/README.md](README.md) for detailed documentation.

---

**That's it! 🎉 Your proxy is ready to use!**

