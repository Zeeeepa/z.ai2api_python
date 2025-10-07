# 🚀 Z.AI Claude Code Integration

Complete guide for using Z.AI GLM models with Claude Code via the standalone launcher.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [What Does It Do?](#-what-does-it-do)
- [Prerequisites](#-prerequisites)
- [Usage](#-usage)
- [Command-Line Options](#-command-line-options)
- [Advanced Usage](#-advanced-usage)
- [Troubleshooting](#-troubleshooting)
- [Model Reference](#-model-reference)

## ⚡ Quick Start

### One-Line Setup

```bash
python zai_cc.py
```

That's it! The script will:
1. ✅ Configure your environment
2. ✅ Start the Z.AI API server
3. ✅ Configure Claude Code Router
4. ✅ Start Claude Code Router
5. ✅ Test the integration
6. ✅ Keep everything running until you press Ctrl+C

### What You'll See

```
======================================================================
🚀 Z.AI Claude Code Router Launcher
======================================================================
ℹ️  API Port: 8080
ℹ️  CCR Port: 3456
ℹ️  Default Model: GLM-4.5

[1/6] Configuring Environment
✅ Created .env configuration

[2/6] Creating Claude Code Router Plugin
✅ Created plugin: /Users/you/.claude-code-router/plugins/zai.js

[3/6] Creating Claude Code Router Configuration
✅ Created config: /Users/you/.claude-code-router/config.js

[4/6] Starting Z.AI API Server
✅ Z.AI API server started successfully

[5/6] Testing API Connection
✅ API test successful!
ℹ️  Model: GLM-4.5
ℹ️  Response: I am GLM-4.5, a large language model...

[6/6] Starting Claude Code Router
✅ Claude Code Router started on port 3456

======================================================================
✅ Setup Complete!
======================================================================
🎯 Next Steps:
   1. Open Claude Code in your editor
   2. Ask: 'What model are you?'
   3. You should see GLM model responses!

⚠️  Press Ctrl+C to stop all services and exit
```

## 🎯 What Does It Do?

The `zai_cc.py` script is a **complete lifecycle manager** that automates everything:

### Automatic Configuration

#### 1. **Environment Setup** (`.env`)
```bash
# Automatically creates with optimal settings:
LISTEN_PORT=8080
DEBUG_LOGGING=true
ANONYMOUS_MODE=true
SKIP_AUTH_TOKEN=true
# ... and all model configurations
```

#### 2. **Claude Code Router Config** (`~/.claude-code-router/config.js`)
```javascript
{
  "Providers": [{
    "name": "GLM",
    "api_base_url": "http://127.0.0.1:8080/v1/chat/completions",
    "models": ["GLM-4.5", "GLM-4.6", "GLM-4.5V", ...],
    "transformers": { "use": ["zai"] }
  }],
  "Router": {
    "default": "GLM,GLM-4.5",
    "think": "GLM,GLM-4.5-Thinking",
    "longContext": "GLM,GLM-4.6",
    "image": "GLM,GLM-4.5V"
  }
}
```

#### 3. **CCR Plugin** (`~/.claude-code-router/plugins/zai.js`)
Automatically creates the Z.AI transformer plugin for request/response handling.

### Service Management

#### Startup
- ✅ Starts Z.AI API server (`python main.py`)
- ✅ Starts Claude Code Router (`ccr --dangerously-skip-update`)
- ✅ Monitors both processes
- ✅ Tests connectivity

#### Shutdown (Automatic on Exit)
- ✅ Gracefully stops Claude Code Router
- ✅ Gracefully stops API server
- ✅ Cleans up all resources
- ✅ Handles Ctrl+C / SIGTERM / SIGINT

## 📦 Prerequisites

### Required

1. **Python 3.8+** with dependencies:
   ```bash
   pip install fastapi uvicorn httpx pydantic pydantic-settings python-dotenv loguru
   ```

2. **Claude Code Router**:
   ```bash
   npm install -g @zinkawaii/claude-code-router
   ```

3. **OpenAI Python SDK** (optional, for testing):
   ```bash
   pip install openai
   ```

### Verify Installation

```bash
# Check Python
python --version

# Check CCR
ccr --version

# Check if in correct directory
ls main.py  # Should exist
```

## 💻 Usage

### Basic Usage

#### Full Setup (Recommended)
```bash
python zai_cc.py
```
Starts everything and keeps it running until Ctrl+C.

#### Test Only (No CCR)
```bash
python zai_cc.py --test-only
```
Just tests the API, doesn't start Claude Code Router.

#### Use Existing Server
```bash
python zai_cc.py --skip-server
```
Assumes API server is already running, only starts CCR.

### Advanced Usage

#### Custom Ports
```bash
python zai_cc.py --port 9000 --ccr-port 4000
```

#### Different Default Model
```bash
python zai_cc.py --model GLM-4.6
```

#### No Automatic Cleanup
```bash
python zai_cc.py --no-cleanup
```
Services keep running after script exits.

## 🎛️ Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--port PORT` | Z.AI API server port | `8080` |
| `--ccr-port PORT` | Claude Code Router port | `3456` |
| `--model MODEL` | Default model for CCR router | `GLM-4.5` |
| `--skip-server` | Don't start API server (use existing) | `false` |
| `--skip-ccr` | Don't start Claude Code Router | `false` |
| `--test-only` | Test API without starting CCR | `false` |
| `--no-cleanup` | Don't stop services on exit | `false` |

### Environment Variables

You can also configure via environment variables:

```bash
export ZAI_API_PORT=9000
export CCR_PORT=4000
python zai_cc.py
```

## 🔧 Advanced Usage

### Running in Background

#### Using nohup
```bash
nohup python zai_cc.py --no-cleanup > launcher.log 2>&1 &
```

#### Stop Background Services
```bash
pkill -f "python zai_cc.py"
pkill -f "python main.py"
pkill -f "ccr"
```

### Development Workflow

#### 1. Test API First
```bash
python zai_cc.py --test-only
```
Verify API is working before starting CCR.

#### 2. Use Existing Server
```bash
# Terminal 1: Start API manually
python main.py

# Terminal 2: Start CCR via launcher
python zai_cc.py --skip-server
```

#### 3. Debug Mode
```bash
# Check what's happening
python zai_cc.py --test-only
tail -f launcher.log  # If running in background
```

### Multiple Instances

Run multiple instances with different ports:

```bash
# Instance 1
python zai_cc.py --port 8080 --ccr-port 3456 &

# Instance 2
python zai_cc.py --port 8081 --ccr-port 3457 &
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "ccr not found"

**Problem:** Claude Code Router not installed.

**Solution:**
```bash
npm install -g @zinkawaii/claude-code-router
ccr --version  # Verify
```

#### 2. "Port already in use"

**Problem:** Port 8080 or 3456 is occupied.

**Solution:**
```bash
# Check what's using the port
lsof -i :8080
lsof -i :3456

# Kill the process or use different port
python zai_cc.py --port 9000 --ccr-port 4000
```

#### 3. "Server failed to start"

**Problem:** Missing dependencies or configuration error.

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Check main.py exists
ls main.py

# Try manual start to see error
python main.py
```

#### 4. "API test failed"

**Problem:** Server started but not responding.

**Solution:**
```bash
# Wait longer for server startup
sleep 10

# Test manually
curl http://127.0.0.1:8080/

# Check logs
tail -f nohup.out  # or wherever logs are
```

#### 5. "Invalid API key" (even with SKIP_AUTH_TOKEN)

**Problem:** .env not loaded properly or server needs restart.

**Solution:**
```bash
# Stop all services
pkill -f "python main.py"

# Remove old .env
rm .env

# Run launcher again
python zai_cc.py
```

### Debug Checklist

When something goes wrong:

```bash
# 1. Check if services are running
ps aux | grep "python main.py"
ps aux | grep "ccr"

# 2. Check ports
netstat -an | grep 8080
netstat -an | grep 3456

# 3. Test API manually
curl http://127.0.0.1:8080/

# 4. Check configurations
cat .env
cat ~/.claude-code-router/config.js

# 5. Check logs
tail -f nohup.out
```

### Getting Help

If you're still stuck:

1. Run with `--test-only` to isolate issues
2. Check server logs for error messages
3. Verify all prerequisites are installed
4. Try manual setup to identify the problem:
   ```bash
   # Start API manually
   python main.py
   
   # In another terminal, test
   curl http://127.0.0.1:8080/
   
   # Start CCR manually
   ccr --dangerously-skip-update
   ```

## 📊 Model Reference

### Available Models

| Model | Context | Parameters | Best For |
|-------|---------|-----------|----------|
| **GLM-4.5** | 128K | 360B | General purpose |
| **GLM-4.5-Air** | 128K | 106B | Speed & efficiency |
| **GLM-4.6** | 200K | ~360B | Long documents |
| **GLM-4.5V** | 128K | 201B | Vision/images |
| **GLM-4.5-Thinking** | 128K | 360B | Complex reasoning |
| **GLM-4.5-Search** | 128K | 360B | Web-enhanced |

### Model Routing

The launcher automatically configures Claude Code Router to use optimal models:

```javascript
{
  "default": "GLM,GLM-4.5",        // General queries
  "think": "GLM,GLM-4.5-Thinking", // Reasoning tasks
  "longContext": "GLM,GLM-4.6",    // Long documents
  "image": "GLM,GLM-4.5V"          // Image analysis
}
```

### Switching Models

#### Via Command Line
```bash
python zai_cc.py --model GLM-4.6
```

#### In Claude Code
Just ask using the model name:
```
[Use GLM-4.6] Analyze this long document...
```

#### Manual Configuration
Edit `~/.claude-code-router/config.js` and restart CCR.

## 🎓 Best Practices

### Development
- ✅ Use `--test-only` first to verify API
- ✅ Enable `DEBUG_LOGGING=true` in .env
- ✅ Check logs regularly
- ✅ Use `--skip-server` for faster CCR restarts

### Production
- ✅ Use reverse proxy (nginx/caddy) for HTTPS
- ✅ Set proper `AUTH_TOKEN` value
- ✅ Disable `SKIP_AUTH_TOKEN`
- ✅ Monitor with systemd or supervisor
- ✅ Set up log rotation

### Performance
- ✅ Use `GLM-4.5-Air` for speed
- ✅ Use `GLM-4.6` only for long contexts
- ✅ Enable caching if supported
- ✅ Monitor token usage

## 📝 Examples

### Example 1: Quick Test
```bash
# Test without starting CCR
python zai_cc.py --test-only
```

### Example 2: Custom Configuration
```bash
# Use port 9000, GLM-4.6 as default
python zai_cc.py --port 9000 --model GLM-4.6
```

### Example 3: Development Setup
```bash
# Terminal 1: Start API with debug
DEBUG_LOGGING=true python main.py

# Terminal 2: Start CCR only
python zai_cc.py --skip-server
```

### Example 4: Background Service
```bash
# Start in background
nohup python zai_cc.py --no-cleanup > ~/zai_launcher.log 2>&1 &

# Check status
tail -f ~/zai_launcher.log

# Stop when done
pkill -f "python zai_cc.py"
```

## 🔗 Links

- **Repository:** https://github.com/Zeeeepa/z.ai2api_python
- **Branch:** `CC`
- **Z.AI Official:** https://chat.z.ai
- **Claude Code Router:** https://github.com/zinkawaii/claude-code-router

## 📄 License

This project is part of the Z.AI2API Python repository.

---

**🎉 Happy Coding with Z.AI and Claude Code! 🎉**

