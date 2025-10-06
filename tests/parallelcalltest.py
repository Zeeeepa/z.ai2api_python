#!/usr/bin/env python3
"""
Parallel API Call Test
Tests 2 concurrent requests to different providers (ZAI and Qwen)
"""

import asyncio
import time
from openai import AsyncOpenAI

async def test_zai():
    """Test ZAI provider with GLM-4.6 model"""
    print("\n" + "="*60)
    print("🔵 Request 1: ZAI Provider (GLM-4.6)")
    print("="*60)
    
    start_time = time.time()
    
    client = AsyncOpenAI(
        api_key="sk-anything",
        base_url="http://localhost:8080/v1"
    )
    
    print("⏳ Sending request to ZAI...")
    response = await client.chat.completions.create(
        model="GLM-4.6",
        messages=[{"role": "user", "content": "what is your model!"}]
    )
    
    elapsed = time.time() - start_time
    
    print(f"✅ ZAI Response received in {elapsed:.2f}s")
    print("-" * 60)
    print("Response:")
    print(response.choices[0].message.content)
    print("-" * 60)
    
    return elapsed, response.choices[0].message.content


async def test_qwen():
    """Test Qwen provider with qwen-turbo model"""
    print("\n" + "="*60)
    print("🟢 Request 2: Qwen Provider (qwen-turbo)")
    print("="*60)
    
    start_time = time.time()
    
    client = AsyncOpenAI(
        api_key="sk-anything",
        base_url="http://localhost:8080/v1"
    )
    
    print("⏳ Sending request to Qwen...")
    response = await client.chat.completions.create(
        model="qwen-turbo",
        messages=[{"role": "user", "content": "what is your model!"}]
    )
    
    elapsed = time.time() - start_time
    
    print(f"✅ Qwen Response received in {elapsed:.2f}s")
    print("-" * 60)
    print("Response:")
    print(response.choices[0].message.content)
    print("-" * 60)
    
    return elapsed, response.choices[0].message.content


async def main():
    """Run both tests concurrently"""
    print("\n" + "🚀" * 30)
    print("Starting Parallel API Call Test")
    print("🚀" * 30)
    
    total_start = time.time()
    
    # Run both requests in parallel
    print("\n⚡ Sending both requests simultaneously...")
    results = await asyncio.gather(
        test_zai(),
        test_qwen(),
        return_exceptions=True
    )
    
    total_elapsed = time.time() - total_start
    
    # Process results
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    if isinstance(results[0], Exception):
        print(f"❌ ZAI Request failed: {results[0]}")
        zai_time = None
    else:
        zai_time, zai_response = results[0]
        print(f"🔵 ZAI (GLM-4.6): {zai_time:.2f}s")
    
    if isinstance(results[1], Exception):
        print(f"❌ Qwen Request failed: {results[1]}")
        qwen_time = None
    else:
        qwen_time, qwen_response = results[1]
        print(f"🟢 Qwen (qwen-turbo): {qwen_time:.2f}s")
    
    print(f"\n⏱️  Total elapsed time: {total_elapsed:.2f}s")
    
    # Analysis
    print("\n" + "=" * 60)
    print("💡 ANALYSIS")
    print("=" * 60)
    
    if zai_time and qwen_time:
        if total_elapsed < (zai_time + qwen_time) * 0.75:
            print("✅ Requests processed in PARALLEL! 🎉")
            print(f"   If sequential: ~{zai_time + qwen_time:.2f}s")
            print(f"   Actual time:   {total_elapsed:.2f}s")
            print(f"   Time saved:    {(zai_time + qwen_time) - total_elapsed:.2f}s")
        else:
            print("⚠️  Requests may have been processed sequentially")
    
    print("\n" + "🎯" * 30)
    print("Test Complete!")
    print("🎯" * 30)


if __name__ == "__main__":
    asyncio.run(main())

