#!/usr/bin/env python3
"""
Comprehensive Model Testing Script
Tests all available models across Z.AI, K2Think, Qwen, and Grok providers
"""

import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Any
import time
from datetime import datetime

# Initialize OpenAI client
client = AsyncOpenAI(
    api_key="sk-anything",
    base_url="http://localhost:8080/v1"
)

# Define all models to test
ALL_MODELS = {
    "Z.AI Models (GLM)": [
        "GLM-4.5",
        "GLM-4.5-Thinking",
        "GLM-4.5-Search",
        "GLM-4.5-Air",
        "GLM-4.6",
        "GLM-4.6-Thinking",
        "GLM-4.6-Search",
    ],
    "K2Think Models": [
        "MBZUAI-IFM/K2-Think",
    ],
    "Qwen Models (Base)": [
        "qwen-max",
        "qwen-plus",
        "qwen-turbo",
        "qwen-long",
    ],
    "Qwen Models (Thinking)": [
        "qwen-max-thinking",
        "qwen-plus-thinking",
        "qwen-turbo-thinking",
        "qwen-long-thinking",
    ],
    "Qwen Models (Search)": [
        "qwen-max-search",
        "qwen-plus-search",
        "qwen-turbo-search",
        "qwen-long-search",
    ],
    "Qwen Models (Image Generation)": [
        "qwen-max-image",
        "qwen-plus-image",
        "qwen-turbo-image",
        "qwen-long-image",
    ],
    "Qwen Models (Deep Research)": [
        "qwen-max-deep-research",
        "qwen-plus-deep-research",
        "qwen-turbo-deep-research",
        "qwen-long-deep-research",
        "qwen-deep-research",
    ],
    "Qwen Models (Aliases)": [
        "qwen-max-latest",
        "qwen-max-0428",
        "qwen-plus-latest",
        "qwen-turbo-latest",
        "qwen3-coder-plus",
        "qwen-coder-plus",
    ],
    "Grok Models": [
        "grok-3",
        "grok-4",
        "grok-auto",
        "grok-fast",
        "grok-expert",
        "grok-deepsearch",
        "grok-image",
    ],
}

# Test question
TEST_QUESTION = "What model are you? Please respond with your model name only."


async def test_model(model_name: str) -> Dict[str, Any]:
    """
    Test a single model and return results
    
    Args:
        model_name: Name of the model to test
        
    Returns:
        Dictionary containing test results
    """
    start_time = time.time()
    result = {
        "model": model_name,
        "status": "pending",
        "response": None,
        "error": None,
        "duration": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": TEST_QUESTION}],
            timeout=30.0
        )
        
        result["status"] = "success"
        result["response"] = response.choices[0].message.content
        result["duration"] = time.time() - start_time
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["duration"] = time.time() - start_time
    
    return result


async def test_all_models() -> List[Dict[str, Any]]:
    """
    Test all models concurrently
    
    Returns:
        List of test results for all models
    """
    print("=" * 80)
    print(f"🚀 Starting Comprehensive Model Testing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Flatten all models into a single list
    all_models_flat = []
    for category, models in ALL_MODELS.items():
        all_models_flat.extend(models)
    
    print(f"📊 Total models to test: {len(all_models_flat)}")
    print()
    
    # Create tasks for all models
    tasks = [test_model(model) for model in all_models_flat]
    
    # Run all tests concurrently
    print("⏳ Running tests concurrently...")
    results = await asyncio.gather(*tasks, return_exceptions=False)
    
    return results


def print_results(results: List[Dict[str, Any]]):
    """
    Print formatted test results grouped by category
    
    Args:
        results: List of test results
    """
    print()
    print("=" * 80)
    print("📋 TEST RESULTS")
    print("=" * 80)
    print()
    
    # Create a mapping of model to result
    results_map = {r["model"]: r for r in results}
    
    # Print results grouped by category
    total_success = 0
    total_error = 0
    
    for category, models in ALL_MODELS.items():
        print(f"\n{'─' * 80}")
        print(f"📂 {category}")
        print(f"{'─' * 80}")
        
        for model in models:
            result = results_map.get(model)
            if not result:
                continue
            
            status_icon = "✅" if result["status"] == "success" else "❌"
            duration_str = f"{result['duration']:.2f}s"
            
            print(f"\n{status_icon} Model: {model}")
            print(f"   ⏱️  Duration: {duration_str}")
            
            if result["status"] == "success":
                total_success += 1
                response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
                print(f"   💬 Response: {response_preview}")
            else:
                total_error += 1
                error_preview = result["error"][:100] + "..." if len(result["error"]) > 100 else result["error"]
                print(f"   ⚠️  Error: {error_preview}")
    
    # Print summary
    print()
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {total_success}/{len(results)}")
    print(f"❌ Failed: {total_error}/{len(results)}")
    print(f"📈 Success Rate: {(total_success/len(results)*100):.1f}%")
    print()
    
    # Print detailed error report if any
    if total_error > 0:
        print("=" * 80)
        print("⚠️  ERROR DETAILS")
        print("=" * 80)
        for result in results:
            if result["status"] == "error":
                print(f"\n❌ {result['model']}")
                print(f"   Error: {result['error']}")
    
    print()


async def main():
    """Main execution function"""
    try:
        # Test all models
        results = await test_all_models()
        
        # Print results
        print_results(results)
        
        # Print completion message
        print("=" * 80)
        print(f"✅ Testing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

