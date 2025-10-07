#!/bin/bash

################################################################################
# Z.AI2API - Quick Deploy, Test, and Run Script
# 
# This script automates the complete deployment and testing workflow:
# 1. Install dependencies
# 2. Configure providers
# 3. Start the server
# 4. Run comprehensive tests
# 5. Display results
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_PORT=8080
SERVER_LOG="$SCRIPT_DIR/server.log"
TEST_LOG="$SCRIPT_DIR/test_results.log"
PID_FILE="$SCRIPT_DIR/server.pid"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ️  $1${NC}"
}

wait_for_server() {
    local max_attempts=30
    local attempt=1
    
    print_step "Waiting for server to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:$SERVER_PORT/ > /dev/null 2>&1; then
            print_success "Server is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "Server failed to start within 30 seconds"
    return 1
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_step "Stopping existing server (PID: $pid)..."
            kill "$pid"
            sleep 2
            rm -f "$PID_FILE"
            print_success "Server stopped"
        fi
    fi
}

################################################################################
# Check Prerequisites
################################################################################

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Python
    print_step "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python found: $PYTHON_VERSION"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
        print_success "Python found: $PYTHON_VERSION"
    else
        print_error "Python is not installed!"
        print_info "Please install Python 3.11 or higher:"
        print_info "  Ubuntu/Debian: sudo apt install python3 python3-pip"
        print_info "  CentOS/RHEL: sudo yum install python3 python3-pip"
        print_info "  MacOS: brew install python3"
        exit 1
    fi
    
    # Check pip
    print_step "Checking pip installation..."
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
        print_success "pip3 found"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
        print_success "pip found"
    elif $PYTHON_CMD -m pip --version &> /dev/null; then
        PIP_CMD="$PYTHON_CMD -m pip"
        print_success "pip module found"
    else
        print_error "pip is not installed!"
        print_info "Installing pip..."
        curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
        
        if $PYTHON_CMD -m pip --version &> /dev/null; then
            PIP_CMD="$PYTHON_CMD -m pip"
            print_success "pip installed successfully"
        else
            print_error "Failed to install pip"
            exit 1
        fi
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        print_warning "curl is not installed - some features may not work"
        print_info "Install with: sudo apt install curl (Ubuntu/Debian)"
    fi
    
    echo ""
    print_info "Using Python: $PYTHON_CMD"
    print_info "Using pip: $PIP_CMD"
}

################################################################################
# Step 1: Install Dependencies
################################################################################

install_dependencies() {
    print_header "STEP 1: Installing Dependencies"
    
    print_step "Installing Python dependencies..."
    if [ -f requirements.txt ]; then
        $PIP_CMD install -q -r requirements.txt 2>&1 | grep -E "Successfully|ERROR" || true
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found, installing minimal dependencies..."
        $PIP_CMD install -q openai httpx fastapi uvicorn playwright 2>&1 | grep -E "Successfully|ERROR" || true
        print_success "Minimal dependencies installed"
    fi
    
    print_step "Installing Playwright browsers..."
    if $PYTHON_CMD -m playwright --version &> /dev/null; then
        print_info "Playwright already installed, installing browsers..."
    else
        print_info "Installing Playwright..."
        $PIP_CMD install -q playwright
    fi
    
    $PYTHON_CMD -m playwright install chromium > /dev/null 2>&1 || {
        print_warning "Could not install Playwright browsers automatically"
        print_info "You may need to run: $PYTHON_CMD -m playwright install chromium"
    }
    print_success "Playwright browsers installed"
}

################################################################################
# Step 2: Configure Providers
################################################################################

configure_providers() {
    print_header "STEP 2: Configuring Providers"
    
    if [ ! -f "$SCRIPT_DIR/config/providers.json" ]; then
        print_warning "config/providers.json not found"
        
        if [ -f "$SCRIPT_DIR/config/providers.json.example" ]; then
            print_step "Creating config/providers.json from example..."
            cp "$SCRIPT_DIR/config/providers.json.example" "$SCRIPT_DIR/config/providers.json"
            
            print_warning "Please edit config/providers.json with your credentials:"
            print_info "  - Z.AI: email and password"
            print_info "  - K2Think: email and password"
            print_info "  - Qwen: email and password"
            echo ""
            read -p "Press Enter after you've configured the credentials..."
        else
            print_error "config/providers.json.example not found!"
            print_info "Please create config/providers.json manually"
            exit 1
        fi
    else
        print_success "config/providers.json found"
    fi
    
    # Validate JSON
    if ${PYTHON_CMD:-python3} -c "import json; json.load(open('$SCRIPT_DIR/config/providers.json'))" 2>/dev/null; then
        print_success "Configuration file is valid JSON"
    else
        print_error "Configuration file has invalid JSON syntax"
        exit 1
    fi
}

################################################################################
# Step 3: Start Server
################################################################################

start_server() {
    print_header "STEP 3: Starting Server"
    
    # Stop any existing server
    stop_server
    
    # Clear old logs
    > "$SERVER_LOG"
    
    print_step "Starting server on port $SERVER_PORT..."
    
    # Start server in background
    cd "$SCRIPT_DIR"
    nohup ${PYTHON_CMD:-python3} main.py > "$SERVER_LOG" 2>&1 &
    echo $! > "$PID_FILE"
    
    # Wait for server to be ready
    if wait_for_server; then
        print_success "Server started successfully (PID: $(cat $PID_FILE))"
        print_info "Server URL: http://localhost:$SERVER_PORT"
        print_info "Server logs: $SERVER_LOG"
        
        # Show initial server info
        sleep 2
        if [ -f "$SERVER_LOG" ]; then
            echo ""
            print_step "Server initialization:"
            tail -20 "$SERVER_LOG" | grep -E "INFO|models|Listening" || true
        fi
    else
        print_error "Failed to start server"
        print_info "Check logs: tail -50 $SERVER_LOG"
        exit 1
    fi
}

################################################################################
# Step 4: Run Quick Health Check
################################################################################

health_check() {
    print_header "STEP 4: Health Check"
    
    print_step "Testing server connectivity..."
    
    if response=$(curl -s http://localhost:$SERVER_PORT/); then
        print_success "Server is responding"
        echo "$response" | ${PYTHON_CMD:-python3} -m json.tool 2>/dev/null || echo "$response"
    else
        print_error "Server health check failed"
        return 1
    fi
    
    echo ""
    print_step "Listing available models..."
    
    if models=$(curl -s http://localhost:$SERVER_PORT/v1/models); then
        model_count=$(echo "$models" | ${PYTHON_CMD:-python3} -c "import json,sys; print(len(json.load(sys.stdin)['data']))" 2>/dev/null || echo "unknown")
        print_success "Found $model_count models available"
        
        echo ""
        echo "$models" | ${PYTHON_CMD:-python3} -c "
import json, sys
data = json.load(sys.stdin)
print('📋 Available Models:')
for model in data['data'][:10]:
    print(f\"  • {model['id']}\")
if len(data['data']) > 10:
    print(f\"  ... and {len(data['data']) - 10} more\")
" 2>/dev/null || echo "$models"
    else
        print_error "Failed to list models"
        return 1
    fi
}

################################################################################
# Step 5: Run Single Model Tests
################################################################################

test_single_model() {
    local model=$1
    local question=$2
    
    print_step "Testing $model..."
    
    local response=$(curl -s -X POST http://localhost:$SERVER_PORT/v1/chat/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer sk-anything" \
        -d "{
            \"model\": \"$model\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$question\"}],
            \"max_tokens\": 100
        }" 2>&1)
    
    # Check if response contains error
    if echo "$response" | grep -q "error\|401\|Invalid"; then
        print_warning "$model - Authentication required"
        echo "     $(echo "$response" | ${PYTHON_CMD:-python3} -c "import json,sys; print(json.load(sys.stdin).get('error', {}).get('message', 'Authentication needed'))" 2>/dev/null || echo "Auth needed")"
        return 1
    elif echo "$response" | grep -q "content"; then
        local content=$(echo "$response" | ${PYTHON_CMD:-python3} -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'][:80] + '...')" 2>/dev/null || echo "Response received")
        print_success "$model - Response: $content"
        return 0
    else
        print_error "$model - Unknown error"
        return 1
    fi
}

run_quick_tests() {
    print_header "STEP 5: Running Quick Tests"
    
    local success_count=0
    local total_count=0
    
    # Test a few models from each provider
    local test_models=(
        "GLM-4.5:What model are you?"
        "qwen-max:What model are you?"
        "MBZUAI-IFM/K2-Think:What is 2+2?"
    )
    
    for test in "${test_models[@]}"; do
        IFS=':' read -r model question <<< "$test"
        total_count=$((total_count + 1))
        
        if test_single_model "$model" "$question"; then
            success_count=$((success_count + 1))
        fi
        
        sleep 1  # Rate limiting
    done
    
    echo ""
    print_info "Quick Test Results: $success_count/$total_count successful"
    
    if [ $success_count -eq 0 ]; then
        print_warning "No models responded successfully - authentication may be required"
        print_info "This is expected if providers haven't been authenticated yet"
    fi
}

################################################################################
# Step 6: Run Comprehensive Tests
################################################################################

run_comprehensive_tests() {
    print_header "STEP 6: Running Comprehensive Tests (AllCall.py)"
    
    if [ ! -f "$SCRIPT_DIR/AllCall.py" ]; then
        print_error "AllCall.py not found"
        return 1
    fi
    
    print_step "Running tests on all 42+ models concurrently..."
    print_info "This will test all models simultaneously and may take 1-2 minutes"
    echo ""
    
    # Run AllCall.py and capture output
    cd "$SCRIPT_DIR"
    ${PYTHON_CMD:-python3} AllCall.py 2>&1 | tee "$TEST_LOG"
    
    echo ""
    print_success "Comprehensive tests completed!"
    print_info "Full results saved to: $TEST_LOG"
}

################################################################################
# Step 7: Display Results Summary
################################################################################

display_results() {
    print_header "STEP 7: Results Summary"
    
    if [ -f "$TEST_LOG" ]; then
        print_step "Test Results:"
        echo ""
        
        # Extract summary from test log
        if grep -q "SUMMARY" "$TEST_LOG"; then
            sed -n '/SUMMARY/,/Testing completed/p' "$TEST_LOG" | head -20
        fi
        
        echo ""
        print_step "Error Analysis:"
        
        # Count error types
        local auth_errors=$(grep -c "Invalid API key\|401" "$TEST_LOG" 2>/dev/null || echo "0")
        local timeout_errors=$(grep -c "timeout\|Timeout" "$TEST_LOG" 2>/dev/null || echo "0")
        local other_errors=$(grep -c "Error" "$TEST_LOG" 2>/dev/null || echo "0")
        
        echo "  • Authentication errors: $auth_errors"
        echo "  • Timeout errors: $timeout_errors"
        echo "  • Other errors: $other_errors"
        
        if [ "$auth_errors" -gt 0 ]; then
            echo ""
            print_warning "Authentication errors detected"
            print_info "Next steps:"
            echo "  1. Verify credentials in config/providers.json"
            echo "  2. Ensure provider accounts are active"
            echo "  3. Check server logs: tail -f $SERVER_LOG"
        fi
    fi
    
    echo ""
    print_step "Server Status:"
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_success "Server is running (PID: $pid)"
            print_info "Server URL: http://localhost:$SERVER_PORT"
        else
            print_error "Server is not running"
        fi
    fi
}

################################################################################
# Step 8: Interactive Menu
################################################################################

interactive_menu() {
    print_header "Interactive Testing Menu"
    
    while true; do
        echo ""
        echo "What would you like to do?"
        echo ""
        echo "  1) Test a specific model"
        echo "  2) Run comprehensive tests (all models)"
        echo "  3) View server logs"
        echo "  4) View test results"
        echo "  5) Check server status"
        echo "  6) Restart server"
        echo "  7) Stop server and exit"
        echo ""
        read -p "Enter choice (1-7): " choice
        
        case $choice in
            1)
                echo ""
                read -p "Enter model name (e.g., GLM-4.5): " model_name
                read -p "Enter test question: " test_question
                test_single_model "$model_name" "$test_question"
                ;;
            2)
                run_comprehensive_tests
                ;;
            3)
                echo ""
                print_step "Server logs (last 50 lines):"
                tail -50 "$SERVER_LOG"
                ;;
            4)
                echo ""
                print_step "Test results:"
                if [ -f "$TEST_LOG" ]; then
                    cat "$TEST_LOG" | less
                else
                    print_warning "No test results found. Run tests first."
                fi
                ;;
            5)
                echo ""
                health_check
                ;;
            6)
                stop_server
                start_server
                ;;
            7)
                stop_server
                print_success "Server stopped. Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter 1-7."
                ;;
        esac
    done
}

################################################################################
# Main Execution
################################################################################

main() {
    clear
    
    print_header "Z.AI2API - Automated Deployment & Testing"
    
    echo -e "${CYAN}This script will:${NC}"
    echo "  1. Install dependencies"
    echo "  2. Configure providers"
    echo "  3. Start the server"
    echo "  4. Run health checks"
    echo "  5. Run quick tests"
    echo "  6. Run comprehensive tests"
    echo "  7. Display results"
    echo ""
    
    # Check if running in non-interactive mode
    if [ "$1" == "--auto" ] || [ "$1" == "-a" ]; then
        AUTO_MODE=true
        print_info "Running in automatic mode"
    else
        read -p "Press Enter to continue or Ctrl+C to cancel..."
    fi
    
    # Check prerequisites first
    check_prerequisites
    
    # Execute steps
    install_dependencies
    configure_providers
    start_server
    
    echo ""
    sleep 2
    
    health_check
    
    echo ""
    sleep 1
    
    run_quick_tests
    
    echo ""
    print_step "Would you like to run comprehensive tests now?"
    if [ "$AUTO_MODE" == "true" ]; then
        run_comprehensive_tests
        display_results
    else
        read -p "Run comprehensive tests? (y/n): " run_tests
        if [[ $run_tests =~ ^[Yy]$ ]]; then
            run_comprehensive_tests
            display_results
        fi
        
        echo ""
        read -p "Enter interactive menu? (y/n): " enter_menu
        if [[ $enter_menu =~ ^[Yy]$ ]]; then
            interactive_menu
        fi
    fi
    
    echo ""
    print_header "Deployment Complete!"
    
    echo -e "${GREEN}Server is running at: http://localhost:$SERVER_PORT${NC}"
    echo ""
    echo "Useful commands:"
    echo "  • View logs:        tail -f $SERVER_LOG"
    echo "  • View test results: cat $TEST_LOG"
    echo "  • Stop server:      kill \$(cat $PID_FILE)"
    echo "  • Test single model: curl -X POST http://localhost:$SERVER_PORT/v1/chat/completions \\"
    echo "                         -H 'Content-Type: application/json' \\"
    echo "                         -H 'Authorization: Bearer sk-anything' \\"
    echo "                         -d '{\"model\": \"GLM-4.5\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}]}'"
    echo ""
}

# Trap Ctrl+C and cleanup
trap 'echo ""; print_warning "Interrupted. Server is still running."; exit 130' INT

# Run main function
main "$@"
