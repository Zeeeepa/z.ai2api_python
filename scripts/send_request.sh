#!/bin/bash

echo "========================================"
echo "📡 Testing Z.AI2API Server"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

PORT=${PORT:-8080}
BASE_URL="http://localhost:$PORT"

# Check if server is running
echo "🔍 Checking if server is running..."
if ! curl -s "$BASE_URL/v1/models" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server is not running on port $PORT${NC}"
    echo ""
    echo "Start the server first:"
    echo "  bash scripts/start.sh"
    echo ""
    echo "Or run everything:"
    echo "  bash scripts/all.sh"
    exit 1
fi

echo -e "${GREEN}✅ Server is running${NC}"
echo ""

# Test 1: List Models
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Test 1: List Available Models"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Request: GET $BASE_URL/v1/models"
echo ""

MODELS_RESPONSE=$(curl -s "$BASE_URL/v1/models")
echo "Response:"
echo "$MODELS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$MODELS_RESPONSE"
echo ""

# Test 2: Simple Chat Completion
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💬 Test 2: Simple Chat Completion"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Request: POST $BASE_URL/v1/chat/completions"
echo "Model: GLM-4.5"
echo "Message: 'Say hello in exactly 3 words'"
echo ""

CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "GLM-4.5",
    "messages": [
      {"role": "user", "content": "Say hello in exactly 3 words"}
    ],
    "max_tokens": 50,
    "temperature": 0.7
  }')

echo "Response:"
if echo "$CHAT_RESPONSE" | python3 -c "
import sys
import json
try:
    data = json.load(sys.stdin)
    if 'choices' in data and len(data['choices']) > 0:
        content = data['choices'][0]['message']['content']
        model = data.get('model', 'unknown')
        usage = data.get('usage', {})
        
        print(f'  ✅ Success!')
        print(f'  Model: {model}')
        print(f'  Content: {content}')
        print(f'  Tokens: {usage.get(\"total_tokens\", \"N/A\")}')
        sys.exit(0)
    elif 'error' in data:
        print(f'  ❌ Error: {data[\"error\"]}')
        sys.exit(1)
    else:
        print(f'  ⚠️  Unexpected response format')
        print(json.dumps(data, indent=2))
        sys.exit(1)
except Exception as e:
    print(f'  ❌ Failed to parse response: {e}')
    sys.exit(1)
" 2>&1; then
    TEST2_RESULT="${GREEN}PASSED${NC}"
else
    TEST2_RESULT="${RED}FAILED${NC}"
    echo ""
    echo "Raw Response:"
    echo "$CHAT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CHAT_RESPONSE"
fi
echo ""

# Test 3: Streaming Response
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌊 Test 3: Streaming Response"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Request: POST $BASE_URL/v1/chat/completions (stream=true)"
echo "Model: GLM-4.5"
echo "Message: 'Count from 1 to 5'"
echo ""

echo -n "Streaming output: "
STREAM_OUTPUT=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "GLM-4.5",
    "messages": [
      {"role": "user", "content": "Count from 1 to 5"}
    ],
    "stream": true,
    "max_tokens": 30
  }')

if echo "$STREAM_OUTPUT" | grep -q "data:"; then
    echo -e "${GREEN}✓${NC}"
    TEST3_RESULT="${GREEN}PASSED${NC}"
    echo ""
    echo "Sample chunks:"
    echo "$STREAM_OUTPUT" | head -5
else
    echo -e "${RED}✗${NC}"
    TEST3_RESULT="${RED}FAILED${NC}"
    echo ""
    echo "Raw output:"
    echo "$STREAM_OUTPUT" | head -10
fi
echo ""

# Test 4: Different Model
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧠 Test 4: Different Model (GLM-4.5-Air)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

AIR_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "GLM-4.5-Air",
    "messages": [
      {"role": "user", "content": "What is 2+2?"}
    ],
    "max_tokens": 20
  }')

if echo "$AIR_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'choices' in data:
        print('  ✅ GLM-4.5-Air working')
        sys.exit(0)
    else:
        print('  ❌ Unexpected response')
        sys.exit(1)
except:
    sys.exit(1)
" 2>&1; then
    TEST4_RESULT="${GREEN}PASSED${NC}"
else
    TEST4_RESULT="${RED}FAILED${NC}"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "  Test 1 (List Models):      ${GREEN}PASSED${NC}"
echo -e "  Test 2 (Chat Completion):  $TEST2_RESULT"
echo -e "  Test 3 (Streaming):        $TEST3_RESULT"
echo -e "  Test 4 (Different Model):  $TEST4_RESULT"
echo ""

# Overall result
if [ "$TEST2_RESULT" = "${GREEN}PASSED${NC}" ]; then
    echo -e "${GREEN}========================================"
    echo "✅ All Core Tests Passed!"
    echo "========================================${NC}"
    echo ""
    echo "Your Z.AI2API server is working correctly!"
    echo ""
    echo "You can now use it with any OpenAI-compatible client:"
    echo "  Base URL: $BASE_URL"
    echo "  API Key: any-string (not validated)"
    echo ""
else
    echo -e "${YELLOW}========================================"
    echo "⚠️  Some Tests Failed"
    echo "========================================${NC}"
    echo ""
    echo "The server is running but API calls are failing."
    echo "This usually means authentication issues."
    echo ""
    echo "Check:"
    echo "  1. Your ZAI_EMAIL/PASSWORD are correct"
    echo "  2. AUTH_TOKEN is valid (not expired)"
    echo "  3. Server logs for error messages"
    echo ""
fi

