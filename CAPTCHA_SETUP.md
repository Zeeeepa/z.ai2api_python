# 🔐 Captcha Solver Setup Guide

This project includes comprehensive captcha solving capabilities to handle Z.AI's login verification requirements.

## Supported Captcha Services

The system supports three major captcha solving services:

1. **2Captcha** (Recommended) - https://2captcha.com
2. **AntiCaptcha** - https://anti-captcha.com  
3. **CapSolver** - https://capsolver.com

## Supported Captcha Types

- ✅ reCAPTCHA v2
- ✅ hCaptcha
- ✅ Cloudflare Turnstile

## Quick Setup

### Step 1: Choose a Captcha Service

We recommend **2Captcha** for its reliability and pricing:

1. Sign up at https://2captcha.com
2. Add funds to your account (rates start at $0.50-3.00 per 1000 captchas)
3. Get your API key from the dashboard

### Step 2: Find the Site Key

To find Z.AI's captcha site key:

**Method 1: Browser DevTools**
1. Open https://chat.z.ai in your browser
2. Open DevTools (F12)
3. Go to the **Network** tab
4. Try to login
5. Look for captcha-related requests
6. Find the `sitekey` or `site_key` parameter

**Method 2: Page Source**
1. Open https://chat.z.ai
2. View page source (Ctrl+U)
3. Search for "sitekey" or "data-sitekey"

### Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
# Email and Password (required)
ZAI_EMAIL=your-email@example.com
ZAI_PASSWORD=your-password

# Captcha Service Configuration
CAPTCHA_SERVICE=2captcha              # Options: 2captcha, anticaptcha, capsolver
CAPTCHA_API_KEY=your-2captcha-api-key # Get from 2captcha.com dashboard
CAPTCHA_SITE_KEY=z.ai-site-key        # Found in browser DevTools
```

### Step 4: Test the Setup

```bash
# Set environment variables
export ZAI_EMAIL="your-email@example.com"
export ZAI_PASSWORD="your-password"
export CAPTCHA_API_KEY="your-2captcha-api-key"
export CAPTCHA_SITE_KEY="z.ai-site-key"

# Start the server
bash scripts/start.sh

# Test with an API call
bash scripts/send_request.sh
```

## How It Works

1. **Automatic Detection**: When you configure both `CAPTCHA_API_KEY` and `CAPTCHA_SITE_KEY`, the system automatically uses captcha solving
2. **Multi-Type Support**: The system tries different captcha types automatically (reCAPTCHA → hCaptcha → Turnstile)
3. **Fallback**: If captcha solving fails, it attempts login without captcha
4. **Smart Retry**: The system handles captcha solving asynchronously with proper timeout handling

## Pricing

Typical costs per 1000 captchas solved:

| Service | reCAPTCHA v2 | hCaptcha | Turnstile |
|---------|--------------|----------|-----------|
| 2Captcha | $0.50-1.00 | $0.50-1.00 | $2.00-3.00 |
| AntiCaptcha | $0.50-1.00 | $0.50-1.00 | N/A |
| CapSolver | $0.60-1.00 | $0.60-1.00 | $0.80-1.20 |

## Alternative: Manual Token Method

If you don't want to use paid captcha services, you can manually extract tokens:

1. Login to https://chat.z.ai in your browser
2. Open DevTools → Application → Cookies
3. Copy the `token` cookie value
4. Set `AUTH_TOKEN=your-token` in `.env`
5. Leave `CAPTCHA_API_KEY` and `CAPTCHA_SITE_KEY` empty

The server will use the manual token instead of attempting captcha-based login.

## Troubleshooting

### "Captcha verification failed"
- Verify your `CAPTCHA_SITE_KEY` is correct
- Check your captcha service API key is valid and has funds
- Ensure you're using the right captcha type

### "API Key invalid"
- Verify your captcha service API key
- Check your account balance
- Ensure the API key has proper permissions

### Timeout errors
- Captcha solving typically takes 10-30 seconds
- The system has a 120-second timeout by default
- Check your network connection
- Verify the captcha service is not experiencing downtime

## Environment Variables Reference

```bash
# Required for email/password login
ZAI_EMAIL=                    # Your Z.AI email
ZAI_PASSWORD=                 # Your Z.AI password

# Captcha Configuration (Optional - if not set, uses manual token)
CAPTCHA_SERVICE=2captcha      # Service to use: 2captcha, anticaptcha, capsolver
CAPTCHA_API_KEY=              # Your captcha service API key
CAPTCHA_SITE_KEY=             # Z.AI's captcha site key

# Alternative: Manual Token (if not using captcha solver)
AUTH_TOKEN=                   # Manually extracted token from browser
```

## Best Practices

1. **Cost Management**: Only enable captcha solving when necessary
2. **Token Reuse**: Extracted tokens are valid for extended periods
3. **Service Selection**: 2Captcha offers the best balance of price and reliability
4. **Monitoring**: Check your captcha service dashboard for usage and costs
5. **Fallback**: Always have a backup authentication method (manual token)

## Advanced Configuration

### Using Different Services for Different Captcha Types

The system automatically tries multiple captcha types. You can customize this in `app/providers/zai_provider.py` by modifying the captcha solving order.

### Custom Timeout

Default timeout is 120 seconds. Adjust in the captcha solver calls if needed:

```python
captcha_response = await captcha_solver.solve_recaptcha_v2(
    site_key=settings.CAPTCHA_SITE_KEY,
    page_url="https://chat.z.ai/",
    timeout=180  # Custom 3-minute timeout
)
```

## Security Notes

- **Never commit** your `.env` file or API keys to git
- Store captcha API keys securely
- Rotate keys periodically
- Monitor usage to detect anomalies
- Consider using environment-specific keys for dev/prod

## Support

For issues with:
- **This implementation**: Open an issue in this repository
- **2Captcha service**: https://2captcha.com/support
- **AntiCaptcha service**: https://anti-captcha.com/support
- **CapSolver service**: https://capsolver.com/support

