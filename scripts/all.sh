#!/usr/bin/env bash
# all.sh - Complete workflow: setup, start server, and test

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Z.AI2API Complete Setup & Test Workflow        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Step 1: Setup
echo -e "${BLUE}════════ Step 1: Setup ════════${NC}"
bash "$SCRIPT_DIR/setup.sh"
echo ""

# Step 2: Start server in background
echo -e "${BLUE}════════ Step 2: Starting Server ════════${NC}"
echo -e "${YELLOW}Starting server in background...${NC}"

# Create log file
LOG_FILE="$PROJECT_DIR/server.log"
> "$LOG_FILE"  # Clear log file

# Start server in background, redirecting output to log file (clear PYTHONPATH to avoid conflicts)
PYTHONPATH="" .venv/bin/python main.py > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

echo -e "${GREEN}✅ Server started with PID: $SERVER_PID${NC}"
echo -e "${YELLOW}📝 Server logs: $LOG_FILE${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping server (PID: $SERVER_PID)...${NC}"
        kill $SERVER_PID 2>/dev/null || true
        sleep 2
        # Force kill if still running
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            kill -9 $SERVER_PID 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ Server stopped${NC}"
    fi
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Wait a bit for server initialization
echo -e "${YELLOW}⏳ Waiting for server initialization...${NC}"
sleep 3

# Step 3: Run tests
echo -e "${BLUE}════════ Step 3: Running Tests ════════${NC}"
echo ""

bash "$SCRIPT_DIR/send_request.sh"

# Show some server logs
echo ""
echo -e "${BLUE}════════ Server Logs (last 20 lines) ════════${NC}"
tail -n 20 "$LOG_FILE"
echo ""

echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🎉 Complete workflow finished! 🎉           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Note: The server will be stopped automatically.${NC}"
echo -e "${YELLOW}To keep it running, use: bash scripts/start.sh${NC}"
echo ""
