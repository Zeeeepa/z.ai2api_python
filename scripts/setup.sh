#!/usr/bin/env bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================="
echo "🔧 Z.AI2API Setup Script"
echo -e "==================================${NC}\n"

# Check Python version
echo -e "${BLUE}📦 Step 1: Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}\n"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo -e "${BLUE}📥 Installing uv package manager...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install dependencies
echo -e "${BLUE}📦 Step 2: Installing dependencies...${NC}"
echo "   Installing packages with uv..."
uv pip install --system -e . || {
    echo -e "${YELLOW}⚠️  System install failed, trying venv...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    uv pip install -e .
}

# Install Playwright for browser automation
echo -e "\n${BLUE}🌐 Step 3: Installing Playwright...${NC}"
if [ -f ".venv/bin/python" ]; then
    .venv/bin/pip install playwright
    .venv/bin/playwright install chromium
else
    python3 -m pip install --user playwright
    python3 -m playwright install chromium
fi

echo -e "${GREEN}✅ Playwright installed${NC}\n"

# Setup authentication
echo -e "${BLUE}🔐 Step 4: Setting up authentication...${NC}"

# Check for email/password
if [ -n "$ZAI_EMAIL" ] && [ -n "$ZAI_PASSWORD" ]; then
    echo -e "${GREEN}✅ Email/Password detected: ${ZAI_EMAIL}${NC}"
    
    echo -e "\n${BLUE}🎭 Initializing authentication tokens...${NC}"
    
    # Try browser-based login first
    echo -e "\n${BLUE}🌐 Attempting browser-based login...${NC}"
    if [ -f ".venv/bin/python" ]; then
        .venv/bin/python scripts/browser_login.py || {
            echo -e "${YELLOW}⚠️  Browser login failed, will try direct API${NC}"
        }
    else
        python3 scripts/browser_login.py || {
            echo -e "${YELLOW}⚠️  Browser login failed, will try direct API${NC}"
        }
    fi
    
elif [ -n "$AUTH_TOKEN" ]; then
    echo -e "${GREEN}✅ Manual token detected${NC}"
    echo "$AUTH_TOKEN" > .zai_token
else
    echo -e "${YELLOW}⚠️  No credentials found${NC}"
    echo -e "${YELLOW}   Please set either:${NC}"
    echo -e "${YELLOW}   - ZAI_EMAIL + ZAI_PASSWORD (for browser login)${NC}"
    echo -e "${YELLOW}   - AUTH_TOKEN (manual token)${NC}"
fi

# Create .env file
echo -e "\n${BLUE}📝 Step 5: Configuration...${NC}"
cat > .env << EOF
# Server Configuration
LISTEN_PORT=${LISTEN_PORT:-8080}
DEBUG=${DEBUG:-false}

# Authentication  
ZAI_EMAIL=${ZAI_EMAIL:-}
ZAI_PASSWORD=${ZAI_PASSWORD:-}
AUTH_TOKEN=${AUTH_TOKEN:-}

# Feature Flags
ANONYMOUS_MODE=${ANONYMOUS_MODE:-false}
SKIP_AUTH_TOKEN=true
EOF

echo -e "${GREEN}   Server will run on: http://0.0.0.0:${LISTEN_PORT:-8080}${NC}"
echo -e "${GREEN}   Debug mode: ${DEBUG:-false}${NC}"

echo -e "\n${GREEN}========================================"
echo "✅ Setup Complete!"
echo -e "========================================\\033[0m\n"

echo "Next steps:"
echo "  1. Start server: bash scripts/start.sh"
echo "  2. Test API: bash scripts/send_request.sh"
echo "  Or run everything: bash scripts/all.sh"

