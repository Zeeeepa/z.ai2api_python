# Grok Provider Documentation

## Overview

The Grok provider enables integration with Grok AI models through automated authentication using Playwright. It supports all Grok model variants with automatic login, token management, and session persistence.

## Supported Models

- `grok-3` - Base Grok 3 model
- `grok-4` - Base Grok 4 model  
- `grok-auto` - Automatic model selection
- `grok-fast` - Fast inference mode
- `grok-expert` - Expert mode with enhanced capabilities
- `grok-deepsearch` - Deep search with web integration
- `grok-image` - Image generation capabilities

## Configuration

### config/providers.json

```json
{
  "providers": [
    {
      "name": "grok",
      "loginUrl": "https://accounts.x.ai/sign-in?redirect=grok-com&email=true",
      "chatUrl": "https://grok.com/chat",
      "email": "your-email@example.com",
      "password": "your-password",
      "enabled": true
    }
  ]
}
```

### Configuration Options

- `loginUrl`: X.AI login page URL (default: `https://accounts.x.ai/sign-in?redirect=grok-com&email=true`)
- `chatUrl`: Grok chat page URL (default: `https://grok.com/chat`)
- `email`: Your Grok account email
- `password`: Your Grok account password
- `proxy` (optional): Proxy URL for requests
- `enabled`: Enable/disable the provider

## Installation

### 1. Install Playwright Browsers

After installing requirements, run:

```bash
playwright install chromium
```

This downloads the Chrome browser (~300MB) needed for automated authentication.

### 2. Configure Provider

Edit `config/providers.json` and add your Grok credentials:

```json
{
  "name": "grok",
  "email": "your-email@example.com",
  "password": "your-password",
  "enabled": true
}
```

## Usage

### OpenAI-Compatible API

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"
)

response = client.chat.completions.create(
    model="grok-3",  # or grok-4, grok-fast, etc.
    messages=[
        {"role": "user", "content": "Hello, Grok!"}
    ]
)

print(response.choices[0].message.content)
```

### Streaming

```python
response = client.chat.completions.create(
    model="grok-expert",
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## How It Works

### 1. Automated Authentication

On first request:
- Playwright launches a headless Chrome browser
- Navigates to X.AI login page
- Fills in email and password
- Completes login flow
- Extracts authentication cookies
- Captures `x-statsig-id` header from API calls
- Saves credentials to `data/grok_tokens.json`

### 2. Token Management

- Tokens cached for 1 hour
- Automatic refresh when expired
- Failure tracking and recovery
- Session persistence across restarts

### 3. Request Flow

```
Client Request → Token Manager → Auth Manager → Grok API → Response Transform → Client
                       ↓                ↓
                  Get Credentials   Auto-login if needed
```

## File Structure

```
app/providers/
├── grok_auth.py           # Automated authentication
├── grok_token_manager.py  # Token pool management
└── grok_provider.py       # Main provider implementation

data/
├── grok_tokens.json       # Cached credentials (gitignored)
└── grok_browser_data/     # Browser session data (gitignored)
```

## Troubleshooting

### "Login failed" Error

**Cause**: Incorrect credentials or captcha challenge

**Solution**:
1. Verify credentials in `config/providers.json`
2. Try manual login at https://grok.com to ensure account works
3. Check for captcha challenges (may require manual intervention)

### "x-statsig-id not captured" Warning

**Cause**: Failed to intercept authentication headers

**Solution**:
- Uses fallback header (should still work)
- If persistent, check browser console logs
- May indicate Grok API changes

### Playwright Installation Issues

**Cause**: Missing system dependencies

**Solution**:
```bash
# Linux
sudo apt-get install libgbm1 libasound2

# macOS
# Usually no additional dependencies needed

# Verify installation
playwright install --with-deps chromium
```

### "Browser not found" Error

**Cause**: Chromium browser not installed

**Solution**:
```bash
playwright install chromium
```

## Performance Considerations

- **First Request**: 10-15 seconds (includes login)
- **Subsequent Requests**: <2 seconds (uses cached credentials)
- **Token Refresh**: Automatic, transparent to clients
- **Memory Usage**: ~100MB (browser process)

## Security Notes

### Credential Storage

- Credentials stored in `config/providers.json` (plain text)
- Tokens cached in `data/grok_tokens.json` (plain text)
- Both should be gitignored and kept secure
- Consider using environment variables for production

### Browser Data

- Persistent browser session in `data/grok_browser_data/`
- Contains cookies and local storage
- Should be gitignored and kept secure

## Advanced Configuration

### Custom Proxy

```json
{
  "name": "grok",
  "proxy": "http://proxy.example.com:8080",
  ...
}
```

### Custom Cache Duration

Edit `grok_token_manager.py`:

```python
self._auth_duration = 7200  # 2 hours
```

## API Rate Limits

Grok enforces rate limits per account:
- **Normal accounts**: ~5 requests per 12 hours per model
- **Super accounts**: ~50 requests per 12 hours per model

The provider will automatically handle rate limit errors and refresh credentials when needed.

## Contributing

When modifying the Grok provider:

1. Test automated login flow
2. Verify token persistence
3. Check streaming and non-streaming modes
4. Test error handling and recovery
5. Update this documentation

## Known Limitations

- Requires real Grok account
- Browser automation adds latency
- May break with Grok UI changes
- Requires ~300MB for browser binaries
- Not suitable for high-frequency requests (due to auth overhead)

## Future Improvements

- [ ] Support for multiple Grok accounts (load balancing)
- [ ] Background token refresh
- [ ] Health check endpoint
- [ ] Metrics and monitoring
- [ ] Rate limit prediction
- [ ] Fallback to manual SSO tokens

## Support

For issues specific to the Grok provider:

1. Check logs in application output
2. Verify credentials work on grok.com
3. Try refreshing tokens: `rm data/grok_tokens.json`
4. Check Playwright installation: `playwright --version`

For Grok API issues, contact X.AI support.

