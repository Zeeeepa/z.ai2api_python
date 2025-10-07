#!/usr/bin/env python
"""
Quick Test - Messages All 43 Models
Simplest possible script - just run it!
"""

import asyncio
import sys

try:
    import httpx
except ImportError:
    print("❌ Please install httpx: pip install httpx")
    sys.exit(1)

# All 43 models
MODELS = {
    "Z.AI": ["GLM-4.5", "GLM-4.5-Thinking", "GLM-4.5-Search", "GLM-4.5-Air", 
             "GLM-4.6", "GLM-4.6-Thinking", "GLM-4.6-Search"],
    "K2Think": ["MBZUAI-IFM/K2-Think"],
    "Qwen": ["qwen-max", "qwen-max-thinking", "qwen-max-search", "qwen-max-image",
             "qwen-max-image_edit", "qwen-max-video", "qwen-max-deep-research",
             "qwen-plus", "qwen-plus-thinking", "qwen-plus-search", "qwen-plus-image",
             "qwen-plus-image_edit", "qwen-plus-video", "qwen-plus-deep-research",
             "qwen-turbo", "qwen-turbo-thinking", "qwen-turbo-search", "qwen-turbo-image",
             "qwen-turbo-image_edit", "qwen-turbo-video", "qwen-turbo-deep-research",
             "qwen-long", "qwen-long-thinking", "qwen-long-search", "qwen-long-image",
             "qwen-long-image_edit", "qwen-long-video", "qwen-long-deep-research",
             "qwen-max-latest", "qwen-max-0428", "qwen-plus-latest", "qwen-turbo-latest",
             "qwen-deep-research", "qwen3-coder-plus", "qwen-coder-plus"]
}

async def test_model(client, model, idx):
    """Test one model"""
    try:
        resp = await client.post(
            "http://localhost:8080/v1/chat/completions",
            json={"model": model, "messages": [{"role": "user", "content": "Hello! What model are you?"}], 
                  "stream": False, "max_tokens": 100},
            timeout=60.0
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            print(f"✅ {idx:2d}. {model:45} → {content[:80]}...")
            return True
        else:
            print(f"❌ {idx:2d}. {model:45} → HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ {idx:2d}. {model:45} → {str(e)[:60]}")
        return False

async def main():
    """Test all models"""
    print(f"\n{'='*100}")
    print(f"{'🚀 TESTING ALL 43 MODELS'.center(100)}")
    print(f"{'='*100}\n")
    
    async with httpx.AsyncClient() as client:
        idx = 1
        tasks = []
        for provider, models in MODELS.items():
            print(f"\n📦 {provider} ({len(models)} models):\n")
            for model in models:
                tasks.append(test_model(client, model, idx))
                idx += 1
        
        print(f"\n⏳ Running {len(tasks)} concurrent requests...\n")
        results = await asyncio.gather(*tasks)
    
    success = sum(results)
    print(f"\n{'='*100}")
    print(f"✅ Success: {success}/{len(results)} ({success/len(results)*100:.1f}%)")
    print(f"{'='*100}\n")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════════════╗
║  Quick Test - Messages All 43 Models                                              ║
║                                                                                    ║
║  Requirements:                                                                     ║
║    • Server running: python main.py                                                ║
║    • httpx installed: pip install httpx                                            ║
╚════════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

