#!/bin/bash
set -e

echo "╔════════════════════════════════════════╗"
echo "║   Z.AI2API - Complete Workflow         ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "This script will:"
echo "  1. Setup environment and retrieve token"
echo "  2. Start the OpenAI-compatible API server"
echo "  3. Send test requests in OpenAI format"
echo "  4. Keep server running for continued use"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Must run from project root${NC}"
    exit 1
fi

# ============================================
# STEP 1: SETUP & AUTHENTICATION
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 STEP 1/4: Setup & Authentication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash scripts/setup.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Setup failed${NC}"
    exit 1
fi

echo ""
sleep 2

# ============================================
# STEP 2: START SERVER
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 STEP 2/4: Starting OpenAI-Compatible Server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Kill any existing server
LISTEN_PORT=${LISTEN_PORT:-8080}
if lsof -Pi :$LISTEN_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "🧹 Cleaning up existing server on port $LISTEN_PORT..."
    lsof -ti:$LISTEN_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start server in background
echo "🔄 Starting server in background..."
bash scripts/start.sh > /tmp/z.ai2api_server.log 2>&1 &
SERVER_PID=$!

echo "   Server PID: $SERVER_PID"
echo "   Log file: /tmp/z.ai2api_server.log"
echo ""
echo "⏳ Waiting for server to be ready..."

# Wait for server (max 30 seconds)
MAX_WAIT=30
WAITED=0
SERVER_READY=false

while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:$LISTEN_PORT/health > /dev/null 2>&1; then
        SERVER_READY=true
        break
    fi
    echo -n "."
    sleep 1
    WAITED=$((WAITED + 1))
done

echo ""

if [ "$SERVER_READY" = false ]; then
    echo -e "${RED}❌ Server failed to start within ${MAX_WAIT} seconds${NC}"
    echo ""
    echo "Last 20 lines of server log:"
    tail -20 /tmp/z.ai2api_server.log
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Server is ready!${NC}"
echo "   URL: http://localhost:$LISTEN_PORT"
echo ""

sleep 2

# ============================================
# STEP 3: TEST API WITH OPENAI FORMAT
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 STEP 3/4: Testing OpenAI-Compatible API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash scripts/send_request.sh

TEST_RESULT=$?

# ============================================
# STEP 4: SHOW PYTHON USAGE EXAMPLE
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 STEP 4/4: Python Usage Example"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cat << 'EOF'
You can now use the server with OpenAI Python SDK:

```python
import openai

# Initialize client pointing to local server
client = openai.OpenAI(
    base_url=f"http://localhost:8080/v1",  # Routes to Z.AI
    api_key="your-zai-token"  # Z.AI bearer token
)

# Send chat completion request (OpenAI format)
response = client.chat.completions.create(
    model="GLM-4.5",
    messages=[
        {"role": "user", "content": "What is Python?"}
    ],
    stream=False
)

# Print response
print(response.choices[0].message.content)

# Streaming example
stream = client.chat.completions.create(
    model="GLM-4.5",
    messages=[{"role": "user", "content": "Count to 5"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

The server automatically converts OpenAI format to Z.AI format:
- OpenAI format IN: http://localhost:8080/v1/chat/completions
- Z.AI format OUT: https://chat.z.ai/api/v1/chat/completions
EOF

echo ""

# ============================================
# SUMMARY
# ============================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Complete Workflow Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ✅ Setup: Complete"
echo "  ✅ Server: Running (PID: $SERVER_PID)"
if [ $TEST_RESULT -eq 0 ]; then
    echo "  ✅ Tests: All Passed"
else
    echo "  ⚠️  Tests: Some failures (check above)"
fi
echo ""
echo "Server Details:"
echo "  📍 URL: http://localhost:$LISTEN_PORT/v1"
echo "  📄 Log: /tmp/z.ai2api_server.log"
echo "  🔢 PID: $SERVER_PID"
echo "  🔄 Routes to: https://chat.z.ai/api/v1"
echo ""
echo "Useful Commands:"
echo "  📊 View logs: tail -f /tmp/z.ai2api_server.log"
echo "  🧪 Test again: bash scripts/send_request.sh"
echo "  🛑 Stop server: kill $SERVER_PID"
echo ""

# ============================================
# KEEP SERVER RUNNING
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Server is running and ready for requests!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "The server will keep running in the background."
echo "You can now use it with OpenAI SDK or curl."
echo ""

read -p "Press Enter to view live server logs (Ctrl+C to exit)..." 
echo ""

# Show live logs
tail -f /tmp/z.ai2api_server.log

