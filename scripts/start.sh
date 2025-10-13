#!/usr/bin/env bash
# start.sh - Start an already-setup server

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Starting Z.AI2API Server..."

# Verify setup
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found. Run setup first:${NC}"
    echo -e "   ${YELLOW}bash scripts/setup.sh${NC}"
    exit 1
fi

if [ ! -d .venv ] && [ ! -f uv.lock ]; then
    echo -e "${RED}❌ Error: Dependencies not installed. Run setup first:${NC}"
    echo -e "   ${YELLOW}bash scripts/setup.sh${NC}"
    exit 1
fi

# Load environment variables
export PATH="$HOME/.local/bin:$PATH"

# Start the server
echo -e "${GREEN}🌐 Starting server on http://localhost:8080${NC}"
echo -e "${YELLOW}📊 Admin panel: http://localhost:8080/admin${NC}"
echo -e "${YELLOW}📖 API docs: http://localhost:8080/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run with venv python directly (clear PYTHONPATH to avoid conflicts)
PYTHONPATH="" .venv/bin/python main.py
