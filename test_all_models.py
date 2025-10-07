#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Single-File All-Models Tester
Messages all 43 models with "Hello! What model are you?" and displays responses
No imports needed from project - standalone script
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any


# ========================================
# Configuration
# ========================================

BASE_URL = "http://localhost:8080/v1"
PROMPT = "Hello! What model are you? Please identify yourself briefly."
TIMEOUT = 90.0

# All models hardcoded for standalone operation
ALL_MODELS = {
    "Z.AI": [
        "GLM-4.5",
        "GLM-4.5-Thinking",
        "GLM-4.5-Search",
        "GLM-4.5-Air",
        "GLM-4.6",
        "GLM-4.6-Thinking",
        "GLM-4.6-Search",
    ],
    "K2Think": [
        "MBZUAI-IFM/K2-Think",
    ],
    "Qwen": [
        "qwen-max", "qwen-max-thinking", "qwen-max-search", "qwen-max-image",
        "qwen-max-image_edit", "qwen-max-video", "qwen-max-deep-research",
        "qwen-plus", "qwen-plus-thinking", "qwen-plus-search", "qwen-plus-image",
        "qwen-plus-image_edit", "qwen-plus-video", "qwen-plus-deep-research",
        "qwen-turbo", "qwen-turbo-thinking", "qwen-turbo-search", "qwen-turbo-image",
        "qwen-turbo-image_edit", "qwen-turbo-video", "qwen-turbo-deep-research",
        "qwen-long", "qwen-long-thinking", "qwen-long-search", "qwen-long-image",
        "qwen-long-image_edit", "qwen-long-video", "qwen-long-deep-research",
        "qwen-max-latest", "qwen-max-0428", "qwen-plus-latest", "qwen-turbo-latest",
        "qwen-deep-research", "qwen3-coder-plus", "qwen-coder-plus",
    ]
}


# ========================================
# Colors
# ========================================

class C:
    """Colors for output"""
    B = '\033[1m'      # Bold
    R = '\033[91m'     # Red
    G = '\033[92m'     # Green
    Y = '\033[93m'     # Yellow
    C = '\033[96m'     # Cyan
    M = '\033[95m'     # Magenta
    E = '\033[0m'      # End


# ========================================
# Test Single Model
# ========================================

async def test_model(client: httpx.AsyncClient, provider: str, model: str, idx: int) -> Dict[str, Any]:
    """Test a single model"""
    start = datetime.now()
    
    try:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": PROMPT}],
                "stream": False,
                "max_tokens": 150
            }
        )
        
        duration = (datetime.now() - start).total_seconds()
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "idx": idx,
                "provider": provider,
                "model": model,
                "success": True,
                "response": content,
                "duration": duration
            }
        else:
            return {
                "idx": idx,
                "provider": provider,
                "model": model,
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:100]}",
                "duration": duration
            }
    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        return {
            "idx": idx,
            "provider": provider,
            "model": model,
            "success": False,
            "error": str(e)[:150],
            "duration": duration
        }


# ========================================
# Main Test Function
# ========================================

async def main():
    """Test all models"""
    
    # Header
    print(f"\n{C.B}{C.C}{'='*100}{C.E}")
    print(f"{C.B}{C.C}{'ALL MODELS IDENTITY TEST'.center(100)}{C.E}")
    print(f"{C.B}{C.C}{'='*100}{C.E}\n")
    
    # Calculate totals
    total = sum(len(models) for models in ALL_MODELS.values())
    
    print(f"{C.B}Configuration:{C.E}")
    print(f"  • API: {C.C}{BASE_URL}{C.E}")
    print(f"  • Prompt: {C.Y}\"{PROMPT}\"{C.E}")
    print(f"  • Total Models: {C.G}{total}{C.E} across {C.G}{len(ALL_MODELS)}{C.E} providers")
    
    for provider, models in ALL_MODELS.items():
        print(f"    - {C.C}{provider}{C.E}: {C.G}{len(models)}{C.E} models")
    
    print(f"\n{C.B}Starting concurrent requests to all {total} models...{C.E}\n")
    
    # Create tasks
    start_time = datetime.now()
    tasks = []
    idx = 1
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for provider, models in ALL_MODELS.items():
            for model in models:
                tasks.append(test_model(client, provider, model, idx))
                idx += 1
        
        # Execute all
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    total_duration = (datetime.now() - start_time).total_seconds()
    
    # Group by provider
    by_provider = {}
    for result in results:
        if isinstance(result, dict):
            prov = result["provider"]
            if prov not in by_provider:
                by_provider[prov] = []
            by_provider[prov].append(result)
    
    # Display results
    print(f"\n{C.B}{C.C}{'='*100}{C.E}")
    print(f"{C.B}{C.C}{'RESULTS'.center(100)}{C.E}")
    print(f"{C.B}{C.C}{'='*100}{C.E}\n")
    
    for provider, results_list in by_provider.items():
        print(f"\n{C.B}{C.Y}┌{'─'*98}┐{C.E}")
        print(f"{C.B}{C.Y}│ {provider.upper()} - {len(results_list)} Models{' '*(88-len(provider))}│{C.E}")
        print(f"{C.B}{C.Y}└{'─'*98}┘{C.E}\n")
        
        for r in sorted(results_list, key=lambda x: x["idx"]):
            status = f"{C.G}✅{C.E}" if r["success"] else f"{C.R}❌{C.E}"
            
            print(f"{status} {C.B}#{r['idx']:2d}{C.E} {C.C}{r['model']:50}{C.E} {C.M}{r['duration']:.2f}s{C.E}")
            
            if r["success"]:
                # Show first 120 chars
                resp = r["response"].replace('\n', ' ')[:120]
                print(f"     {C.G}{resp}...{C.E}\n")
            else:
                print(f"     {C.R}Error: {r['error']}{C.E}\n")
    
    # Summary
    print(f"\n{C.B}{C.C}{'='*100}{C.E}")
    print(f"{C.B}{C.C}{'SUMMARY'.center(100)}{C.E}")
    print(f"{C.B}{C.C}{'='*100}{C.E}\n")
    
    successful = [r for r in results if isinstance(r, dict) and r["success"]]
    failed = [r for r in results if isinstance(r, dict) and not r["success"]]
    
    success_rate = len(successful) / total * 100 if total > 0 else 0
    avg_duration = sum(r["duration"] for r in successful) / len(successful) if successful else 0
    
    print(f"{C.B}Total Models:{C.E} {C.C}{total}{C.E}")
    print(f"{C.B}Successful:{C.E} {C.G}{len(successful)}{C.E}")
    print(f"{C.B}Failed:{C.E} {C.R}{len(failed)}{C.E}")
    print(f"{C.B}Success Rate:{C.E} {C.G if success_rate >= 80 else C.R}{success_rate:.1f}%{C.E}")
    print(f"{C.B}Total Duration:{C.E} {C.M}{total_duration:.2f}s{C.E}")
    print(f"{C.B}Avg Response Time:{C.E} {C.M}{avg_duration:.2f}s{C.E}")
    
    print(f"\n{C.B}Provider Breakdown:{C.E}")
    for provider, results_list in by_provider.items():
        prov_success = [r for r in results_list if r["success"]]
        prov_rate = len(prov_success) / len(results_list) * 100
        color = C.G if prov_rate >= 80 else C.Y if prov_rate >= 50 else C.R
        
        print(f"  • {C.C}{provider:12}{C.E}: {color}{len(prov_success):2d}/{len(results_list):2d}{C.E} ({color}{prov_rate:.0f}%{C.E})")
    
    if failed:
        print(f"\n{C.B}{C.R}Failed Models:{C.E}")
        for r in failed:
            print(f"  • {C.R}{r['provider']:12} - {r['model']}{C.E}")
            print(f"    {r['error'][:80]}")
    
    print()


# ========================================
# Entry Point
# ========================================

if __name__ == "__main__":
    print(f"""
{C.B}{C.C}╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                 ALL MODELS IDENTITY TEST                                         ║
║                                                                                                  ║
║  This script tests all 43 models across all providers with a single prompt                      ║
║                                                                                                  ║
║  Requirements:                                                                                   ║
║    • API server running at http://localhost:8080                                                ║
║    • All providers configured                                                                    ║
║                                                                                                  ║
║  The script will:                                                                                ║
║    1. Send "Hello! What model are you?" to ALL 43 models simultaneously                         ║
║    2. Display each model's response                                                              ║
║    3. Show timing and success metrics                                                            ║
║                                                                                                  ║
║  Press Ctrl+C to interrupt                                                                       ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝{C.E}
    """)
    
    try:
        asyncio.run(main())
        print(f"{C.B}{C.G}✅ Test completed successfully!{C.E}\n")
    except KeyboardInterrupt:
        print(f"\n{C.Y}⚠️  Test interrupted by user{C.E}\n")
    except Exception as e:
        print(f"\n{C.R}❌ Error: {e}{C.E}\n")
        raise

