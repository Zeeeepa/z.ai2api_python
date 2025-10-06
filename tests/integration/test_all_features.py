#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Complete Feature Test Suite for z.ai2api_python
Tests all 10 implemented features with real API calls
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from app.providers.qwen_provider import QwenProvider
from app.models.schemas import OpenAIRequest, Message
from app.utils.logger import get_logger

logger = get_logger()


class FeatureTester:
    """Test all Qwen features"""
    
    def __init__(self, auth_config: Dict[str, str]):
        self.provider = QwenProvider(auth_config)
        self.results = {}
        
    async def test_basic_chat(self) -> bool:
        """Test 1: Basic Chat Completion"""
        print("\n" + "="*70)
        print("TEST 1: Basic Chat Completion")
        print("="*70)
        
        try:
            request = OpenAIRequest(
                model="qwen-max",
                messages=[
                    Message(role="user", content="Say 'Hello' in one word")
                ],
                temperature=0.7,
                max_tokens=50,
                stream=False
            )
            
            response = await self.provider.chat_completion(request)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            print(f"✅ Basic chat works!")
            print(f"Response: {content}")
            return True
            
        except Exception as e:
            print(f"❌ Basic chat failed: {e}")
            logger.error(f"Basic chat test failed", exc_info=True)
            return False
    
    async def test_streaming_chat(self) -> bool:
        """Test 2: Streaming Chat"""
        print("\n" + "="*70)
        print("TEST 2: Streaming Chat")
        print("="*70)
        
        try:
            request = OpenAIRequest(
                model="qwen-max",
                messages=[
                    Message(role="user", content="Count from 1 to 5")
                ],
                temperature=0.7,
                max_tokens=100,
                stream=True
            )
            
            chunks = []
            async for chunk in await self.provider.chat_completion(request):
                if chunk.startswith("data: "):
                    data_str = chunk[6:].strip()
                    if data_str == "[DONE]":
                        break
                    chunks.append(data_str)
            
            print(f"✅ Streaming works! Received {len(chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"❌ Streaming failed: {e}")
            logger.error(f"Streaming test failed", exc_info=True)
            return False
    
    async def test_thinking_mode(self) -> bool:
        """Test 3: Thinking Mode"""
        print("\n" + "="*70)
        print("TEST 3: Thinking Mode")
        print("="*70)
        
        try:
            request = OpenAIRequest(
                model="qwen-max-thinking",
                messages=[
                    Message(role="user", content="What is 2+2?")
                ],
                temperature=0.7,
                max_tokens=200,
                stream=False
            )
            
            response = await self.provider.chat_completion(request)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            print(f"✅ Thinking mode works!")
            print(f"Response: {content[:100]}...")
            return True
            
        except Exception as e:
            print(f"❌ Thinking mode failed: {e}")
            logger.error(f"Thinking mode test failed", exc_info=True)
            return False
    
    async def test_search_mode(self) -> bool:
        """Test 4: Search Mode"""
        print("\n" + "="*70)
        print("TEST 4: Search Mode")
        print("="*70)
        
        try:
            request = OpenAIRequest(
                model="qwen-max-search",
                messages=[
                    Message(role="user", content="What's the weather today?")
                ],
                temperature=0.7,
                max_tokens=200,
                stream=False
            )
            
            response = await self.provider.chat_completion(request)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            print(f"✅ Search mode works!")
            print(f"Response: {content[:100]}...")
            return True
            
        except Exception as e:
            print(f"❌ Search mode failed: {e}")
            logger.error(f"Search mode test failed", exc_info=True)
            return False
    
    async def test_image_generation(self) -> bool:
        """Test 5: Image Generation"""
        print("\n" + "="*70)
        print("TEST 5: Image Generation (T2I)")
        print("="*70)
        
        try:
            result = await self.provider.generate_image(
                prompt="A serene landscape with mountains",
                model="qwen-max-image",
                size="1024x1024",
                n=1
            )
            
            if result and "data" in result and result["data"]:
                image_url = result["data"][0].get("url", "")
                print(f"✅ Image generation works! URL: {image_url[:60]}...")
                return True
            else:
                print(f"❌ Image generation returned invalid response")
                return False
            
        except Exception as e:
            print(f"❌ Image generation failed: {e}")
            logger.error(f"Image generation test failed", exc_info=True)
            return False
    
    async def test_image_editing(self) -> bool:
        """Test 6: Image Editing"""
        print("\n" + "="*70)
        print("TEST 6: Image Editing")
        print("="*70)
        
        try:
            # This will be implemented in Phase 6
            print("⏳ Image editing endpoint not yet implemented")
            return None  # Pending
            
        except Exception as e:
            print(f"❌ Image editing failed: {e}")
            return False
    
    async def test_video_generation(self) -> bool:
        """Test 7: Video Generation"""
        print("\n" + "="*70)
        print("TEST 7: Video Generation (T2V)")
        print("="*70)
        
        try:
            # This will be implemented in Phase 7
            print("⏳ Video generation endpoint not yet implemented")
            return None  # Pending
            
        except Exception as e:
            print(f"❌ Video generation failed: {e}")
            return False
    
    async def test_deep_research(self) -> bool:
        """Test 8: Deep Research Mode"""
        print("\n" + "="*70)
        print("TEST 8: Deep Research Mode")
        print("="*70)
        
        try:
            result = await self.provider.deep_research(
                query="What are the latest developments in AI in 2024?",
                model="qwen-max-deep-research",
                max_iterations=2
            )
            
            if result and "answer" in result:
                print(f"✅ Deep research works!")
                print(f"Answer preview: {result['answer'][:100]}...")
                print(f"Citations found: {len(result.get('citations', []))}")
                return True
            else:
                print(f"❌ Deep research returned invalid response")
                return False
            
        except Exception as e:
            print(f"❌ Deep research failed: {e}")
            logger.error(f"Deep research test failed", exc_info=True)
            return False
    
    async def test_session_creation(self) -> bool:
        """Test 9: Session Creation"""
        print("\n" + "="*70)
        print("TEST 9: Session Creation")
        print("="*70)
        
        try:
            chat_id = await self.provider.create_chat_session(
                model="qwen-max",
                chat_type="t2i"
            )
            
            if chat_id:
                print(f"✅ Session creation works! Chat ID: {chat_id}")
                return True
            else:
                print(f"❌ Session creation returned None")
                return False
                
        except Exception as e:
            print(f"❌ Session creation failed: {e}")
            logger.error(f"Session creation test failed", exc_info=True)
            return False
    
    async def test_model_list(self) -> bool:
        """Test 10: Model List with Variants"""
        print("\n" + "="*70)
        print("TEST 10: Model List Expansion")
        print("="*70)
        
        try:
            models = self.provider.get_supported_models()
            print(f"✅ Model list works! Found {len(models)} model variants")
            print(f"Models: {', '.join(models[:5])}...")
            return True
            
        except Exception as e:
            print(f"❌ Model list failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests and generate report"""
        print("\n" + "="*70)
        print("🚀 RUNNING COMPLETE FEATURE TEST SUITE")
        print("="*70)
        
        tests = [
            ("Basic Chat", self.test_basic_chat),
            ("Streaming", self.test_streaming_chat),
            ("Thinking Mode", self.test_thinking_mode),
            ("Search Mode", self.test_search_mode),
            ("Image Generation", self.test_image_generation),
            ("Image Editing", self.test_image_editing),
            ("Video Generation", self.test_video_generation),
            ("Deep Research", self.test_deep_research),
            ("Session Creation", self.test_session_creation),
            ("Model List", self.test_model_list),
        ]
        
        results = {}
        for name, test_func in tests:
            try:
                result = await test_func()
                results[name] = result
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Test {name} crashed", exc_info=True)
                results[name] = False
        
        # Generate report
        print("\n" + "="*70)
        print("📊 TEST RESULTS SUMMARY")
        print("="*70)
        
        passed = sum(1 for v in results.values() if v is True)
        failed = sum(1 for v in results.values() if v is False)
        pending = sum(1 for v in results.values() if v is None)
        total = len(results)
        
        for name, result in results.items():
            if result is True:
                status = "✅ PASS"
            elif result is False:
                status = "❌ FAIL"
            else:
                status = "⏳ PENDING"
            print(f"{status:15} {name}")
        
        print("=" * 70)
        print(f"TOTAL: {passed} passed, {failed} failed, {pending} pending out of {total} tests")
        print(f"Pass Rate: {passed}/{total-pending} = {passed/(total-pending)*100:.1f}%" if total-pending > 0 else "N/A")
        print("=" * 70)
        
        return results


async def main():
    """Main test runner"""
    # Get credentials from environment
    email = os.getenv("QWEN_EMAIL")
    password = os.getenv("QWEN_PASSWORD")
    
    if not email or not password:
        print("❌ Error: QWEN_EMAIL and QWEN_PASSWORD environment variables required")
        print("Usage: QWEN_EMAIL=xxx QWEN_PASSWORD=xxx python test_all_features.py")
        sys.exit(1)
    
    auth_config = {
        "email": email,
        "password": password
    }
    
    tester = FeatureTester(auth_config)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
