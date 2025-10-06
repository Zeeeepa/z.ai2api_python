#!/bin/bash
# Post-installation script to set up Playwright browsers

echo "🎭 Installing Playwright browsers..."

# Check if playwright is installed
if ! command -v playwright &> /dev/null; then
    echo "❌ Playwright not found. Please install requirements first:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Install chromium browser for Playwright
playwright install chromium

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "✅ Playwright chromium browser installed successfully!"
    echo ""
    echo "You can now start the server with:"
    echo "  python main.py"
else
    echo "❌ Failed to install Playwright browsers"
    echo "Please run manually: playwright install chromium"
    exit 1
fi
