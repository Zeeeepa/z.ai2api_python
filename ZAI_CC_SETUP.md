# ZAI Claude Code Setup Guide

Comprehensive setup script for integrating Claude Code with Z.AI models through Claude Code Router.

## 🎯 What This Script Does

The `zai_cc.py` script automates the complete setup process:

1. **System Detection**: Automatically detects Windows, WSL2, or Linux
2. **Node.js Installation**: Installs Node.js and npm if not present (Linux/WSL)
3. **Claude Code Installation**: Installs `@anthropic-ai/claude-code` and `claude-code-router`
4. **Plugin Configuration**: Sets up the ZAI transformer plugin
5. **Router Configuration**: Creates proper `config.json` with GLM-4.6 and GLM-4.5V models
6. **Server Management**: Starts the Z.AI API proxy server

## 📋 Prerequisites

### Windows
- Python 3.9-3.12 installed
- Node.js installed (download from https://nodejs.org/)

### Linux/WSL2
- Python 3.9-3.12 installed
- `curl` installed (`sudo apt-get install curl`)
- `sudo` access (for Node.js installation)

## 🚀 Quick Start

### Option 1: One-Command Setup
```bash
python3 zai_cc.py
```

### Option 2: Step-by-Step
```bash
# 1. Make script executable (Linux/WSL)
chmod +x zai_cc.py

# 2. Run the setup
./zai_cc.py

# Or with python
python3 zai_cc.py
```

## 📁 What Gets Created

### File Structure

#### Windows
```
C:\Users\L\Desktop\PROJECTS\CC\
└── zai.js                          # ZAI transformer plugin

C:\Users\L\.claude-code-router\
├── config.json                     # Router configuration
└── plugins\                        # (empty, plugin is elsewhere)
```

#### WSL2/Linux
```
/home/l/zaicc/
└── zai.js                          # ZAI transformer plugin

~/.claude-code-router/
├── config.json                     # Router configuration
└── plugins\                        # (empty, plugin is elsewhere)
```

### Configuration Details

The script creates a `config.json` with these settings:

```json
{
  "HOST": "127.0.0.1",
  "PORT": 3456,
  "transformers": [
    {
      "name": "zai",
      "path": "<dynamic-path-to-zai.js>",
      "options": {}
    }
  ],
  "Providers": [
    {
      "name": "GLM",
      "api_base_url": "http://127.0.0.1:8080/v1/chat/completions",
      "api_key": "sk-your-api-key",
      "models": ["GLM-4.6", "GLM-4.5V"],
      "transformers": {
        "use": ["zai"]
      }
    }
  ],
  "Router": {
    "default": "GLM,GLM-4.6",
    "background": "GLM,GLM-4.6",
    "think": "GLM,GLM-4.6",
    "longContext": "GLM,GLM-4.6",
    "longContextThreshold": 80000,
    "webSearch": "GLM,GLM-4.6",
    "image": "GLM,GLM-4.5V"
  }
}
```

## 🔧 Using Claude Code with ZAI

After running the setup script:

### Terminal 1: Z.AI API Server
```bash
# Server should already be running, but if not:
python3 main.py
# Server runs on http://127.0.0.1:8080
```

### Terminal 2: Claude Code Router
```bash
claude-code-router
# Router runs on http://127.0.0.1:3456
```

### Terminal 3: Claude Code
```bash
claude-code
```

Claude Code will now use Z.AI's GLM models through the router!

## 🛠 Customization

### Change API Settings
Edit `.env` file in the repository:
```bash
# Z.AI API Server settings
AUTH_TOKEN=sk-your-custom-key
LISTEN_PORT=8080
ANONYMOUS_MODE=true
DEBUG_LOGGING=false
TOOL_SUPPORT=true
```

### Change Router Settings
Edit `~/.claude-code-router/config.json`:
```json
{
  "PORT": 3456,
  "Providers": [
    {
      "api_base_url": "http://127.0.0.1:8080/v1/chat/completions",
      "models": ["GLM-4.6", "GLM-4.5V"]
    }
  ]
}
```

### Change Model Selection
In `config.json`, update the Router section:
```json
{
  "Router": {
    "default": "GLM,GLM-4.6",      # Default model
    "think": "GLM,GLM-4.6",         # For reasoning tasks
    "image": "GLM,GLM-4.5V"         # For vision tasks
  }
}
```

## 🐛 Troubleshooting

### Node.js Not Found (Windows)
- Download and install from https://nodejs.org/
- Restart terminal after installation
- Run script again

### Permission Denied (Linux/WSL)
```bash
chmod +x zai_cc.py
sudo python3 zai_cc.py  # If Node.js installation fails
```

### Port Already in Use
```bash
# Check what's using port 8080
lsof -i :8080  # Linux/WSL
netstat -ano | findstr :8080  # Windows

# Kill the process or change port in .env
LISTEN_PORT=8081
```

### Claude Code Can't Connect
1. Verify Z.AI server is running:
   ```bash
   curl http://127.0.0.1:8080/
   ```

2. Verify router is running:
   ```bash
   curl http://127.0.0.1:3456/
   ```

3. Check router logs for errors

### Models Not Available
- Ensure `config.json` lists correct models: `GLM-4.6`, `GLM-4.5V`
- Restart claude-code-router after config changes
- Check Z.AI API server logs for errors

## 📊 Script Features

### Cross-Platform Support
- ✅ Windows (native paths)
- ✅ WSL2 Ubuntu (Linux paths in WSL)
- ✅ Linux (standard Unix paths)

### Automatic Detection
- System type (Windows/WSL/Linux)
- Existing installations (Node.js, Claude Code, Router)
- Running services (Z.AI server)

### Intelligent Installation
- Skips already installed components
- Uses package managers (npm for global installs)
- Creates necessary directories
- Handles path conversions

### Configuration Management
- Dynamic path resolution
- Platform-specific formatting
- JSON validation
- UTF-8 encoding support

## 🔍 Verification

After setup, verify everything works:

```bash
# Check Node.js
node --version
npm --version

# Check Claude Code
claude-code --version
claude-code-router --version

# Check Z.AI server
curl http://127.0.0.1:8080/

# Check configuration
cat ~/.claude-code-router/config.json
```

## 📚 Additional Resources

- [Z.AI API Documentation](https://github.com/Zeeeepa/z.ai2api_python)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Claude Code Router](https://github.com/anthropics/claude-code-router)

## 💡 Tips

1. **First Time Setup**: Run the script once, it handles everything
2. **Updates**: Re-run to update configurations
3. **Multiple Environments**: Script adapts to your environment automatically
4. **Debug Mode**: Enable `DEBUG_LOGGING=true` in `.env` for detailed logs

## ⚙️ Advanced Usage

### Custom ZAI Plugin Location
Edit `zai_cc.py` and modify `SystemDetector.get_zai_js_path()`:
```python
def get_zai_js_path(self) -> Path:
    return Path("/your/custom/path/zai.js")
```

### Custom Router Port
Edit the generated `config.json`:
```json
{
  "PORT": 3456,  # Change this
}
```

### Add More Providers
Edit `config.json` to add additional AI providers:
```json
{
  "Providers": [
    {
      "name": "GLM",
      "api_base_url": "http://127.0.0.1:8080/v1/chat/completions",
      "models": ["GLM-4.6", "GLM-4.5V"]
    },
    {
      "name": "AnotherProvider",
      "api_base_url": "http://localhost:9000/v1/chat/completions",
      "models": ["model-name"]
    }
  ]
}
```

## 🎉 Success!

Once everything is set up, you can use Claude Code with Z.AI's powerful GLM models:
- **GLM-4.6**: Advanced reasoning and long context (80K tokens)
- **GLM-4.5V**: Vision capabilities with image understanding

Happy coding! 🚀

