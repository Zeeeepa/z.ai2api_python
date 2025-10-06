#!/bin/bash

# ==============================================
# Z.AI2API Docker Deployment Script
# ==============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🚀 Z.AI2API Docker Deployment"
echo "================================"
echo

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo
    echo "📝 Please edit .env and add your credentials:"
    echo "   - ZAI_EMAIL and ZAI_PASSWORD"
    echo "   - K2THINK_EMAIL and K2THINK_PASSWORD"
    echo "   - QWEN_EMAIL and QWEN_PASSWORD"
    echo
    echo "Then run this script again."
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

echo "📦 Building Docker image..."
cd docker
docker-compose build

echo
echo "🚀 Starting services..."
docker-compose up -d

echo
echo "⏳ Waiting for service to be ready..."
sleep 5

# Check if service is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Service is running!"
    echo
    echo "🌐 API Endpoints:"
    echo "   Base URL: http://localhost:${PORT:-8080}"
    echo "   Chat Completions: http://localhost:${PORT:-8080}/v1/chat/completions"
    echo "   List Models: http://localhost:${PORT:-8080}/v1/models"
    echo "   API Docs: http://localhost:${PORT:-8080}/docs"
    echo
    
    # Check if FlareProx is enabled
    if [ "${FLAREPROX_ENABLED}" = "true" ]; then
        echo "🔥 FlareProx is ENABLED"
        echo "   Proxy Count: ${FLAREPROX_PROXY_COUNT:-3}"
        echo "   Auto Rotate: ${FLAREPROX_AUTO_ROTATE:-true}"
        echo
    fi
    
    echo "📊 View logs: docker-compose -f docker/docker-compose.yml logs -f"
    echo "🛑 Stop service: docker-compose -f docker/docker-compose.yml down"
else
    echo "❌ Service failed to start!"
    echo "Check logs: docker-compose -f docker/docker-compose.yml logs"
    exit 1
fi

echo
echo "✅ Deployment complete!"

