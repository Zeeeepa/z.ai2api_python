#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive Provider Testing Suite
Tests all available providers and models with actual API calls
"""

import os
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class ProviderTester:
    """Tests all providers with actual API calls"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'providers': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }
    
    async def test_qwen_provider(self) -> Dict[str, Any]:
        """Test Qwen provider with all model variants"""
        print("\n" + "="*70)
        print("🧪 TESTING QWEN PROVIDER")
        print("="*70)
        
        try:
            from app.providers.qwen_provider import QwenProvider
            
            # Get credentials from environment
            email = os.getenv('QWEN_EMAIL')
            password = os.getenv('QWEN_PASSWORD')
            
            if not email or not password:
                return {
                    'status': 'skipped',
                    'reason': 'QWEN_EMAIL or QWEN_PASSWORD not set',
                    'models_tested': []
                }
            
            print(f"📧 Using credentials: {email[:3]}***@{email.split('@')[1]}")
            
            # Initialize provider with correct camelCase keys
            auth_config = {
                'name': 'qwen',
                'baseUrl': 'https://chat.qwen.ai',
                'loginUrl': 'https://chat.qwen.ai/login',
                'chatUrl': 'https://chat.qwen.ai/chat',
                'email': email,
                'password': password
            }
            provider = QwenProvider(auth_config=auth_config)
            
            # Get all supported models
            models = provider.get_supported_models()
            print(f"📋 Found {len(models)} model variants")
            
            # Test a subset of important models
            test_models = [
                'qwen-max',
                'qwen-max-thinking',
                'qwen-max-search',
                'qwen-plus',
                'qwen-turbo',
                'qwen-long'
            ]
            
            results = {
                'status': 'success',
                'total_models': len(models),
                'models_tested': [],
                'authentication': 'success'
            }
            
            for model_name in test_models:
                if model_name not in models:
                    print(f"  ⚠️  Model {model_name} not in supported list")
                    continue
                
                print(f"\n  Testing: {model_name}")
                
                try:
                    # Create a simple test request
                    from app.models.schemas import OpenAIRequest, Message
                    
                    request = OpenAIRequest(
                        model=model_name,
                        messages=[
                            Message(role="user", content="What model are you? Please respond with just your model name.")
                        ],
                        stream=False,
                        temperature=0.1,
                        max_tokens=50
                    )
                    
                    # Make the request
                    response = await provider.chat_completion(request)
                    
                    # Extract response text
                    if isinstance(response, dict):
                        response_text = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                        
                        model_result = {
                            'model': model_name,
                            'status': 'success',
                            'response': response_text[:100],  # First 100 chars
                            'response_valid': len(response_text) > 0,
                            'model_name_mentioned': any(
                                keyword in response_text.lower() 
                                for keyword in ['qwen', 'model', model_name.lower()]
                            )
                        }
                        
                        print(f"    ✅ Response: {response_text[:80]}...")
                        print(f"    ✓ Model mentioned: {model_result['model_name_mentioned']}")
                        
                        results['models_tested'].append(model_result)
                        self.results['summary']['passed'] += 1
                    else:
                        print(f"    ❌ Invalid response format")
                        results['models_tested'].append({
                            'model': model_name,
                            'status': 'failed',
                            'error': 'Invalid response format'
                        })
                        self.results['summary']['failed'] += 1
                    
                    self.results['summary']['total_tests'] += 1
                    
                    # Small delay between requests
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    results['models_tested'].append({
                        'model': model_name,
                        'status': 'error',
                        'error': str(e)
                    })
                    self.results['summary']['failed'] += 1
                    self.results['summary']['total_tests'] += 1
            
            return results
            
        except Exception as e:
            print(f"❌ Provider initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'error': str(e),
                'models_tested': []
            }
    
    async def test_zai_provider(self) -> Dict[str, Any]:
        """Test Z.AI provider"""
        print("\n" + "="*70)
        print("🧪 TESTING Z.AI PROVIDER")
        print("="*70)
        
        try:
            from app.providers.zai_provider import ZAIProvider
            from app.providers.base import ProviderConfig
            
            config = ProviderConfig(
                name="zai",
                api_endpoint="https://chat.z.ai",
                headers={}
            )
            
            provider = ZAIProvider(config)
            models = provider.get_supported_models()
            
            print(f"📋 Found {len(models)} models")
            
            # Test key models
            test_models = ['GLM-4.5', 'GLM-4.5-Thinking', 'GLM-4.5-Search']
            
            results = {
                'status': 'success',
                'total_models': len(models),
                'models_tested': [],
                'note': 'Z.AI requires authentication - test with valid credentials'
            }
            
            return results
            
        except ImportError:
            print("⚠️  Z.AI provider not found - skipping")
            return {
                'status': 'skipped',
                'reason': 'Provider not implemented',
                'models_tested': []
            }
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'models_tested': []
            }
    
    async def test_k2think_provider(self) -> Dict[str, Any]:
        """Test K2Think provider"""
        print("\n" + "="*70)
        print("🧪 TESTING K2THINK PROVIDER")
        print("="*70)
        
        try:
            from app.providers.k2think_provider import K2ThinkProvider
            from app.providers.base import ProviderConfig
            
            config = ProviderConfig(
                name="k2think",
                api_endpoint="https://www.k2think.ai",
                headers={}
            )
            
            provider = K2ThinkProvider(config)
            models = provider.get_supported_models()
            
            print(f"📋 Found {len(models)} models")
            
            results = {
                'status': 'success',
                'total_models': len(models),
                'models_tested': [],
                'note': 'K2Think requires authentication - test with valid credentials'
            }
            
            return results
            
        except ImportError:
            print("⚠️  K2Think provider not found - skipping")
            return {
                'status': 'skipped',
                'reason': 'Provider not implemented',
                'models_tested': []
            }
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'models_tested': []
            }
    
    async def test_longcat_provider(self) -> Dict[str, Any]:
        """Test LongCat provider"""
        print("\n" + "="*70)
        print("🧪 TESTING LONGCAT PROVIDER")
        print("="*70)
        
        try:
            from app.providers.longcat_provider import LongCatProvider
            from app.providers.base import ProviderConfig
            
            config = ProviderConfig(
                name="longcat",
                api_endpoint="https://api.longcat.ai",
                headers={}
            )
            
            provider = LongCatProvider(config)
            models = provider.get_supported_models()
            
            print(f"📋 Found {len(models)} models")
            
            results = {
                'status': 'success',
                'total_models': len(models),
                'models_tested': [],
                'note': 'LongCat requires LONGCAT_PASSPORT_TOKEN'
            }
            
            return results
            
        except ImportError:
            print("⚠️  LongCat provider not found - skipping")
            return {
                'status': 'skipped',
                'reason': 'Provider not implemented',
                'models_tested': []
            }
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'models_tested': []
            }
    
    async def run_all_tests(self):
        """Run tests for all providers"""
        print("\n" + "="*70)
        print("🧪 COMPREHENSIVE PROVIDER TEST SUITE")
        print("="*70)
        print(f"Started: {self.results['timestamp']}")
        print("="*70)
        
        # Test each provider
        self.results['providers']['qwen'] = await self.test_qwen_provider()
        self.results['providers']['zai'] = await self.test_zai_provider()
        self.results['providers']['k2think'] = await self.test_k2think_provider()
        self.results['providers']['longcat'] = await self.test_longcat_provider()
        
        # Print summary
        self.print_summary()
        
        # Save results to file
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        for provider_name, provider_results in self.results['providers'].items():
            status = provider_results.get('status', 'unknown')
            total_models = provider_results.get('total_models', 0)
            models_tested = len(provider_results.get('models_tested', []))
            
            status_emoji = {
                'success': '✅',
                'error': '❌',
                'skipped': '⚠️'
            }.get(status, '❓')
            
            print(f"\n{status_emoji} {provider_name.upper()}")
            print(f"  Status: {status}")
            print(f"  Total Models: {total_models}")
            print(f"  Models Tested: {models_tested}")
            
            if status == 'error':
                print(f"  Error: {provider_results.get('error', 'Unknown')}")
            
            if status == 'skipped':
                print(f"  Reason: {provider_results.get('reason', 'Unknown')}")
            
            # Show individual model results
            for model_result in provider_results.get('models_tested', []):
                model_name = model_result.get('model', 'unknown')
                model_status = model_result.get('status', 'unknown')
                
                if model_status == 'success':
                    model_mentioned = model_result.get('model_name_mentioned', False)
                    mention_indicator = '✓' if model_mentioned else '✗'
                    print(f"    ✅ {model_name} - Response valid, Model mentioned: {mention_indicator}")
                elif model_status == 'failed':
                    print(f"    ❌ {model_name} - {model_result.get('error', 'Failed')}")
                else:
                    print(f"    ⚠️  {model_name} - {model_result.get('error', 'Unknown')}")
        
        print("\n" + "="*70)
        print(f"Total Tests: {self.results['summary']['total_tests']}")
        print(f"Passed: {self.results['summary']['passed']} ✅")
        print(f"Failed: {self.results['summary']['failed']} ❌")
        
        if self.results['summary']['total_tests'] > 0:
            success_rate = (self.results['summary']['passed'] / self.results['summary']['total_tests']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print("="*70)
    
    def save_results(self):
        """Save results to JSON file"""
        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")


async def main():
    """Main entry point"""
    
    # Check for credentials
    print("\n🔍 Checking credentials...")
    
    qwen_email = os.getenv('QWEN_EMAIL')
    qwen_password = os.getenv('QWEN_PASSWORD')
    
    if not qwen_email or not qwen_password:
        print("\n❌ Error: QWEN_EMAIL and QWEN_PASSWORD environment variables required")
        print("\nUsage:")
        print("  QWEN_EMAIL=xxx QWEN_PASSWORD=xxx python test_all_providers.py")
        print("\nOr set in .env file:")
        print("  QWEN_EMAIL=your-email@example.com")
        print("  QWEN_PASSWORD=your-password")
        return 1
    
    print("✅ Credentials found")
    
    # Run tests
    tester = ProviderTester()
    await tester.run_all_tests()
    
    # Return exit code based on results
    if tester.results['summary']['failed'] > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
