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

# Step 1: Find suitable Python version (3.9-3.12)
log_info "Finding suitable Python version (3.9-3.12)..."

SUITABLE_PYTHON=""
SUITABLE_VERSION=""

# Try different Python versions in order of preference (avoid 3.13 due to pydantic issues)
for py_cmd in python3.11 python3.12 python3.10 python3.9 python3; do
    if command -v $py_cmd &> /dev/null; then
        version=$($py_cmd --version 2>&1 | cut -d' ' -f2)
        major=$(echo $version | cut -d'.' -f1)
        minor=$(echo $version | cut -d'.' -f2)
        
        # Check if version is 3.9-3.12 (exclude 3.13+)
        if [ "$major" -eq 3 ] && [ "$minor" -ge 9 ] && [ "$minor" -le 12 ]; then
            SUITABLE_PYTHON=$py_cmd
            SUITABLE_VERSION=$version
            break
        fi
    fi
done

if [ -z "$SUITABLE_PYTHON" ]; then
    log_error "No suitable Python version found!"
    echo ""
    echo "Python 3.9-3.12 is required (Python 3.13+ has compatibility issues)"
    echo ""
    echo "Please install one of these Python versions:"
    echo "  - Python 3.11 (recommended)"
    echo "  - Python 3.12"
    echo "  - Python 3.10"
    echo "  - Python 3.9"
    exit 1
fi

log_success "Found suitable Python: $SUITABLE_PYTHON ($SUITABLE_VERSION)"

# Step 1b: Create virtual environment if it doesn't exist
VENV_DIR="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment with $SUITABLE_PYTHON..."
    
    if command -v uv &> /dev/null; then
        # Use uv to create venv (faster)
        uv venv --python $SUITABLE_PYTHON "$VENV_DIR"
    else
        # Use standard Python venv
        $SUITABLE_PYTHON -m venv "$VENV_DIR"
    fi
    
    if [ $? -eq 0 ]; then
        log_success "Virtual environment created at $VENV_DIR"
    else
        log_error "Failed to create virtual environment"
        exit 1
    fi
else
    log_success "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

if [ $? -eq 0 ]; then
    log_success "Virtual environment activated"
    log_info "Python: $(which python)"
else
    log_error "Failed to activate virtual environment"
    exit 1
fi

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

# Determine which Python command to use
if command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
    PLAYWRIGHT_CMD="uv run playwright"
else
    PYTHON_CMD="python3"
    PLAYWRIGHT_CMD="python3 -m playwright"
fi

if ! $PYTHON_CMD -c "import playwright" 2>/dev/null; then
    log_info "Playwright not found, installing..."
    $PIP_CMD playwright
fi

# Install Playwright browsers
log_info "Installing Playwright browsers (this may take a few minutes)..."
$PLAYWRIGHT_CMD install chromium
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
log_success "Virtual environment is active!"
log_info "To activate in new terminals, run:"
echo ""
echo "    source .venv/bin/activate"
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
echo "💡 Note: The virtual environment will remain active in this shell"
echo ""
echo "============================================================"
echo ""
