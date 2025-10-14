#!/bin/bash
set -e

echo "========================================"
echo "🔧 Z.AI2API Setup Script"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in project root
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Must run from project root${NC}"
    exit 1
fi

echo "📦 Step 1: Installing dependencies..."
if [ ! -d ".venv" ]; then
    echo "   Creating virtual environment..."
    uv venv
fi

echo "   Installing packages with uv..."
uv pip install -e .

echo ""
echo "🔐 Step 2: Setting up authentication..."

# Check if we have email/password for automatic login
if [ -n "$ZAI_EMAIL" ] && [ -n "$ZAI_PASSWORD" ]; then
    echo -e "${GREEN}✅ Email/Password detected: $ZAI_EMAIL${NC}"
    
    # Check if captcha is configured
    if [ -n "$CAPTCHA_API_KEY" ] && [ -n "$CAPTCHA_SITE_KEY" ]; then
        echo -e "${GREEN}✅ Captcha solver configured${NC}"
        echo "   Service: ${CAPTCHA_SERVICE:-2captcha}"
        echo "   Will automatically solve captchas during login"
    else
        echo -e "${YELLOW}⚠️  No captcha solver configured${NC}"
        echo "   Login may fail if Z.AI requires captcha"
        echo "   See CAPTCHA_SETUP.md for setup instructions"
    fi
    
    # Attempt to get token automatically
    echo ""
    echo "🎟️  Attempting automatic token retrieval..."
    
    # Create a simple Python script to get token
    .venv/bin/python << 'ENDPYTHON'
import sys
import os
import asyncio

# Add project to path
sys.path.insert(0, os.getcwd())

async def get_token():
    try:
        from app.providers.zai_provider import ZAIProvider
        from app.core.config import settings
        
        provider = ZAIProvider()
        token = await provider.get_token()
        
        if token:
            print(f"✅ Token retrieved successfully!")
            print(f"   Token: {token[:30]}...")
            
            # Save to .env
            env_file = ".env"
            lines = []
            token_found = False
            
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('AUTH_TOKEN='):
                            lines.append(f'AUTH_TOKEN={token}\n')
                            token_found = True
                        else:
                            lines.append(line)
            
            if not token_found:
                lines.append(f'\nAUTH_TOKEN={token}\n')
            
            with open(env_file, 'w') as f:
                f.writelines(lines)
            
            print(f"✅ Token saved to .env file")
            return True
        else:
            print("❌ Failed to retrieve token")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run async function
success = asyncio.run(get_token())
sys.exit(0 if success else 1)
ENDPYTHON
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Token retrieval successful!${NC}"
    else
        echo -e "${YELLOW}⚠️  Automatic token retrieval failed${NC}"
        echo "   Will use environment variables or guest mode"
    fi
    
elif [ -n "$AUTH_TOKEN" ]; then
    echo -e "${GREEN}✅ Manual AUTH_TOKEN detected${NC}"
    echo "   Token: ${AUTH_TOKEN:0:30}..."
    
elif [ "$ANONYMOUS_MODE" = "true" ]; then
    echo -e "${BLUE}ℹ️  Anonymous mode enabled${NC}"
    echo "   Will use guest tokens (limited features)"
    
else
    echo -e "${RED}❌ No authentication configured!${NC}"
    echo ""
    echo "Please set one of:"
    echo "  1. ZAI_EMAIL + ZAI_PASSWORD (+ optional CAPTCHA_* for auto-login)"
    echo "  2. AUTH_TOKEN (manual token from browser)"
    echo "  3. ANONYMOUS_MODE=true (guest mode, limited)"
    echo ""
    echo "See QUICK_START.md for instructions"
    exit 1
fi

echo ""
echo "📝 Step 3: Checking configuration..."
PORT=${PORT:-8080}
HOST=${HOST:-0.0.0.0}

echo "   Server will run on: http://${HOST}:${PORT}"
echo "   Debug mode: ${DEBUG:-false}"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📄 Creating .env file..."
    cat > .env << EOF
# Server Configuration
PORT=${PORT}
HOST=${HOST}
DEBUG=${DEBUG:-false}

# Authentication (set one of these)
ZAI_EMAIL=${ZAI_EMAIL:-}
ZAI_PASSWORD=${ZAI_PASSWORD:-}
AUTH_TOKEN=${AUTH_TOKEN:-}
ANONYMOUS_MODE=${ANONYMOUS_MODE:-false}

# Captcha Configuration (optional for auto-login)
CAPTCHA_SERVICE=${CAPTCHA_SERVICE:-2captcha}
CAPTCHA_API_KEY=${CAPTCHA_API_KEY:-}
CAPTCHA_SITE_KEY=${CAPTCHA_SITE_KEY:-}

# Security
SKIP_AUTH_TOKEN=true

# Model Settings
DEFAULT_MODEL=GLM-4.5
EOF
    echo -e "${GREEN}✅ Created .env file${NC}"
fi

echo ""
echo -e "${GREEN}========================================"
echo "✅ Setup Complete!"
echo "========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Start server: bash scripts/start.sh"
echo "  2. Test API: bash scripts/send_request.sh"
echo "  Or run everything: bash scripts/all.sh"
echo ""

