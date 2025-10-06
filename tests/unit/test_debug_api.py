#!/usr/bin/env python
"""
Debug script to see actual API response
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.providers.qwen_provider import QwenProvider
from app.models.schemas import OpenAIRequest, Message


async def debug_api_call():
    """Debug what the actual API returns"""
    
    # Load config
    with open("config/providers.json", "r") as f:
        config = json.load(f)
    
    qwen_config = next(
        (p for p in config["providers"] if p["name"] == "qwen"),
        None
    )
    
    # Initialize provider
    provider = QwenProvider(auth_config=qwen_config)
    
    # Create request
    request = OpenAIRequest(
        model="qwen-max",
        messages=[
            Message(role="user", content="Say hello")
        ],
        temperature=0.7,
        max_tokens=50,
        stream=False
    )
    
    print("\n" + "="*60)
    print("DEBUG: Actual API Response")
    print("="*60)
    
    # Transform request
    transformed = await provider.transform_request(request)
    
    print("\n📤 Request URL:", transformed["url"])
    print("\n📦 Request Body:")
    print(json.dumps(transformed["body"], indent=2))
    
    print("\n📋 Request Headers (sanitized):")
    headers_safe = {k: v for k, v in transformed["headers"].items() if k != "Cookie"}
    print(json.dumps(headers_safe, indent=2))
    
    # Make actual HTTP request
    import httpx
    
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            transformed["url"],
            json=transformed["body"],
            headers=transformed["headers"]
        )
        
        print(f"\n📨 Response Status: {response.status_code}")
        print(f"\n📄 Response Headers:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
        
        print(f"\n📝 Response Body (first 1000 chars):")
        body = response.text
        print(body[:1000])
        
        if len(body) > 1000:
            print(f"\n... (truncated, total length: {len(body)})")


if __name__ == "__main__":
    asyncio.run(debug_api_call())

