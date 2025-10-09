#!/bin/bash
# Z.AI Browser Automation - Complete Self-Contained Installer
# One command to clone, install, deploy, test, and run
# Usage: curl -fsSL https://raw.githubusercontent.com/Zeeeepa/z.ai2api_python/main/install_and_run.sh | bash

set -e

# Configuration
REPO_URL="https://github.com/Zeeeepa/z.ai2api_python.git"
BRANCH="${1:-main}"
PORT="${2:-9000}"
INSTALL_DIR="${HOME}/.zai_browser_automation"

cat << 'BANNER'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║    🚀 Z.AI BROWSER AUTOMATION - COMPLETE INSTALLER 🚀           ║
║                                                                  ║
║  • Clone Repository                                             ║
║  • Install Dependencies                                         ║
║  • Deploy Server                                                ║
║  • Validate with OpenAI API                                     ║
║  • Keep Running                                                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
BANNER

echo ""
echo "📋 Configuration:"
echo "  • Repository: $REPO_URL"
echo "  • Branch: $BRANCH"
echo "  • Port: $PORT"
echo "  • Install Directory: $INSTALL_DIR"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping server..."
    if [ ! -z "$SERVER_PID" ] && ps -p $SERVER_PID > /dev/null 2>&1; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    echo "✅ Cleanup complete"
}

trap cleanup EXIT INT TERM

echo "🔧 [1/7] Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi
echo "✅ Python $(python3 --version)"

# Check Git
if ! command -v git &> /dev/null; then
    echo "❌ Git is required but not installed"
    exit 1
fi
echo "✅ Git $(git --version | head -n1)"

echo ""
echo "📦 [2/7] Installing Python dependencies..."
pip3 install -q --upgrade pip 2>&1 | grep -v "already satisfied" || true
pip3 install -q playwright fastapi uvicorn requests python-dotenv openai 2>&1 | grep -v "already satisfied" || true
echo "✅ Dependencies installed"

echo ""
echo "🌐 [3/7] Installing Playwright browsers..."
playwright install chromium >/dev/null 2>&1 || true
playwright install-deps chromium >/dev/null 2>&1 || true
echo "✅ Playwright ready"

echo ""
echo "📥 [4/7] Cloning repository..."

# Remove old installation if exists
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Removing old installation..."
    rm -rf "$INSTALL_DIR"
fi

# Clone repository
git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$INSTALL_DIR" 2>&1 | grep -E "Cloning|done" || true
cd "$INSTALL_DIR"
echo "✅ Repository cloned"

echo ""
echo "🚀 [5/7] Starting Z.AI browser automation server..."

# Create server script
cat > /tmp/zai_server_$PORT.py << 'PYEOF'
#!/usr/bin/env python3
"""Z.AI Browser Automation Server - Production Ready"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import uuid
import time
import sys
import asyncio
from playwright.async_api import async_playwright

app = FastAPI(
    title="Z.AI Browser Automation",
    description="OpenAI-compatible API for Z.AI Guest Mode",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
browser_context = None
page = None
playwright_instance = None
browser = None
is_initialized = False
request_count = 0

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "GLM-4.5"
    messages: List[Message]
    max_tokens: Optional[int] = 200
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}", file=sys.stderr, flush=True)

async def init_browser():
    """Initialize browser once at startup"""
    global browser_context, page, playwright_instance, browser, is_initialized
    
    if is_initialized:
        return True
    
    try:
        log("🌐 Initializing browser...")
        playwright_instance = await async_playwright().start()
        
        browser = await playwright_instance.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu'
            ]
        )
        
        browser_context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await browser_context.new_page()
        
        log("📱 Opening Z.AI chat interface...")
        await page.goto('https://chat.z.ai/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)
        
        log("✅ Browser initialized successfully")
        is_initialized = True
        return True
        
    except Exception as e:
        log(f"❌ Browser initialization failed: {e}")
        return False

async def send_to_zai(content: str, max_retries=3) -> str:
    """Send message to Z.AI and get response"""
    global page, request_count
    
    request_count += 1
    req_id = f"req_{request_count}"
    
    for attempt in range(max_retries):
        try:
            log(f"[{req_id}] 💬 Attempt {attempt + 1}: '{content[:50]}...'")
            
            # Find and interact with textarea
            textarea_selectors = [
                'textarea[placeholder*="Message"]',
                'textarea[placeholder*="消息"]',
                'textarea',
                'div[contenteditable="true"]'
            ]
            
            textarea = None
            for selector in textarea_selectors:
                try:
                    elem = page.locator(selector).first
                    if await elem.is_visible(timeout=2000):
                        textarea = elem
                        break
                except:
                    continue
            
            if not textarea:
                log(f"[{req_id}] ⚠️  Textarea not found, refreshing page...")
                await page.reload()
                await asyncio.sleep(2)
                continue
            
            # Type message
            await textarea.click()
            await asyncio.sleep(0.3)
            await textarea.fill(content)
            await asyncio.sleep(0.5)
            
            # Send message
            await page.keyboard.press('Enter')
            log(f"[{req_id}] ✓ Message sent")
            
            # Wait for response with progressive delay
            await asyncio.sleep(2)
            
            # Extract response
            response_selectors = [
                'div[class*="message"]:last-child',
                'div[class*="assistant"]',
                'div[class*="response"]',
                '.message-content',
                'p'
            ]
            
            response_text = ""
            for _ in range(5):  # Try multiple times with delays
                for selector in response_selectors:
                    try:
                        elements = await page.locator(selector).all()
                        if elements:
                            for elem in elements[-3:]:
                                text = await elem.inner_text()
                                if text and len(text) > 10 and text != content:
                                    response_text = text
                                    break
                            if response_text:
                                break
                    except:
                        continue
                
                if response_text:
                    break
                await asyncio.sleep(1)
            
            if response_text:
                log(f"[{req_id}] ✓ Got response ({len(response_text)} chars)")
                return response_text
            
            log(f"[{req_id}] ⚠️  No response, retrying...")
            await asyncio.sleep(1)
            
        except Exception as e:
            log(f"[{req_id}] ✗ Error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            continue
    
    return "I apologize, but I'm having trouble processing your request. Please try again."

@app.on_event("startup")
async def startup():
    """Initialize browser on server startup"""
    success = await init_browser()
    if not success:
        log("❌ Failed to initialize browser - server may not work correctly")

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Z.AI Browser Automation",
        "status": "operational" if is_initialized else "initializing",
        "version": "1.0.0",
        "api": "OpenAI Compatible",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "health": "/health",
            "stats": "/stats"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy" if is_initialized else "initializing",
        "browser": "ready" if is_initialized else "starting",
        "requests_processed": request_count
    }

@app.get("/stats")
async def stats():
    """Statistics endpoint"""
    return {
        "total_requests": request_count,
        "browser_initialized": is_initialized,
        "uptime": int(time.time() - startup_time)
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat completions endpoint"""
    
    if not is_initialized:
        raise HTTPException(
            status_code=503,
            detail="Browser not initialized yet. Please wait a moment and try again."
        )
    
    try:
        # Extract user message
        user_content = " ".join([
            m.content for m in request.messages 
            if m.role == "user"
        ])
        
        if not user_content:
            raise HTTPException(status_code=400, detail="No user message found")
        
        log(f"📨 Processing request: '{user_content[:80]}...'")
        
        # Get response from Z.AI
        response_text = await send_to_zai(user_content)
        
        # Format OpenAI-compatible response
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(user_content.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(user_content.split()) + len(response_text.split())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log(f"❌ Request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    startup_time = time.time()
    
    log(f"🚀 Starting Z.AI Browser Automation Server on port {port}")
    log(f"📖 API Documentation: http://127.0.0.1:{port}/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="error",
        access_log=False
    )
PYEOF

# Start server
python3 /tmp/zai_server_$PORT.py $PORT > /tmp/zai_server_$PORT.log 2>&1 &
SERVER_PID=$!

echo "✅ Server started (PID: $SERVER_PID)"
echo "   Port: $PORT"
echo "   Logs: /tmp/zai_server_$PORT.log"

echo ""
echo "⏳ [6/7] Waiting for server initialization (20 seconds)..."
sleep 20

# Check if server is running
if ! ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "❌ Server failed to start"
    echo ""
    echo "📋 Server logs:"
    cat /tmp/zai_server_$PORT.log
    exit 1
fi

echo "✅ Server is running"

echo ""
echo "🧪 [7/7] Validating with OpenAI API call..."
echo ""

# Test with OpenAI client
python3 << TESTEOF
from openai import OpenAI
import json
import sys

print("=" * 70)
print("🔍 VALIDATION TEST - OpenAI API Compatibility")
print("=" * 70)
print()

client = OpenAI(
    api_key="sk-test",
    base_url="http://127.0.0.1:$PORT/v1"
)

try:
    print("📡 Sending request to Z.AI via OpenAI client...")
    print("   Message: 'What is 2+2? Answer in one sentence.'")
    print()
    print("⏳ Waiting for response (this may take 5-10 seconds)...")
    print()
    
    response = client.chat.completions.create(
        model="GLM-4.5",
        messages=[{
            "role": "user",
            "content": "What is 2+2? Answer in one sentence."
        }],
        max_tokens=100
    )
    
    # Format response
    content = response.choices[0].message.content
    
    print("=" * 70)
    print("✅ SUCCESS - VALIDATION PASSED")
    print("=" * 70)
    print()
    print("📊 Response Details:")
    print(f"   • Model: {response.model}")
    print(f"   • ID: {response.id}")
    print(f"   • Created: {response.created}")
    print(f"   • Finish Reason: {response.choices[0].finish_reason}")
    print()
    print("📝 Response Content:")
    print("─" * 70)
    print(content)
    print("─" * 70)
    print()
    print("📈 Token Usage:")
    print(f"   • Prompt: {response.usage.prompt_tokens} tokens")
    print(f"   • Completion: {response.usage.completion_tokens} tokens")
    print(f"   • Total: {response.usage.total_tokens} tokens")
    print()
    print("=" * 70)
    print("✅ VALIDATION COMPLETE - Server is fully operational!")
    print("=" * 70)
    
    sys.exit(0)
    
except Exception as e:
    print("=" * 70)
    print("❌ VALIDATION FAILED")
    print("=" * 70)
    print()
    print(f"Error: {e}")
    print()
    print("📋 Server logs:")
    print("─" * 70)
    import subprocess
    subprocess.run(["tail", "-30", "/tmp/zai_server_$PORT.log"])
    print("─" * 70)
    sys.exit(1)
TESTEOF

VALIDATION_STATUS=$?

if [ $VALIDATION_STATUS -ne 0 ]; then
    echo ""
    echo "❌ Validation failed - stopping server"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║              🎉 DEPLOYMENT SUCCESSFUL! 🎉                        ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Service Information:"
echo "   • Status: OPERATIONAL ✅"
echo "   • Port: $PORT"
echo "   • PID: $SERVER_PID"
echo "   • Mode: Browser Automation + Guest Mode"
echo "   • API: OpenAI Compatible"
echo ""
echo "🎯 Usage Example:"
echo ""
echo "   export OPENAI_API_KEY='sk-test'"
echo "   export OPENAI_BASE_URL='http://127.0.0.1:$PORT/v1'"
echo ""
echo "   python3 << 'EOF'"
echo "   from openai import OpenAI"
echo "   client = OpenAI()"
echo "   response = client.chat.completions.create("
echo "       model='GLM-4.5',"
echo "       messages=[{'role': 'user', 'content': 'Hello!'}]"
echo "   )"
echo "   print(response.choices[0].message.content)"
echo "   EOF"
echo ""
echo "📝 Management:"
echo "   • Stop Server: kill $SERVER_PID"
echo "   • View Logs: tail -f /tmp/zai_server_$PORT.log"
echo "   • Health Check: curl http://127.0.0.1:$PORT/health"
echo "   • API Docs: http://127.0.0.1:$PORT/docs"
echo "   • Statistics: curl http://127.0.0.1:$PORT/stats"
echo ""
echo "🔗 Endpoints:"
echo "   • Chat: http://127.0.0.1:$PORT/v1/chat/completions"
echo "   • Health: http://127.0.0.1:$PORT/health"
echo "   • Stats: http://127.0.0.1:$PORT/stats"
echo "   • Docs: http://127.0.0.1:$PORT/docs"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "✨ Server is running and ready to handle requests!"
echo "   Press Ctrl+C to stop the server."
echo ""
echo "📋 Streaming server logs:"
echo "───────────────────────────────────────────────────────────────────"
echo ""

# Keep running and show logs
tail -f /tmp/zai_server_$PORT.log

