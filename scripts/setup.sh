#!/bin/bash
#
# setup.sh - Z.AI2API Setup Script
# 
# This script performs initial setup:
# 1. Installs Python dependencies
# 2. Installs Playwright and browsers
# 3. Creates .env file if needed
# 4. Retrieves authentication token via Playwright login
# 5. Initializes the database
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
echo "         Z.AI2API Python - Setup Script"
echo "============================================================"
echo ""

# Check for required environment variables
log_info "Checking environment variables..."
if [ -z "$ZAI_EMAIL" ] || [ -z "$ZAI_PASSWORD" ]; then
    log_error "ZAI_EMAIL and ZAI_PASSWORD environment variables must be set"
    echo ""
    echo "Usage:"
    echo "  export ZAI_EMAIL=your-email@example.com"
    echo "  export ZAI_PASSWORD=your-password"
    echo "  bash scripts/setup.sh"
    echo ""
    exit 1
fi
log_success "Environment variables found"

# Navigate to project root
cd "$PROJECT_ROOT"
log_info "Working directory: $PROJECT_ROOT"

# Step 1: Check Python version
log_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    log_error "Python 3.9+ is required (found: $PYTHON_VERSION)"
    exit 1
fi
log_success "Python version: $(python3 --version)"

# Step 2: Install Python dependencies
log_info "Installing Python dependencies..."
if command -v uv &> /dev/null; then
    log_info "Using uv for dependency management..."
    uv sync
    PIP_CMD="uv pip install"
else
    log_info "Using pip for dependency management..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    PIP_CMD="python3 -m pip install"
fi
log_success "Python dependencies installed"

# Step 3: Install Playwright
log_info "Installing Playwright..."
if ! python3 -c "import playwright" 2>/dev/null; then
    log_info "Playwright not found, installing..."
    $PIP_CMD playwright
fi

# Install Playwright browsers
log_info "Installing Playwright browsers (this may take a few minutes)..."
python3 -m playwright install chromium
log_success "Playwright and browsers installed"

# Step 4: Create .env file if it doesn't exist
log_info "Checking .env file..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        log_info "Creating .env from .env.example..."
        cp .env.example .env
        log_success ".env file created"
    else
        log_warning ".env.example not found, creating minimal .env..."
        cat > .env << EOF
# Z.AI2API Configuration
AUTH_TOKEN=sk-placeholder
SKIP_AUTH_TOKEN=false
TOKEN_FAILURE_THRESHOLD=3
TOKEN_RECOVERY_TIMEOUT=1800
ANONYMOUS_MODE=true
LISTEN_PORT=8080
SERVICE_NAME=z-ai2api-server
DEBUG_LOGGING=false
TOOL_SUPPORT=true
SCAN_LIMIT=200000
EOF
        log_success "Minimal .env file created"
    fi
else
    log_success ".env file already exists"
fi

# Step 5: Retrieve authentication token
log_info "Retrieving authentication token from Z.AI..."
echo ""
echo "============================================================"
echo "              Token Retrieval (Playwright)"
echo "============================================================"
echo ""

if command -v uv &> /dev/null; then
    uv run python scripts/retrieve_token.py
    TOKEN_EXIT_CODE=$?
else
    python3 scripts/retrieve_token.py
    TOKEN_EXIT_CODE=$?
fi

echo ""
if [ $TOKEN_EXIT_CODE -eq 0 ]; then
    log_success "Token retrieved and saved to .env"
else
    log_error "Failed to retrieve token"
    log_warning "You can manually set AUTH_TOKEN in .env file"
    exit 1
fi

# Step 6: Create logs directory
log_info "Creating logs directory..."
mkdir -p logs
log_success "Logs directory ready"

# Step 7: Test database initialization
log_info "Testing database initialization..."
if command -v uv &> /dev/null; then
    uv run python -c "
import asyncio
from app.services.token_dao import init_token_database

async def test():
    await init_token_database()
    print('Database initialized successfully')

asyncio.run(test())
" 2>&1 | tail -1
else
    python3 -c "
import asyncio
from app.services.token_dao import init_token_database

async def test():
    await init_token_database()
    print('Database initialized successfully')

asyncio.run(test())
" 2>&1 | tail -1
fi

if [ $? -eq 0 ]; then
    log_success "Database initialization test passed"
else
    log_warning "Database will be initialized on first server start"
fi

# Final summary
echo ""
echo "============================================================"
echo "                   Setup Complete! ✨"
echo "============================================================"
echo ""
echo "📋 Next steps:"
echo "  1. Review .env file and adjust settings if needed"
echo "  2. Run: bash scripts/start.sh"
echo "  3. Or run everything at once: bash scripts/all.sh"
echo ""
echo "🌐 Server will be available at: http://localhost:8080"
echo "📖 API Documentation: http://localhost:8080/docs"
echo "🔧 Admin Panel: http://localhost:8080/admin"
echo ""
echo "============================================================"
echo ""

