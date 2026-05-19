#!/usr/bin/env bash
# deploy.sh - Install dependencies and setup virtual environment

set -e  # Exit on any error

echo "🚀 Starting deployment of z.ai2api_python..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed."
    echo "📦 Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 2
fi

echo "✅ uv found: $(uv --version)"

# Check for required files
if [[ ! -f "main.py" ]]; then
    echo "❌ Error: main.py not found. Are you in the project root?"
    exit 1
fi

if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ Error: pyproject.toml not found. Are you in the project root?"
    exit 1
fi

# Create/sync virtual environment
echo "📦 Creating virtual environment and syncing dependencies..."
uv venv

echo "📥 Installing project dependencies..."
uv sync

# Install OpenAI client for testing
echo "🔧 Installing OpenAI client for API testing..."
uv pip install "openai>=1.0.0,<2"

echo ""
echo "✅ Deployment complete!"
echo "📁 Virtual environment: .venv/"
echo "🐍 Python: $(./.venv/bin/python --version)"
echo ""
echo "Next steps:"
echo "  1. Export credentials: export ZAI_EMAIL='your@email.com' ZAI_PASSWORD='yourpass'"
echo "  2. Start server: bash scripts/start.sh"
echo "  3. Or run all: bash scripts/all.sh"

