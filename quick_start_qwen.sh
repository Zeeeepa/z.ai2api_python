#!/bin/bash

# Qwen Standalone Server - Quick Start Script
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main menu
show_menu() {
    clear
    echo -e "${GREEN}"
    cat << "EOF"
   ____                      _____                            
  / __ \__      _____  ____ / ___/___  ______   _____  _____ 
 / / / / | /| / / _ \/ __ \\__ \/ _ \/ ___/ | / / _ \/ ___/ 
/ /_/ /| |/ |/ /  __/ / / /__/ /  __/ /   | |/ /  __/ /     
\___\_\ |__/|__/\___/_/ /_/____/\___/_/    |___/\___/_/      
                                                              
EOF
    echo -e "${NC}"
    print_header "Qwen Standalone Server - Quick Start"
    echo "1) Install Dependencies"
    echo "2) Configure Environment"
    echo "3) Run Server (Development)"
    echo "4) Run Server (Docker)"
    echo "5) Test Server"
    echo "6) Setup FlareProx"
    echo "7) View Logs"
    echo "8) Stop Server"
    echo "9) Clean Up"
    echo "0) Exit"
    echo ""
    read -p "Select option [0-9]: " choice
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    required_version="3.11"
    
    if (( $(echo "$python_version < $required_version" | bc -l) )); then
        print_error "Python 3.11+ required. Found: $python_version"
        exit 1
    fi
    
    print_success "Python version: $python_version"
    
    # Install package
    print_info "Installing package..."
    pip install -e . > /dev/null 2>&1
    
    # Install additional dependencies
    print_info "Installing uvicorn..."
    pip install uvicorn[standard] > /dev/null 2>&1
    
    print_success "Dependencies installed successfully"
    read -p "Press Enter to continue..."
}

# Configure environment
configure_environment() {
    print_header "Configure Environment"
    
    if [ -f ".env.qwen" ]; then
        print_warning ".env.qwen already exists"
        read -p "Overwrite? (y/N): " overwrite
        if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
            return
        fi
    fi
    
    echo ""
    print_info "Enter Qwen credentials:"
    read -p "Email: " qwen_email
    read -sp "Password: " qwen_password
    echo ""
    read -p "Port (default 8081): " port
    port=${port:-8081}
    
    echo ""
    print_info "FlareProx configuration (optional):"
    read -p "Enable FlareProx? (y/N): " enable_flareprox
    
    if [ "$enable_flareprox" = "y" ] || [ "$enable_flareprox" = "Y" ]; then
        read -p "Cloudflare API Key: " cf_api_key
        read -p "Cloudflare Account ID: " cf_account_id
        read -p "Cloudflare Email: " cf_email
        flareprox_enabled="true"
    else
        cf_api_key=""
        cf_account_id=""
        cf_email=""
        flareprox_enabled="false"
    fi
    
    # Create .env file
    cat > .env.qwen << EOF
# Qwen Standalone Server Configuration
PORT=${port}
DEBUG=false

# Qwen Authentication
QWEN_EMAIL=${qwen_email}
QWEN_PASSWORD=${qwen_password}

# FlareProx Configuration
ENABLE_FLAREPROX=${flareprox_enabled}
CLOUDFLARE_API_KEY=${cf_api_key}
CLOUDFLARE_ACCOUNT_ID=${cf_account_id}
CLOUDFLARE_EMAIL=${cf_email}

# Advanced Settings
DEFAULT_MODEL=qwen-turbo-latest
MAX_TOKENS=4096
TEMPERATURE=0.7
EOF
    
    print_success "Configuration saved to .env.qwen"
    read -p "Press Enter to continue..."
}

# Run server (development)
run_server_dev() {
    print_header "Starting Server (Development Mode)"
    
    if [ ! -f ".env.qwen" ]; then
        print_error "Configuration not found. Please configure first."
        read -p "Press Enter to continue..."
        return
    fi
    
    # Load environment
    source .env.qwen
    
    print_info "Starting server on port $PORT..."
    print_info "Press Ctrl+C to stop"
    echo ""
    
    python qwen_server.py
}

# Run server (Docker)
run_server_docker() {
    print_header "Starting Server (Docker)"
    
    if [ ! -f ".env.qwen" ]; then
        print_error "Configuration not found. Please configure first."
        read -p "Press Enter to continue..."
        return
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        read -p "Press Enter to continue..."
        return
    fi
    
    print_info "Building Docker image..."
    docker-compose -f docker-compose.qwen.yml build
    
    print_info "Starting container..."
    docker-compose -f docker-compose.qwen.yml up -d
    
    sleep 3
    
    # Check status
    if docker-compose -f docker-compose.qwen.yml ps | grep -q "Up"; then
        print_success "Server started successfully"
        print_info "Access at: http://localhost:8081"
        print_info "View logs: docker-compose -f docker-compose.qwen.yml logs -f"
    else
        print_error "Server failed to start"
        print_info "Check logs: docker-compose -f docker-compose.qwen.yml logs"
    fi
    
    read -p "Press Enter to continue..."
}

# Test server
test_server() {
    print_header "Testing Server"
    
    if [ ! -f ".env.qwen" ]; then
        print_error "Configuration not found."
        read -p "Press Enter to continue..."
        return
    fi
    
    source .env.qwen
    PORT=${PORT:-8081}
    
    echo "1) Quick Test (3 models)"
    echo "2) Comprehensive Test (all models)"
    echo "3) Health Check Only"
    echo ""
    read -p "Select test [1-3]: " test_choice
    
    case $test_choice in
        1)
            python test_qwen_server.py --quick
            ;;
        2)
            python test_qwen_server.py
            ;;
        3)
            print_info "Checking server health..."
            curl -s http://localhost:$PORT/health | python -m json.tool
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

# Setup FlareProx
setup_flareprox() {
    print_header "FlareProx Setup"
    
    echo "1) Configure FlareProx"
    echo "2) Create Workers"
    echo "3) List Workers"
    echo "4) Test Workers"
    echo "5) Clean Up Workers"
    echo ""
    read -p "Select option [1-5]: " fp_choice
    
    case $fp_choice in
        1)
            python flareprox.py config
            ;;
        2)
            read -p "Number of workers to create: " count
            python flareprox.py create --count ${count:-3}
            ;;
        3)
            python flareprox.py list
            ;;
        4)
            python flareprox.py test
            ;;
        5)
            read -p "Delete all workers? (y/N): " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                python flareprox.py cleanup
            fi
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
}

# View logs
view_logs() {
    print_header "View Logs"
    
    if docker ps | grep -q "qwen-api"; then
        print_info "Viewing Docker logs (Ctrl+C to exit)..."
        docker-compose -f docker-compose.qwen.yml logs -f
    else
        print_warning "Docker container not running"
        if [ -f "logs/qwen_server.log" ]; then
            print_info "Viewing local logs (Ctrl+C to exit)..."
            tail -f logs/qwen_server.log
        else
            print_error "No logs found"
        fi
    fi
    
    read -p "Press Enter to continue..."
}

# Stop server
stop_server() {
    print_header "Stopping Server"
    
    if docker ps | grep -q "qwen-api"; then
        print_info "Stopping Docker container..."
        docker-compose -f docker-compose.qwen.yml down
        print_success "Container stopped"
    else
        print_warning "No Docker container running"
    fi
    
    # Kill any Python processes
    if pgrep -f "qwen_server.py" > /dev/null; then
        print_info "Stopping Python server..."
        pkill -f "qwen_server.py"
        print_success "Python server stopped"
    fi
    
    read -p "Press Enter to continue..."
}

# Clean up
clean_up() {
    print_header "Clean Up"
    
    print_warning "This will remove:"
    echo "  - __pycache__ directories"
    echo "  - .pyc files"
    echo "  - build directories"
    echo ""
    read -p "Continue? (y/N): " confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        print_info "Cleaning..."
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
        rm -rf build/ dist/ .pytest_cache/ 2>/dev/null || true
        print_success "Cleanup complete"
    fi
    
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    show_menu
    
    case $choice in
        1) install_dependencies ;;
        2) configure_environment ;;
        3) run_server_dev ;;
        4) run_server_docker ;;
        5) test_server ;;
        6) setup_flareprox ;;
        7) view_logs ;;
        8) stop_server ;;
        9) clean_up ;;
        0)
            print_success "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            sleep 2
            ;;
    esac
done

