#!/usr/bin/env bash
# setup.sh - Full setup of the program (dependencies + configuration)

set -e

echo "🚀 Starting Z.AI2API Setup..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}📦 Installing uv package manager...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    
    # Verify installation
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}❌ Failed to install uv. Please install manually: https://github.com/astral-sh/uv${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ uv installed successfully${NC}"
else
    echo -e "${GREEN}✅ uv is already installed${NC}"
fi

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies with Python 3.11...${NC}"
uv sync --python /usr/bin/python3.11
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env configuration file...${NC}"
    cat > .env << 'EOF'
# Z.AI2API Configuration

# ========== API Authentication ==========
# Your custom API key for clients to access this service
AUTH_TOKEN=sk-z-ai2api-local-test-key
SKIP_AUTH_TOKEN=false

# ========== Z.AI Token Pool Configuration ==========
TOKEN_FAILURE_THRESHOLD=3
TOKEN_RECOVERY_TIMEOUT=1800

# Z.AI Anonymous Mode
# true: Automatically get temporary tokens from Z.AI
# false: Use authenticated tokens from database
ANONYMOUS_MODE=true

# ========== Server Configuration ==========
LISTEN_PORT=8080
SERVICE_NAME=z-ai2api-server
DEBUG_LOGGING=true

# ========== Feature Flags ==========
TOOL_SUPPORT=true
SCAN_LIMIT=200000
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Initialize database (will auto-create on first run)
echo -e "${GREEN}✅ Setup complete! Database will initialize on first server start.${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Start server: ${GREEN}bash scripts/start.sh${NC}"
echo -e "  2. Or run everything: ${GREEN}bash scripts/all.sh${NC}"
echo ""
