#!/usr/bin/env python3
"""
Get list of Z.AI models
"""

import requests
import json

BASE = "https://chat.z.ai"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "X-FE-Version": "prod-fe-1.0.79",
    "Origin": BASE,
}

print("Getting guest token...")
r = requests.get(f"{BASE}/api/v1/auths/", headers=headers, timeout=10)
token = r.json().get("token")
print(f"Token: {token[:30]}...")

headers["Authorization"] = f"Bearer {token}"

print("\nFetching models list...")
r = requests.get(f"{BASE}/api/models", headers=headers, timeout=10)

models_data = r.json()
print(f"\nTotal models: {len(models_data.get('data', []))}")

print("\n" + "="*80)
print("AVAILABLE MODELS:")
print("="*80)

for model in models_data.get("data", []):
    model_id = model.get("id", "")
    model_name = model.get("name", "")
    is_active = model.get("info", {}).get("is_active", True)
    
    if is_active and model_id.startswith(("GLM", "Z")):
        print(f"\n📌 Model ID: {model_id}")
        print(f"   Name: {model_name}")
        print(f"   Active: {is_active}")
        
        # Show full model info
        print(f"   Full info: {json.dumps(model, indent=4)[:500]}...")

