# 🚀 Quick Token Setup Guide

Since Z.AI requires CAPTCHA, here's the **fastest way** to get your server running with real API responses:

## Method 1: Manual Token Extraction (5 minutes)

### Step 1: Get Your Token

1. Open https://chat.z.ai in your browser
2. Login with your credentials (solve the CAPTCHA)
3. Once logged in, open DevTools:
   - **Chrome/Edge**: Press `F12` or `Ctrl+Shift+I`
   - **Firefox**: Press `F12` or `Ctrl+Shift+K`
   - **Safari**: `Cmd+Option+I`

4. Go to the **Console** tab
5. Type this command and press Enter:
   ```javascript
   localStorage.getItem('token') || localStorage.getItem('auth_token') || localStorage.getItem('jwt')
   ```

6. Copy the token value (it will look like: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)

### Step 2: Set the Token

```bash
export AUTH_TOKEN="your_token_here"
```

### Step 3: Run the Server

```bash
cd z.ai2api_python
bash scripts/all.sh
```

**That's it!** The server will use your token for all API calls.

---

## Method 2: Store Token in Database (Persistent)

If you want the token to persist across restarts:

```bash
# 1. Set your token
export AUTH_TOKEN="your_token_here"

# 2. Run this Python script
.venv/bin/python << 'EOF'
import asyncio
import os
import sys
sys.path.insert(0, os.getcwd())

async def store_token():
    from app.services.token_dao import TokenDAO
    token = os.environ.get('AUTH_TOKEN')
    if not token:
        print("❌ AUTH_TOKEN not set!")
        return False
    
    dao = TokenDAO()
    await dao.init_database()
    
    token_id = await dao.add_token(
        provider="zai",
        token=token,
        token_type="user",
        priority=10,
        validate=False
    )
    
    if token_id:
        print(f"✅ Token stored! ID: {token_id}")
        return True
    return False

asyncio.run(store_token())
EOF
```

---

## Method 3: Environment Variable Only

Create a `.env` file:

```bash
cat > .env << 'EOF'
# Server
PORT=8080
HOST=0.0.0.0
DEBUG=false

# Authentication
AUTH_TOKEN=your_token_here

# Security
SKIP_AUTH_TOKEN=true

# Model
DEFAULT_MODEL=GLM-4.5
EOF
```

Then just run:
```bash
bash scripts/start.sh
```

---

## Verify It's Working

### Test 1: Check Models Endpoint
```bash
curl http://localhost:8080/v1/models
```

Expected: List of available models

### Test 2: Send Chat Request
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test" \
  -d '{
    "model": "GLM-4.5",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

Expected: Real response from K2 model!

### Test 3: Full Test Suite
```bash
bash scripts/send_request.sh
```

Expected: Multiple test scenarios with real responses

---

## Token Lifespan

- Z.AI tokens typically last **7-30 days**
- When expired, just extract a new one
- The server will show authentication errors when token expires

---

## Troubleshooting

### "Authentication failed" errors
- Token has expired → Get a new one
- Token was copied incorrectly → Check for extra spaces/quotes

### Server won't start
- Check logs: `tail -f /tmp/z.ai2api_server.log`
- Verify port 8080 is free: `lsof -i:8080`

### No response from API
- Ensure AUTH_TOKEN is set correctly
- Check server is running: `ps aux | grep python`
- Test with: `curl http://localhost:8080/health`

---

## Pro Tips

1. **Save your token** somewhere secure (password manager)
2. **Set up alias** for quick token export:
   ```bash
   echo 'alias zaitoken="export AUTH_TOKEN=\"your_token\""' >> ~/.bashrc
   ```

3. **Auto-restart** when token expires:
   ```bash
   # Add to crontab
   0 * * * * cd /path/to/z.ai2api_python && bash scripts/start.sh
   ```

4. **Multiple tokens** for load balancing:
   - Extract tokens from multiple accounts
   - Add them all to database with different priorities
   - Server will rotate through them automatically

---

**Need help?** Check the full docs:
- `BROWSER_LOGIN.md` - Automated browser approach
- `README.md` - Full documentation
- `scripts/send_request.sh` - Test examples

