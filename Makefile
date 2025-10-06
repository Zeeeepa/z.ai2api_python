.PHONY: install install-playwright setup test clean help

help:
	@echo "Available commands:"
	@echo "  make install           - Install Python dependencies"
	@echo "  make install-playwright - Install Playwright browsers"
	@echo "  make setup             - Complete setup (install + playwright)"
	@echo "  make test              - Run all tests"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make clean             - Clean temporary files and cache"
	@echo "  make run               - Start the server"

install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt

install-playwright:
	@echo "🎭 Installing Playwright browsers..."
	playwright install chromium
	@echo "✅ Playwright chromium installed"

setup: install install-playwright
	@echo "✅ Setup complete! You can now run 'make run' to start the server"

test:
	@echo "🧪 Running all tests..."
	pytest tests/ -v

test-integration:
	@echo "🧪 Running integration tests..."
	pytest tests/integration/ -v

test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/unit/ -v

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "test_results*.json" -delete
	@echo "✅ Cleanup complete"

run:
	@echo "🚀 Starting server..."
	python main.py

