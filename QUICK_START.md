# ⚡ Quick Start Guide

Get your Z.AI2API server running in 5 minutes!

## 🚀 Three Ways to Authenticate

### Option 1: Manual Token (Fastest, Free)

```bash
# 1. Login to https://chat.z.ai in browser
# 2. Open DevTools (F12) → Application → Cookies  
# 3. Copy the 'token' cookie value
# 4. Set environment variable:
export AUTH_TOKEN="your-token-here"

# 5. Run server:
bash scripts/all.sh
```

**Pros:** ✅ Free, ✅ Fast, ✅ Simple  
**Cons:** ❌ Manual process, ❌ Token expires eventually

---

### Option 2: Captcha Solver (Automated, Small Cost)

```bash
# 1. Sign up at https://2captcha.com (~$5 minimum)
# 2. Get API key from dashboard
# 3. Find Z.AI site key (see CAPTCHA_SETUP.md)
# 4. Configure:

export ZAI_EMAIL="your-email@example.com"
export ZAI_PASSWORD="your-password"
export CAPTCHA_SERVICE="2captcha"
export CAPTCHA_API_KEY="your-2captcha-key"
export CAPTCHA_SITE_KEY="z.ai-site-key"

# 5. Run server:
bash scripts/all.sh
```

**Pros:** ✅ Fully automated, ✅ No manual steps  
**Cons:** ❌ Small cost ($0.50-1.00 per 1000 logins)

---

### Option 3: Guest Mode (Limited, Free)

```bash
# 1. Configure:
export ANONYMOUS_MODE=true

# 2. Run server:
bash scripts/all.sh
```

**Pros:** ✅ Free, ✅ No account needed  
**Cons:** ❌ Limited features, ❌ May have restrictions

---

## 📝 Test Your Setup

Once the server is running on `http://localhost:8080`:

```bash
# Test with send_request.sh:
bash scripts/send_request.sh

# Or manually:
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test" \
  -d '{
    "model": "GLM-4.5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🔧 Scripts Overview

| Script | Purpose |
|--------|---------|
| `scripts/all.sh` | Full setup, init, start server, and test |
| `scripts/setup.sh` | One-time setup (install deps, etc.) |
| `scripts/start.sh` | Start already-configured server |
| `scripts/send_request.sh` | Send test requests to server |

---

## 📚 Need More Help?

- **Captcha Setup:** See `CAPTCHA_SETUP.md`
- **Full Documentation:** See `README.md`
- **Config Examples:** See `.env.captcha.example`

---

## ⚠️ Troubleshooting

**Server won't start?**
```bash
# Check if port 8080 is free:
lsof -ti:8080 | xargs kill -9

# Reinstall dependencies:
bash scripts/setup.sh
```

**Authentication fails?**
```bash
# Check your .env file:
cat .env | grep -E "EMAIL|PASSWORD|TOKEN|CAPTCHA"

# For manual token: ensure AUTH_TOKEN is set
# For captcha: ensure all CAPTCHA_* vars are set
```

**Captcha errors?**
- Verify your 2Captcha API key is valid
- Check account balance at https://2captcha.com
- Ensure CAPTCHA_SITE_KEY is correct (see CAPTCHA_SETUP.md)

---

## 🎯 Recommended Setup

For most users, we recommend **Option 1 (Manual Token)** to start:
1. It's free and instant
2. Tokens last a long time  
3. You can upgrade to captcha solver later if needed

Then switch to **Option 2 (Captcha Solver)** when:
- You need automation
- Token keeps expiring
- Running in production

---

**Happy coding!** 🎉

