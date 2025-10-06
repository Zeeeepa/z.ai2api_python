#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Browser-based authentication and comprehensive model testing
Uses Playwright to properly authenticate with all providers
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Provider configurations with correct auth endpoints
PROVIDERS = {
    "zai": {
        "name": "Z.AI",
        "baseUrl": "https://chat.z.ai",
        "authUrl": "https://chat.z.ai/auth",
        "email": "developer@pixelium.uk",
        "password": "developer123?",
        "continueButtonXPath": "/html/body/div/div[1]/div[3]/div/div/div[1]/form/div[3]/button[2]",
    },
    "k2think": {
        "name": "K2Think",
        "baseUrl": "https://www.k2think.ai",
        "authUrl": "https://www.k2think.ai/auth",
        "email": "developer@pixelium.uk",
        "password": "developer123?",
        "continueButtonXPath": None,  # Will discover
    },
    "qwen": {
        "name": "Qwen",
        "baseUrl": "https://chat.qwen.ai",
        "authUrl": "https://chat.qwen.ai/auth",
        "email": "developer@pixelium.uk",
        "password": "developer1?",
        "continueButtonXPath": None,  # Will discover
    },
}


class BrowserAuthenticator:
    """Handles browser-based authentication for providers"""
    
    def __init__(self, provider_name: str, config: Dict):
        self.name = provider_name
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cookies: List[Dict] = []
        self.local_storage: Dict = {}
        
    async def launch_browser(self, headless: bool = False):
        """Launch browser with proper settings"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        self.page = await self.context.new_page()
        print(f"✅ {self.name}: Browser launched")
        
    async def login(self) -> bool:
        """Perform login with credentials"""
        try:
            print(f"\n🔐 {self.name}: Starting login process...")
            print(f"   Navigating to: {self.config['authUrl']}")
            
            # Navigate to auth page
            await self.page.goto(self.config['authUrl'], wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # Take screenshot for debugging
            await self.page.screenshot(path=f"/tmp/{self.name}_1_auth_page.png")
            print(f"   📸 Screenshot saved: /tmp/{self.name}_1_auth_page.png")
            
            # Click "Continue with Email" button FIRST (if present)
            print(f"   Looking for 'Continue with Email' button...")
            email_button_selectors = [
                'button:has-text("Continue with Email")',
                'button:has-text("Continue with email")',
                'button:has-text("Email")',
            ]
            
            email_button_clicked = False
            for selector in email_button_selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        await button.click()
                        email_button_clicked = True
                        print(f"   ✅ Clicked 'Continue with Email' button")
                        await asyncio.sleep(2)  # Wait for email form to appear
                        
                        # Take screenshot after clicking
                        await self.page.screenshot(path=f"/tmp/{self.name}_1b_email_form.png")
                        print(f"   📸 Screenshot saved: /tmp/{self.name}_1b_email_form.png")
                        break
                except:
                    continue
            
            # Fill email
            print(f"   Filling email: {self.config['email']}")
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                'input[id*="email" i]',
            ]
            email_filled = False
            for selector in email_selectors:
                try:
                    await self.page.fill(selector, self.config['email'], timeout=2000)
                    email_filled = True
                    print(f"   ✅ Email filled using selector: {selector}")
                    break
                except:
                    continue
            
            if not email_filled:
                print(f"   ❌ Could not find email input field")
                return False
            
            await asyncio.sleep(1)
            
            # Note: Z.AI shows password field immediately after filling email
            # No need to click XPath button - that was "Skip for now"
            
            # Fill password
            print(f"   Filling password...")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]',
                'input[id*="password" i]',
            ]
            password_filled = False
            for selector in password_selectors:
                try:
                    await self.page.fill(selector, self.config['password'], timeout=2000)
                    password_filled = True
                    print(f"   ✅ Password filled using selector: {selector}")
                    break
                except:
                    continue
            
            if not password_filled:
                print(f"   ❌ Could not find password input field")
                return False
            
            await asyncio.sleep(1)
            
            # Take screenshot before submit
            await self.page.screenshot(path=f"/tmp/{self.name}_3_before_submit.png")
            print(f"   📸 Screenshot saved: /tmp/{self.name}_3_before_submit.png")
            
            # Find and click submit/login button
            print(f"   Looking for submit button...")
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Log in")',
                'button:has-text("Sign in")',
                'button:has-text("Continue")',
                'button:has-text("登录")',
                'button:has-text("继续")',
            ]
            
            submit_clicked = False
            for selector in submit_selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        await button.click()
                        submit_clicked = True
                        print(f"   ✅ Clicked submit button: {selector}")
                        break
                except:
                    continue
            
            if not submit_clicked:
                # Try pressing Enter as fallback
                print(f"   Trying Enter key as fallback...")
                await self.page.keyboard.press("Enter")
            
            # Wait for navigation/authentication
            print(f"   Waiting for authentication...")
            await asyncio.sleep(5)
            
            # Take screenshot after login
            await self.page.screenshot(path=f"/tmp/{self.name}_4_after_login.png")
            print(f"   📸 Screenshot saved: /tmp/{self.name}_4_after_login.png")
            
            # Check if we're logged in (URL should change)
            current_url = self.page.url
            print(f"   Current URL: {current_url}")
            
            # Capture cookies and storage
            self.cookies = await self.context.cookies()
            self.local_storage = await self.page.evaluate("() => Object.assign({}, localStorage)")
            
            print(f"   ✅ Captured {len(self.cookies)} cookies")
            print(f"   ✅ Captured {len(self.local_storage)} localStorage items")
            
            # Check for auth tokens
            auth_tokens = []
            for cookie in self.cookies:
                if any(keyword in cookie['name'].lower() for keyword in ['token', 'auth', 'session']):
                    auth_tokens.append(cookie['name'])
            
            for key in self.local_storage:
                if any(keyword in key.lower() for keyword in ['token', 'auth', 'session']):
                    auth_tokens.append(f"localStorage.{key}")
            
            print(f"   🔑 Found auth tokens: {', '.join(auth_tokens) if auth_tokens else 'None'}")
            
            # Consider login successful if we have cookies/tokens or URL changed
            success = (
                len(self.cookies) > 0 or 
                len(self.local_storage) > 0 or
                current_url != self.config['authUrl']
            )
            
            if success:
                print(f"✅ {self.name}: Login SUCCESSFUL!")
            else:
                print(f"❌ {self.name}: Login FAILED - no cookies/tokens captured")
            
            return success
            
        except Exception as e:
            print(f"❌ {self.name}: Login exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def get_models(self) -> List[Dict]:
        """Get available models after authentication"""
        try:
            print(f"\n📋 {self.name}: Fetching models list...")
            
            models_url = f"{self.config['baseUrl']}/api/models"
            print(f"   Navigating to: {models_url}")
            
            response = await self.page.goto(models_url, wait_until="networkidle", timeout=10000)
            
            if response.status == 200:
                content = await response.text()
                data = json.loads(content)
                models = data.get('data', [])
                print(f"✅ {self.name}: Found {len(models)} models")
                return models
            else:
                print(f"❌ {self.name}: Models request failed: {response.status}")
                return []
                
        except Exception as e:
            print(f"❌ {self.name}: Error fetching models: {e}")
            return []
    
    async def test_completion(self, model_id: str, stream: bool = False) -> Tuple[bool, str]:
        """Test chat completion with authenticated session"""
        try:
            print(f"\n💬 {self.name}: Testing completion for {model_id} (stream={stream})...")
            
            chat_id = f"test-{int(time.time())}"
            completion_url = f"{self.config['baseUrl']}/api/chat/completions"
            
            body = {
                "model": model_id,
                "messages": [{"role": "user", "content": "Hello, respond with just 'Hi'"}],
                "stream": stream,
                "chat_id": chat_id,
                "id": f"msg-{int(time.time())}",
                "features": {"enable_thinking": False},
            }
            
            # Use page.evaluate to make API call with cookies
            result = await self.page.evaluate("""
                async ({url, body, stream}) => {
                    try {
                        const response = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(body),
                        });
                        
                        if (!response.ok) {
                            return {
                                success: false,
                                status: response.status,
                                error: await response.text()
                            };
                        }
                        
                        // For streaming responses, just check we got data
                        const text = await response.text();
                        
                        // Check if response looks like streaming (starts with "data:")
                        if (text.startsWith('data:')) {
                            return {
                                success: true,
                                status: 200,
                                message: 'Streaming response received',
                                preview: text.substring(0, 100)
                            };
                        }
                        
                        // Try to parse as JSON
                        try {
                            const data = JSON.parse(text);
                            return {
                                success: true,
                                status: 200,
                                data: data
                            };
                        } catch {
                            // Not JSON, but got response
                            return {
                                success: true,
                                status: 200,
                                message: 'Non-JSON response',
                                preview: text.substring(0, 100)
                            };
                        }
                    } catch (error) {
                        return {
                            success: false,
                            error: error.toString()
                        };
                    }
                }
            """, {"url": completion_url, "body": body, "stream": stream})
            
            if result.get('success'):
                print(f"✅ {self.name}: Completion test PASSED for {model_id}")
                return True, "Success"
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ {self.name}: Completion test FAILED for {model_id}: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            print(f"❌ {self.name}: Exception testing completion: {e}")
            return False, str(e)
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            print(f"🔒 {self.name}: Browser closed")


async def test_provider(provider_name: str, headless: bool = False):
    """Test a single provider"""
    print(f"\n{'='*80}")
    print(f"Testing Provider: {PROVIDERS[provider_name]['name']}")
    print(f"{'='*80}")
    
    config = PROVIDERS[provider_name]
    auth = BrowserAuthenticator(provider_name, config)
    
    try:
        # Launch browser
        await auth.launch_browser(headless=headless)
        
        # Login
        login_success = await auth.login()
        if not login_success:
            print(f"\n❌ {config['name']}: Login failed, skipping model tests")
            return
        
        # Get models
        models = await auth.get_models()
        if not models:
            print(f"\n⚠️ {config['name']}: No models available")
            return
        
        # Display models
        print(f"\n📋 {config['name']} Available Models:")
        for i, model in enumerate(models, 1):
            print(f"   {i}. {model.get('id')}: {model.get('name', 'N/A')}")
        
        # Test first 3 models (or all if less than 3)
        models_to_test = models[:3]
        print(f"\n🧪 Testing {len(models_to_test)} models...")
        
        for model in models_to_test:
            model_id = model.get('id')
            
            # Test non-streaming
            success, error = await auth.test_completion(model_id, stream=False)
            
            # Test streaming
            if success:
                await auth.test_completion(model_id, stream=True)
            
            await asyncio.sleep(2)  # Rate limiting
        
    finally:
        await auth.close()


async def test_all_providers(headless: bool = False):
    """Test all providers"""
    print("\n" + "="*80)
    print("COMPREHENSIVE PROVIDER TESTING WITH BROWSER AUTHENTICATION")
    print("="*80)
    
    for provider_name in PROVIDERS.keys():
        try:
            await test_provider(provider_name, headless=headless)
        except Exception as e:
            print(f"\n❌ Error testing {provider_name}: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n{'='*80}\n")


async def test_server_endpoints():
    """Test the actual server endpoints"""
    import httpx
    
    print("\n" + "="*80)
    print("TESTING SERVER ENDPOINTS")
    print("="*80)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            print(f"\n✅ Health check: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
    
    # Test models endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/v1/models")
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                print(f"\n✅ Models endpoint: {len(models)} models available")
                for model in models[:10]:  # Show first 10
                    print(f"   - {model.get('id')}")
            else:
                print(f"\n❌ Models endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Models endpoint error: {e}")
    
    # Test completion endpoint
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            body = {
                "model": "GLM-4.5",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False,
            }
            response = await client.post(f"{base_url}/v1/chat/completions", json=body)
            if response.status_code == 200:
                print(f"\n✅ Completion endpoint: Working!")
            else:
                print(f"\n❌ Completion endpoint: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"\n❌ Completion endpoint error: {e}")


if __name__ == "__main__":
    import sys
    
    # Check if server testing is requested
    if "--server" in sys.argv:
        asyncio.run(test_server_endpoints())
    else:
        # Browser authentication testing
        headless = "--headless" in sys.argv
        
        if len(sys.argv) > 1 and sys.argv[1] in PROVIDERS:
            # Test specific provider
            provider_name = sys.argv[1]
            asyncio.run(test_provider(provider_name, headless=headless))
        else:
            # Test all providers
            asyncio.run(test_all_providers(headless=headless))
