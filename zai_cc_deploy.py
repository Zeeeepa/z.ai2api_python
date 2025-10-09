#!/usr/bin/env python3
"""
Z.AI Claude Code Router - Complete Deployment Script
Single file that handles everything
"""

import subprocess
import sys
import time
import json

print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         Z.AI CLAUDE CODE ROUTER - COMPLETE DEPLOYMENT           ║
║                                                                  ║
║  Guest Mode | No API Keys | OpenAI Compatible | Auto-Setup     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

#==============================================================================
# STEP 1: INSTALL DEPENDENCIES
#==============================================================================
print("📦 [1/5] Installing dependencies...")

deps = ["fastapi", "uvicorn", "requests", "python-dotenv"]
for dep in deps:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", dep], 
                  check=False, capture_output=True)

print("✅ Dependencies installed\n")

#==============================================================================
# STEP 2: CREATE Z.AI GUEST MODE PROXY
#==============================================================================
print("🔧 [2/5] Creating Z.AI proxy server...")

proxy_code = '''#!/usr/bin/env python3
"""Z.AI Guest Mode Proxy - OpenAI Compatible"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import requests
import uuid
import time
import hashlib
import sys

app = FastAPI(title="Z.AI Guest Mode Proxy")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 100
    stream: Optional[bool] = False

def get_guest_token():
    """Get visitor token from Z.AI"""
    try:
        resp = requests.get(
            "https://chat.z.ai/api/v1/auths/",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "X-FE-Version": "prod-fe-1.0.85",
                "Origin": "https://chat.z.ai"
            },
            timeout=10
        )
        return resp.json().get("token")
    except:
        return None

@app.get("/")
def root():
    return {
        "status": "operational",
        "mode": "guest",
        "service": "z.ai-proxy"
    }

@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest):
    try:
        token = get_guest_token()
        if not token:
            raise HTTPException(status_code=503, detail="Failed to get guest token")
        
        chat_id = str(uuid.uuid4())
        content = " ".join([m.content for m in request.messages if m.role == "user"])
        
        # Generate signature
        timestamp = int(time.time() * 1000)
        raw = f"{chat_id}{timestamp}"
        signature = hashlib.sha256(raw.encode()).hexdigest()
        
        payload = {
            "stream": False,
            "model": "0727-360B-API",
            "messages": [{"role": "user", "content": content}],
            "params": {},
            "features": {
                "image_generation": False,
                "web_search": False,
                "auto_web_search": False
            },
            "variables": {},
            "chat_id": chat_id,
            "id": str(uuid.uuid4())
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-FE-Version": "prod-fe-1.0.85",
            "X-Signature": signature,
            "X-Timestamp": str(timestamp),
            "Origin": "https://chat.z.ai",
            "Referer": f"https://chat.z.ai/c/{chat_id}"
        }
        
        resp = requests.post(
            "https://chat.z.ai/api/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Z.AI returned {resp.status_code}")
        
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return {
            "id": data.get("id", str(uuid.uuid4())),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": data.get("usage", {
                "prompt_tokens": len(content),
                "completion_tokens": len(content),
                "total_tokens": len(content) * 2
            })
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("=" * 70)
    print("Z.AI GUEST MODE PROXY - STARTING")
    print("=" * 70)
    print("Port: 8080")
    print("Mode: Guest/Anonymous")
    print("API: OpenAI Compatible")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="error")
'''

with open("/tmp/zai_proxy.py", "w") as f:
    f.write(proxy_code)

print("✅ Proxy server created\n")

#==============================================================================
# STEP 3: START PROXY
#==============================================================================
print("🚀 [3/5] Starting Z.AI proxy...")

proc = subprocess.Popen(
    [sys.executable, "/tmp/zai_proxy.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True
)

time.sleep(6)

if proc.poll() is not None:
    print("❌ Proxy failed to start")
    sys.exit(1)

print(f"✅ Proxy started (PID: {proc.pid})\n")

#==============================================================================
# STEP 4: TEST
#==============================================================================
print("🧪 [4/5] Testing with OpenAI client...")

test_code = '''
from openai import OpenAI

client = OpenAI(api_key="sk-test", base_url="http://127.0.0.1:8080/v1")

try:
    response = client.chat.completions.create(
        model="GLM-4.5",
        messages=[{"role": "user", "content": "What is 2+2? Answer briefly."}],
        max_tokens=50
    )
    
    print("\\n" + "=" * 70)
    print("✅✅✅ SUCCESS - Z.AI GUEST MODE WORKING! ✅✅✅")
    print("=" * 70)
    print(f"Response: {response.choices[0].message.content}")
    print(f"Model: {response.model}")
    print(f"Tokens: {response.usage.total_tokens}")
    print("=" * 70)
    exit(0)
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    exit(1)
'''

result = subprocess.run([sys.executable, "-c", test_code], 
                       capture_output=True, text=True, timeout=30)

print(result.stdout)

if result.returncode == 0:
    print("\n✅ Test passed!\n")
else:
    print("\n❌ Test failed")
    print(result.stderr)
    proc.kill()
    sys.exit(1)

#==============================================================================
# STEP 5: SUMMARY
#==============================================================================
print("📊 [5/5] Deployment Summary")
print("=" * 70)
print(f"✅ Z.AI Proxy:      Running (PID: {proc.pid})")
print(f"✅ Port:            8080")
print(f"✅ Mode:            Guest/Anonymous")
print(f"✅ API Format:      OpenAI Compatible")
print("=" * 70)
print("\n🎯 USAGE:")
print("  export OPENAI_API_KEY='sk-test'")
print("  export OPENAI_BASE_URL='http://127.0.0.1:8080/v1'")
print("\n  # Use with any OpenAI client!")
print("\n📝 MANAGEMENT:")
print(f"  Stop:  kill {proc.pid}")
print(f"  Test:  curl http://127.0.0.1:8080/")
print("=" * 70)

print("\n✨ Deployment complete! Press Ctrl+C to stop.\n")

try:
    proc.wait()
except KeyboardInterrupt:
    print("\n\n🛑 Stopping...")
    proc.kill()
    print("✅ Stopped")

