#!/bin/bash
set -e

echo "╔════════════════════════════════════════╗"
echo "║   Z.AI2API - Complete Workflow         ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "This script will:"
echo "  1. Setup environment and retrieve token"
echo "  2. Start the API server"
echo "  3. Run comprehensive tests"
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

# Step 1: Setup
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 STEP 1/3: Setup & Authentication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash scripts/setup.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Setup failed${NC}"
    exit 1
fi

echo ""
read -p "Press Enter to continue to server startup..." -t 5 || true
echo ""

# Step 2: Start Server
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 STEP 2/3: Starting Server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Kill any existing server
PORT=${PORT:-8080}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Cleaning up existing server on port $PORT..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start server in background
echo "Starting server in background..."
bash scripts/start.sh > /tmp/z.ai2api_server.log 2>&1 &
SERVER_PID=$!

echo "Server PID: $SERVER_PID"
echo "Waiting for server to be ready..."

# Wait for server to be ready (max 30 seconds)
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:$PORT/v1/models > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
    WAITED=$((WAITED + 1))
done

echo ""

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "${RED}❌ Server failed to start within ${MAX_WAIT} seconds${NC}"
    echo ""
    echo "Last 20 lines of server log:"
    tail -20 /tmp/z.ai2api_server.log
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo ""
read -p "Press Enter to continue to API tests..." -t 5 || true
echo ""

# Step 3: Test API
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 STEP 3/3: Testing API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash scripts/send_request.sh

TEST_RESULT=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Complete Workflow Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ✅ Setup: Complete"
echo "  ✅ Server: Running (PID: $SERVER_PID)"
if [ $TEST_RESULT -eq 0 ]; then
    echo "  ✅ Tests: Passed"
else
    echo "  ⚠️  Tests: Some failures"
fi
echo ""
echo "Server Details:"
echo "  URL: http://localhost:$PORT"
echo "  Log: /tmp/z.ai2api_server.log"
echo "  PID: $SERVER_PID"
echo ""

# Ask if user wants to keep server running
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Keep server running? (Y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Stopping server..."
    kill $SERVER_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Server stopped${NC}"
else
    echo -e "${GREEN}✅ Server is still running${NC}"
    echo ""
    echo "To stop the server later:"
    echo "  kill $SERVER_PID"
    echo "  OR: lsof -ti:$PORT | xargs kill"
    echo ""
    echo "To view logs:"
    echo "  tail -f /tmp/z.ai2api_server.log"
    echo ""
    echo "To test again:"
    echo "  bash scripts/send_request.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 All done!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

