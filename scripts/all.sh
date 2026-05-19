#!/usr/bin/env bash
# all.sh - Run complete deployment, start server, and test

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Z.AI to OpenAI API Proxy - Full Setup             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Trap errors
trap 'echo -e "${RED}❌ Setup failed at step: $CURRENT_STEP${NC}"; exit 1' ERR

# Check if we're in the correct directory
if [[ ! -f "main.py" ]]; then
    echo -e "${RED}❌ Error: main.py not found. Please run from project root.${NC}"
    exit 1
fi

# Display environment
echo -e "${YELLOW}📋 Environment:${NC}"
echo "   PWD: $(pwd)"
echo "   Python: $(command -v python3 || echo 'not found')"
echo "   uv: $(command -v uv || echo 'not found')"

if [[ -n "$ZAI_EMAIL" ]]; then
    echo "   ZAI_EMAIL: $ZAI_EMAIL"
else
    echo "   ZAI_EMAIL: (not set - will use anonymous mode)"
fi

if [[ -n "$ZAI_PASSWORD" ]]; then
    echo "   ZAI_PASSWORD: ***"
else
    echo "   ZAI_PASSWORD: (not set - will use anonymous mode)"
fi

echo "   SERVER_PORT: ${SERVER_PORT:-7300 (default)}"
echo ""

# Step 1: Deploy
CURRENT_STEP="deploy"
echo -e "${GREEN}━━━ Step 1/3: Deployment ━━━${NC}"
bash scripts/deploy.sh
echo ""

# Step 2: Start server
CURRENT_STEP="start server"
echo -e "${GREEN}━━━ Step 2/3: Starting Server ━━━${NC}"
bash scripts/start.sh
echo ""

# Give server extra time to stabilize
sleep 2

# Step 3: Test API
CURRENT_STEP="test API"
echo -e "${GREEN}━━━ Step 3/3: Testing API ━━━${NC}"
bash scripts/send_openai_request.sh
echo ""

# Success!
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  ✅ Setup Complete!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Server Information:${NC}"

if [[ -f "server.port" ]]; then
    PORT=$(cat server.port)
    echo "   URL: http://localhost:$PORT"
    echo "   API: http://localhost:$PORT/v1"
fi

if [[ -f "server.pid" ]]; then
    PID=$(cat server.pid)
    echo "   PID: $PID"
fi

echo ""
echo -e "${YELLOW}💡 Useful Commands:${NC}"
echo "   View logs:  tail -f server.log"
echo "   Stop server: kill \$(cat server.pid)"
echo "   Restart:     bash scripts/start.sh"
echo "   Test API:    bash scripts/send_openai_request.sh"
echo ""
echo -e "${GREEN}🎉 Your OpenAI-compatible API proxy is ready!${NC}"

