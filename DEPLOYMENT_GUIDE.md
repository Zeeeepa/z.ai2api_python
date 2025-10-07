# Deployment and Testing Guide

## 🚀 Quick Start Deployment

### Step 1: Install Dependencies

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install Playwright browsers (required for authentication)
playwright install chromium
```

### Step 2: Configure Provider Credentials

Create `config/providers.json` from the example:

```bash
cp config/providers.json.example config/providers.json
```

Edit `config/providers.json` and add your actual credentials:

```json
{
  "providers": [
    {
      "name": "zai",
      "enabled": true,
      "baseUrl": "https://chat.z.ai",
      "loginUrl": "https://chat.z.ai/auth",
      "chatUrl": "https://chat.z.ai",
      "email": "your-zai-email@example.com",
      "password": "your-zai-password"
    },
    {
      "name": "k2think",
      "enabled": true,
      "baseUrl": "https://www.k2think.ai",
      "loginUrl": "https://www.k2think.ai/login",
      "chatUrl": "https://www.k2think.ai/chat",
      "email": "your-k2think-email@example.com",
      "password": "your-k2think-password"
    },
    {
      "name": "qwen",
      "enabled": true,
      "baseUrl": "https://chat.qwen.ai",
      "loginUrl": "https://chat.qwen.ai/auth?action=signin",
      "chatUrl": "https://chat.qwen.ai",
      "email": "your-qwen-email@example.com",
      "password": "your-qwen-password"
    }
  ]
}
```

### Step 3: Set Environment Variables (Optional)

If using Cloudflare FlareProx for IP rotation:

```bash
# Copy the example file
cp .env.flareprox .env

# Or set directly
export CLOUDFLARE_API_TOKEN="your-token"
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
```

### Step 4: Start the Server

```bash
# Start the server
python3 main.py

# Or with custom port
export LISTEN_PORT=8080
python3 main.py
```

The server will:
- ✅ Initialize all providers
- ✅ Authenticate with each provider (using Playwright)
- ✅ Start listening on http://0.0.0.0:8080

---

## 🧪 Testing Individual Models

### Method 1: Using AllCall.py (Recommended)

The comprehensive test script we created:

```bash
python3 AllCall.py
```

**What it does:**
- Tests all 42+ models concurrently
- Shows response from each model
- Provides detailed error reporting
- Calculates success rate

### Method 2: Using curl (Manual Testing)

Test a single model:

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{
    "model": "GLM-4.5",
    "messages": [{"role": "user", "content": "Hello, what model are you?"}]
  }'
```

### Method 3: Using Python Script (Custom Testing)

Create a custom test script:

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8080/v1"
)

# Test Z.AI model
response = client.chat.completions.create(
    model="GLM-4.5",
    messages=[{"role": "user", "content": "What model are you?"}]
)
print(f"GLM-4.5: {response.choices[0].message.content}")

# Test Qwen model
response = client.chat.completions.create(
    model="qwen-max",
    messages=[{"role": "user", "content": "What model are you?"}]
)
print(f"Qwen-Max: {response.choices[0].message.content}")

# Test K2Think model
response = client.chat.completions.create(
    model="MBZUAI-IFM/K2-Think",
    messages=[{"role": "user", "content": "What model are you?"}]
)
print(f"K2-Think: {response.choices[0].message.content}")
```

### Method 4: Using the OpenAI Python Library (Streaming)

Test with streaming responses:

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8080/v1"
)

stream = client.chat.completions.create(
    model="GLM-4.6",
    messages=[{"role": "user", "content": "Write a short poem"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

---

## 📋 Testing Each Model Category

### Z.AI GLM Models

```bash
# Standard models
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{"model": "GLM-4.5", "messages": [{"role": "user", "content": "Hello"}]}'

# Thinking mode (shows reasoning process)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{"model": "GLM-4.5-Thinking", "messages": [{"role": "user", "content": "Solve: 2+2"}]}'

# Search mode (includes web search)
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{"model": "GLM-4.5-Search", "messages": [{"role": "user", "content": "Latest news?"}]}'
```

### Qwen Models

```bash
# Base model
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{"model": "qwen-max", "messages": [{"role": "user", "content": "Hello"}]}'

# Thinking mode
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{"model": "qwen-max-thinking", "messages": [{"role": "user", "content": "Explain quantum physics"}]}'

# Image generation
curl -X POST http://localhost:8080/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{"model": "qwen-max-image", "prompt": "A sunset over mountains", "n": 1}'
```

### K2Think Model

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{"model": "MBZUAI-IFM/K2-Think", "messages": [{"role": "user", "content": "Solve this problem step by step: What is 15% of 240?"}]}'
```

### Grok Models

```bash
# Grok-3
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{"model": "grok-3", "messages": [{"role": "user", "content": "Hello"}]}'

# Grok with search
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-anything" \
  -d '{"model": "grok-deepsearch", "messages": [{"role": "user", "content": "Latest AI news"}]}'
```

---

## 🔍 Monitoring and Debugging

### Check Server Logs

```bash
# View real-time logs
tail -f server.log

# Search for specific model
grep "GLM-4.5" server.log

# Check for errors
grep "ERROR" server.log
```

### Check Model Availability

```bash
# List all available models
curl http://localhost:8080/v1/models | jq
```

### Test Authentication Status

```bash
# Check if providers are authenticated
grep "authenticated" server.log
grep "token" server.log
```

---

## 🐛 Troubleshooting

### Issue: "Invalid API key" (401 Error)

**Cause:** Provider authentication hasn't completed successfully.

**Solution:**
1. Check credentials in `config/providers.json`
2. Ensure Playwright is installed: `playwright install chromium`
3. Check server logs for authentication errors
4. Try manual login to verify credentials work

### Issue: Models returning empty responses

**Cause:** Provider may require session refresh.

**Solution:**
1. Restart the server: `pkill -f "python3 main.py" && python3 main.py`
2. Clear session cache: `rm -rf data/sessions/*`
3. Check if provider's website is accessible

### Issue: Timeout errors

**Cause:** Model taking too long to respond.

**Solution:**
1. Increase timeout in AllCall.py or your test script
2. Try a faster model variant (e.g., `qwen-turbo` instead of `qwen-max`)
3. Check internet connection

### Issue: Rate limiting

**Cause:** Too many requests to provider.

**Solution:**
1. Enable FlareProx for IP rotation
2. Add delays between requests
3. Use fewer concurrent requests

---

## 📊 Performance Testing

### Load Testing Script

Create `load_test.py`:

```python
import asyncio
import time
from openai import AsyncOpenAI

async def test_model(client, model, question):
    start = time.time()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question}],
            timeout=30.0
        )
        duration = time.time() - start
        return {
            "model": model,
            "success": True,
            "duration": duration,
            "response_length": len(response.choices[0].message.content)
        }
    except Exception as e:
        return {
            "model": model,
            "success": False,
            "duration": time.time() - start,
            "error": str(e)
        }

async def main():
    client = AsyncOpenAI(
        api_key="sk-anything",
        base_url="http://localhost:8080/v1"
    )
    
    models = ["GLM-4.5", "qwen-max", "MBZUAI-IFM/K2-Think"]
    question = "What is artificial intelligence?"
    
    # Test each model 10 times
    tasks = []
    for _ in range(10):
        for model in models:
            tasks.append(test_model(client, model, question))
    
    results = await asyncio.gather(*tasks)
    
    # Print statistics
    for model in models:
        model_results = [r for r in results if r["model"] == model]
        successes = [r for r in model_results if r["success"]]
        avg_duration = sum(r["duration"] for r in successes) / len(successes) if successes else 0
        success_rate = len(successes) / len(model_results) * 100
        
        print(f"\n{model}:")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Avg Duration: {avg_duration:.2f}s")

asyncio.run(main())
```

Run: `python3 load_test.py`

---

## 🚢 Production Deployment

### Using Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run server
CMD ["python3", "main.py"]
```

Build and run:
```bash
docker build -t z-ai2api .
docker run -p 8080:8080 -v $(pwd)/config:/app/config z-ai2api
```

### Using systemd (Linux Service)

Create `/etc/systemd/system/z-ai2api.service`:

```ini
[Unit]
Description=Z.AI2API Proxy Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/z-ai2api
Environment="LISTEN_PORT=8080"
ExecStart=/usr/bin/python3 /opt/z-ai2api/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable z-ai2api
sudo systemctl start z-ai2api
sudo systemctl status z-ai2api
```

### Using Process Manager (PM2)

```bash
# Install PM2
npm install -g pm2

# Start server
pm2 start main.py --name z-ai2api --interpreter python3

# Monitor
pm2 monit

# View logs
pm2 logs z-ai2api

# Set to start on boot
pm2 startup
pm2 save
```

---

## 📈 Monitoring in Production

### Health Check Endpoint

```bash
# Add health check
curl http://localhost:8080/
# Should return: {"message": "OpenAI Compatible API Server"}
```

### Prometheus Metrics (Optional)

Add to your code for metrics collection:

```python
from prometheus_client import Counter, Histogram, start_http_server

# Start metrics server
start_http_server(9090)

# Track requests
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['model'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration', ['model'])
```

### Log Rotation

```bash
# Setup logrotate
sudo nano /etc/logrotate.d/z-ai2api

# Add:
/opt/z-ai2api/server.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## 🔐 Security Best Practices

1. **Never commit credentials**
   - Keep `config/providers.json` in `.gitignore`
   - Use environment variables for sensitive data

2. **Use HTTPS in production**
   - Deploy behind nginx with SSL
   - Use Let's Encrypt for free SSL certificates

3. **Implement rate limiting**
   - Limit requests per IP
   - Implement token-based authentication

4. **Regular updates**
   - Keep dependencies updated
   - Monitor security advisories

---

## 📚 Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Playwright Documentation](https://playwright.dev/python/)

---

## 🆘 Getting Help

If you encounter issues:

1. Check server logs: `tail -f server.log`
2. Test individual providers
3. Verify credentials are correct
4. Ensure all dependencies are installed
5. Check if provider websites are accessible

For debugging, enable verbose logging:
```bash
export DEBUG_LOGGING=true
python3 main.py
```

