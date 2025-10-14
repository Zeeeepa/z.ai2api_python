#!/bin/bash
#
# start.sh - Z.AI2API Server Startup Script
#
# This script starts the Z.AI2API server using the AUTH_TOKEN from .env
# The token was retrieved via Playwright automation in setup.sh
#
# The server will:
#  ✅ Load AUTH_TOKEN from .env file
#  ✅ Use it to authenticate with Z.AI's chat interface
#  ✅ Proxy all OpenAI API requests to real Z.AI service
#  ✅ Return actual AI-generated responses
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/.server.pid"

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Banner
echo ""
echo "============================================================"
echo "         Z.AI2API Python - Server Startup"
echo "============================================================"
echo ""

# Navigate to project root
cd "$PROJECT_ROOT"

# Step 1: Check if .env file exists
log_info "Checking configuration..."
if [ ! -f ".env" ]; then
    log_error ".env file not found"
    log_info "Please run: bash scripts/setup.sh"
    exit 1
fi
log_success "Configuration file found"

# Load environment variables
set -a
source .env
set +a

# Verify AUTH_TOKEN is loaded
if [ -n "$AUTH_TOKEN" ]; then
    TOKEN_PREVIEW="${AUTH_TOKEN:0:10}..."
    log_success "AUTH_TOKEN loaded: $TOKEN_PREVIEW"
else
    log_warning "AUTH_TOKEN not found in .env"
fi

# Get port from .env or use default
PORT=${LISTEN_PORT:-8080}

# Step 2: Check if port is available
log_info "Checking if port $PORT is available..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    PID=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
    log_warning "Port $PORT is already in use by PID $PID"
    
    # Check if it's our server
    if [ -f "$PID_FILE" ] && [ "$(cat $PID_FILE)" == "$PID" ]; then
        log_info "Server is already running (PID: $PID)"
        log_success "Server is healthy at http://localhost:$PORT"
        exit 0
    else
        log_error "Another process is using port $PORT"
        log_info "Please stop the process or change LISTEN_PORT in .env"
        exit 1
    fi
fi
log_success "Port $PORT is available"

# Step 3: Check Python dependencies
log_info "Checking dependencies..."
if ! python3 -c "import fastapi, granian, httpx" 2>/dev/null; then
    log_error "Required dependencies not found"
    log_info "Please run: bash scripts/setup.sh"
    exit 1
fi
log_success "Dependencies verified"

# Step 4: Start the server
log_info "Starting server..."
echo ""
echo "============================================================"
echo "                  Server Starting..."
echo "============================================================"
echo ""

# Determine which Python command to use
if command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
    log_info "Using uv runtime"
else
    PYTHON_CMD="python3"
    log_info "Using system Python"
fi

# Start server in background
nohup $PYTHON_CMD main.py > logs/server.log 2>&1 &
SERVER_PID=$!

# Save PID to file
echo $SERVER_PID > "$PID_FILE"
log_success "Server started with PID: $SERVER_PID"

# Step 5: Wait for server to be ready
log_info "Waiting for server to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -f "http://localhost:$PORT/" > /dev/null 2>&1; then
        log_success "Server is ready!"
        break
    fi
    
    # Check if process is still running
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        log_error "Server process died unexpectedly"
        log_info "Check logs/server.log for details"
        rm -f "$PID_FILE"
        exit 1
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep 1
done

echo ""

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    log_error "Server failed to start within ${MAX_ATTEMPTS} seconds"
    log_info "Check logs/server.log for details"
    kill $SERVER_PID 2>/dev/null || true
    rm -f "$PID_FILE"
    exit 1
fi

# Step 6: Display server information
echo ""
echo "============================================================"
echo "             Server Started Successfully! 🚀"
echo "============================================================"
echo ""
echo "📊 Server Information:"
echo "  PID:        $SERVER_PID"
echo "  Port:       $PORT"
echo "  Log file:   logs/server.log"
echo "  PID file:   $PID_FILE"
echo ""
echo "🌐 Endpoints:"
echo "  API Root:   http://localhost:$PORT/"
echo "  API Docs:   http://localhost:$PORT/docs"
echo "  Admin:      http://localhost:$PORT/admin"
echo ""
echo "📝 Commands:"
echo "  View logs:  tail -f logs/server.log"
echo "  Stop:       kill $SERVER_PID  (or: kill \$(cat $PID_FILE))"
echo "  Test API:   bash scripts/send_openai_request.sh"
echo ""
echo "============================================================"
echo ""

# Keep script running to show initial logs
log_info "Showing initial logs (press Ctrl+C to exit, server will keep running):"
echo ""
tail -f logs/server.log &
TAIL_PID=$!

# Trap Ctrl+C to stop tail but keep server running
trap "kill $TAIL_PID 2>/dev/null; echo ''; log_success 'Server is running in background'; exit 0" INT

# Wait for tail to finish (won't happen unless killed)
wait $TAIL_PID
