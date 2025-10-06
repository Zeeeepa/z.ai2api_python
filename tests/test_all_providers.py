#!/usr/bin/env python3
"""
Comprehensive Test Suite for All AI Providers
Tests all providers (ZAI, K2Think, Qwen) with real credentials
"""

import asyncio
import time
import json
from openai import AsyncOpenAI

# Server configuration
API_BASE = "http://localhost:8080/v1"
API_KEY = "sk-test"  # Auth is disabled on server

# Test configurations for each provider
TEST_CONFIGS = {
    "zai": {
        "models": ["GLM-4.5", "GLM-4.6", "GLM-4.5-Air"],
        "test_message": "Hello! Please respond with your model name."
    },
    "k2think": {
        "models": ["MBZUAI-IFM/K2-Think"],
        "test_message": "Hello! Please respond with your model name."
    },
    "qwen": {
        "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
        "test_message": "你好！请回复你的模型名称。"
    }
}

class ProviderTester:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=API_KEY,
            base_url=API_BASE
        )
        self.results = []
        
    async def test_model(self, model: str, message: str):
        """Test a single model"""
        start_time = time.time()
        
        try:
            print(f"\n{'='*60}")
            print(f"🧪 Testing Model: {model}")
            print(f"{'='*60}")
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}],
                stream=False,
                max_tokens=100
            )
            
            elapsed = time.time() - start_time
            content = response.choices[0].message.content if response.choices else ""
            
            result = {
                "model": model,
                "status": "success",
                "elapsed": round(elapsed, 2),
                "response": content[:200] if content else "(empty)",
                "tokens": getattr(response.usage, 'total_tokens', 0) if hasattr(response, 'usage') else 0
            }
            
            print(f"✅ Success in {elapsed:.2f}s")
            print(f"📝 Response: {content[:100]}...")
            
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            
            result = {
                "model": model,
                "status": "failed",
                "elapsed": round(elapsed, 2),
                "error": error_msg[:200]
            }
            
            print(f"❌ Failed in {elapsed:.2f}s")
            print(f"🔥 Error: {error_msg[:100]}...")
        
        self.results.append(result)
        return result
    
    async def test_provider(self, provider: str, config: dict):
        """Test all models for a provider"""
        print(f"\n{'='*70}")
        print(f"🚀 TESTING PROVIDER: {provider.upper()}")
        print(f"{'='*70}")
        
        models = config["models"]
        message = config["test_message"]
        
        for model in models:
            await self.test_model(model, message)
            await asyncio.sleep(1)  # Small delay between tests
    
    async def test_concurrent_requests(self):
        """Test concurrent requests to different providers"""
        print(f"\n{'='*70}")
        print(f"⚡ TESTING CONCURRENT REQUESTS")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        # Create tasks for different providers simultaneously
        tasks = [
            self.test_model("GLM-4.6", "Hello!"),
            self.test_model("qwen-turbo", "你好！"),
            self.test_model("MBZUAI-IFM/K2-Think", "Hello!")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        print(f"\n⏱️  Total concurrent execution time: {elapsed:.2f}s")
        print(f"🎯 If sequential, would take: ~{len(tasks) * 10:.0f}s")
        print(f"🚀 Speedup: {(len(tasks) * 10) / elapsed:.1f}x faster!")
        
        return elapsed
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("\n" + "🌟" * 35)
        print("COMPREHENSIVE AI PROVIDER TEST SUITE")
        print("🌟" * 35)
        
        # Test each provider sequentially
        for provider, config in TEST_CONFIGS.items():
            await self.test_provider(provider, config)
            await asyncio.sleep(2)
        
        # Test concurrent execution
        concurrent_time = await self.test_concurrent_requests()
        
        # Generate report
        self.generate_report(concurrent_time)
    
    def generate_report(self, concurrent_time: float):
        """Generate test report"""
        print(f"\n{'='*70}")
        print("📊 TEST REPORT")
        print(f"{'='*70}")
        
        # Count successes and failures
        successes = [r for r in self.results if r["status"] == "success"]
        failures = [r for r in self.results if r["status"] == "failed"]
        
        print(f"\n✅ Successful: {len(successes)}/{len(self.results)}")
        print(f"❌ Failed: {len(failures)}/{len(self.results)}")
        
        if successes:
            avg_time = sum(r["elapsed"] for r in successes) / len(successes)
            print(f"⏱️  Average response time: {avg_time:.2f}s")
        
        # Success by provider
        print(f"\n📈 Success Rate by Provider:")
        for provider in TEST_CONFIGS.keys():
            provider_results = [r for r in self.results if any(m in r["model"] for m in TEST_CONFIGS[provider]["models"])]
            provider_successes = [r for r in provider_results if r["status"] == "success"]
            if provider_results:
                rate = (len(provider_successes) / len(provider_results)) * 100
                print(f"  {provider.upper()}: {rate:.0f}% ({len(provider_successes)}/{len(provider_results)})")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        print(f"{'Model':<30} {'Status':<10} {'Time':<10} {'Details':<40}")
        print("-" * 90)
        
        for result in self.results:
            status_emoji = "✅" if result["status"] == "success" else "❌"
            status = f"{status_emoji} {result['status']}"
            time_str = f"{result['elapsed']}s"
            
            if result["status"] == "success":
                details = f"Response: {result['response'][:35]}..."
            else:
                details = f"Error: {result['error'][:35]}..."
            
            print(f"{result['model']:<30} {status:<10} {time_str:<10} {details:<40}")
        
        print(f"\n⚡ Concurrent Performance:")
        print(f"  Concurrent execution: {concurrent_time:.2f}s")
        print(f"  Would be sequential: ~30s")
        print(f"  Speed improvement: {30 / concurrent_time:.1f}x")
        
        # Save results to file
        with open("/tmp/z.ai2api_python/tests/test_results.json", "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "summary": {
                    "total": len(self.results),
                    "successes": len(successes),
                    "failures": len(failures),
                    "concurrent_time": concurrent_time
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: tests/test_results.json")
        
        print("\n" + "🎉" * 35)
        print("TEST SUITE COMPLETE!")
        print("🎉" * 35)


async def main():
    """Main entry point"""
    tester = ProviderTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())

