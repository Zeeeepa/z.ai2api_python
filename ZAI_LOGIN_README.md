# 🔐 Z.AI Automated Login Script

Automated login script for Z.AI that extracts authentication tokens using Playwright browser automation.

## 📋 Features

- ✅ **Automated Login Flow** - Complete email/password authentication
- ✅ **Slider CAPTCHA Solver** - Automatically solves slider CAPTCHAs
- ✅ **Token Extraction** - Extracts auth token from cookies/localStorage
- ✅ **`.env` Integration** - Optionally saves token to `.env` file
- ✅ **Cookie Persistence** - Saves browser cookies for reuse
- ✅ **Headless Mode** - Run without visible browser
- ✅ **Human-like Behavior** - Simulates realistic mouse movements

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install playwright

# Install Playwright browsers
playwright install chromium
```

### 2. Run the Script

```bash
# Basic usage (visible browser)
python zai_login.py --email your@email.com --password yourpassword

# Headless mode
python zai_login.py --email your@email.com --password yourpassword --headless

# Save token to .env file
python zai_login.py --email your@email.com --password yourpassword --save-env

# Save cookies for reuse
python zai_login.py --email your@email.com --password yourpassword --save-cookies
```

### 3. Use the Token

After successful login, the script will display your authentication token:

```bash
╔══════════════════════════════════════════════════════════════╗
║                    TOKEN EXTRACTED                           ║
╚══════════════════════════════════════════════════════════════╝

Token:
eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9...

✅ Token saved to .env as AUTH_TOKEN
```

Use it with the API server:

```bash
export AUTH_TOKEN='your-token-here'
python main.py --port 8080
```

## 📚 Complete Usage Guide

### Command-Line Options

```
usage: zai_login.py [-h] --email EMAIL --password PASSWORD
                    [--headless] [--save-env] [--save-cookies]
                    [--timeout TIMEOUT]

Automated Z.AI login and token extraction

options:
  -h, --help           show this help message and exit
  --email EMAIL        Z.AI account email
  --password PASSWORD  Z.AI account password
  --headless           Run browser in headless mode
  --save-env           Save token to .env file
  --save-cookies       Save cookies to file
  --timeout TIMEOUT    Timeout in seconds (default: 30)
```

### Examples

**1. Basic Login (Visible Browser)**
```bash
python zai_login.py \
    --email your@email.com \
    --password yourpassword
```
- Opens Chrome browser
- You can watch the automation
- Displays token in terminal

**2. Headless Mode (Production)**
```bash
python zai_login.py \
    --email your@email.com \
    --password yourpassword \
    --headless
```
- No visible browser window
- Faster execution
- Perfect for servers/CI/CD

**3. Save Everything**
```bash
python zai_login.py \
    --email your@email.com \
    --password yourpassword \
    --headless \
    --save-env \
    --save-cookies
```
- Saves token to `.env` file
- Saves cookies to `zai_cookies.json`
- Ready to use immediately

**4. Custom Timeout**
```bash
python zai_login.py \
    --email your@email.com \
    --password yourpassword \
    --timeout 60
```
- Increases timeout to 60 seconds
- Useful for slow networks

## 🔧 How It Works

### Login Flow

The script follows this automated flow:

```
1. Navigate to https://chat.z.ai/auth
   ├─ Load login page
   └─ Wait for elements to load

2. Click "Continue with Email" button
   ├─ Locate button by text/selector
   └─ Trigger click event

3. Enter email address
   ├─ Find email input field
   ├─ Click to focus
   └─ Type email

4. Enter password
   ├─ Find password input field
   ├─ Click to focus
   └─ Type password

5. Solve slider CAPTCHA (if present)
   ├─ Detect slider element
   ├─ Calculate drag distance
   ├─ Simulate human-like dragging
   └─ Wait for validation

6. Click "Sign In" button
   ├─ Locate submit button
   └─ Trigger click event

7. Wait for successful login
   ├─ Detect URL change to homepage
   ├─ Verify navigation completed
   └─ Confirm login success

8. Extract authentication token
   ├─ Check cookies for 'token'
   ├─ Check localStorage for 'token'
   └─ Return extracted token
```

### Slider CAPTCHA Solver

The script includes an intelligent slider CAPTCHA solver:

```python
# Features:
- Detects slider automatically
- Calculates exact drag distance
- Simulates human-like mouse movements
- Uses multiple small steps (not instant)
- Adds random delays between steps
- Validates solution automatically
```

**How it works:**
1. Finds slider wrapper and button elements
2. Gets their dimensions and positions
3. Calculates drag distance to the end
4. Moves mouse to button center
5. Presses mouse button down
6. Drags in 20 small steps with delays
7. Releases mouse button
8. Waits for validation

### Token Extraction

The script extracts tokens from two sources:

**1. Cookies:**
```python
cookies = await context.cookies()
for cookie in cookies:
    if cookie['name'] == 'token':
        return cookie['value']
```

**2. LocalStorage:**
```python
token = await page.evaluate("() => localStorage.getItem('token')")
```

## 📝 Output Files

### `.env` File (when using `--save-env`)

```bash
# Z.AI Authentication Token
# Generated: [timestamp]

AUTH_TOKEN=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9...
```

### `zai_cookies.json` (when using `--save-cookies`)

```json
[
  {
    "name": "token",
    "value": "eyJhbGciOiJFUzI1NiIs...",
    "domain": "chat.z.ai",
    "path": "/",
    "expires": 1234567890,
    "httpOnly": true,
    "secure": true,
    "sameSite": "Lax"
  },
  ...
]
```

## 🔒 Security Considerations

### ⚠️ Important Security Notes:

1. **Never commit tokens or passwords to git:**
   ```bash
   # Add to .gitignore
   .env
   zai_cookies.json
   *.token
   ```

2. **Use environment variables:**
   ```bash
   # Instead of hardcoding
   export ZAI_EMAIL="your@email.com"
   export ZAI_PASSWORD="yourpassword"
   
   python zai_login.py --email $ZAI_EMAIL --password $ZAI_PASSWORD
   ```

3. **Tokens are time-sensitive:**
   - Tokens may expire after a period
   - Re-run script to get fresh token
   - Check token validity before use

4. **Use headless mode on servers:**
   ```bash
   # Always use --headless on production servers
   python zai_login.py --email ... --password ... --headless
   ```

5. **Secure credential storage:**
   - Use password managers
   - Use encrypted environment files
   - Never log credentials

## 🐛 Troubleshooting

### Browser Won't Launch

**Error:** `playwright._impl._api_types.Error: Executable doesn't exist`

**Solution:**
```bash
playwright install chromium
```

### Slider CAPTCHA Failed

**Error:** `Failed to solve slider CAPTCHA`

**Solutions:**
1. Increase timeout: `--timeout 60`
2. Run without headless to watch: remove `--headless`
3. Try multiple times (CAPTCHA difficulty varies)
4. Check internet connection

### Login Failed

**Error:** `Login failed - still on auth page`

**Solutions:**
1. **Check credentials:** Verify email and password
2. **Check 2FA:** Script doesn't support 2FA yet
3. **Check rate limiting:** Wait a few minutes
4. **View browser:** Remove `--headless` to see errors

### Token Not Found

**Error:** `Token not found in cookies or localStorage`

**Solutions:**
1. Login may have failed - check previous errors
2. Z.AI may have changed token storage
3. Try running without `--headless` to debug
4. Check if account is verified

### CAPTCHA Keeps Appearing

If slider CAPTCHA appears repeatedly:

1. **Use residential IP:** VPN/proxy may trigger more CAPTCHAs
2. **Add delays:** Use longer `--timeout`
3. **Slow down:** Script may be too fast
4. **Manual solve:** Run without `--headless`, solve manually

## 🔄 Integration with API Server

### Method 1: Environment Variable

```bash
# Get token
python zai_login.py --email ... --password ... --save-env

# Token is now in .env
# Start server (automatically loads .env)
python main.py --port 8080
```

### Method 2: Direct Export

```bash
# Get token and export in one command
export AUTH_TOKEN=$(python zai_login.py \
    --email your@email.com \
    --password yourpassword \
    --headless | grep -A 1 "Token:" | tail -1)

# Start server
python main.py --port 8080
```

### Method 3: Automated Script

Create `start_with_auth.sh`:

```bash
#!/bin/bash

# Login and get token
python zai_login.py \
    --email "$ZAI_EMAIL" \
    --password "$ZAI_PASSWORD" \
    --headless \
    --save-env

# Start server if login successful
if [ $? -eq 0 ]; then
    echo "✅ Login successful, starting server..."
    python main.py --port 8080
else
    echo "❌ Login failed, cannot start server"
    exit 1
fi
```

Make it executable:
```bash
chmod +x start_with_auth.sh
```

Run:
```bash
export ZAI_EMAIL="your@email.com"
export ZAI_PASSWORD="yourpassword"
./start_with_auth.sh
```

## 📊 Exit Codes

- `0` - Success (token extracted)
- `1` - Failure (login failed, token not found, or error)
- `130` - Interrupted by user (Ctrl+C)

Use in scripts:

```bash
python zai_login.py --email ... --password ... --headless

if [ $? -eq 0 ]; then
    echo "Success!"
else
    echo "Failed!"
fi
```

## 🎯 Advanced Usage

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy with Z.AI Auth

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install playwright
          playwright install chromium
      
      - name: Get Z.AI token
        env:
          ZAI_EMAIL: ${{ secrets.ZAI_EMAIL }}
          ZAI_PASSWORD: ${{ secrets.ZAI_PASSWORD }}
        run: |
          python zai_login.py \
            --email "$ZAI_EMAIL" \
            --password "$ZAI_PASSWORD" \
            --headless \
            --save-env
      
      - name: Start server
        run: python main.py --port 8080 &
      
      - name: Run tests
        run: python test_all.py
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.10

# Install Playwright
RUN pip install playwright && \
    playwright install --with-deps chromium

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Entry script
CMD ["bash", "-c", "python zai_login.py --email $ZAI_EMAIL --password $ZAI_PASSWORD --headless --save-env && python main.py --port 8080"]
```

Run with:
```bash
docker run -e ZAI_EMAIL=... -e ZAI_PASSWORD=... -p 8080:8080 myimage
```

## 📚 Related Documentation

- [Main README](README.md) - API server documentation
- [Test Suite README](TEST_ALL_README.md) - Testing documentation
- [Z.AI Official Docs](https://chat.z.ai/docs) - API documentation

## 🤝 Contributing

Found a bug or want to improve the login script? 

1. Test your changes thoroughly
2. Update this README if needed
3. Submit a pull request

## ⚠️ Disclaimer

This script is for educational and personal use only. Make sure you comply with Z.AI's Terms of Service. Automated access may be restricted or result in account suspension if abused.

## 📄 License

Same license as the parent project.

