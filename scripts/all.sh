#!/bin/bash
set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to create .env file  
create_env_file() {
    print_step "Creating .env configuration..."
    
    cat > .env <<EOF
# Z.AI 2 API Configuration - Auto-generated

# Server Configuration
LISTEN_PORT=8080
SERVICE_NAME=z-ai2api-server
DEBUG_LOGGING=true

# Authentication
AUTH_TOKEN=sk-test-key
SKIP_AUTH_TOKEN=false
ANONYMOUS_MODE=true

# Z.AI Token Pool - Not needed in anonymous mode
TOKEN_FAILURE_THRESHOLD=3
TOKEN_RECOVERY_TIMEOUT=1800
TOKEN_HEALTH_CHECK_INTERVAL=300

# Features
TOOL_SUPPORT=true
SCAN_LIMIT=200000

# Error Handling
MAX_RETRIES=6
RETRY_DELAY=1
EOF
    
    print_success ".env file created with ANONYMOUS_MODE=true"
}

# Function to check if server is running
check_server() {
    local max_attempts=30
    local attempt=1
    
    print_step "Waiting for server to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://127.0.0.1:8080/ > /dev/null 2>&1; then
            print_success "Server is ready!"
            return 0
        fi
        sleep 1
        echo -n "."
        ((attempt++))
    done
    
    echo ""
    print_error "Server failed to start within 30 seconds"
    return 1
}

# Function to send OpenAI API request and show real response
test_openai_api() {
    print_step "Testing OpenAI-compatible API endpoint..."
    echo ""
    
    # Create test request
    local request_data='{
  "model": "GLM-4-6-API-V1",
  "messages": [
    {
      "role": "user",
      "content": "Hello! Please introduce yourself in one sentence."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 100,
  "stream": false
}'
    
    print_step "Sending request to http://127.0.0.1:8080/v1/chat/completions"
    echo -e "${YELLOW}=== REQUEST ===${NC}"
    echo "$request_data" | jq '.' 2>/dev/null || echo "$request_data"
    echo ""
    
    # Send request and capture response
    print_step "Calling API..."
    local response=$(curl -s -X POST "http://127.0.0.1:8080/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer sk-test-key" \
        -d "$request_data")
    
    echo ""
    
    # Check if response is valid JSON
    if echo "$response" | jq '.' > /dev/null 2>&1; then
        print_success "Received valid JSON response!"
        echo -e "\n${GREEN}=== ACTUAL OPENAI API RESPONSE (NOT MOCK!) ===${NC}\n"
        echo "$response" | jq '.'
        
        # Extract and display the actual message content
        local content=$(echo "$response" | jq -r '.choices[0].message.content' 2>/dev/null)
        if [ ! -z "$content" ] && [ "$content" != "null" ]; then
            echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║       MODEL GENERATED RESPONSE FROM Z.AI GLM          ║${NC}"
            echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}\n"
            echo -e "${BLUE}$content${NC}\n"
            print_success "This is a REAL response from Z.AI, not a mock!"
        fi
        
        # Show response metadata
        local model=$(echo "$response" | jq -r '.model' 2>/dev/null)
        local usage=$(echo "$response" | jq '.usage' 2>/dev/null)
        if [ ! -z "$model" ] && [ "$model" != "null" ]; then
            echo -e "${YELLOW}Model used: $model${NC}"
        fi
        if [ ! -z "$usage" ] && [ "$usage" != "null" ]; then
            echo -e "${YELLOW}Token usage:${NC}"
            echo "$usage" | jq '.'
        fi
        
        return 0
    else
        print_error "Invalid JSON response!"
        echo -e "${RED}=== RAW RESPONSE ===${NC}"
        echo "$response"
        echo ""
        print_error "Check server.log for more details"
        return 1
    fi
}

# Function to start server in background
start_server() {
    print_step "Starting Z.AI API server..."
    
    # Kill any existing server on port 8080
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port 8080 is in use, killing existing process..."
        kill $(lsof -t -i:8080) 2>/dev/null || true
        sleep 2
    fi
    
    # Start server in background
    python3 main.py > server.log 2>&1 &
    local server_pid=$!
    echo $server_pid > server.pid
    
    print_success "Server started with PID: $server_pid"
    print_step "Server logs are being written to server.log"
    
    # Wait for server to be ready
    if ! check_server; then
        print_error "Server startup failed. Check server.log for details:"
        echo ""
        tail -n 30 server.log
        return 1
    fi
    
    # Show initial server logs
    echo ""
    print_step "Server startup logs:"
    head -n 10 server.log | grep -E "(启动|监听|Ready|Started|Listening)" || true
}

# Function to show server info
show_server_info() {
    echo ""
    print_success "═══════════════════════════════════════════════════════"
    print_success "    Server is running successfully!"
    print_success "═══════════════════════════════════════════════════════"
    echo ""
    echo -e "${BLUE}  Base URL:${NC}     http://127.0.0.1:8080"
    echo -e "${BLUE}  Endpoints:${NC}    /v1/chat/completions, /v1/models"
    echo -e "${BLUE}  API Key:${NC}      sk-test-key"
    echo -e "${BLUE}  Server PID:${NC}   $(cat server.pid)"
    echo ""
    echo -e "${YELLOW}  Management Commands:${NC}"
    echo -e "    View logs:     ${GREEN}tail -f server.log${NC}"
    echo -e "    Stop server:   ${RED}kill \$(cat server.pid)${NC}"
    echo -e "    Restart:       ${BLUE}./scripts/all.sh${NC}"
    echo ""
}

# Cleanup function
cleanup() {
    if [ -f server.pid ]; then
        local pid=$(cat server.pid)
        if kill -0 $pid 2>/dev/null; then
            print_step "Shutting down server (PID: $pid)..."
            kill $pid
            sleep 1
        fi
        rm -f server.pid
    fi
}

# Set up trap for cleanup
trap cleanup EXIT INT TERM

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║                                                        ║"
    echo "║       Z.AI OpenAI API Proxy - Complete Setup          ║"
    echo "║                                                        ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Check if we're in the project directory
    if [ ! -f "main.py" ]; then
        print_error "main.py not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Check Python availability
    if ! command -v python3 &> /dev/null; then
        print_error "python3 not found. Please install Python 3.9+"
        exit 1
    fi
    
    # Step 1: Create .env file with anonymous mode enabled
    create_env_file
    echo ""
    
    # Step 2: Start server
    start_server
    if [ $? -ne 0 ]; then
        print_error "Failed to start server"
        exit 1
    fi
    echo ""
    
    # Step 3: Test the API
    sleep 3  # Give server a moment to fully initialize
    test_openai_api
    if [ $? -ne 0 ]; then
        print_error "API test failed"
        print_warning "Check server.log for more details"
        exit 1
    fi
    
    # Show server info
    show_server_info
    
    # Keep script running and show logs
    print_step "Showing live server logs (Ctrl+C to exit and stop server)..."
    echo ""
    tail -f server.log
}

# Run main function
main

