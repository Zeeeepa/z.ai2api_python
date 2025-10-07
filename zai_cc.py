#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Z.AI Claude Code Integration Test Script

This script tests the Z.AI API with Claude Code by asking
"What model are you?" to verify model identity.

Usage:
    python zai_cc.py

Configuration:
    Set API_BASE_URL environment variable to your Z.AI proxy URL
    Default: http://127.0.0.1:8080/v1
"""

import os
from openai import OpenAI

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8080/v1")
API_KEY = os.getenv("API_KEY", "")  # Empty for anonymous mode

# Initialize OpenAI client with Z.AI proxy
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY or "dummy-key"  # Use dummy if empty
)

def test_model_identity(model="GLM-4.5"):
    """
    Test asking the model "What model are you?"
    
    Args:
        model: Model name to test (GLM-4.5, GLM-4.6, GLM-4.5V, etc.)
    
    Returns:
        dict: Response with model info
    """
    print("=" * 70)
    print(f"🤖 Testing Model: {model}")
    print("=" * 70)
    print(f"📍 Base URL: {API_BASE_URL}")
    print(f"🔑 API Key: {'[Set]' if API_KEY else '[Empty/Anonymous]'}")
    print("-" * 70)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "What model are you? Please respond briefly with your model name and key capabilities."
                }
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        print(f"\n✅ Success!")
        print(f"📊 Model: {response.model}")
        print(f"💬 Response:\n{response.choices[0].message.content}")
        print(f"\n📈 Usage:")
        print(f"   - Prompt tokens: {response.usage.prompt_tokens}")
        print(f"   - Completion tokens: {response.usage.completion_tokens}")
        print(f"   - Total tokens: {response.usage.total_tokens}")
        
        return {
            "success": True,
            "model": response.model,
            "response": response.choices[0].message.content,
            "usage": response.usage
        }
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Make sure the server is running at {API_BASE_URL}")
        print(f"   2. Check if SKIP_AUTH_TOKEN=true in your .env file")
        print(f"   3. Verify the server logs for detailed error information")
        print(f"   4. Try setting API_KEY environment variable if auth is required")
        
        return {
            "success": False,
            "error": str(e)
        }

def test_all_models():
    """Test all available GLM models"""
    models = [
        ("GLM-4.5", "Base model - 128K context"),
        ("GLM-4.5-Air", "Lightweight - Fast & efficient"),
        ("GLM-4.6", "Extended context - 200K tokens"),
        ("GLM-4.5V", "Vision model - Multimodal"),
    ]
    
    print("\n" + "=" * 70)
    print("🔬 Testing All Available Models")
    print("=" * 70)
    
    results = []
    for model, description in models:
        print(f"\n📋 {model}: {description}")
        print("-" * 70)
        result = test_model_identity(model)
        results.append((model, result))
        if not result["success"]:
            print(f"⚠️  Skipping remaining models due to error\n")
            break
    
    return results

def test_streaming(model="GLM-4.5"):
    """Test streaming response"""
    print("\n" + "=" * 70)
    print(f"🌊 Testing Streaming with {model}")
    print("=" * 70)
    
    try:
        print("Streaming response:")
        print("-" * 70)
        
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "Count from 1 to 5 and tell me your model name."
                }
            ],
            max_tokens=150,
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        
        print("\n" + "-" * 70)
        print("✅ Streaming test completed successfully!")
        
        return {"success": True, "response": full_response}
        
    except Exception as e:
        print(f"\n❌ Streaming error: {e}")
        return {"success": False, "error": str(e)}

def main():
    """Main test function"""
    print("\n" + "=" * 70)
    print("🚀 Z.AI Claude Code Integration Test")
    print("=" * 70)
    print("\n📝 This script tests the Z.AI API integration by asking:")
    print('   "What model are you?"')
    print("\n🎯 Testing models: GLM-4.5, GLM-4.5-Air, GLM-4.6, GLM-4.5V")
    print("=" * 70)
    
    # Test basic model identity
    result = test_model_identity("GLM-4.5")
    
    if result["success"]:
        # Test streaming
        test_streaming("GLM-4.5")
        
        # Test all models
        test_all_models()
    
    print("\n" + "=" * 70)
    print("🏁 Test Suite Completed!")
    print("=" * 70)
    print("\n💡 Next Steps:")
    print("   1. Configure Claude Code to use this proxy")
    print("   2. Set base_url in your IDE settings")
    print("   3. Start building with Z.AI models!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

