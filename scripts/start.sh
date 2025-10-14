#!/bin/bash
set -e

echo "🚀 Starting Z.AI2API Server..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if in project root
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Must run from project root${NC}"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Set defaults
LISTEN_PORT=${LISTEN_PORT:-8080}
HOST=${HOST:-0.0.0.0}
WORKERS=${WORKERS:-1}

echo "📋 Configuration:"
echo "   Host: $HOST"
echo "   Port: $LISTEN_PORT"
echo "   Workers: $WORKERS"
echo ""

# Check if port is in use
if lsof -Pi :$LISTEN_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $LISTEN_PORT is already in use${NC}"
    read -p "Kill existing process? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Killing existing process..."
        lsof -ti:$LISTEN_PORT | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo "Exiting..."
        exit 1
    fi
fi

echo "🔄 Starting server with granian..."
echo ""

# Start server
exec .venv/bin/python main.py

