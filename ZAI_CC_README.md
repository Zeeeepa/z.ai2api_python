# Z.AI Claude Code Integration

This script (`zai_cc.py`) automatically sets up Claude Code to work with Z.AI through the z.ai2api_python proxy service.

## 🎯 What It Does

The script automates the complete setup process for integrating Z.AI with Claude Code:

1. ✅ Creates `.claude-code-router` directory structure
2. ✅ Generates the Z.AI transformer plugin (`zai.js`)
3. ✅ Creates Claude Code Router configuration (`config.js`)
4. ✅ Starts the Z.AI API proxy server
5. ✅ Launches Claude Code with Z.AI integration

## 📋 Prerequisites

### Required
- **Python 3.9+** - For running the z.ai2api_python service
- **Node.js** - For running Claude Code and the transformer plugin
- **npm** - For installing Claude Code

### Optional
- **Claude Code** - Will prompt to install if not found
- **Z.AI Token** - Can use anonymous mode if not provided

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# Install Claude Code (if not installed)
npm install -g claude-code
```

### 2. Configure Environment (Optional)

Create a `.env` file or set environment variables:

```bash
# Optional: Set your Z.AI token
export AUTH_TOKEN="sk-your-api-key"

# Or use anonymous mode (default)
export ANONYMOUS_MODE="true"
```

### 3. Run the Setup Script

```bash
# Make executable
chmod +x zai_cc.py

# Run the setup
python zai_cc.py
```

The script will:
- ✓ Check for Node.js installation
- ✓ Create configuration directories
- ✓ Generate the Z.AI plugin
- ✓ Create the Claude Code Router config
- ✓ Start the API proxy server
- ✓ Launch Claude Code

### 4. Test Claude Code

Once Claude Code starts, ask it:
```
What model are you?
```

Expected response should mention **GLM-4.5** or similar Z.AI models.

## 📁 Generated Files

The script creates the following files:

```
~/.claude-code-router/
├── config.js           # Claude Code Router configuration
└── plugins/
    └── zai.js         # Z.AI transformer plugin
```

### config.js
Contains the routing configuration that tells Claude Code to use the Z.AI service through the local proxy.

### plugins/zai.js
Transformer plugin that:
- Fetches anonymous tokens from Z.AI
- Converts OpenAI format to Z.AI format
- Handles streaming responses
- Supports tool calling
- Manages system prompts

## ⚙️ Configuration

### Default Configuration

```javascript
{
  "Providers": [{
    "name": "GLM",
    "api_base_url": "http://127.0.0.1:8080/v1/chat/completions",
    "api_key": "sk-your-api-key",
    "models": ["GLM-4.5", "GLM-4.5-Air"],
    "transformers": {
      "use": ["zai"]
    }
  }],
  "Router": {
    "default": "GLM,GLM-4.5",
    "background": "GLM,GLM-4.5",
    "think": "GLM,GLM-4.5",
    "longContext": "GLM,GLM-4.5",
    "image": "GLM,GLM-4.5"
  }
}
```

### Customization

You can modify the generated `~/.claude-code-router/config.js` to:
- Change the API endpoint
- Add more models
- Configure different routing strategies
- Enable logging for debugging

## 🔧 Troubleshooting

### Issue: "Claude Code not found"
**Solution**: Install Claude Code
```bash
npm install -g claude-code
```

### Issue: "Node.js not found"
**Solution**: Install Node.js
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node

# Windows
# Download from https://nodejs.org/
```

### Issue: "API server not starting"
**Solution**: Start the server manually
```bash
python main.py
```

Check if port 8080 is already in use:
```bash
lsof -i :8080
# or
netstat -tulpn | grep 8080
```

### Issue: "Connection refused"
**Solution**: Verify the API server is running
```bash
curl http://127.0.0.1:8080/
```

Expected response:
```json
{"message": "OpenAI Compatible API Server"}
```

### Issue: Claude Code shows errors
**Solution**: Enable debug logging

Edit `~/.claude-code-router/config.js`:
```javascript
{
  "LOG": true,
  "LOG_LEVEL": "debug",
  ...
}
```

## 🔐 Authentication Modes

### Anonymous Mode (Default)
```bash
export ANONYMOUS_MODE="true"
python zai_cc.py
```

The plugin automatically fetches temporary tokens from Z.AI. No authentication needed!

### Authenticated Mode
```bash
# Set your Z.AI token
export AUTH_TOKEN="your-zai-token"
export ANONYMOUS_MODE="false"
python zai_cc.py
```

## 🌟 Features

### Supported Capabilities
- ✅ Streaming responses
- ✅ Tool/Function calling
- ✅ System prompts
- ✅ Multi-turn conversations
- ✅ Thinking/reasoning mode
- ✅ Long context handling
- ✅ Image understanding (GLM-4.5V)

### Z.AI Models Available
- **GLM-4.5**: Latest general-purpose model
- **GLM-4.5-Air**: Faster, lightweight variant
- **GLM-4.5V**: Multimodal (vision) support

## 📚 Advanced Usage

### Manual Configuration

If you prefer manual setup, follow these steps:

1. **Create directories**:
```bash
mkdir -p ~/.claude-code-router/plugins
```

2. **Copy the plugin**:
```bash
cp /path/to/zai.js ~/.claude-code-router/plugins/
```

3. **Create config.js**:
```bash
cat > ~/.claude-code-router/config.js << 'EOF'
module.exports = {
  // Your configuration here
};
EOF
```

4. **Start the API server**:
```bash
python main.py
```

5. **Run Claude Code**:
```bash
claude-code
```

### Multiple Providers

You can configure multiple AI providers in `config.js`:

```javascript
{
  "Providers": [
    {
      "name": "GLM",
      "api_base_url": "http://127.0.0.1:8080/v1/chat/completions",
      "models": ["GLM-4.5"],
      "transformers": { "use": ["zai"] }
    },
    {
      "name": "K2Think",
      // Additional provider config
    }
  ]
}
```

## 🤝 Contributing

Found an issue or want to improve the setup script? Contributions are welcome!

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Related Resources

- [Z.AI Official Website](https://chat.z.ai)
- [Claude Code Router](https://github.com/your-repo/claude-code-router)
- [z.ai2api_python](https://github.com/ZyphrZero/z.ai2api_python)

## 💡 Tips

1. **First Run**: The first API call may take a few seconds as it fetches the anonymous token
2. **Token Caching**: Tokens are cached for better performance
3. **Rate Limits**: Be mindful of Z.AI rate limits when using anonymous mode
4. **Model Selection**: Use `GLM-4.5` for best results, `GLM-4.5-Air` for faster responses

## ❓ FAQ

**Q: Do I need a Z.AI account?**
A: No! Anonymous mode works without an account. However, authenticated mode provides better rate limits.

**Q: Can I use this with other Claude Code projects?**
A: Yes! The configuration is global and works with any Claude Code project.

**Q: How do I switch back to regular Claude?**
A: Simply modify the `Router` configuration in `config.js` to use a different provider.

**Q: Is this secure?**
A: The proxy runs locally on your machine. Anonymous tokens are temporary and auto-refresh.

**Q: Can I use multiple models simultaneously?**
A: Yes! Configure different models in the Router section for different use cases.

## 🐛 Known Issues

- Claude Code Router must be v1.0.47 or higher for full compatibility
- Anonymous tokens expire after some time (auto-refreshed by the plugin)
- Some advanced features may require authenticated mode

## 🎓 Learning Resources

### Understanding the Flow

```
Claude Code → Claude Code Router → zai.js Plugin → Local Proxy (8080) → Z.AI API
```

1. **Claude Code**: Sends OpenAI-formatted requests
2. **Router**: Routes to appropriate provider (GLM)
3. **Plugin**: Transforms request for Z.AI format
4. **Proxy**: Handles authentication and forwarding
5. **Z.AI**: Processes and returns response

### Key Components

- **Transformer Plugin**: Converts between API formats
- **Router Configuration**: Determines which provider/model to use
- **Proxy Service**: Handles authentication and token management

---

Happy coding with Claude Code and Z.AI! 🚀

