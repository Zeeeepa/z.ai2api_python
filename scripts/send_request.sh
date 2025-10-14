#!/bin/bash

echo "╔════════════════════════════════════════╗"
echo "║   Z.AI2API - API Testing Suite         ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PORT=${LISTEN_PORT:-8080}
BASE_URL="http://localhost:$PORT"
BEARER_TOKEN="test-token"

echo "🎯 Target: $BASE_URL"
echo "🔑 Bearer: $BEARER_TOKEN"
echo ""

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0

# Test function
run_test() {
    local test_name=$1
    local endpoint=$2
    local method=$3
    local data=$4
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${CYAN}TEST $TOTAL_TESTS: $test_name${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $BEARER_TOKEN" \
            "$BASE_URL$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $BEARER_TOKEN" \
            -d "$data" \
            "$BASE_URL$endpoint" 2>&1)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    echo "📍 Endpoint: $method $endpoint"
    echo "📊 Status: $http_code"
    echo ""
    echo "📦 Response:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    echo ""
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
    fi
}

# Test 1: Health Check
run_test "Health Check" "/health" "GET" ""

# Test 2: List Models
run_test "List Available Models" "/v1/models" "GET" ""

# Test 3: Basic Chat Completion (Non-streaming)
run_test "Basic Chat Completion" "/v1/chat/completions" "POST" '{
  "model": "GLM-4.5",
  "messages": [
    {"role": "user", "content": "Say hello in one word"}
  ],
  "stream": false
}'

# Test 4: Chat with System Message
run_test "Chat with System Message" "/v1/chat/completions" "POST" '{
  "model": "GLM-4.5",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is 2+2?"}
  ],
  "stream": false,
  "temperature": 0.7
}'

# Test 5: Multi-turn Conversation
run_test "Multi-turn Conversation" "/v1/chat/completions" "POST" '{
  "model": "GLM-4.5",
  "messages": [
    {"role": "user", "content": "My name is Alice"},
    {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
    {"role": "user", "content": "What is my name?"}
  ],
  "stream": false
}'

# Test 6: Temperature & Max Tokens
run_test "With Temperature & Max Tokens" "/v1/chat/completions" "POST" '{
  "model": "GLM-4.5",
  "messages": [
    {"role": "user", "content": "Write a very short poem"}
  ],
  "stream": false,
  "temperature": 0.9,
  "max_tokens": 50
}'

# Test 7: Different Model (if available)
run_test "Alternative Model (GLM-4.5-Air)" "/v1/chat/completions" "POST" '{
  "model": "GLM-4.5-Air",
  "messages": [
    {"role": "user", "content": "Count to 3"}
  ],
  "stream": false
}'

# Test 8: Streaming Test (will show first chunk)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}TEST $((TOTAL_TESTS + 1)): Streaming Chat Completion${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Endpoint: POST /v1/chat/completions (stream=true)"
echo ""
echo "📦 Streaming Response (first 5 chunks):"
echo ""

curl -s -N \
    -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $BEARER_TOKEN" \
    -d '{
      "model": "GLM-4.5",
      "messages": [{"role": "user", "content": "Count from 1 to 5"}],
      "stream": true
    }' \
    "$BASE_URL/v1/chat/completions" 2>&1 | head -10

echo ""
echo ""
TOTAL_TESTS=$((TOTAL_TESTS + 1))
PASSED_TESTS=$((PASSED_TESTS + 1))
echo -e "${GREEN}✅ Streaming test completed${NC}"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"
echo ""

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ ALL TESTS PASSED! 🎉               ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  SOME TESTS FAILED                 ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
    exit 1
fi

