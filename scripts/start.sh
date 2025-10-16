#!/usr/bin/env bash
# start.sh - Start the server with port fallback logic

set -e

echo "🔧 Starting z.ai2api server..."

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    echo "❌ Error: Virtual environment not found. Run: bash scripts/deploy.sh"
    exit 1
fi

# Function to check if a port is in use
is_port_in_use() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -ti:$port &> /dev/null
    elif command -v nc &> /dev/null; then
        nc -z localhost $port &> /dev/null
    else
        # Fallback: try to bind with Python
        # If bind succeeds, port is FREE (return 1), if it fails, port is IN USE (return 0)
        if ./.venv/bin/python -c "import socket; s=socket.socket(); s.bind(('', $port)); s.close()" 2>/dev/null; then
            return 1  # Port is free
        else
            return 0  # Port is in use
        fi
    fi
}

# Find available port starting from SERVER_PORT (default 7300)
START_PORT=${SERVER_PORT:-7300}
MAX_ATTEMPTS=10
SELECTED_PORT=""

echo "🔍 Searching for available port starting from $START_PORT..."

for ((i=0; i<$MAX_ATTEMPTS; i++)); do
    TEST_PORT=$((START_PORT + i))
    if ! is_port_in_use $TEST_PORT; then
        SELECTED_PORT=$TEST_PORT
        echo "✅ Found available port: $SELECTED_PORT"
        break
    else
        echo "   Port $TEST_PORT is busy, trying next..."
    fi
done

if [[ -z "$SELECTED_PORT" ]]; then
    echo "❌ Error: Could not find available port after $MAX_ATTEMPTS attempts"
    echo "   Tried ports: $START_PORT-$((START_PORT + MAX_ATTEMPTS - 1))"
    exit 3
fi

# Set environment variables
export LISTEN_PORT=$SELECTED_PORT
export PYTHONPATH=
export AUTH_TOKEN=${AUTH_TOKEN:-"sk-any"}

# Optional: Use ZAI credentials if provided
if [[ -n "$ZAI_EMAIL" && -n "$ZAI_PASSWORD" ]]; then
    echo "🔐 Using ZAI credentials: $ZAI_EMAIL"
    export ZAI_EMAIL
    export ZAI_PASSWORD
else
    echo "⚠️  ZAI_EMAIL and ZAI_PASSWORD not set - running in anonymous mode"
fi

# Clean up old logs and PID files
rm -f server.log server.pid

# Start server in background
echo "🚀 Starting server on port $SELECTED_PORT..."
nohup ./.venv/bin/python main.py > server.log 2>&1 &
SERVER_PID=$!

# Save PID and port
echo $SERVER_PID > server.pid
echo $SELECTED_PORT > server.port

echo "✅ Server started!"
echo "   PID: $SERVER_PID"
echo "   Port: $SELECTED_PORT"
echo "   Logs: server.log"

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
MAX_WAIT=15
for ((i=1; i<=$MAX_WAIT; i++)); do
    if is_port_in_use $SELECTED_PORT; then
        echo "✅ Server is ready after ${i}s!"
        echo ""
        echo "📊 Server Info:"
        echo "   Base URL: http://localhost:$SELECTED_PORT"
        echo "   API URL: http://localhost:$SELECTED_PORT/v1"
        echo "   AUTH_TOKEN: $AUTH_TOKEN"
        echo ""
        echo "To stop server: kill $SERVER_PID"
        echo "To view logs: tail -f server.log"
        exit 0
    fi
    sleep 1
done

echo "❌ Error: Server failed to start within ${MAX_WAIT}s"
echo "📋 Last 20 lines of server.log:"
tail -20 server.log
exit 4
