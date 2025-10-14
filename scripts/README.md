# Z.AI OpenAI API Proxy - Bash Scripts

This directory contains automation scripts for setting up and testing the Z.AI OpenAI-compatible API proxy.

## 📜 all.sh - Complete Setup and Test Script

The `all.sh` script provides a fully automated workflow for:
1. ✅ Creating `.env` configuration file with optimal settings
2. 🚀 Starting the Z.AI API proxy server on port 8080
3. 🧪 Sending a real OpenAI-compatible API request
4. 📊 Displaying the **actual response from Z.AI GLM model** (NOT a mock!)
5. 📝 Keeping the server running with live log streaming

### Usage

```bash
# From the project root directory
./scripts/all.sh
```

Or:

```bash
bash scripts/all.sh
```

### What It Does Step-by-Step

#### 1. Environment Configuration
Creates a `.env` file with:
- `ANONYMOUS_MODE=true` - Uses Z.AI's anonymous access (no token required)
- `LISTEN_PORT=8080` - Server listens on port 8080
- `DEBUG_LOGGING=true` - Enables detailed logging
- `TOOL_SUPPORT=true` - Enables function calling support

#### 2. Server Startup
- Kills any existing process on port 8080
- Starts the FastAPI server in the background
- Waits up to 30 seconds for server to be ready
- Logs output to `server.log`
- Saves PID to `server.pid`

#### 3. API Testing
Sends a real request to the API:
```json
{
  "model": "GLM-4-6-API-V1",
  "messages": [
    {
      "role": "user",
      "content": "Hello! Please introduce yourself in one sentence."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 100,
  "stream": false
}
```

The script then:
- ✅ Validates the response is proper JSON
- 📊 Displays the full OpenAI-compatible response
- 💬 Extracts and highlights the actual model-generated content
- 📈 Shows token usage and metadata

#### 4. Server Management
- Keeps the server running
- Streams logs in real-time
- Cleans up on exit (Ctrl+C)

### Example Output

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║       Z.AI OpenAI API Proxy - Complete Setup          ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

==> Creating .env configuration...
✓ .env file created with ANONYMOUS_MODE=true

==> Starting Z.AI API server...
✓ Server started with PID: 12345
==> Server logs are being written to server.log
==> Waiting for server to start...
✓ Server is ready!

==> Testing OpenAI-compatible API endpoint...

==> Sending request to http://127.0.0.1:8080/v1/chat/completions
=== REQUEST ===
{
  "model": "GLM-4-6-API-V1",
  "messages": [
    {
      "role": "user",
      "content": "Hello! Please introduce yourself in one sentence."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 100,
  "stream": false
}

==> Calling API...

✓ Received valid JSON response!

=== ACTUAL OPENAI API RESPONSE (NOT MOCK!) ===

{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1697651234,
  "model": "GLM-4-6-API-V1",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I am GLM-4.6, an advanced language model developed by Zhipu AI..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 45,
    "total_tokens": 60
  }
}

╔════════════════════════════════════════════════════════╗
║       MODEL GENERATED RESPONSE FROM Z.AI GLM          ║
╚════════════════════════════════════════════════════════╝

I am GLM-4.6, an advanced language model developed by Zhipu AI...

✓ This is a REAL response from Z.AI, not a mock!

═══════════════════════════════════════════════════════
    Server is running successfully!
═══════════════════════════════════════════════════════

  Base URL:     http://127.0.0.1:8080
  Endpoints:    /v1/chat/completions, /v1/models
  API Key:      sk-test-key
  Server PID:   12345

  Management Commands:
    View logs:     tail -f server.log
    Stop server:   kill $(cat server.pid)
    Restart:       ./scripts/all.sh

==> Showing live server logs (Ctrl+C to exit and stop server)...
```

### Server Management

#### View Logs
```bash
tail -f server.log
```

#### Stop Server
```bash
kill $(cat server.pid)
```

#### Restart Server
```bash
./scripts/all.sh
```

### Testing the API Manually

Once the server is running, you can test it with curl:

```bash
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-test-key" \
  -d '{
    "model": "GLM-4-6-API-V1",
    "messages": [
      {"role": "user", "content": "What is 2+2?"}
    ]
  }'
```

Or with Python:

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-test-key",
    base_url="http://127.0.0.1:8080/v1"
)

response = client.chat.completions.create(
    model="GLM-4-6-API-V1",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Available Models

The proxy supports these Z.AI models:
- `GLM-4-6-API-V1` - GLM-4.6 (Advanced reasoning, 80K context)
- `GLM-4.5` - Balanced performance
- `GLM-4.5V` - Vision-capable model
- `GLM-4-Air` - Lightweight fast model

### Features

✅ **No Token Required** - Uses Z.AI's anonymous mode  
✅ **OpenAI Compatible** - Drop-in replacement for OpenAI API  
✅ **Function Calling** - Supports tool/function calls  
✅ **Streaming** - Real-time streaming responses  
✅ **Vision** - Image understanding with GLM-4.5V  
✅ **Auto-Retry** - Automatic retry on failures  
✅ **Color Output** - Beautiful terminal output  
✅ **Error Handling** - Comprehensive error messages  

### Troubleshooting

#### Port 8080 Already in Use
The script automatically kills existing processes on port 8080. If issues persist:
```bash
# Find and kill the process manually
lsof -ti:8080 | xargs kill -9
```

#### Server Fails to Start
Check the server logs:
```bash
cat server.log
```

Common issues:
- Missing Python dependencies: `pip install -r requirements.txt`
- Python version < 3.9: Upgrade Python
- Network issues: Check firewall settings

#### API Returns Errors
Enable debug logging in `.env`:
```bash
DEBUG_LOGGING=true
```

Then restart the server and check `server.log`.

### Requirements

- Python 3.9+
- curl (for API requests)
- jq (for JSON formatting)
- lsof (for port checking)

Install missing tools:
```bash
# Ubuntu/Debian
sudo apt-get install curl jq lsof

# macOS
brew install curl jq lsof
```

### Notes

- The script uses `ANONYMOUS_MODE=true` which doesn't require Z.AI tokens
- Server runs in background and auto-cleanup on exit
- All responses are **real** from Z.AI GLM models, not mocked
- Logs are saved to `server.log` for debugging
- PID is saved to `server.pid` for management

### Contributing

To improve this script:
1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request

### License

This script is part of the z.ai2api_python project.

