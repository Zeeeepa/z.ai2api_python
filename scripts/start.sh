#!/usr/bin/env bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load environment
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

PORT=${LISTEN_PORT:-8080}
LOG_FILE=${LOG_FILE:-/tmp/z.ai2api_server.log}

echo -e "${BLUE}=================================="
echo "🚀 Starting Z.AI2API Server"
echo -e "==================================${NC}\n"

# Check if port is in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"
    PID=$(lsof -ti:$PORT)
    echo -e "${YELLOW}   Killing existing process (PID: $PID)${NC}"
    kill -9 $PID 2>/dev/null || true
    sleep 2
fi

# Find Python
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
else
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
fi

echo -e "${BLUE}🔧 Configuration:${NC}"
echo -e "   Port: ${PORT}"
echo -e "   Workers: 1"
echo -e ""

# Start server
echo -e "${BLUE}🔄 Starting server with granian...${NC}\n"

# Run server in background
nohup $PYTHON main.py > $LOG_FILE 2>&1 &
SERVER_PID=$!

echo -e "${GREEN}✅ Server started (PID: $SERVER_PID)${NC}"
echo -e "${GREEN}   Log file: $LOG_FILE${NC}\n"

# Wait for server to be ready
echo -e "${BLUE}⏳ Waiting for server to be ready...${NC}"
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:$PORT/v1/models >/dev/null 2>&1; then
        echo -e "\n${GREEN}✅ Server is ready!${NC}\n"
        echo -e "${GREEN}=================================="
        echo "Server running on:"
        echo -e "  http://0.0.0.0:$PORT"
        echo -e "==================================${NC}\n"
        
        echo "Test endpoints:"
        echo "  curl http://localhost:$PORT/v1/models"
        echo "  bash scripts/send_request.sh"
        echo ""
        echo "View logs:"
        echo "  tail -f $LOG_FILE"
        echo ""
        exit 0
    fi
    sleep 1
    WAITED=$((WAITED + 1))
    echo -n "."
done

echo -e "\n${RED}❌ Server failed to start within $MAX_WAIT seconds${NC}\n"
echo "Last 20 lines of server log:"
tail -20 $LOG_FILE

exit 1

