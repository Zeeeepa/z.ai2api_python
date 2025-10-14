#!/usr/bin/env python3
"""
Token Retrieval Script using Playwright
Automates login to Z.AI and extracts the authentication token
"""
import asyncio
import sys
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def retrieve_zai_token(email: str, password: str, timeout: int = 60000) -> dict:
    """
    Login to Z.AI and retrieve authentication token
    
    Args:
        email: User email for login
        password: User password for login
        timeout: Timeout in milliseconds (default: 60s)
    
    Returns:
        dict: Contains 'success' (bool), 'token' (str), 'error' (str)
    """
    result = {
        'success': False,
        'token': None,
        'error': None
    }
    
    async with async_playwright() as p:
        try:
            # Launch browser in headless mode
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            print("🌐 Navigating to Z.AI login page...")
            await page.goto('https://z.ai/', timeout=timeout)
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Wait for and click login button
            print("🔍 Looking for login button...")
            try:
                # Try multiple possible selectors for login button
                selectors = [
                    'button:has-text("登录")',
                    'button:has-text("Login")',
                    'a:has-text("登录")',
                    'a:has-text("Login")',
                    '[href*="login"]',
                    '.login-button',
                    '#login-btn'
                ]
                
                login_clicked = False
                for selector in selectors:
                    try:
                        await page.click(selector, timeout=5000)
                        login_clicked = True
                        print(f"✅ Clicked login button using selector: {selector}")
                        break
                    except:
                        continue
                
                if not login_clicked:
                    raise Exception("Could not find login button")
                
                await page.wait_for_load_state('networkidle', timeout=10000)
            except Exception as e:
                result['error'] = f"Login button not found: {str(e)}"
                await browser.close()
                return result
            
            # Enter email
            print("✉️  Entering email...")
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="邮箱"]',
                'input[placeholder*="email"]',
                '#email'
            ]
            
            email_entered = False
            for selector in email_selectors:
                try:
                    await page.fill(selector, email, timeout=5000)
                    email_entered = True
                    print(f"✅ Entered email using selector: {selector}")
                    break
                except:
                    continue
            
            if not email_entered:
                result['error'] = "Email input field not found"
                await browser.close()
                return result
            
            # Enter password
            print("🔐 Entering password...")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="密码"]',
                'input[placeholder*="password"]',
                '#password'
            ]
            
            password_entered = False
            for selector in password_selectors:
                try:
                    await page.fill(selector, password, timeout=5000)
                    password_entered = True
                    print(f"✅ Entered password using selector: {selector}")
                    break
                except:
                    continue
            
            if not password_entered:
                result['error'] = "Password input field not found"
                await browser.close()
                return result
            
            # Submit login form
            print("📤 Submitting login form...")
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("登录")',
                'button:has-text("Login")',
                '.submit-button',
                '#submit-btn'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    await page.click(selector, timeout=5000)
                    submitted = True
                    print(f"✅ Clicked submit button using selector: {selector}")
                    break
                except:
                    continue
            
            if not submitted:
                # Try pressing Enter as fallback
                await page.keyboard.press('Enter')
            
            # Wait for navigation after login
            print("⏳ Waiting for login to complete...")
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(3)  # Additional wait for tokens to be set
            
            # Extract token from localStorage/cookies/network
            print("🔍 Extracting authentication token...")
            
            # Method 1: Check localStorage
            token = await page.evaluate('''() => {
                return localStorage.getItem('token') || 
                       localStorage.getItem('auth_token') ||
                       localStorage.getItem('access_token') ||
                       localStorage.getItem('jwt');
            }''')
            
            # Method 2: Check cookies if localStorage didn't work
            if not token:
                cookies = await context.cookies()
                for cookie in cookies:
                    if cookie['name'] in ['token', 'auth_token', 'access_token', 'jwt', 'session']:
                        token = cookie['value']
                        break
            
            # Method 3: Check network requests for auth headers
            if not token:
                # Make a test API request to trigger auth header
                try:
                    response = await page.request.get('https://z.ai/api/config')
                    headers = response.headers
                    auth_header = headers.get('authorization', '')
                    if auth_header.startswith('Bearer '):
                        token = auth_header.replace('Bearer ', '')
                except:
                    pass
            
            if token:
                result['success'] = True
                result['token'] = token
                print(f"✅ Token retrieved successfully: {token[:20]}...")
            else:
                result['error'] = "Token not found in localStorage, cookies, or network requests"
                print("❌ Could not extract token from any source")
            
            await browser.close()
            
        except PlaywrightTimeout as e:
            result['error'] = f"Timeout during login process: {str(e)}"
            print(f"⏱️ Timeout: {result['error']}")
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            print(f"❌ Error: {result['error']}")
    
    return result


async def main():
    """Main entry point"""
    # Get credentials from environment variables
    email = os.getenv('ZAI_EMAIL')
    password = os.getenv('ZAI_PASSWORD')
    
    if not email or not password:
        print("❌ Error: ZAI_EMAIL and ZAI_PASSWORD environment variables must be set")
        sys.exit(1)
    
    print("=" * 60)
    print("Z.AI Token Retrieval Script")
    print("=" * 60)
    print(f"📧 Email: {email}")
    print(f"🔐 Password: {'*' * len(password)}")
    print("=" * 60)
    
    result = await retrieve_zai_token(email, password)
    
    if result['success']:
        # Write token to .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        
        # Read existing .env or create new one
        env_content = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_content[key.strip()] = value.strip()
        
        # Update AUTH_TOKEN
        env_content['AUTH_TOKEN'] = result['token']
        
        # Write back to .env
        with open(env_path, 'w') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ Token saved to {env_path}")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"❌ Failed to retrieve token: {result['error']}")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

