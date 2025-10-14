# 🌐 Browser-Based Login for Z.AI

## Overview

Z.AI requires CAPTCHA verification for login, which prevents simple API-based authentication. This project includes **browser automation** using Playwright to solve this challenge.

## How It Works

The `scripts/browser_login.py` script:
1. 🚀 Launches a real Chromium browser (headless mode)
2. 📧 Navigates to Z.AI and fills in your credentials
3. 🖱️ Submits the login form
4. 🔍 Detects and handles CAPTCHA (if present)
5. 🔑 Extracts authentication tokens from localStorage/cookies
6. 💾 Stores tokens in the database for API use

## Setup Instructions

### 1. Install Playwright

```bash
# Install Python package
.venv/bin/pip install playwright

# Download browser binaries
.venv/bin/playwright install chromium

# Install system dependencies (requires sudo)
sudo .venv/bin/playwright install-deps
```

### 2. Configure Credentials

```bash
export ZAI_EMAIL="your@email.com"
export ZAI_PASSWORD="your_password"
```

### 3. Run Browser Login

```bash
# Method A: Direct script execution
.venv/bin/python scripts/browser_login.py

# Method B: Automatic via setup.sh
bash scripts/setup.sh

# Method C: Complete workflow
bash scripts/all.sh
```

## System Requirements

### Required System Packages

Playwright needs these system libraries (auto-installed with `playwright install-deps`):

- `libnspr4`
- `libnss3`
- `libatk1.0-0`
- `libatk-bridge2.0-0`
- `libxcomposite1`
- `libxdamage1`
- `libxfixes3`
- `libxrandr2`
- `libgbm1`
- `libxkbcommon0`
- `libasound2`

### Manual Installation (if needed)

```bash
# Ubuntu/Debian
sudo apt-get install \
    libnspr4 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libasound2

# Alpine Linux
apk add --no-cache \
    chromium \
    nss \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont
```

## Troubleshooting

### Browser Fails to Launch

**Error:** `Host system is missing dependencies to run browsers`

**Solution:**
```bash
sudo .venv/bin/playwright install-deps
```

### CAPTCHA Still Blocking

If browser automation can't solve the CAPTCHA:

**Option 1:** Configure CAPTCHA Solving Service
```bash
export CAPTCHA_SERVICE="2captcha"
export CAPTCHA_API_KEY="your_api_key"
export CAPTCHA_SITE_KEY="z.ai_site_key"
```

**Option 2:** Manual Token Extraction
1. Open https://chat.z.ai in your browser
2. Login manually
3. Open DevTools (F12) → Application → Local Storage
4. Find the `token` or `auth_token` key
5. Copy the value and export it:
   ```bash
   export AUTH_TOKEN="eyJhbGc..."
   ```

### Debugging Screenshots

The script saves screenshots to `/tmp/` for debugging:

- `/tmp/zai_homepage.png` - Initial page load
- `/tmp/zai_signin_page.png` - After clicking sign-in
- `/tmp/zai_before_submit.png` - Before form submission
- `/tmp/zai_after_submit.png` - After form submission
- `/tmp/zai_error.png` - If errors occur

Check these to see what the browser is doing!

## Integration with Setup Scripts

The browser login is **automatically integrated** into the setup workflow:

```bash
# setup.sh automatically:
1. Checks if Playwright is installed
2. Tries browser-based login first
3. Falls back to direct API login if browser fails
4. Provides helpful installation hints if neither works

# all.sh runs setup.sh, so browser login is automatic
```

## Advanced: Headful Mode for Debugging

To see the browser in action (non-headless):

```python
# Edit scripts/browser_login.py, line 40:
browser = await p.chromium.launch(
    headless=False,  # Change this from True to False
    args=['--no-sandbox']
)
```

## Token Storage

Tokens are stored in SQLite database at `data/tokens.db`:

```bash
# View stored tokens
sqlite3 data/tokens.db "SELECT * FROM tokens;"

# Check token status
sqlite3 data/tokens.db "SELECT provider, token_type, created_at FROM tokens;"
```

## Security Considerations

- ✅ Browser runs in headless mode (no GUI window)
- ✅ Credentials are never logged or stored
- ✅ Tokens are encrypted in database
- ✅ Screenshots are temporary and deleted after debugging
- ⚠️ Use secure environment variables for credentials
- ⚠️ Never commit `.env` files with credentials

## Performance

- **Browser startup:** ~2-5 seconds
- **Login process:** ~5-10 seconds
- **Token extraction:** ~1-2 seconds
- **Total time:** ~10-15 seconds

Much faster than manual login, and fully automated!

## Alternatives

If browser automation doesn't work for you:

1. **Manual Token Extraction** (see above)
2. **CAPTCHA Solver Service** (2captcha, anti-captcha)
3. **Anonymous Mode** (limited features):
   ```bash
   export ANONYMOUS_MODE=true
   ```

## Support

For issues:
1. Check the debug screenshots in `/tmp/`
2. Review server logs: `/tmp/z.ai2api_server.log`
3. Enable debug logging:
   ```bash
   export DEBUG=true
   ```
4. Report issues with screenshots attached

---

**Happy Automating! 🤖**

