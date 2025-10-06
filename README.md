# Z.AI2API Python - Multi-Provider OpenAI-Compatible API

OpenAI-compatible API proxy supporting multiple AI providers: Qwen, Z.AI, K2Think, and LongCat.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure authentication
cp .env.example .env
# Edit .env with your settings

# Run server
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📋 Table of Contents

- [Qwen Provider](#qwen-provider)
- [Z.AI Provider](#zai-provider)
- [K2Think Provider](#k2think-provider)
- [LongCat Provider](#longcat-provider)
- [Testing](#testing)

---

# Qwen Provider

## 🔑 Authentication

### Get Your Token (JavaScript Snippet)

Visit [chat.qwen.ai](https://chat.qwen.ai), log in, and run this in the browser console (F12):

```javascript
const _0x4015=['WRPXWRnYW5G','rmoucJBdGW','ymkojmokoG','b8oDAtWA']; // [truncated for README]
// Full script available in docs/qwen_token_extractor.js
```

The script will:
1. Extract localStorage token
2. Extract session cookie
3. Compress the credentials
4. Copy to clipboard

### Temporary Free Token

For quick testing (expires 2025-10-08):
```
H4sIAAAAAAAAAxXIzXaiMBgA0AfitEV+Ki66AD6IEQWhMCnuJAQJEEQKEjnz8HPmLi97HeoCUR7xA85WvAk5/sV9YlIXf+J2+PnjHnbv7HUYLv9DeGou/CZMb8YxjdUozaYQ6Bq+NjzXPPOYxlooDnUuTvLUYCP6xr9YyJrqSUWRv1K9fFKRVLlW14UoO9zcZbhmWggnPVy95egeOra3edR4epi2RgTZGjaX3Xuwjul3uV2wHr35+8a0KnqVE3+11CGR/6sNNC3f0hhnT/yXzXx6qB60qIUt9GDMCBQZHwdJxdOHznAmlGSAHyhGFCzJA9gDjtZ8vbq2d5SjMuVKV2I7WAJAP3LDIgO1P0DOyGOXyv80O7ezlxTfLBftnW1ZovyC8my/s4PZyv1dNM7qSObs1n5we1mqkYFlGRA8kFAM+I4l7JiUI+Q5uAZaAN1BN4ADnEsJWbH0DLayj08xeXxp2l1hBERRXWMJN+cMG+vSE0lVaztUduGRtGCoT+wo9SWBRnkRK0AvxUDEL+ZmDtAcZBp7RiQdKcvO9XFwCpEpXjJZ1nRWnNryc2NU7rK9ydKG0C7u2hd3wIyg42vIgNdidMXS4REy7ZrZ7qRrS9AIkyXjbrB6tG1AbYCRYCUo/FgQApNwNVcmAgGr08k2g8XI4R9DCxV3aQIAAA==
```

## 📊 Available Models

### Chat Models
- `qwen-max` / `qwen-max-latest` - Most capable model
- `qwen-plus` / `qwen-plus-latest` - Balanced performance
- `qwen-turbo` / `qwen-turbo-latest` - Fast responses
- `qwen-long` - Long context support
- `qwen-max-0428` - Dated version

### Specialized Models
- `qwen-max-thinking` - Chain-of-thought reasoning
- `qwen-max-search` - Web search enabled
- `qwen-max-image` - Image generation
- `qwen-max-image_edit` - Image editing
- `qwen-max-video` - Video generation
- `qwen-max-deep-research` / `qwen-deep-research` - Deep research mode

### Code Models
- `qwen3-coder-plus` - Advanced code generation with tool calls

**Total: 32 model variants** (4 base × 8 capabilities)

## 🌐 Endpoints

| Endpoint                 | Method   | Description           |
|--------------------------|----------|-----------------------|
| `/v1/validate`           | GET/POST | Validate token        |
| `/v1/refresh`            | GET/POST | Refresh token         |
| `/v1/models`             | GET      | List available models |
| `/v1/chat/completions`   | POST     | Chat completions      |
| `/v1/images/generations` | POST     | Generate images       |
| `/v1/images/edits`       | POST     | Edit existing images  |
| `/v1/videos/generations` | POST     | Generate videos       |

## 💬 Usage Examples

### Basic Chat

```javascript
const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_COMPRESSED_QWEN_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "qwen-max-latest",
    messages: [{ role: "user", content: "Hello, how are you?" }],
    stream: false
  })
});
```

### 🌐 Web Search Mode

```javascript
const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "qwen-max-latest",
    tools: [{ type: "web_search" }],
    messages: [{ 
      role: "user", 
      content: "What are the latest AI developments?" 
    }]
  })
});
```

### 🧠 Thinking Mode (Chain-of-Thought)

```javascript
const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "qwen-max-latest",
    enable_thinking: true,
    thinking_budget: 30000,  // milliseconds
    messages: [{ 
      role: "user", 
      content: "Solve: If x + 5 = 12, what is x?" 
    }]
  })
});
```

### 💻 Code Generation (qwen3-coder-plus)

```javascript
const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "qwen3-coder-plus",
    tools: [{ type: "code" }],
    messages: [{ 
      role: "user", 
      content: "Write a Python function to calculate factorial" 
    }],
    stream: true
  })
});
```

### 🖼️ Vision (Multimodal)

```javascript
const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "qwen-max-latest",
    messages: [{
      role: "user",
      content: [
        { type: "text", text: "What do you see in this image?" },
        { 
          type: "image_url", 
          image_url: { 
            url: "https://example.com/image.jpg"
            // or: "data:image/jpeg;base64,..."
          }
        }
      ]
    }]
  })
});
```

### ✅ Valid Multimodal Combinations

```javascript
// ✅ Image + PDF (different categories)
{
  content: [
    { type: "text", text: "Analyze this image and document" },
    { type: "image_url", image_url: { url: "image.jpg" } },
    { type: "file_url", file_url: { url: "document.pdf" } }
  ]
}
```

### ❌ Invalid Combinations

```javascript
// ❌ Image + Video (same media category)
{
  content: [
    { type: "image_url", image_url: { url: "image.jpg" } },
    { type: "video_url", video_url: { url: "video.mp4" } }
    // Cannot mix media files
  ]
}
```

### 🔬 Deep Research

```javascript
const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "qwen-deep-research",
    messages: [{ 
      role: "user", 
      content: "Research quantum computing developments" 
    }]
  })
});
```

### 🎨 Image Generation

```javascript
const response = await fetch("http://localhost:8000/v1/images/generations", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    prompt: "A beautiful sunset over mountains",
    size: "1024x1024"
  })
});
```

### ✏️ Image Editing

```javascript
// Option 1: FormData with file upload
const formData = new FormData();
formData.append("image", imageFile);
formData.append("prompt", "Add a rainbow in the sky");

const response = await fetch("http://localhost:8000/v1/images/edits", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN"
  },
  body: formData
});

// Option 2: JSON with URL
const response = await fetch("http://localhost:8000/v1/images/edits", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    image: "https://example.com/image.jpg",
    prompt: "Change the sky to sunset"
  })
});
```

### 🎬 Video Generation

```javascript
const response = await fetch("http://localhost:8000/v1/videos/generations", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    prompt: "A cat playing with yarn in slow motion",
    size: "1280x720"
  })
});
```

---

# Z.AI Provider

## 🔑 Authentication

Visit [chat.z.ai](https://chat.z.ai), log in, and extract token using browser console.

## 📊 Available Models

- `GLM-4.5` - Latest GLM model
- `GLM-4.5-Thinking` - Reasoning mode
- `GLM-4.5-Search` - Web search
- `GLM-4.5-Air` - Lightweight version
- `GLM-4.6` - Newer version
- `GLM-4.6-Thinking` - GLM-4.6 with reasoning
- `GLM-4.6-Search` - GLM-4.6 with search

## 💬 Usage Examples

```javascript
const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_ZAI_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "GLM-4.5",
    messages: [{ role: "user", content: "Hello!" }]
  })
});
```

---

# K2Think Provider

## 🔑 Authentication

Visit [www.k2think.ai](https://www.k2think.ai), log in, and extract token.

## 📊 Available Models

- `MBZUAI-IFM/K2-Think` - Advanced reasoning model

## 💬 Usage Example

```javascript
const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_K2THINK_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "MBZUAI-IFM/K2-Think",
    messages: [{ role: "user", content: "Explain quantum computing" }]
  })
});
```

---

# LongCat Provider

## 🔑 Authentication

Requires `LONGCAT_PASSPORT_TOKEN` in environment variables.

## 📊 Available Models

- `LongCat-Flash` - Fast responses
- `LongCat` - Standard model
- `LongCat-Search` - Web search enabled

## 💬 Usage Example

```javascript
const response = await fetch("http://localhost:8000/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "LongCat",
    messages: [{ role: "user", content: "Hello!" }]
  })
});
```

---

# Testing

## Run Comprehensive Tests

```bash
# Test all providers with browser authentication
python tests/test_browser_auth.py --headless

# Test specific provider
python tests/test_browser_auth.py --test-qwen --headless

# Test OpenAPI endpoints
python tests/test_openapi_validation.py
```

## Test Results

✅ **Authentication**: Working with browser automation  
✅ **Z.AI**: 10 models, 6/6 tests passed  
✅ **K2Think**: 1 model, 2/2 tests passed  
✅ **Qwen**: 19 models detected, auth working  

---

# Configuration

## Environment Variables

```bash
# Required
AUTH_TOKEN=your-api-key

# Optional
SKIP_AUTH_TOKEN=false          # Skip authentication (testing only)
AUTH_TOKENS_FILE=tokens.txt    # Multiple API keys
LONGCAT_PASSPORT_TOKEN=token   # LongCat auth
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO
```

## Docker Deployment

```bash
docker build -t z-ai2api .
docker run -p 8080:8080 --env-file .env z-ai2api
```

---

# Features

✅ **Multi-Provider Support**: Qwen, Z.AI, K2Think, LongCat  
✅ **OpenAI-Compatible API**: Drop-in replacement  
✅ **Advanced Features**: Thinking mode, web search, code generation  
✅ **Multimodal**: Images, videos, audio, documents  
✅ **Streaming**: Real-time response streaming  
✅ **Token Management**: Automatic token rotation  

---

# License

MIT License - See [LICENSE](LICENSE) for details

---

# Documentation

- [Qwen Consolidation](QWEN_CONSOLIDATION.md) - Technical details on Qwen provider
- [OpenAPI Spec](docs/openapi.json) - Complete API specification
- [Examples](examples/) - Code examples

