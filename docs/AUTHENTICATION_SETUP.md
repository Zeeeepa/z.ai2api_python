# Authentication Setup Guide

This document explains how the automatic authentication system works and how to use it.

## Overview

The project uses **Playwright** for automatic browser-based authentication. This ensures that:
- ✅ Real browser sessions are created
- ✅ Cookies are automatically extracted and saved
- ✅ Authentication persists across sessions
- ✅ Both active sessions and tests use the same authentication

## How It Works

### 1. Automatic Login Flow

When you make a request to a provider (ZAI, K2Think, or Qwen), the system:

1. **Checks for cached session** (12-hour validity)
   - If valid session exists → Use cached cookies/token
   - If no valid session → Proceed to login

2. **Automatic Browser Login** (using Playwright)
   - Opens headless Chromium browser
   - Navigates to login page
   - Fills in email and password
   - Clicks login button
   - Waits for successful login

3. **Extract Authentication Data**
   - Extracts cookies from browser
   - Extracts tokens from localStorage/sessionStorage
   - Extracts any API tokens from responses

4. **Save for Future Use**
   - Saves cookies to `~/.zai2api/sessions/{provider}_session.json`
   - Caches in memory for immediate reuse
   - Valid for 12 hours (configurable)

### 2. Session Persistence

Sessions are automatically saved and reused:

```
~/.zai2api/sessions/
├── zai_session.json      # ZAI cookies and token
├── k2think_session.json  # K2Think cookies and token
└── qwen_session.json     # Qwen cookies and token
```

## Configuration

### Provider Credentials

Edit `auth_config.json` in the project root:

```json
{
  "providers": [
    {
      "name": "zai",
      "baseUrl": "https://chat.z.ai",
      "loginUrl": "https://chat.z.ai/login",
      "chatUrl": "https://chat.z.ai/chat",
      "email": "your-email@example.com",
      "password": "your-password"
    },
    {
      "name": "k2think",
      "baseUrl": "https://www.k2think.ai",
      "loginUrl": "https://www.k2think.ai/login",
      "chatUrl": "https://www.k2think.ai/chat",
      "email": "your-email@example.com",
      "password": "your-password"
    },
    {
      "name": "qwen",
      "baseUrl": "https://chat.qwen.ai",
      "loginUrl": "https://chat.qwen.ai/login",
      "chatUrl": "https://chat.qwen.ai/chat",
      "email": "your-email@example.com",
      "password": "your-password"
    }
  ]
}
```

## Usage

### In Python Code

```python
from app.auth.provider_auth import create_auth

# Create auth instance for ZAI
config = {
    "name": "zai",
    "baseUrl": "https://chat.z.ai",
    "loginUrl": "https://chat.z.ai/login",
    "email": "your-email@example.com",
    "password": "your-password"
}

auth = create_auth(config)

# Get valid session (auto-login if needed)
session = await auth.get_valid_session()
cookies = session["cookies"]
token = session["token"]

# Use cookies in requests
async with httpx.AsyncClient(cookies=cookies) as client:
    response = await client.get("https://chat.z.ai/api/...")
```

### In Tests

Tests automatically use the authentication system through fixtures in `tests/conftest.py`:

```python
import pytest

@pytest.mark.asyncio
async def test_zai_api(zai_credentials):
    """Test will automatically authenticate using Playwright"""
    # Your test code here
    pass
```

## Provider-Specific Details

### ZAI Authentication

**Authentication Method**: Browser-based login + localStorage token extraction

**Extracted Data**:
- Cookies from browser session
- Auth token from localStorage or `/api/v1/auths/` endpoint

**Usage**: Token is used in Authorization header for API requests

### K2Think Authentication

**Authentication Method**: Browser-based login + session cookie extraction

**Extracted Data**:
- Session cookies from browser
- Optional auth token from localStorage/sessionStorage

**Usage**: Session cookies are used for authenticated requests

### Qwen Authentication

**Authentication Method**: Browser-based login + Bearer token generation

**Extracted Data**:
- `web_api_auth_token` from localStorage
- `ssxmod_itna` cookie
- Compressed Bearer token (gzip + base64 encoded)

**Usage**: Bearer token in Authorization header

## Troubleshooting

### Login Fails

1. **Check credentials** in `auth_config.json`
2. **Verify provider is accessible**:
   ```bash
   curl https://chat.z.ai
   ```
3. **Check Playwright installation**:
   ```bash
   playwright install chromium
   ```
4. **Enable debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Session Expired

Sessions automatically refresh after 12 hours. To force refresh:

```python
# Force new login
session = await auth.get_valid_session(force_refresh=True)
```

Or clear cached session:

```python
auth.clear_session()
```

### Cookies Not Working

1. **Check session file exists**:
   ```bash
   ls ~/.zai2api/sessions/
   ```
2. **Verify cookie format**:
   ```bash
   cat ~/.zai2api/sessions/zai_session.json
   ```
3. **Force re-authentication**:
   ```python
   auth.clear_session()
   session = await auth.get_valid_session()
   ```

## Installation

### Prerequisites

1. **Install Playwright**:
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Install Project Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### First-Time Setup

1. Configure credentials in `auth_config.json`
2. Run test to verify authentication:
   ```bash
   pytest tests/integration/test_zai_real.py::TestZAIAuthentication::test_guest_token_retrieval -v
   ```

## Security Notes

⚠️ **IMPORTANT**: The `auth_config.json` file contains sensitive credentials!

- **Do NOT commit** `auth_config.json` to version control
- **Use environment variables** in production:
  ```python
  import os
  config = {
      "email": os.getenv("ZAI_EMAIL"),
      "password": os.getenv("ZAI_PASSWORD"),
      ...
  }
  ```
- **Protect session files**: `~/.zai2api/sessions/` contains authentication cookies

## Advanced Configuration

### Custom Session Directory

```python
from app.auth.session_store import SessionStore

# Use custom directory
store = SessionStore("zai", base_dir="/custom/path")
```

### Session Validity Period

```python
# Check if session is valid (custom max_age in seconds)
if store.is_valid(max_age=7200):  # 2 hours
    session = store.load_session()
```

### Headless vs Headful Browser

For debugging, use headful browser:

```python
browser = await p.chromium.launch(headless=False)  # Show browser
```

## Architecture

```
┌─────────────────┐
│  API Request    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Provider Auth  │ ← get_valid_session()
└────────┬────────┘
         │
         ↓
    ┌────┴────┐
    │ Cached? │
    └────┬────┘
         │
    ┌────┴────┐
    │   YES   │───→ Return cached session
    └─────────┘
         │
         │ NO
         ↓
┌─────────────────┐
│  Playwright     │
│  Auto-Login     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Extract Cookies │
│ Extract Tokens  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Save Session   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Return Session  │
└─────────────────┘
```

## FAQ

**Q: Do I need to manually login every time?**
A: No! Authentication is automatic. Sessions are cached for 12 hours.

**Q: Can I use different credentials for testing?**
A: Yes! Create separate config files and use environment variables.

**Q: Does this work in CI/CD?**
A: Yes! Playwright works in headless mode. Ensure Playwright browsers are installed.

**Q: How do I update credentials?**
A: Edit `auth_config.json` and clear cached sessions with `auth.clear_session()`.

**Q: Can I see the browser during login?**
A: Yes! Set `headless=False` in the Playwright launch options for debugging.

