#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Real-world provider tests with actual credentials
Tests Z.AI, K2Think, and Qwen providers with all available models
"""

import pytest
import requests
import json
import time
from typing import List, Dict, Any

# Test credentials
PROVIDERS = {
    "zai": {
        "name": "Z.AI",
        "baseUrl": "https://chat.z.ai",
        "loginUrl": "https://chat.z.ai/login",
        "chatUrl": "https://chat.z.ai/chat",
        "email": "developer@pixelium.uk",
        "password": "developer123?",
    },
    "k2think": {
        "name": "K2Think",
        "baseUrl": "https://www.k2think.ai",
        "loginUrl": "https://www.k2think.ai/login",
        "chatUrl": "https://www.k2think.ai/chat",
        "email": "developer@pixelium.uk",
        "password": "developer123?",
    },
    "qwen": {
        "name": "Qwen",
        "baseUrl": "https://chat.qwen.ai",
        "loginUrl": "https://chat.qwen.ai/login",
        "chatUrl": "https://chat.qwen.ai/chat",
        "email": "developer@pixelium.uk",
        "password": "developer1?",
    },
}


class ProviderTester:
    """Test helper for provider testing"""
    
    def __init__(self, provider_name: str, config: Dict[str, str]):
        self.name = provider_name
        self.config = config
        self.token = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": config["baseUrl"],
        }
    
    def get_guest_token(self) -> str:
        """Get guest token (anonymous mode)"""
        try:
            auth_url = f"{self.config['baseUrl']}/api/v1/auths/"
            response = requests.get(auth_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                token = data.get("token", "")
                print(f"✅ {self.name}: Got guest token: {token[:30]}...")
                return token
            else:
                print(f"❌ {self.name}: Failed to get guest token: {response.status_code}")
                return ""
        except Exception as e:
            print(f"❌ {self.name}: Exception getting guest token: {e}")
            return ""
    
    def login(self) -> bool:
        """Login with credentials"""
        try:
            login_data = {
                "email": self.config["email"],
                "password": self.config["password"],
            }
            response = requests.post(
                self.config["loginUrl"], 
                json=login_data,
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token") or data.get("access_token")
                print(f"✅ {self.name}: Login successful, token: {self.token[:30] if self.token else 'None'}...")
                return bool(self.token)
            else:
                print(f"❌ {self.name}: Login failed: {response.status_code} - {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ {self.name}: Exception during login: {e}")
            return False
    
    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models"""
        try:
            models_url = f"{self.config['baseUrl']}/api/models"
            auth_headers = self.headers.copy()
            if self.token:
                auth_headers["Authorization"] = f"Bearer {self.token}"
            
            response = requests.get(models_url, headers=auth_headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                print(f"✅ {self.name}: Found {len(models)} models")
                return models
            else:
                print(f"❌ {self.name}: Failed to get models: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ {self.name}: Exception getting models: {e}")
            return []
    
    def test_completion(self, model: str, stream: bool = False) -> bool:
        """Test chat completion"""
        try:
            chat_id = f"test-{int(time.time())}"
            chat_url = f"{self.config['baseUrl']}/api/chat/completions"
            
            auth_headers = self.headers.copy()
            if self.token:
                auth_headers["Authorization"] = f"Bearer {self.token}"
            auth_headers["Referer"] = f"{self.config['chatUrl']}/{chat_id}"
            
            body = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello, respond with just 'Hi'"}],
                "stream": stream,
                "chat_id": chat_id,
                "id": f"msg-{int(time.time())}",
                "features": {"enable_thinking": False},
            }
            
            response = requests.post(
                chat_url,
                json=body,
                headers=auth_headers,
                stream=stream,
                timeout=30
            )
            
            if response.status_code == 200:
                if stream:
                    # Test streaming response
                    lines_received = 0
                    for line in response.iter_lines():
                        if line and line.startswith(b"data: "):
                            lines_received += 1
                            if lines_received >= 3:  # Got some streaming data
                                break
                    success = lines_received > 0
                else:
                    # Test non-streaming response
                    data = response.json()
                    success = bool(data.get("choices"))
                
                status = "✅" if success else "⚠️"
                print(f"{status} {self.name}: Completion test {'streaming' if stream else 'non-streaming'} for {model}: {'PASSED' if success else 'NO DATA'}")
                return success
            else:
                print(f"❌ {self.name}: Completion failed for {model}: {response.status_code} - {response.text[:200]}")
                return False
        except Exception as e:
            print(f"❌ {self.name}: Exception testing completion for {model}: {e}")
            return False


@pytest.mark.parametrize("provider_name", ["zai", "k2think", "qwen"])
class TestProviderReal:
    """Real-world provider tests"""
    
    def test_guest_token(self, provider_name: str):
        """Test getting guest token"""
        config = PROVIDERS[provider_name]
        tester = ProviderTester(provider_name, config)
        
        token = tester.get_guest_token()
        assert token, f"{config['name']}: Failed to get guest token"
    
    def test_login(self, provider_name: str):
        """Test login with credentials"""
        config = PROVIDERS[provider_name]
        tester = ProviderTester(provider_name, config)
        
        success = tester.login()
        assert success, f"{config['name']}: Failed to login"
    
    def test_models_list(self, provider_name: str):
        """Test getting models list"""
        config = PROVIDERS[provider_name]
        tester = ProviderTester(provider_name, config)
        
        # Try guest token first
        tester.token = tester.get_guest_token()
        models = tester.get_models()
        
        # If guest token doesn't work, try login
        if not models:
            tester.login()
            models = tester.get_models()
        
        assert models, f"{config['name']}: Failed to get models"
        
        # Print models for documentation
        print(f"\n{config['name']} Available Models:")
        for model in models:
            print(f"  - {model.get('id')}: {model.get('name', 'N/A')}")
    
    def test_completion_non_streaming(self, provider_name: str):
        """Test non-streaming completion"""
        config = PROVIDERS[provider_name]
        tester = ProviderTester(provider_name, config)
        
        # Get token
        tester.token = tester.get_guest_token()
        if not tester.token:
            tester.login()
        
        # Get first available model
        models = tester.get_models()
        if not models:
            pytest.skip(f"{config['name']}: No models available")
        
        first_model = models[0].get("id")
        success = tester.test_completion(first_model, stream=False)
        assert success, f"{config['name']}: Non-streaming completion failed"
    
    def test_completion_streaming(self, provider_name: str):
        """Test streaming completion"""
        config = PROVIDERS[provider_name]
        tester = ProviderTester(provider_name, config)
        
        # Get token
        tester.token = tester.get_guest_token()
        if not tester.token:
            tester.login()
        
        # Get first available model
        models = tester.get_models()
        if not models:
            pytest.skip(f"{config['name']}: No models available")
        
        first_model = models[0].get("id")
        success = tester.test_completion(first_model, stream=True)
        assert success, f"{config['name']}: Streaming completion failed"


# Standalone test functions for manual testing
def test_all_providers_manual():
    """Manual test for all providers"""
    print("\n" + "="*80)
    print("TESTING ALL PROVIDERS")
    print("="*80)
    
    for provider_name, config in PROVIDERS.items():
        print(f"\n{'='*80}")
        print(f"Testing: {config['name']}")
        print(f"{'='*80}")
        
        tester = ProviderTester(provider_name, config)
        
        # Test guest token
        print(f"\n1. Testing guest token...")
        token = tester.get_guest_token()
        
        # Test login
        print(f"\n2. Testing login...")
        login_success = tester.login()
        
        # Test models
        print(f"\n3. Testing models list...")
        models = tester.get_models()
        if models:
            print(f"   Found {len(models)} models:")
            for i, model in enumerate(models[:5], 1):  # Show first 5
                print(f"   {i}. {model.get('id')}: {model.get('name', 'N/A')}")
        
        # Test completion (non-streaming)
        if models:
            print(f"\n4. Testing non-streaming completion...")
            tester.test_completion(models[0].get("id"), stream=False)
            
            # Test completion (streaming)
            print(f"\n5. Testing streaming completion...")
            tester.test_completion(models[0].get("id"), stream=True)


if __name__ == "__main__":
    # Run manual tests
    test_all_providers_manual()

