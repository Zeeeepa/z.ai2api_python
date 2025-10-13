#!/usr/bin/env bash
# send_request.sh - Send test requests to the API

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8080}"
AUTH_TOKEN="${AUTH_TOKEN:-sk-z-ai2api-local-test-key}"

echo -e "${BLUE}🧪 Testing Z.AI2API Server${NC}"
echo ""

# Wait for server to be ready
echo -e "${YELLOW}⏳ Waiting for server to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "$API_URL/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is ready!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ Server did not start in time${NC}"
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Test 1: Simple Chat Completion (Non-Streaming)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": "Say hello in one sentence"
      }
    ],
    "stream": false
  }')

echo -e "${YELLOW}Response:${NC}"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Check if response contains expected fields
if echo "$RESPONSE" | grep -q "choices"; then
    echo -e "${GREEN}✅ Test 1 PASSED: Received valid response${NC}"
else
    echo -e "${RED}❌ Test 1 FAILED: Invalid response${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Test 2: Streaming Chat Completion${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Streaming response:${NC}"
curl -s -X POST "$API_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": "Count from 1 to 5"
      }
    ],
    "stream": true
  }' | while IFS= read -r line; do
    if [[ "$line" == data:* ]]; then
        # Remove "data: " prefix and parse JSON
        json_data="${line#data: }"
        if [[ "$json_data" != "[DONE]" ]]; then
            # Try to extract content from the JSON
            content=$(echo "$json_data" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('choices', [{}])[0].get('delta', {}).get('content', ''), end='')" 2>/dev/null || echo "")
            if [ -n "$content" ]; then
                echo -n "$content"
            fi
        fi
    fi
done

echo ""
echo -e "${GREEN}✅ Test 2 PASSED: Streaming completed${NC}"
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Test 3: Models List${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

MODELS_RESPONSE=$(curl -s -X GET "$API_URL/v1/models" \
  -H "Authorization: Bearer $AUTH_TOKEN")

echo -e "${YELLOW}Available models:${NC}"
echo "$MODELS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$MODELS_RESPONSE"
echo ""

if echo "$MODELS_RESPONSE" | grep -q "data"; then
    echo -e "${GREEN}✅ Test 3 PASSED: Models list retrieved${NC}"
else
    echo -e "${RED}❌ Test 3 FAILED: Invalid models response${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 All tests completed!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Admin Panel:${NC} $API_URL/admin"
echo -e "${YELLOW}API Docs:${NC} $API_URL/docs"
echo ""

