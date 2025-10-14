#!/bin/bash
set -e

echo "========================================"
echo "🚀 Starting Z.AI2API Server"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Must run from project root${NC}"
    exit 1
fi

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "   Running setup first..."
    bash scripts/setup.sh
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Handle different port variable names
if [ -n "$LISTEN_PORT" ] && [ -z "$PORT" ]; then
    PORT=$LISTEN_PORT
fi

# Set defaults
PORT=${PORT:-8080}
HOST=${HOST:-0.0.0.0}

# Export for the Python app
export PORT
export HOST

# Check if port is available
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"
    echo "   Killing existing process..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo "📋 Server Configuration:"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Debug: ${DEBUG:-false}"
echo ""

# Check authentication
echo "🔐 Authentication Status:"
if [ -n "$AUTH_TOKEN" ]; then
    echo -e "   ${GREEN}✅ Using AUTH_TOKEN${NC}"
elif [ -n "$ZAI_EMAIL" ] && [ -n "$ZAI_PASSWORD" ]; then
    echo -e "   ${GREEN}✅ Using Email/Password${NC}"
    if [ -n "$CAPTCHA_API_KEY" ]; then
        echo -e "   ${GREEN}✅ Captcha solver enabled${NC}"
    fi
elif [ "$ANONYMOUS_MODE" = "true" ]; then
    echo -e "   ${BLUE}ℹ️  Anonymous mode (guest tokens)${NC}"
else
    echo -e "   ${RED}❌ No authentication configured${NC}"
    echo "   Server may not work properly"
fi

echo ""
echo "🔥 Starting server..."
echo ""

# Start the server
if [ "$DEBUG" = "true" ]; then
    # Debug mode - show all output
    .venv/bin/python main.py
else
    # Production mode - clean output
    .venv/bin/python main.py 2>&1 | grep -v "INFO:" | grep -E "(Started|Listening|✅|❌|⚠️|🔐|🚀)" || true
fi
