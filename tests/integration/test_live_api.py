#!/usr/bin/env python
"""
Live API Testing Script
========================

Tests the Qwen provider implementation against the actual Qwen API
using the configured credentials.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.providers.qwen_provider import QwenProvider
from app.auth.provider_auth import QwenAuth
from app.models.schemas import OpenAIRequest, Message
from app.utils.logger import get_logger

logger = get_logger()


async def test_qwen_authentication():
    """Test 1: Qwen Authentication"""
    print("\n" + "="*60)
    print("TEST 1: Qwen Authentication")
    print("="*60)
    
    try:
        # Load provider config
        with open("config/providers.json", "r") as f:
            config = json.load(f)
        
        qwen_config = next(
            (p for p in config["providers"] if p["name"] == "qwen"),
            None
        )
        
        if not qwen_config:
            print("❌ Qwen provider not found in config")
            return False
        
        print(f"\n📧 Testing authentication for: {qwen_config['email']}")
        
        # Initialize auth
        auth = QwenAuth(qwen_config)
        
        # Test login
        print("🔐 Attempting login...")
        success = await auth.login()
        
        if success:
            print("✅ Authentication successful!")
            
            # Get cookies
            cookies = await auth.get_cookies()
            print(f"🍪 Retrieved {len(cookies)} cookies")
            
            # Get token
            token = await auth.get_token()
            if token:
                print(f"🎟️ Retrieved auth token: {token[:20]}...")
            else:
                print("⚠️ No auth token available (may use cookies only)")
            
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_qwen_basic_chat():
    """Test 2: Basic Text Chat"""
    print("\n" + "="*60)
    print("TEST 2: Basic Text Chat")
    print("="*60)
    
    try:
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
                Message(role="user", content="Say 'Hello, world!' in one sentence.")
            ],
            temperature=0.7,
            max_tokens=50,
            stream=False
        )
        
        print(f"\n📤 Sending request to model: {request.model}")
        print(f"💬 Message: {request.messages[0].content}")
        
        # Make request
        response = await provider.chat_completion(request)
        
        print(f"\n✅ Response received!")
        print(f"📝 Content: {response['choices'][0]['message']['content']}")
        print(f"🆔 ID: {response['id']}")
        print(f"📊 Model: {response['model']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_qwen_streaming():
    """Test 3: Streaming Response"""
    print("\n" + "="*60)
    print("TEST 3: Streaming Response")
    print("="*60)
    
    try:
        # Load config
        with open("config/providers.json", "r") as f:
            config = json.load(f)
        
        qwen_config = next(
            (p for p in config["providers"] if p["name"] == "qwen"),
            None
        )
        
        # Initialize provider
        provider = QwenProvider(auth_config=qwen_config)
        
        # Create streaming request
        request = OpenAIRequest(
            model="qwen-max",
            messages=[
                Message(role="user", content="Count from 1 to 5.")
            ],
            temperature=0.7,
            max_tokens=100,
            stream=True
        )
        
        print(f"\n📤 Sending streaming request to model: {request.model}")
        print(f"💬 Message: {request.messages[0].content}")
        print(f"\n📡 Streaming response:")
        
        # Stream response
        full_content = ""
        chunk_count = 0
        
        async for chunk in provider.chat_completion(request):
            chunk_count += 1
            
            # Parse SSE chunk
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                
                if data_str == "[DONE]":
                    print("\n✅ Stream complete!")
                    break
                
                try:
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        
                        if content:
                            full_content += content
                            print(content, end="", flush=True)
                            
                except json.JSONDecodeError:
                    continue
        
        print(f"\n\n📊 Stats:")
        print(f"  - Chunks received: {chunk_count}")
        print(f"  - Total characters: {len(full_content)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_qwen_thinking_mode():
    """Test 4: Thinking Mode"""
    print("\n" + "="*60)
    print("TEST 4: Thinking Mode")
    print("="*60)
    
    try:
        # Load config
        with open("config/providers.json", "r") as f:
            config = json.load(f)
        
        qwen_config = next(
            (p for p in config["providers"] if p["name"] == "qwen"),
            None
        )
        
        # Initialize provider
        provider = QwenProvider(auth_config=qwen_config)
        
        # Create thinking mode request
        request = OpenAIRequest(
            model="qwen-max-thinking",  # Enables thinking mode
            messages=[
                Message(
                    role="user",
                    content="What is 15 * 23? Show your reasoning."
                )
            ],
            temperature=0.5,
            max_tokens=200,
            stream=False
        )
        
        print(f"\n📤 Sending request to model: {request.model}")
        print(f"💬 Message: {request.messages[0].content}")
        print(f"🧠 Thinking mode enabled")
        
        # Make request
        response = await provider.chat_completion(request)
        
        print(f"\n✅ Response received!")
        print(f"📝 Content: {response['choices'][0]['message']['content']}")
        
        # Check for reasoning content
        if 'reasoning_content' in response['choices'][0]['message']:
            reasoning = response['choices'][0]['message']['reasoning_content']
            print(f"🧠 Reasoning: {reasoning}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_request_structure():
    """Test 5: Verify Request Structure"""
    print("\n" + "="*60)
    print("TEST 5: Request Structure Verification")
    print("="*60)
    
    try:
        from app.providers.qwen_builder import QwenRequestBuilder
        
        builder = QwenRequestBuilder()
        
        # Build a test request
        messages = [
            {"role": "user", "content": "Test message"}
        ]
        
        body = builder.build_text_chat_request(
            model="qwen-max",
            messages=messages,
            stream=True
        )
        
        print("\n📦 Generated request body:")
        print(json.dumps(body, indent=2))
        
        # Verify all critical fields
        print("\n🔍 Verifying critical fields:")
        
        checks = [
            ("session_id", "session_id" in body),
            ("chat_id", "chat_id" in body),
            ("feature_config", "feature_config" in body),
            ("messages[0].chat_type", "chat_type" in body["messages"][0]),
            ("messages[0].extra", "extra" in body["messages"][0]),
        ]
        
        all_passed = True
        for field, present in checks:
            status = "✅" if present else "❌"
            print(f"  {status} {field}: {'Present' if present else 'MISSING'}")
            if not present:
                all_passed = False
        
        if all_passed:
            print("\n✅ All critical fields present!")
            return True
        else:
            print("\n❌ Some critical fields missing!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests sequentially"""
    print("\n" + "="*60)
    print("🧪 QWEN API LIVE TESTING SUITE")
    print("="*60)
    
    tests = [
        ("Authentication", test_qwen_authentication),
        ("Basic Chat", test_qwen_basic_chat),
        ("Streaming", test_qwen_streaming),
        ("Thinking Mode", test_qwen_thinking_mode),
        ("Request Structure", test_request_structure),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            print(f"\n🔄 Running: {name}")
            result = await test_func()
            results.append((name, result))
            
            if result:
                print(f"✅ {name} PASSED")
            else:
                print(f"❌ {name} FAILED")
                
            # Small delay between tests
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ {name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n📈 Total: {passed}/{total} passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Qwen integration is working correctly!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check logs above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

