#!/usr/bin/env python3
"""
Direct Z.AI API test to debug 400 error
"""

import requests
import json

# Get guest token
BASE = "https://chat.z.ai"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Edge";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Origin": BASE,
}

print("1. Getting guest token...")
r = requests.get(f"{BASE}/api/v1/auths/", headers=headers, timeout=10)
print(f"Status: {r.status_code}")
auth_data = r.json()
token = auth_data.get("token")
print(f"Token: {token[:30]}...")

# Make chat request
chat_id = "test-chat-123"
headers["Authorization"] = f"Bearer {token}"
headers["Referer"] = f"{BASE}/c/{chat_id}"
headers["Content-Type"] = "application/json"

# Try with different request formats
test_bodies = [
    # Format 1: Minimal (like working implementation)
    {
        "stream": True,
        "chat_id": chat_id,
        "id": "msg-test-123",
        "model": "GLM-4.5",
        "messages": [{"role": "user", "content": "Hello"}],
        "features": {"enable_thinking": True}
    },
    # Format 2: Model ID instead
    {
        "stream": True,
        "chat_id": chat_id,
        "id": "msg-test-456",
        "model": "0727-360B-API",  # Actual upstream model ID
        "messages": [{"role": "user", "content": "Hello"}],
        "features": {"enable_thinking": True}
    },
]

for i, body in enumerate(test_bodies, 1):
    print(f"\n\n{'='*60}")
    print(f"TEST {i}: Model = {body['model']}")
    print(f"{'='*60}")
    print(f"Request body:\n{json.dumps(body, indent=2)}")
    
    try:
        r = requests.post(
            f"{BASE}/api/chat/completions",
            json=body,
            headers=headers,
            stream=True,
            timeout=10
        )
        
        print(f"\nStatus: {r.status_code}")
        print(f"Headers: {dict(r.headers)}")
        
        if r.status_code == 200:
            print("\n✅ SUCCESS! First few lines:")
            for i, line in enumerate(r.iter_lines()):
                if i > 5:
                    break
                print(line.decode('utf-8', 'ignore'))
        else:
            print(f"\n❌ FAILED!")
            print(f"Response text:\n{r.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

print("\n\n" + "="*60)
print("DONE")
print("="*60)

