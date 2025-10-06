#!/usr/bin/env python3
"""
Direct Z.AI API test with X-FE-Version header
"""

import requests
import json

# Get guest token
BASE = "https://chat.z.ai"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "X-FE-Version": "prod-fe-1.0.79",  # ADD THIS!
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

body = {
    "stream": True,
    "chat_id": chat_id,
    "id": "msg-test-123",
    "model": "GLM-4.5",
    "messages": [{"role": "user", "content": "Say 'Hello World'"}],
    "features": {"enable_thinking": False}
}

print(f"\n{'='*60}")
print(f"Request with X-FE-Version header")
print(f"{'='*60}")
print(f"Headers: {json.dumps({k: v for k, v in headers.items() if 'token' not in k.lower()}, indent=2)}")
print(f"\nRequest body:\n{json.dumps(body, indent=2)}")

try:
    r = requests.post(
        f"{BASE}/api/chat/completions",
        json=body,
        headers=headers,
        stream=True,
        timeout=10
    )
    
    print(f"\nStatus: {r.status_code}")
    
    if r.status_code == 200:
        print("\n✅ SUCCESS! Response:")
        for i, line in enumerate(r.iter_lines()):
            if i > 10:
                break
            decoded = line.decode('utf-8', 'ignore')
            if decoded:
                print(decoded)
    else:
        print(f"\n❌ FAILED!")
        print(f"Response text:\n{r.text[:500]}")
        
except Exception as e:
    print(f"❌ Exception: {e}")

