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
NC='\033[0m'

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
    
    # Initialize tokens
    echo ""
    echo "🎟️  Initializing authentication tokens..."
    echo ""
    
    # Try browser automation if available
    if .venv/bin/python -c "import playwright" 2>/dev/null; then
        echo "🌐 Attempting browser-based login..."
        .venv/bin/python scripts/browser_login.py
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Browser login successful!${NC}"
        else
            echo -e "${YELLOW}⚠️  Browser login failed, trying API...${NC}"
            .venv/bin/python scripts/init_tokens.py
        fi
    else
        echo "📡 Using direct API login..."
        .venv/bin/python scripts/init_tokens.py
        
        if [ $? -ne 0 ]; then
            echo ""
            echo -e "${YELLOW}💡 TIP: Install Playwright for browser automation:${NC}"
            echo "   .venv/bin/pip install playwright"
            echo "   .venv/bin/playwright install chromium"
        fi
    fi
    
elif [ -n "$AUTH_TOKEN" ]; then
    echo -e "${GREEN}✅ Manual AUTH_TOKEN detected${NC}"
    echo "   Token: ${AUTH_TOKEN:0:30}..."
    
    # Store token in database
    echo ""
    echo "💾 Storing token in database..."
    .venv/bin/python << 'ENDPYTHON'
import asyncio
import os
import sys
sys.path.insert(0, os.getcwd())

async def store():
    from app.services.token_dao import TokenDAO
    dao = TokenDAO()
    await dao.init_database()
    token_id = await dao.add_token(
        provider="zai",
        token=os.environ['AUTH_TOKEN'],
        token_type="user",
        priority=10,
        validate=False
    )
    if token_id:
        print(f"✅ Token stored! ID: {token_id}")
    else:
        print("❌ Failed to store token")

asyncio.run(store())
ENDPYTHON
    
elif [ "$ANONYMOUS_MODE" = "true" ]; then
    echo -e "${BLUE}ℹ️  Anonymous mode enabled${NC}"
    echo "   Will use guest tokens (limited features)"
    
else
    echo -e "${RED}❌ No authentication configured!${NC}"
    echo ""
    echo "Please set one of:"
    echo "  1. ZAI_EMAIL + ZAI_PASSWORD (for auto-login)"
    echo "  2. AUTH_TOKEN (manual token)"
    echo "  3. ANONYMOUS_MODE=true (guest mode)"
    echo ""
    echo "📖 See QUICK_TOKEN_SETUP.md for instructions"
    exit 1
fi

echo ""
echo "📝 Step 3: Configuration..."
LISTEN_PORT=${LISTEN_PORT:-8080}
HOST=${HOST:-0.0.0.0}

echo "   Server will run on: http://${HOST}:${LISTEN_PORT}"
echo "   Debug mode: ${DEBUG:-false}"

# Create .env if needed
if [ ! -f ".env" ]; then
    echo ""
    echo "📄 Creating .env file..."
    cat > .env << EOF
# Server Configuration
LISTEN_PORT=${LISTEN_PORT}
HOST=${HOST}
DEBUG=${DEBUG:-false}

# Authentication
ZAI_EMAIL=${ZAI_EMAIL:-}
ZAI_PASSWORD=${ZAI_PASSWORD:-}
AUTH_TOKEN=${AUTH_TOKEN:-}
ANONYMOUS_MODE=${ANONYMOUS_MODE:-false}

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

