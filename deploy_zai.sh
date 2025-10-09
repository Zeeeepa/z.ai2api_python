#!/bin/bash
# Z.AI Guest Mode Proxy - Single Command Deployment
# Usage: bash deploy_zai.sh

set -e

cat << 'BANNER'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         🚀 Z.AI GUEST MODE PROXY - AUTO DEPLOYMENT 🚀           ║
║                                                                  ║
║  • No API Keys Required                                         ║
║  • OpenAI Compatible                                            ║
║  • Auto-Fix & Retry Until Working                              ║
║  • Single Command Setup                                         ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
BANNER

PORT="${1:-8080}"
MAX_RETRIES=5
RETRY_COUNT=0

echo ""
echo "📦 [1/6] Installing dependencies..."
pip3 install -q requests fastapi uvicorn python-dotenv 2>&1 | grep -v "already satisfied" || true
echo "✅ Dependencies installed"

echo ""
echo "🔧 [2/6] Creating Z.AI proxy server..."

cat > /tmp/zai_guest_proxy.py << 'PYEOF'
#!/usr/bin/env python3
"""Z.AI Guest Mode Proxy - Working Version"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import requests
import uuid
import time
import hashlib
import json
import sys

app = FastAPI(title="Z.AI Guest Proxy")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "GLM-4.5"
    messages: List[Message]
    max_tokens: Optional[int] = 100
    stream: Optional[bool] = False

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)

def get_token():
    """Get guest token - try multiple methods"""
    methods = [
        # Method 1: Direct auth endpoint
        {
            "url": "https://chat.z.ai/api/v1/auths/",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Origin": "https://chat.z.ai",
                "Referer": "https://chat.z.ai/",
            }
        },
        # Method 2: With more headers
        {
            "url": "https://chat.z.ai/api/v1/auths/",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://chat.z.ai",
                "Referer": "https://chat.z.ai/",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
        },
    ]
    
    for i, method in enumerate(methods, 1):
        try:
            log(f"Trying token method {i}...")
            resp = requests.get(method["url"], headers=method["headers"], timeout=10)
            if resp.status_code == 200:
                token = resp.json().get("token")
                if token:
                    log(f"✓ Token acquired via method {i}")
                    return token
        except Exception as e:
            log(f"✗ Method {i} failed: {e}")
            continue
    
    return None

@app.get("/")
def root():
    return {"status": "operational", "mode": "guest", "service": "z.ai-proxy"}

@app.get("/health")
def health():
    try:
        token = get_token()
        return {"status": "healthy" if token else "degraded", "token_available": bool(token)}
    except:
        return {"status": "unhealthy"}

@app.post("/v1/chat/completions")
def chat(request: ChatRequest):
    try:
        # Get token
        token = get_token()
        if not token:
            raise HTTPException(status_code=503, detail="Could not acquire guest token")
        
        # Prepare request
        chat_id = str(uuid.uuid4())
        msg_id = str(uuid.uuid4())
        content = " ".join([m.content for m in request.messages if m.role == "user"])
        
        # Try multiple API approaches
        attempts = [
            # Attempt 1: No signature (sometimes works)
            {
                "url": "https://chat.z.ai/api/chat/completions",
                "headers": {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Origin": "https://chat.z.ai",
                    "Referer": f"https://chat.z.ai/c/{chat_id}",
                },
                "use_signature": False
            },
            # Attempt 2: With signature
            {
                "url": "https://chat.z.ai/api/chat/completions",
                "headers": {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "X-FE-Version": "prod-fe-1.0.85",
                    "Origin": "https://chat.z.ai",
                    "Referer": f"https://chat.z.ai/c/{chat_id}",
                },
                "use_signature": True
            },
        ]
        
        for i, attempt in enumerate(attempts, 1):
            try:
                log(f"API attempt {i}...")
                
                headers = attempt["headers"].copy()
                
                # Add signature if needed
                if attempt["use_signature"]:
                    timestamp = int(time.time() * 1000)
                    raw = f"{chat_id}{timestamp}"
                    signature = hashlib.sha256(raw.encode()).hexdigest()
                    headers["X-Signature"] = signature
                    headers["X-Timestamp"] = str(timestamp)
                
                payload = {
                    "stream": False,
                    "model": "0727-360B-API",
                    "messages": [{"role": "user", "content": content}],
                    "params": {},
                    "features": {
                        "image_generation": False,
                        "web_search": False,
                        "auto_web_search": False,
                        "preview_mode": False,
                    },
                    "variables": {},
                    "chat_id": chat_id,
                    "id": msg_id
                }
                
                resp = requests.post(
                    attempt["url"],
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                log(f"Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    content_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    if content_text:
                        log(f"✓ Success with attempt {i}")
                        return {
                            "id": data.get("id", msg_id),
                            "object": "chat.completion",
                            "created": int(time.time()),
                            "model": request.model,
                            "choices": [{
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": content_text
                                },
                                "finish_reason": "stop"
                            }],
                            "usage": data.get("usage", {
                                "prompt_tokens": len(content),
                                "completion_tokens": len(content_text),
                                "total_tokens": len(content) + len(content_text)
                            })
                        }
                
                log(f"✗ Attempt {i} failed: {resp.text[:200]}")
                
            except Exception as e:
                log(f"✗ Attempt {i} error: {e}")
                continue
        
        # All attempts failed
        raise HTTPException(status_code=502, detail="All API attempts failed")
        
    except HTTPException:
        raise
    except Exception as e:
        log(f"✗ Fatal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    log(f"Starting Z.AI Guest Proxy on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")
PYEOF

chmod +x /tmp/zai_guest_proxy.py
echo "✅ Proxy created"

echo ""
echo "🚀 [3/6] Starting proxy server on port $PORT..."

# Kill any existing process on port
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
sleep 1

# Start server
python3 /tmp/zai_guest_proxy.py $PORT > /tmp/zai_proxy.log 2>&1 &
SERVER_PID=$!

echo "✅ Server started (PID: $SERVER_PID)"

echo ""
echo "⏳ [4/6] Waiting for server to initialize..."
sleep 5

# Check if server is running
if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Server failed to start"
    cat /tmp/zai_proxy.log
    exit 1
fi

echo "✅ Server is running"

echo ""
echo "🧪 [5/6] Testing with OpenAI client (will retry until working)..."

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "🔄 Test Attempt $((RETRY_COUNT + 1))/$MAX_RETRIES"
    echo "═══════════════════════════════════════════════════════════════════"
    
    python3 << 'TESTEOF'
from openai import OpenAI
import sys

client = OpenAI(api_key="sk-test", base_url="http://127.0.0.1:8080/v1")

try:
    print("📡 Sending request to Z.AI proxy...")
    
    response = client.chat.completions.create(
        model="GLM-4.5",
        messages=[{"role": "user", "content": "What is 2+2? Answer in one short sentence."}],
        max_tokens=50
    )
    
    content = response.choices[0].message.content
    
    if content and len(content) > 0:
        print("\n" + "=" * 70)
        print("✅✅✅ SUCCESS - Z.AI GUEST MODE WORKING! ✅✅✅")
        print("=" * 70)
        print(f"📝 Response: {content}")
        print(f"🎯 Model: {response.model}")
        print(f"📊 Tokens: {response.usage.total_tokens}")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ Empty response")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
TESTEOF

    TEST_RESULT=$?
    
    if [ $TEST_RESULT -eq 0 ]; then
        echo ""
        echo "✅ Test passed!"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "⚠️  Test failed, retrying in 3 seconds..."
            echo "📋 Server logs:"
            tail -10 /tmp/zai_proxy.log
            sleep 3
        fi
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo ""
    echo "❌ All test attempts failed"
    echo ""
    echo "📋 Full server logs:"
    cat /tmp/zai_proxy.log
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo ""
echo "📊 [6/6] Deployment Summary"
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ Server:       Running (PID: $SERVER_PID)"
echo "✅ Port:         $PORT"
echo "✅ Mode:         Guest/Anonymous"
echo "✅ API:          OpenAI Compatible"
echo "✅ Status:       OPERATIONAL"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 USAGE:"
echo "  export OPENAI_API_KEY='sk-test'"
echo "  export OPENAI_BASE_URL='http://127.0.0.1:$PORT/v1'"
echo ""
echo "  # Test:"
echo "  curl http://127.0.0.1:$PORT/health"
echo ""
echo "📝 MANAGEMENT:"
echo "  Stop:     kill $SERVER_PID"
echo "  Logs:     tail -f /tmp/zai_proxy.log"
echo "  Restart:  bash $0"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "✨ Server is running! Press Ctrl+C to stop, or close terminal to keep running."
echo ""

# Keep running
trap "echo ''; echo '🛑 Stopping server...'; kill $SERVER_PID 2>/dev/null; echo '✅ Stopped'; exit 0" INT TERM

tail -f /tmp/zai_proxy.log

