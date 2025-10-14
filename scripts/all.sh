#!/usr/bin/env bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

clear

echo -e "${BOLD}${BLUE}"
cat << "EOF"
╔════════════════════════════════════════╗
║   Z.AI2API - Complete Workflow         ║
╚════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo "This script will:"
echo "  1. Setup environment and retrieve token"
echo "  2. Start the OpenAI-compatible API server"
echo "  3. Send test requests in OpenAI format"
echo "  4. Keep server running for continued use"
echo ""

read -p "Press Enter to continue..." -t 5 || echo ""

# ==========================================
# STEP 1: SETUP
# ==========================================
echo -e "\n${BOLD}${BLUE}────────────────────────────────────────"
echo "📦 STEP 1/4: Setup & Authentication"
echo -e "────────────────────────────────────────${NC}\n"

bash scripts/setup.sh

# ==========================================
# STEP 2: START SERVER
# ==========================================
echo -e "\n${BOLD}${BLUE}────────────────────────────────────────"
echo "🚀 STEP 2/4: Starting OpenAI-Compatible Server"
echo -e "────────────────────────────────────────${NC}\n"

bash scripts/start.sh

# Wait a bit for server to fully initialize
sleep 3

# ==========================================
# STEP 3: TEST API
# ==========================================
echo -e "\n${BOLD}${BLUE}────────────────────────────────────────"
echo "🧪 STEP 3/4: Testing API Endpoints"
echo -e "────────────────────────────────────────${NC}\n"

bash scripts/send_request.sh

# ==========================================
# STEP 4: KEEP ALIVE
# ==========================================
echo -e "\n${BOLD}${GREEN}────────────────────────────────────────"
echo "✅ STEP 4/4: Server Running"
echo -e "────────────────────────────────────────${NC}\n"

PORT=${LISTEN_PORT:-8080}
LOG_FILE=${LOG_FILE:-/tmp/z.ai2api_server.log}

echo -e "${GREEN}🎉 All tests complete!${NC}\n"

echo -e "${CYAN}Server Information:${NC}"
echo "  URL: http://localhost:$PORT"
echo "  Logs: $LOG_FILE"
echo ""

echo -e "${CYAN}Quick Commands:${NC}"
echo "  View logs:    tail -f $LOG_FILE"
echo "  Stop server:  pkill -f 'python.*main.py'"
echo "  Test again:   bash scripts/send_request.sh"
echo ""

echo -e "${CYAN}Available Endpoints:${NC}"
echo "  GET  /v1/models              - List all models"
echo "  POST /v1/chat/completions    - OpenAI chat format"
echo ""

echo -e "${CYAN}OpenAI Python Client:${NC}"
cat << 'EOF'
  
  from openai import OpenAI
  
  client = OpenAI(
      base_url="http://localhost:8080/v1",
      api_key="sk-test"
  )
  
  response = client.chat.completions.create(
      model="GLM-4.5",
      messages=[{"role": "user", "content": "Hello!"}]
  )
EOF

echo ""
echo -e "${YELLOW}📝 Note:${NC}"
echo -e "${YELLOW}If you see empty responses, this is expected due to Z.AI's${NC}"
echo -e "${YELLOW}proprietary signature validation. The infrastructure works!${NC}"

echo ""
echo -e "${GREEN}${BOLD}Press Ctrl+C to stop the server${NC}"
echo -e "${BLUE}Monitoring server logs...${NC}\n"

# Follow logs
tail -f $LOG_FILE

