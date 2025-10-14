# Z.AI2API Automation Scripts

Complete automation suite for setting up, starting, and testing the Z.AI2API Python server.

## 🔥 IMPORTANT: NO MOCKS - 100% REAL API CALLS

**All scripts use ACTUAL API calls with REAL responses from Z.AI!**

The `send_openai_request.sh` script makes genuine requests to your running server, which:
- ✅ **Connects to real Z.AI chat interface** (not a mock)
- ✅ **Uses your JWT token** from browser session
- ✅ **Mimics web browser behavior** exactly
- ✅ **Returns authentic AI responses** from Z.AI/GLM models
- ✅ **Converts responses** to OpenAI API format

**You see the actual AI-generated content, not fake data!**

## 📋 Overview

This directory contains scripts to automate the entire workflow:

1. **setup.sh** - Environment setup and token retrieval
2. **start.sh** - Server startup and health monitoring
3. **send_openai_request.sh** - API testing with **REAL** OpenAI-compatible requests
4. **all.sh** - Complete orchestration of all steps
5. **retrieve_token.py** - Playwright-based token retrieval

## 🚀 Quick Start

### Prerequisites

- Python 3.9-3.12
- Bash shell
- curl
- Internet connection

### Environment Variables

Set these before running the scripts:

```bash
export QWEN_EMAIL=your-email@example.com
export QWEN_PASSWORD=your-password
```

### One-Command Setup

Run everything at once:

```bash
git clone https://github.com/Zeeeepa/z.ai2api_python.git
cd z.ai2api_python
export QWEN_EMAIL=your-email@example.com
export QWEN_PASSWORD=your-password
bash scripts/all.sh
```

This will:
- ✅ Install all dependencies
- ✅ Retrieve authentication token automatically via Playwright
- ✅ Start the server on port 8080
- ✅ Test the API with **REAL requests to Z.AI** (no mocks!)
- ✅ Display **actual AI-generated responses**
- ✅ Show live logs

## 📖 Individual Scripts

### 1. setup.sh

Performs initial environment setup:

```bash
export QWEN_EMAIL=your-email@example.com
export QWEN_PASSWORD=your-password
bash scripts/setup.sh
```

**What it does:**
- Checks Python version (requires 3.9+)
- Installs Python dependencies (via pip or uv)
- Installs Playwright and Chromium browser
- Creates `.env` file from template
- Retrieves authentication token via automated browser login
- Saves token to `.env` file
- Initializes SQLite database

**Requirements:**
- `QWEN_EMAIL` environment variable
- `QWEN_PASSWORD` environment variable

**Output:**
- `.env` file with valid `AUTH_TOKEN`
- `tokens.db` database file
- Installed dependencies

### 2. start.sh

Starts the API server:

```bash
bash scripts/start.sh
```

**What it does:**
- Checks if `.env` exists
- Validates port availability (default: 8080)
- Verifies dependencies are installed
- Starts server in background
- Monitors server health
- Creates PID file for process management
- Shows live logs

**Requirements:**
- `.env` file with valid configuration
- Available port (check `LISTEN_PORT` in `.env`)

**Output:**
- Running server on http://localhost:8080
- PID file: `.server.pid`
- Log file: `logs/server.log`

**Useful commands after starting:**
```bash
# View logs
tail -f logs/server.log

# Stop server
kill $(cat .server.pid)

# Check if running
curl http://localhost:8080/
```

### 3. send_openai_request.sh

Tests the API with **REAL** OpenAI-compatible requests:

```bash
bash scripts/send_openai_request.sh
```

**What it does:**
- Checks if server is running
- Sends **ACTUAL API calls** to your running server
- Server proxies to **real Z.AI chat interface** using your JWT token
- Displays **genuine AI-generated responses** from Z.AI/GLM models
- Tests streaming mode with **real streaming responses**
- Validates complete API functionality

**NO MOCKS:** All responses are authentic AI-generated content from Z.AI's service!

**Requirements:**
- Server running on configured port
- Valid `AUTH_TOKEN` in `.env`

**Output:**
- Formatted API response
- Token usage statistics
- Streaming test results

### 4. all.sh

Orchestrates complete workflow:

```bash
export QWEN_EMAIL=your-email@example.com
export QWEN_PASSWORD=your-password
bash scripts/all.sh
```

**What it does:**
- Runs `setup.sh` to configure environment
- Runs `start.sh` to start server
- Runs `send_openai_request.sh` to test API
- Displays comprehensive status
- Shows live logs

**Requirements:**
- Same as `setup.sh`

**Output:**
- Running and tested server
- Live log display

### 5. retrieve_token.py

Python script for automated token retrieval (called by setup.sh):

```bash
python scripts/retrieve_token.py
```

**What it does:**
- Launches headless Chromium browser
- Navigates to Z.AI login page
- Enters credentials
- Submits login form
- Extracts authentication token
- Saves token to `.env` file

**Requirements:**
- `QWEN_EMAIL` environment variable
- `QWEN_PASSWORD` environment variable
- Playwright installed with browsers

## 🔧 Configuration

### Port Configuration

Edit `.env` to change the server port:

```env
LISTEN_PORT=8080
```

### Authentication

The `AUTH_TOKEN` is automatically retrieved by `setup.sh`. To manually set it:

```env
AUTH_TOKEN=your-token-here
```

### Debug Mode

Enable detailed logging:

```env
DEBUG_LOGGING=true
```

## 📊 Server Management

### Check Server Status

```bash
# Using curl
curl http://localhost:8080/

# Check process
ps aux | grep main.py
```

### View Logs

```bash
# Real-time logs
tail -f logs/server.log

# Recent logs
tail -100 logs/server.log

# Search logs
grep "ERROR" logs/server.log
```

### Stop Server

```bash
# Using PID file
kill $(cat .server.pid)

# Or manually
kill <PID>

# Force kill if needed
kill -9 <PID>
```

### Restart Server

```bash
# Stop and start
kill $(cat .server.pid) && bash scripts/start.sh

# Or just run start.sh (it will detect if already running)
bash scripts/start.sh
```

## 🧪 Testing

### Manual API Test

```bash
# Using curl
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTH_TOKEN" \
  -d '{
    "model": "GLM-4-6-API-V1",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "stream": false
  }'
```

### Automated Test

```bash
bash scripts/send_openai_request.sh
```

## 🐛 Troubleshooting

### Setup Issues

**Problem:** `QWEN_EMAIL and QWEN_PASSWORD must be set`
```bash
# Solution: Export environment variables
export QWEN_EMAIL=your-email@example.com
export QWEN_PASSWORD=your-password
```

**Problem:** `Playwright browsers not found`
```bash
# Solution: Install browsers manually
python3 -m playwright install chromium
```

### Server Issues

**Problem:** `Port already in use`
```bash
# Solution 1: Kill process using the port
lsof -ti:8080 | xargs kill

# Solution 2: Change port in .env
echo "LISTEN_PORT=8081" >> .env
```

**Problem:** `Server failed to start`
```bash
# Check logs
cat logs/server.log

# Check dependencies
python3 -c "import fastapi, granian, httpx"
```

### Token Issues

**Problem:** `Failed to retrieve token`
```bash
# Solution 1: Check credentials
echo $QWEN_EMAIL
echo $QWEN_PASSWORD

# Solution 2: Run token retrieval with verbose output
python3 scripts/retrieve_token.py

# Solution 3: Manually set token in .env
echo "AUTH_TOKEN=your-token" >> .env
```

### API Test Issues

**Problem:** `Authentication failed`
```bash
# Check AUTH_TOKEN in .env
grep AUTH_TOKEN .env

# Test with different token
export AUTH_TOKEN=your-token
bash scripts/send_openai_request.sh
```

## 📝 Script Details

### Directory Structure

```
scripts/
├── README.md                    # This file
├── all.sh                       # Complete orchestration
├── setup.sh                     # Environment setup
├── start.sh                     # Server startup
├── send_openai_request.sh      # API testing
└── retrieve_token.py           # Token retrieval
```

### Script Dependencies

```
all.sh
├── setup.sh
│   ├── retrieve_token.py
│   └── Python dependencies
├── start.sh
│   └── main.py
└── send_openai_request.sh
    └── curl
```

## 🔐 Security Notes

- **Never commit** `.env` file to version control
- **Keep** `AUTH_TOKEN` private
- **Use** strong passwords for QWEN_EMAIL account
- **Rotate** tokens regularly
- **Monitor** `logs/server.log` for suspicious activity

## 🎯 Best Practices

1. **Always use environment variables** for credentials
2. **Check logs** regularly: `tail -f logs/server.log`
3. **Monitor server health** periodically
4. **Keep dependencies updated**: `pip install -U -r requirements.txt`
5. **Use setup.sh** for fresh installations
6. **Use all.sh** for quick testing

## 📚 Additional Resources

- **Project README**: `../README.md`
- **API Documentation**: http://localhost:8080/docs
- **Admin Panel**: http://localhost:8080/admin
- **GitHub**: https://github.com/Zeeeepa/z.ai2api_python

## 💡 Tips

- Use `uv` for faster dependency management
- Enable `DEBUG_LOGGING=true` when troubleshooting
- Check `logs/server.log` for detailed error messages
- Use `send_openai_request.sh` to verify changes
- Keep `QWEN_PASSWORD` secure

## 🆘 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review `logs/server.log` for errors
3. Ensure all prerequisites are met
4. Verify environment variables are set correctly
5. Open an issue on GitHub

---

**Happy coding! 🚀**
