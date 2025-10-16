# Z.AI to OpenAI API Proxy - Deployment Scripts

Automated deployment and testing scripts for the z.ai2api_python proxy server.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python

# Set credentials (optional - will use anonymous mode if not set)
export ZAI_EMAIL="your-email@example.com"
export ZAI_PASSWORD="your-password"
export SERVER_PORT=7322  # Optional, defaults to 7300

# Run everything
bash scripts/all.sh
```

That's it! The server will be deployed, started, and tested automatically.

## Individual Scripts

### 1. `deploy.sh` - Dependency Installation

Installs all dependencies and sets up the virtual environment.

```bash
bash scripts/deploy.sh
```

**What it does:**
- ✅ Checks for `uv` installation
- ✅ Creates Python virtual environment (`.venv/`)
- ✅ Installs project dependencies via `uv sync`
- ✅ Installs OpenAI client library for testing

**Requirements:**
- `uv` must be installed ([installation guide](https://github.com/astral-sh/uv))

**Exit Codes:**
- `0` - Success
- `1` - Missing required files (main.py, pyproject.toml)
- `2` - `uv` not installed

---

### 2. `start.sh` - Server Startup with Port Fallback

Starts the server with intelligent port selection.

```bash
bash scripts/start.sh
```

**What it does:**
- ✅ Finds available port (tries 7300 → 7301 → 7302, etc.)
- ✅ Starts server in background
- ✅ Waits for server to be ready
- ✅ Saves PID to `server.pid` and port to `server.port`

**Environment Variables:**
- `SERVER_PORT` - Starting port (default: 7300)
- `ZAI_EMAIL` - Your Z.AI email (optional)
- `ZAI_PASSWORD` - Your Z.AI password (optional)
- `AUTH_TOKEN` - API key for clients (default: "sk-any")

**Port Detection:**
The script tries up to 10 ports starting from `SERVER_PORT`. If all are busy, it exits with an error.

**Output Files:**
- `server.log` - Server logs
- `server.pid` - Server process ID
- `server.port` - Selected port number

**Exit Codes:**
- `0` - Success
- `1` - Virtual environment not found
- `3` - No available port found
- `4` - Server failed to start

---

### 3. `send_openai_request.sh` - API Testing

Sends a test OpenAI API request to verify the server is working.

```bash
bash scripts/send_openai_request.sh
```

**What it does:**
- ✅ Reads server port from `server.port`
- ✅ Verifies server is running (checks PID)
- ✅ Sends chat completion request
- ✅ Displays response and timing

**Test Request:**
```python
{
  "model": "gpt-5",
  "messages": [
    {"role": "user", "content": "Write a haiku about code."}
  ]
}
```

**Exit Codes:**
- `0` - Success
- `1` - Virtual environment not found
- `4` - Server not running
- `5` - API request failed

---

### 4. `all.sh` - Complete Setup (Recommended)

Runs all scripts in sequence with nice formatting.

```bash
bash scripts/all.sh
```

**Execution Order:**
1. `deploy.sh` - Install dependencies
2. `start.sh` - Start server
3. `send_openai_request.sh` - Test API

**Features:**
- 🎨 Colored output
- 📊 Environment display
- ❌ Fail-fast behavior (stops on first error)
- ✅ Success summary with useful commands

---

## Usage Examples

### Example 1: Basic Setup (Anonymous Mode)

```bash
cd z.ai2api_python
bash scripts/all.sh
```

Server will run in anonymous mode without Z.AI credentials.

### Example 2: With Z.AI Credentials

```bash
export ZAI_EMAIL="developer@pixelium.uk"
export ZAI_PASSWORD="developer123?"
export SERVER_PORT=7322

cd z.ai2api_python
bash scripts/all.sh
```

Server will authenticate with Z.AI using provided credentials.

### Example 3: Custom Port

```bash
export SERVER_PORT=8080
bash scripts/all.sh
```

Server will try port 8080 first, then 8081, 8082, etc. if busy.

### Example 4: Step-by-Step Execution

```bash
# Step 1: Deploy
bash scripts/deploy.sh

# Step 2: Start server
export ZAI_EMAIL="your@email.com"
export ZAI_PASSWORD="yourpass"
bash scripts/start.sh

# Step 3: Test API
bash scripts/send_openai_request.sh
```

---

## Server Management

### View Logs

```bash
tail -f server.log
```

### Stop Server

```bash
kill $(cat server.pid)
```

### Restart Server

```bash
# Stop current server
kill $(cat server.pid)

# Start new server
bash scripts/start.sh
```

### Check Server Status

```bash
# Check if process is running
ps -p $(cat server.pid)

# Get server port
cat server.port

# Test server endpoint
curl http://localhost:$(cat server.port)/v1/models
```

---

## Troubleshooting

### Error: "uv is not installed"

**Solution:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Error: "No available port found"

**Solution:**
- Check what's using ports: `lsof -ti:7300-7310`
- Kill processes or set different `SERVER_PORT`
- Example: `export SERVER_PORT=8000`

### Error: "Server failed to start"

**Solution:**
```bash
# Check logs
cat server.log

# Common issues:
# 1. Port already in use
# 2. Missing dependencies
# 3. Python version mismatch

# Try manual start for debugging
PYTHONPATH= ./.venv/bin/python main.py
```

### Error: "Virtual environment not found"

**Solution:**
```bash
# Run deploy script first
bash scripts/deploy.sh
```

### API Request Fails

**Solution:**
```bash
# 1. Verify server is running
ps aux | grep "python main.py"

# 2. Check port
cat server.port

# 3. Test with curl
PORT=$(cat server.port)
curl -X POST "http://localhost:$PORT/v1/chat/completions" \
  -H "Authorization: Bearer sk-any" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5","messages":[{"role":"user","content":"test"}]}'

# 4. Check logs
tail -50 server.log
```

### Error: "Z.AI API 错误: 405" or "匿名模式下获取访客令牌失败"

This error indicates that Z.AI's authentication API has changed or is temporarily unavailable.

**Solutions:**

1. **Use authenticated mode with credentials:**
   ```bash
   export ZAI_EMAIL="your-email@example.com"
   export ZAI_PASSWORD="your-password"
   bash scripts/start.sh
   ```

2. **Check Z.AI service status:**
   - Visit https://chat.z.ai/ to verify the service is operational
   - The anonymous token endpoint may have changed

3. **Wait and retry:**
   - Z.AI may be experiencing temporary issues
   - The service typically recovers within a few minutes

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_PORT` | `7300` | Starting port for server |
| `ZAI_EMAIL` | (none) | Z.AI account email |
| `ZAI_PASSWORD` | (none) | Z.AI account password |
| `AUTH_TOKEN` | `"sk-any"` | API key for client requests |
| `LISTEN_PORT` | Auto | Actual port selected by start.sh |

---

## File Structure

```
z.ai2api_python/
├── scripts/
│   ├── deploy.sh              # Install dependencies
│   ├── start.sh               # Start server
│   ├── send_openai_request.sh # Test API
│   ├── all.sh                 # Run all scripts
│   └── README.md              # This file
├── server.log                 # Server logs (generated)
├── server.pid                 # Server PID (generated)
└── server.port                # Server port (generated)
```

---

## Advanced Usage

### Run in Docker

**Note:** A Dockerfile is not currently included in this repository. To run with Docker, you'll need to create a Dockerfile first. Example:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv venv && uv sync
CMD ["bash", "scripts/start.sh"]
```

Then build and run:

```bash
# Build image
docker build -t z-ai2api .

# Run container
docker run -d \
  -p 7300:7300 \
  -e ZAI_EMAIL="your@email.com" \
  -e ZAI_PASSWORD="yourpass" \
  --name z-ai2api \
  z-ai2api
```

### Use with systemd

Create `/etc/systemd/system/z-ai2api.service`:

```ini
[Unit]
Description=Z.AI to OpenAI API Proxy
After=network.target

[Service]
Type=forking
User=youruser
WorkingDirectory=/path/to/z.ai2api_python
Environment="ZAI_EMAIL=your@email.com"
Environment="ZAI_PASSWORD=yourpass"
Environment="SERVER_PORT=7300"
ExecStart=/path/to/z.ai2api_python/scripts/start.sh
PIDFile=/path/to/z.ai2api_python/server.pid

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable z-ai2api
sudo systemctl start z-ai2api
```

---

## Contributing

When modifying scripts:
1. Test with `bash -n script.sh` (syntax check)
2. Test with `shellcheck script.sh` (linting)
3. Test all exit codes
4. Update this README

---

## Support

- **Repository:** https://github.com/Zeeeepa/z.ai2api_python
- **Issues:** https://github.com/Zeeeepa/z.ai2api_python/issues

---

**Made with ❤️ for simplified Z.AI proxy deployment**
