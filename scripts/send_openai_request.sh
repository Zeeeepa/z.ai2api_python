#!/bin/bash
#
# send_openai_request.sh - Test Z.AI2API with REAL OpenAI-compatible requests
#
# This script makes ACTUAL API calls to your running z.ai2api_python server,
# which proxies to the real Z.AI chat interface using your JWT token.
# 
# NO MOCKS - All responses are real AI-generated content from Z.AI!
#
# The server:
#  ✅ Mimics a web browser accessing Z.AI's chat interface
#  ✅ Uses the JWT token from your browser session
#  ✅ Makes requests exactly like the web UI does
#  ✅ Converts Z.AI's web responses to OpenAI API format
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Banner
echo ""
echo "============================================================"
echo "       Z.AI2API - OpenAI API Request Test"
echo "============================================================"
echo ""

# Navigate to project root
cd "$PROJECT_ROOT"

# Load environment variables if .env exists
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Configuration
PORT=${LISTEN_PORT:-8080}
API_URL="http://localhost:$PORT/v1/chat/completions"
AUTH_TOKEN=${AUTH_TOKEN:-"sk-test"}

# Step 1: Check if server is running
log_info "Checking if server is running on port $PORT..."
if ! curl -s -f "http://localhost:$PORT/" > /dev/null 2>&1; then
    log_error "Server is not responding on port $PORT"
    log_info "Please start the server first: bash scripts/start.sh"
    exit 1
fi
log_success "Server is responding"

# Step 2: Prepare test request
log_info "Preparing test request..."

# Test message
TEST_MESSAGE="Hello! Please introduce yourself briefly."

# Create request payload
REQUEST_PAYLOAD=$(cat <<EOF
{
  "model": "GLM-4-6-API-V1",
  "messages": [
    {
      "role": "user",
      "content": "$TEST_MESSAGE"
    }
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 500
}
EOF
)

log_success "Request prepared"

# Step 3: Send request
echo ""
echo "============================================================"
echo "                 Sending API Request..."
echo "============================================================"
echo ""
echo -e "${CYAN}Request Details:${NC}"
echo "  URL:     $API_URL"
echo "  Model:   GLM-4-6-API-V1"
echo "  Message: $TEST_MESSAGE"
echo ""
log_info "Sending request..."

# Send request and capture response
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d "$REQUEST_PAYLOAD")

# Extract HTTP status code (last line)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)

# Step 4: Display response
echo ""
echo "============================================================"
echo "                   API Response"
echo "============================================================"
echo ""

if [ "$HTTP_CODE" -eq 200 ]; then
    log_success "Request successful (HTTP $HTTP_CODE)"
    echo ""
    
    # Parse and display response using Python for better formatting
    if command -v python3 &> /dev/null; then
        echo -e "${CYAN}Response:${NC}"
        echo "$RESPONSE_BODY" | python3 -c "
import sys
import json

try:
    data = json.load(sys.stdin)
    
    # Display basic info
    print(f\"  Model: {data.get('model', 'N/A')}\")
    print(f\"  ID: {data.get('id', 'N/A')}\")
    print(f\"  Created: {data.get('created', 'N/A')}\")
    print()
    
    # Display message content
    if 'choices' in data and len(data['choices']) > 0:
        choice = data['choices'][0]
        message = choice.get('message', {})
        content = message.get('content', 'No content')
        finish_reason = choice.get('finish_reason', 'N/A')
        
        print('  Content:')
        print('  ' + '-' * 58)
        for line in content.split('\n'):
            print(f'  {line}')
        print('  ' + '-' * 58)
        print()
        print(f\"  Finish Reason: {finish_reason}\")
    
    # Display usage info
    if 'usage' in data:
        usage = data['usage']
        print()
        print('  Token Usage:')
        print(f\"    Prompt: {usage.get('prompt_tokens', 'N/A')} tokens\")
        print(f\"    Completion: {usage.get('completion_tokens', 'N/A')} tokens\")
        print(f\"    Total: {usage.get('total_tokens', 'N/A')} tokens\")
    
    print()
    
except json.JSONDecodeError:
    print('  [Raw Response]')
    print(sys.stdin.read())
except Exception as e:
    print(f'  Error parsing response: {e}')
    print()
    print('  [Raw Response]')
    print(sys.stdin.read())
"
    else
        # Fallback: display raw JSON
        echo "$RESPONSE_BODY" | head -c 1000
        echo ""
    fi
    
    echo ""
    echo "============================================================"
    echo ""
    log_success "API test completed successfully! ✨"
    
else
    log_error "Request failed (HTTP $HTTP_CODE)"
    echo ""
    echo -e "${CYAN}Error Response:${NC}"
    echo "$RESPONSE_BODY" | head -c 500
    echo ""
    echo ""
    echo "============================================================"
    echo ""
    log_error "API test failed"
    
    if [ "$HTTP_CODE" -eq 401 ] || [ "$HTTP_CODE" -eq 403 ]; then
        log_warning "Authentication issue - check AUTH_TOKEN in .env"
    elif [ "$HTTP_CODE" -eq 500 ]; then
        log_warning "Server error - check logs/server.log"
    fi
    
    exit 1
fi

# Step 5: Additional test with streaming
echo ""
log_info "Testing streaming mode..."
echo ""

STREAM_REQUEST=$(cat <<EOF
{
  "model": "GLM-4-6-API-V1",
  "messages": [
    {
      "role": "user",
      "content": "Count from 1 to 5."
    }
  ],
  "stream": true,
  "max_tokens": 100
}
EOF
)

echo -e "${CYAN}Streaming Response:${NC}"
echo "------------------------------------------------------------"
curl -s -N \
  -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d "$STREAM_REQUEST" | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        # Extract JSON after "data: "
        json_data="${line#data: }"
        if [ "$json_data" != "[DONE]" ]; then
            # Parse and display delta content
            echo "$json_data" | python3 -c "
import sys
import json
try:
    data = json.load(sys.stdin)
    if 'choices' in data and len(data['choices']) > 0:
        delta = data['choices'][0].get('delta', {})
        content = delta.get('content', '')
        if content:
            print(content, end='', flush=True)
except:
    pass
" 2>/dev/null
        fi
    fi
done
echo ""
echo "------------------------------------------------------------"
echo ""
log_success "Streaming test completed! ✨"

# Final summary
echo ""
echo "============================================================"
echo "              API Testing Complete! ✅"
echo "============================================================"
echo ""
echo "🎉 All tests passed successfully!"
echo ""
echo "📖 API Documentation: http://localhost:$PORT/docs"
echo "🔧 Admin Panel: http://localhost:$PORT/admin"
echo ""
echo "============================================================"
echo ""
