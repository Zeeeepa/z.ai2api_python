#!/usr/bin/env python3
"""
Provider Validation Test Suite

Tests all configured providers against the OpenAI-compatible API
to ensure proper functionality and response formatting.
"""

import openai
import sys
import os
from typing import List, Dict, Any

# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080/v1")
API_KEY = os.getenv("API_KEY", "sk-test-key")

# Test cases: (provider_name, model_name, expected_response_contains)
TEST_CASES = [
    ("Z.AI (GLM-4.5)", "GLM-4.5", ["GLM", "4.5", "model"]),
    ("Z.AI (GLM-4.6)", "GLM-4.6", ["GLM", "4.6", "model"]),
    ("K2Think", "MBZUAI-IFM/K2-Think", ["K2", "Think", "model"]),
    ("LongCat", "LongCat-Flash", ["LongCat", "Flash", "model"]),
    ("Qwen", "qwen-max", ["qwen", "max", "model"]),
]


def print_header():
    """Print test suite header"""
    print("🧪 Provider Validation Test Suite")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"API Key: {API_KEY[:10]}...")
    print("=" * 60)
    print()


def test_provider(
    client: openai.OpenAI,
    provider_name: str,
    model: str,
    expected_keywords: List[str]
) -> Dict[str, Any]:
    """
    Test a single provider
    
    Args:
        client: OpenAI client instance
        provider_name: Human-readable provider name
        model: Model identifier
        expected_keywords: Keywords expected in response
        
    Returns:
        Dictionary with test results
    """
    print(f"\n📋 Testing {provider_name} (model: {model})")
    print("-" * 60)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "What is your model name? Reply in one short sentence."}
            ],
            max_tokens=50,
            stream=False,
            timeout=30
        )
        
        content = response.choices[0].message.content
        model_returned = response.model
        
        # Validate response
        has_expected_keywords = any(
            keyword.lower() in content.lower() 
            for keyword in expected_keywords
        )
        
        if has_expected_keywords:
            print(f"✅ Success!")
            print(f"   Model Requested: {model}")
            print(f"   Model Returned:  {model_returned}")
            print(f"   Response: {content[:100]}...")
            
            return {
                "provider": provider_name,
                "model": model,
                "status": "✅ PASS",
                "response": content,
                "model_returned": model_returned
            }
        else:
            print(f"⚠️  Warning: Response doesn't contain expected keywords")
            print(f"   Expected: {expected_keywords}")
            print(f"   Response: {content}")
            
            return {
                "provider": provider_name,
                "model": model,
                "status": "⚠️  WARN",
                "response": content,
                "warning": "Unexpected response content"
            }
        
    except openai.APIError as e:
        error_msg = str(e)
        print(f"❌ API Error: {error_msg[:200]}")
        return {
            "provider": provider_name,
            "model": model,
            "status": "❌ FAIL",
            "error": error_msg,
            "error_type": "API"
        }
        
    except openai.APIConnectionError as e:
        error_msg = str(e)
        print(f"❌ Connection Error: {error_msg[:200]}")
        return {
            "provider": provider_name,
            "model": model,
            "status": "❌ FAIL",
            "error": error_msg,
            "error_type": "Connection"
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Unexpected Error: {error_msg[:200]}")
        return {
            "provider": provider_name,
            "model": model,
            "status": "❌ FAIL",
            "error": error_msg,
            "error_type": "Unexpected"
        }


def test_models_endpoint(client: openai.OpenAI) -> bool:
    """Test the /v1/models endpoint"""
    print("\n🔍 Testing Models Endpoint")
    print("-" * 60)
    
    try:
        models = client.models.list()
        model_ids = [model.id for model in models.data]
        
        print(f"✅ Found {len(model_ids)} models:")
        for i, model_id in enumerate(model_ids[:10], 1):
            print(f"   {i}. {model_id}")
        
        if len(model_ids) > 10:
            print(f"   ... and {len(model_ids) - 10} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)[:200]}")
        return False


def print_summary(results: List[Dict[str, Any]]):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["status"] == "✅ PASS")
    warned = sum(1 for r in results if r["status"] == "⚠️  WARN")
    failed = sum(1 for r in results if r["status"] == "❌ FAIL")
    
    for result in results:
        status_icon = result["status"]
        provider = result["provider"]
        model = result["model"]
        print(f"{status_icon} {provider} ({model})")
        
        # Print additional details for failures
        if "error" in result:
            error_type = result.get("error_type", "Unknown")
            error = result["error"][:100]
            print(f"      Error ({error_type}): {error}...")
    
    print(f"\n📈 Results: {passed} passed, {warned} warnings, {failed} failed")
    print(f"   Total: {len(results)} tests")
    
    # Return success status
    return failed == 0 and warned == 0


def main():
    """Main test runner"""
    print_header()
    
    # Initialize OpenAI client
    client = openai.OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL
    )
    
    # Test models endpoint first
    models_ok = test_models_endpoint(client)
    if not models_ok:
        print("\n⚠️  Warning: Models endpoint test failed, but continuing with provider tests...")
    
    # Run provider tests
    results = []
    for provider_name, model, expected_keywords in TEST_CASES:
        result = test_provider(client, provider_name, model, expected_keywords)
        results.append(result)
    
    # Print summary
    all_passed = print_summary(results)
    
    # Exit with appropriate code
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed - review errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()

