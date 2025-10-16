#!/usr/bin/env bash
# send_openai_request.sh - Send test OpenAI API request to the server

set -e

echo "🧪 Sending OpenAI API test request..."

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    echo "❌ Error: Virtual environment not found. Run: bash scripts/deploy.sh"
    exit 1
fi

# Get server port
if [[ -f "server.port" ]]; then
    SERVER_PORT=$(cat server.port)
else
    SERVER_PORT=${SERVER_PORT:-7300}
    echo "⚠️  server.port not found, using SERVER_PORT=${SERVER_PORT}"
fi

# Check if server is running
if [[ -f "server.pid" ]]; then
    SERVER_PID=$(cat server.pid)
    if ! ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "❌ Error: Server process (PID: $SERVER_PID) is not running"
        exit 4
    fi
else
    echo "⚠️  server.pid not found, cannot verify server is running"
fi

# Get AUTH_TOKEN
AUTH_TOKEN=${AUTH_TOKEN:-"sk-any"}

echo "📡 Request details:"
echo "   URL: http://localhost:$SERVER_PORT/v1"
echo "   Model: gpt-5"
echo "   AUTH_TOKEN: $AUTH_TOKEN"
echo ""

# Create and run test script
echo "🔄 Executing request..."
PYTHONPATH= ./.venv/bin/python - <<PYEOF
import sys
import time
from openai import OpenAI

try:
    start_time = time.time()
    
    client = OpenAI(
        api_key="${AUTH_TOKEN}",
        base_url="http://localhost:${SERVER_PORT}/v1"
    )
    
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": "Write a haiku about code."}
        ]
    )
    
    elapsed_time = time.time() - start_time
    
    print("✅ Request successful!")
    print(f"⏱️  Response time: {elapsed_time:.2f}s")
    print("")
    print("📝 Response:")
    print("=" * 60)
    print(response.choices[0].message.content)
    print("=" * 60)
    print("")
    print(f"🔧 Model used: {response.model}")
    print(f"📊 Tokens: {response.usage.total_tokens if hasattr(response, 'usage') and response.usage else 'N/A'}")
    
except Exception as e:
    print(f"❌ Request failed: {str(e)}")
    print("")
    print("💡 Troubleshooting:")
    print("   1. Check if server is running: ps aux | grep 'python main.py'")
    print("   2. Check server logs: tail -50 server.log")
    print(f"   3. Test port: curl http://localhost:${SERVER_PORT}/v1/models")
    sys.exit(5)
PYEOF

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ Test completed successfully!"
else
    echo "❌ Test failed with exit code: $EXIT_CODE"
    exit $EXIT_CODE
fi

