#!/bin/bash
#
# all.sh - Complete Z.AI2API Setup, Start, and Test Script
#
# This script orchestrates the complete workflow with REAL API calls:
# 
# 1. Run setup.sh
#    ✅ Install dependencies
#    ✅ Use Playwright to login and retrieve AUTH_TOKEN
#    ✅ Save token to .env file
#
# 2. Run start.sh
#    ✅ Start server using the retrieved AUTH_TOKEN
#    ✅ Server proxies to real Z.AI chat interface
#
# 3. Run send_openai_request.sh
#    ✅ Send REAL OpenAI API request: "What is Graph-RAG?"
#    ✅ Display actual AI-generated response from Z.AI
#
# Usage:
#   export ZAI_EMAIL=your-email@example.com
#   export ZAI_PASSWORD=your-password
#   bash scripts/all.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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

log_step() {
    echo -e "${MAGENTA}$1${NC}"
}

# Error handler
cleanup_on_error() {
    echo ""
    log_error "An error occurred during execution"
    
    # Stop server if it was started
    if [ -f "$PROJECT_ROOT/.server.pid" ]; then
        PID=$(cat "$PROJECT_ROOT/.server.pid")
        if kill -0 $PID 2>/dev/null; then
            log_info "Stopping server (PID: $PID)..."
            kill $PID 2>/dev/null || true
            rm -f "$PROJECT_ROOT/.server.pid"
        fi
    fi
    
    echo ""
    log_warning "Please check the error messages above and try again"
    exit 1
}

trap cleanup_on_error ERR

# Banner
clear
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║         Z.AI2API Python - Complete Setup & Test           ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Pre-flight checks
log_info "Performing pre-flight checks..."

# Check if required environment variables are set
if [ -z "$ZAI_EMAIL" ] || [ -z "$ZAI_PASSWORD" ]; then
    log_error "Required environment variables not set"
    echo ""
    echo "Please export the following environment variables:"
    echo ""
    echo "  export ZAI_EMAIL=your-email@example.com"
    echo "  export ZAI_PASSWORD=your-password"
    echo ""
    echo "Then run:"
    echo "  bash scripts/all.sh"
    echo ""
    exit 1
fi

log_success "Environment variables verified"
log_info "Email: $ZAI_EMAIL"
echo ""

# Confirm with user
echo "This script will:"
echo "  1️⃣  Install dependencies and retrieve authentication token"
echo "  2️⃣  Start the API server using the retrieved token"
echo "  3️⃣  Send REAL API request: 'What is Graph-RAG?'"
echo "  4️⃣  Display actual AI response from Z.AI"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Aborted by user"
    exit 0
fi

echo ""
echo "============================================================"
log_step "STEP 1/3: Running setup.sh"
echo "============================================================"
echo ""

# Execute setup script
bash "$SCRIPT_DIR/setup.sh"

if [ $? -ne 0 ]; then
    log_error "Setup failed"
    exit 1
fi

echo ""
echo "============================================================"
log_step "STEP 2/3: Running start.sh"
echo "============================================================"
echo ""

# Execute start script
# Note: We need to handle this specially since start.sh might tail logs
# We'll start it in a way that returns control to us

# Kill any tail processes from previous runs
pkill -f "tail -f logs/server.log" 2>/dev/null || true

# Start server without tailing logs
bash "$SCRIPT_DIR/start.sh" > /tmp/start_output.log 2>&1 &
START_PID=$!

# Wait for startup to complete
sleep 5

# Check if start script succeeded
if ! wait $START_PID 2>/dev/null; then
    # Check if server is actually running
    if [ -f "$PROJECT_ROOT/.server.pid" ]; then
        SERVER_PID=$(cat "$PROJECT_ROOT/.server.pid")
        if kill -0 $SERVER_PID 2>/dev/null; then
            log_success "Server started successfully (PID: $SERVER_PID)"
        else
            log_error "Server failed to start"
            cat /tmp/start_output.log
            exit 1
        fi
    else
        log_error "Server startup failed"
        cat /tmp/start_output.log
        exit 1
    fi
fi

# Additional health check
log_info "Verifying server health..."
MAX_RETRIES=10
RETRY=0
PORT=${LISTEN_PORT:-8080}

while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s -f "http://localhost:$PORT/" > /dev/null 2>&1; then
        log_success "Server is healthy and responding"
        break
    fi
    RETRY=$((RETRY + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    log_error "Server health check failed"
    exit 1
fi

echo ""
sleep 2  # Give server a moment to fully initialize

echo ""
echo "============================================================"
log_step "STEP 3/3: Running send_openai_request.sh"
echo "============================================================"
echo ""

# Execute test request script
bash "$SCRIPT_DIR/send_openai_request.sh"

if [ $? -ne 0 ]; then
    log_error "API test failed"
    exit 1
fi

# Final success message
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║           🎉 All Steps Completed Successfully! 🎉          ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✨ Your Z.AI2API server is now running and verified! ✨${NC}"
echo ""
echo "📊 Server Status:"
if [ -f "$PROJECT_ROOT/.server.pid" ]; then
    SERVER_PID=$(cat "$PROJECT_ROOT/.server.pid")
    echo "  Status:     Running"
    echo "  PID:        $SERVER_PID"
else
    echo "  Status:     Unknown (PID file not found)"
fi
echo "  Port:       ${PORT:-8080}"
echo "  Log:        logs/server.log"
echo ""
echo "🌐 Access Points:"
echo "  API Root:   http://localhost:${PORT:-8080}/"
echo "  API Docs:   http://localhost:${PORT:-8080}/docs"
echo "  Admin:      http://localhost:${PORT:-8080}/admin"
echo ""
echo "📝 Useful Commands:"
echo "  View logs:          tail -f logs/server.log"
echo "  Test API again:     bash scripts/send_openai_request.sh"
if [ -f "$PROJECT_ROOT/.server.pid" ]; then
    echo "  Stop server:        kill $(cat $PROJECT_ROOT/.server.pid)"
fi
echo "  Restart server:     bash scripts/start.sh"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Server will continue running in the background            ║"
echo "║  Press Ctrl+C to exit (server will keep running)          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Display live logs
log_info "Displaying server logs (press Ctrl+C to exit)..."
echo ""
sleep 1

# Tail logs
if [ -f "$PROJECT_ROOT/logs/server.log" ]; then
    tail -f "$PROJECT_ROOT/logs/server.log"
else
    log_warning "Log file not found: logs/server.log"
fi
