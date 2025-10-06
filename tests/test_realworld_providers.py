#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Real-world provider validation tests
Tests all providers, all models, all modes with actual authentication
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright, Page
from app.utils.logger import setup_logger

logger = setup_logger(log_dir="logs/tests", debug_mode=True)


# Provider configurations
PROVIDERS = {
    "qwen": {
        "name": "Qwen",
        "login_url": "https://chat.qwen.ai/auth?action=signin",
        "chat_url": "https://chat.qwen.ai",
        "email": "developer@pixelium.uk",
        "password": "developer1?",
        "models": [
            "qwen-max-latest",
            "qwen-plus-latest", 
            "qwen-turbo-latest",
            "qwen-max-thinking",
            "qwen-max-search",
            "qwen-deep-research",
            "qwen3-coder-plus"
        ],
        "modes": ["chat", "thinking", "search", "code", "vision", "deep_research"]
    },
    "zai": {
        "name": "Z.AI",
        "login_url": "https://chat.z.ai/auth",
        "chat_url": "https://chat.z.ai",
        "email": "developer@pixelium.uk",
        "password": "developer123?",
        "models": [
            "GLM-4.5",
            "GLM-4.5-Thinking",
            "GLM-4.5-Search",
            "GLM-4.5-Air",
            "GLM-4.6",
            "GLM-4.6-Thinking",
            "GLM-4.6-Search"
        ],
        "modes": ["chat", "thinking", "search"]
    },
    "k2think": {
        "name": "K2Think",
        "login_url": "https://www.k2think.ai/login",
        "chat_url": "https://www.k2think.ai/chat",
        "email": "developer@pixelium.uk",
        "password": "developer123?",
        "models": [
            "MBZUAI-IFM/K2-Think"
        ],
        "modes": ["chat", "thinking"]
    }
}


class ProviderValidator:
    """Validates providers with real-world testing"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.results = {
            "providers": {},
            "summary": {
                "total_providers": 0,
                "total_models": 0,
                "total_tests": 0,
                "passed": 0,
                "failed": 0
            }
        }
    
    async def authenticate_provider(self, page: Page, provider_config: Dict) -> Dict[str, Any]:
        """Authenticate with a provider and extract tokens"""
        provider_name = provider_config["name"]
        logger.info(f"🔐 Authenticating with {provider_name}...")
        
        try:
            # Navigate to login page
            await page.goto(provider_config["login_url"], wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # Provider-specific authentication
            if provider_name == "Qwen":
                return await self._auth_qwen(page, provider_config)
            elif provider_name == "Z.AI":
                return await self._auth_zai(page, provider_config)
            elif provider_name == "K2Think":
                return await self._auth_k2think(page, provider_config)
            
            return {"success": False, "error": "Unknown provider"}
            
        except Exception as e:
            logger.error(f"❌ Authentication failed for {provider_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _auth_qwen(self, page: Page, config: Dict) -> Dict[str, Any]:
        """Authenticate with Qwen"""
        try:
            # Fill email
            await page.fill('input[type="email"], input[name="email"], input[placeholder*="email" i]', 
                          config["email"], timeout=10000)
            await asyncio.sleep(1)
            
            # Fill password
            await page.fill('input[type="password"], input[name="password"]', 
                          config["password"], timeout=10000)
            await asyncio.sleep(1)
            
            # Click login button
            await page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("登录")', 
                           timeout=10000)
            
            # Wait for navigation
            await page.wait_for_url(f"{config['chat_url']}/**", timeout=30000)
            await asyncio.sleep(3)
            
            # Extract tokens
            local_storage = await page.evaluate("""
                () => JSON.stringify(localStorage)
            """)
            
            cookies = await page.context.cookies()
            
            storage_data = json.loads(local_storage)
            token = storage_data.get("token") or storage_data.get("auth_token")
            session_cookie = next((c["value"] for c in cookies if "session" in c["name"].lower()), None)
            
            if token or session_cookie:
                logger.info(f"✅ Qwen authentication successful")
                return {
                    "success": True,
                    "token": token,
                    "cookie": session_cookie,
                    "combined": f"{token}|{session_cookie}" if token and session_cookie else token or session_cookie
                }
            
            return {"success": False, "error": "No tokens found"}
            
        except Exception as e:
            logger.error(f"❌ Qwen auth failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _auth_zai(self, page: Page, config: Dict) -> Dict[str, Any]:
        """Authenticate with Z.AI"""
        try:
            # Wait for page load
            await asyncio.sleep(2)
            
            # Fill email
            await page.fill('input[type="email"], input[name="email"]', 
                          config["email"], timeout=10000)
            await asyncio.sleep(1)
            
            # Fill password
            await page.fill('input[type="password"], input[name="password"]', 
                          config["password"], timeout=10000)
            await asyncio.sleep(1)
            
            # Click login
            await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")', 
                           timeout=10000)
            
            # Wait for chat page
            await page.wait_for_url(f"**/chat**", timeout=30000)
            await asyncio.sleep(3)
            
            # Extract tokens
            local_storage = await page.evaluate("() => JSON.stringify(localStorage)")
            cookies = await page.context.cookies()
            
            storage_data = json.loads(local_storage)
            token = storage_data.get("token") or storage_data.get("accessToken")
            
            if token:
                logger.info(f"✅ Z.AI authentication successful")
                return {"success": True, "token": token}
            
            return {"success": False, "error": "No token found"}
            
        except Exception as e:
            logger.error(f"❌ Z.AI auth failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _auth_k2think(self, page: Page, config: Dict) -> Dict[str, Any]:
        """Authenticate with K2Think"""
        try:
            await asyncio.sleep(2)
            
            # Fill credentials
            await page.fill('input[type="email"], input[name="email"]', 
                          config["email"], timeout=10000)
            await asyncio.sleep(1)
            
            await page.fill('input[type="password"], input[name="password"]', 
                          config["password"], timeout=10000)
            await asyncio.sleep(1)
            
            # Login
            await page.click('button[type="submit"], button:has-text("Login")' , timeout=10000)
            
            # Wait for chat
            await page.wait_for_url("**/chat**", timeout=30000)
            await asyncio.sleep(3)
            
            # Extract token
            local_storage = await page.evaluate("() => JSON.stringify(localStorage)")
            storage_data = json.loads(local_storage)
            token = storage_data.get("token") or storage_data.get("auth_token")
            
            if token:
                logger.info(f"✅ K2Think authentication successful")
                return {"success": True, "token": token}
            
            return {"success": False, "error": "No token found"}
            
        except Exception as e:
            logger.error(f"❌ K2Think auth failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_model(self, provider_name: str, model: str, token: str, mode: str = "chat") -> Dict[str, Any]:
        """Test a specific model with a specific mode"""
        logger.info(f"🧪 Testing {provider_name} - {model} - {mode} mode")
        
        # Test payloads for different modes
        test_payloads = {
            "chat": {
                "model": model,
                "messages": [{"role": "user", "content": "Say 'Hello' in exactly 1 word"}],
                "stream": False
            },
            "thinking": {
                "model": model,
                "messages": [{"role": "user", "content": "What is 2+2? Think step by step."}],
                "enable_thinking": True,
                "thinking_budget": 10000,
                "stream": False
            },
            "search": {
                "model": model,
                "messages": [{"role": "user", "content": "What is today's date?"}],
                "tools": [{"type": "web_search"}],
                "stream": False
            },
            "code": {
                "model": model,
                "messages": [{"role": "user", "content": "Write hello world in Python"}],
                "tools": [{"type": "code"}],
                "stream": False
            },
            "vision": {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image briefly"},
                        {"type": "image_url", "image_url": {"url": "https://download.samplelib.com/png/sample-hut-400x300.png"}}
                    ]
                }],
                "stream": False
            },
            "deep_research": {
                "model": model,
                "messages": [{"role": "user", "content": "Brief overview of AI"}],
                "stream": False
            }
        }
        
        payload = test_payloads.get(mode, test_payloads["chat"])
        
        try:
            import httpx
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:8000/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    logger.info(f"✅ {model} ({mode}): {content[:50]}...")
                    return {
                        "success": True,
                        "model": model,
                        "mode": mode,
                        "response": content[:100]
                    }
                else:
                    error_msg = f"Status {response.status_code}: {response.text[:200]}"
                    logger.error(f"❌ {model} ({mode}): {error_msg}")
                    return {
                        "success": False,
                        "model": model,
                        "mode": mode,
                        "error": error_msg
                    }
                    
        except Exception as e:
            logger.error(f"❌ {model} ({mode}) test failed: {e}")
            return {
                "success": False,
                "model": model,
                "mode": mode,
                "error": str(e)
            }
    
    async def validate_provider(self, provider_key: str, provider_config: Dict):
        """Validate a complete provider"""
        provider_name = provider_config["name"]
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 VALIDATING {provider_name.upper()} PROVIDER")
        logger.info(f"{'='*80}\n")
        
        self.results["providers"][provider_key] = {
            "name": provider_name,
            "auth": {},
            "models": {},
            "summary": {"total_tests": 0, "passed": 0, "failed": 0}
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Authenticate
            auth_result = await self.authenticate_provider(page, provider_config)
            self.results["providers"][provider_key]["auth"] = auth_result
            
            if not auth_result.get("success"):
                logger.error(f"❌ {provider_name} authentication failed. Skipping tests.")
                await browser.close()
                return
            
            token = auth_result.get("token") or auth_result.get("combined")
            
            await browser.close()
        
        # Test all models and modes
        for model in provider_config["models"]:
            self.results["providers"][provider_key]["models"][model] = {}
            
            for mode in provider_config["modes"]:
                # Skip invalid combinations
                if "thinking" in model.lower() and mode != "thinking":
                    continue
                if "search" in model.lower() and mode != "search":
                    continue
                if "coder" in model.lower() and mode not in ["chat", "code"]:
                    continue
                
                result = await self.test_model(provider_name, model, token, mode)
                
                self.results["providers"][provider_key]["models"][model][mode] = result
                self.results["providers"][provider_key]["summary"]["total_tests"] += 1
                self.results["summary"]["total_tests"] += 1
                
                if result["success"]:
                    self.results["providers"][provider_key]["summary"]["passed"] += 1
                    self.results["summary"]["passed"] += 1
                else:
                    self.results["providers"][provider_key]["summary"]["failed"] += 1
                    self.results["summary"]["failed"] += 1
                
                # Small delay between tests
                await asyncio.sleep(2)
    
    async def validate_all(self):
        """Validate all providers"""
        logger.info(f"\n{'#'*80}")
        logger.info(f"🔬 REAL-WORLD PROVIDER VALIDATION TEST SUITE")
        logger.info(f"{'#'*80}\n")
        
        self.results["summary"]["total_providers"] = len(PROVIDERS)
        
        for provider_key, provider_config in PROVIDERS.items():
            try:
                await self.validate_provider(provider_key, provider_config)
                self.results["summary"]["total_models"] += len(provider_config["models"])
            except Exception as e:
                logger.error(f"❌ Provider {provider_key} validation failed: {e}")
        
        self._print_summary()
    
    def _print_summary(self):
        """Print test results summary"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 VALIDATION SUMMARY")
        logger.info(f"{'='*80}\n")
        
        summary = self.results["summary"]
        logger.info(f"Providers Tested: {summary['total_providers']}")
        logger.info(f"Total Models: {summary['total_models']}")
        logger.info(f"Total Tests: {summary['total_tests']}")
        logger.info(f"✅ Passed: {summary['passed']}")
        logger.info(f"❌ Failed: {summary['failed']}")
        
        success_rate = (summary['passed'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        logger.info(f"📈 Success Rate: {success_rate:.1f}%\n")
        
        # Per-provider breakdown
        for provider_key, provider_data in self.results["providers"].items():
            logger.info(f"\n{provider_data['name']}:")
            logger.info(f"  Auth: {'✅' if provider_data['auth'].get('success') else '❌'}")
            logger.info(f"  Tests: {provider_data['summary']['total_tests']}")
            logger.info(f"  Passed: {provider_data['summary']['passed']}")
            logger.info(f"  Failed: {provider_data['summary']['failed']}")
        
        # Save results to JSON
        with open("tests/validation_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"\n💾 Results saved to tests/validation_results.json")


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-world provider validation")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--provider", choices=["qwen", "zai", "k2think", "all"], default="all", 
                       help="Test specific provider")
    args = parser.parse_args()
    
    validator = ProviderValidator(headless=args.headless)
    
    if args.provider == "all":
        await validator.validate_all()
    else:
        provider_config = PROVIDERS[args.provider]
        await validator.validate_provider(args.provider, provider_config)


if __name__ == "__main__":
    asyncio.run(main())

