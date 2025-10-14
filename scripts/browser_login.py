#!/usr/bin/env python3
"""
Browser-based login using Playwright
Automates Z.AI login and extracts authentication token
"""
import asyncio
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.utils.logger import logger


async def browser_login():
    """Login to Z.AI using browser automation"""
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("❌ Playwright not installed!")
        logger.error("   Install with: pip install playwright")
        logger.error("   Then run: playwright install chromium")
        return None
    
    if not settings.ZAI_EMAIL or not settings.ZAI_PASSWORD:
        logger.error("❌ ZAI_EMAIL or ZAI_PASSWORD not configured!")
        return None
    
    logger.info("🌐 Starting browser automation...")
    logger.info(f"📧 Email: {settings.ZAI_EMAIL}")
    
    async with async_playwright() as p:
        # Launch browser
        logger.info("🚀 Launching browser...")
        browser = await p.chromium.launch(
            headless=True,  # Run in headless mode
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to Z.AI
            logger.info("🔗 Navigating to https://chat.z.ai...")
            await page.goto('https://chat.z.ai/', wait_until='networkidle', timeout=30000)
            
            # Wait for page to load
            await page.wait_for_timeout(3000)
            
            # Take screenshot for debugging
            await page.screenshot(path='/tmp/zai_homepage.png')
            logger.info("📸 Screenshot saved to /tmp/zai_homepage.png")
            
            # Look for sign-in button or form
            logger.info("🔍 Looking for login form...")
            
            # Try to find sign-in link/button
            signin_selectors = [
                'a:has-text("Sign in")',
                'button:has-text("Sign in")', 
                'a:has-text("Login")',
                'button:has-text("Login")',
                '[href*="signin"]',
                '[href*="login"]'
            ]
            
            signin_element = None
            for selector in signin_selectors:
                try:
                    signin_element = await page.wait_for_selector(selector, timeout=2000)
                    if signin_element:
                        logger.info(f"✅ Found sign-in element: {selector}")
                        break
                except:
                    continue
            
            if signin_element:
                # Click sign-in
                logger.info("🖱️  Clicking sign-in button...")
                await signin_element.click()
                await page.wait_for_timeout(2000)
                await page.screenshot(path='/tmp/zai_signin_page.png')
            
            # Look for email input
            logger.info("📧 Looking for email input...")
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email"]',
                'input[id*="email"]'
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = await page.wait_for_selector(selector, timeout=2000)
                    if email_input:
                        logger.info(f"✅ Found email input: {selector}")
                        break
                except:
                    continue
            
            if not email_input:
                logger.error("❌ Could not find email input field")
                await page.screenshot(path='/tmp/zai_error.png')
                return None
            
            # Fill email
            logger.info("✍️  Entering email...")
            await email_input.fill(settings.ZAI_EMAIL)
            await page.wait_for_timeout(500)
            
            # Look for password input
            logger.info("🔒 Looking for password input...")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password"]',
                'input[id*="password"]'
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = await page.wait_for_selector(selector, timeout=2000)
                    if password_input:
                        logger.info(f"✅ Found password input: {selector}")
                        break
                except:
                    continue
            
            if not password_input:
                logger.error("❌ Could not find password input field")
                await page.screenshot(path='/tmp/zai_error.png')
                return None
            
            # Fill password
            logger.info("✍️  Entering password...")
            await password_input.fill(settings.ZAI_PASSWORD)
            await page.wait_for_timeout(500)
            
            # Take screenshot before submit
            await page.screenshot(path='/tmp/zai_before_submit.png')
            logger.info("📸 Form filled, screenshot saved")
            
            # Look for submit button
            logger.info("🔍 Looking for submit button...")
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign in")',
                'button:has-text("Login")',
                'button:has-text("Continue")',
                'input[type="submit"]'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = await page.wait_for_selector(selector, timeout=2000)
                    if submit_button:
                        logger.info(f"✅ Found submit button: {selector}")
                        break
                except:
                    continue
            
            if not submit_button:
                logger.error("❌ Could not find submit button")
                # Try pressing Enter instead
                logger.info("⌨️  Trying Enter key...")
                await page.keyboard.press('Enter')
            else:
                logger.info("🖱️  Clicking submit button...")
                await submit_button.click()
            
            # Wait for navigation or CAPTCHA
            logger.info("⏳ Waiting for response...")
            await page.wait_for_timeout(5000)
            
            # Check current URL
            current_url = page.url
            logger.info(f"📍 Current URL: {current_url}")
            
            # Take screenshot after submit
            await page.screenshot(path='/tmp/zai_after_submit.png')
            logger.info("📸 After submit screenshot saved")
            
            # Check for CAPTCHA
            page_content = await page.content()
            if 'captcha' in page_content.lower() or 'recaptcha' in page_content.lower():
                logger.warning("⚠️  CAPTCHA detected!")
                logger.warning("   Z.AI requires CAPTCHA solving")
                logger.warning("   Consider using a CAPTCHA solving service")
                return None
            
            # Try to extract token from localStorage or cookies
            logger.info("🔑 Attempting to extract authentication token...")
            
            # Method 1: localStorage
            try:
                token = await page.evaluate('''() => {
                    return localStorage.getItem('token') || 
                           localStorage.getItem('auth_token') ||
                           localStorage.getItem('access_token') ||
                           localStorage.getItem('jwt');
                }''')
                
                if token:
                    logger.info(f"✅ Token found in localStorage!")
                    logger.info(f"   Token: {token[:30]}...")
                    return token
            except Exception as e:
                logger.debug(f"localStorage check failed: {e}")
            
            # Method 2: Cookies
            try:
                cookies = await context.cookies()
                for cookie in cookies:
                    if 'token' in cookie['name'].lower() or 'auth' in cookie['name'].lower():
                        logger.info(f"✅ Token found in cookie: {cookie['name']}")
                        logger.info(f"   Token: {cookie['value'][:30]}...")
                        return cookie['value']
            except Exception as e:
                logger.debug(f"Cookie check failed: {e}")
            
            # Method 3: Check if logged in by looking for user elements
            logger.info("🔍 Checking if login successful...")
            logged_in = False
            
            logged_in_selectors = [
                '[data-user]',
                '.user-profile',
                '.avatar',
                'button:has-text("Logout")',
                'a:has-text("Settings")'
            ]
            
            for selector in logged_in_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(f"✅ Login indicator found: {selector}")
                        logged_in = True
                        break
                except:
                    continue
            
            if logged_in:
                logger.info("✅ Login appears successful!")
                logger.info("💡 Token extraction may require different method")
                logger.info("   Check browser DevTools for token location")
            else:
                logger.error("❌ Login may have failed")
                logger.error("   Check screenshots in /tmp/ for details")
            
            return None
            
        finally:
            await browser.close()
            logger.info("🔒 Browser closed")
    
    return None


async def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("🌐 Z.AI Browser Login Automation")
    logger.info("=" * 50)
    logger.info("")
    
    token = await browser_login()
    
    if token:
        logger.info("")
        logger.info("=" * 50)
        logger.info("✅ SUCCESS! Token retrieved")
        logger.info("=" * 50)
        logger.info(f"Token: {token[:50]}...")
        logger.info("")
        logger.info("💾 Storing token...")
        
        # Store in database
        from app.services.token_dao import TokenDAO
        token_dao = TokenDAO()
        await token_dao.init_database()
        
        token_id = await token_dao.add_token(
            provider="zai",
            token=token,
            token_type="user",
            priority=10,
            validate=False
        )
        
        if token_id:
            logger.info(f"✅ Token stored in database! ID: {token_id}")
            return 0
        else:
            logger.error("❌ Failed to store token")
            return 1
    else:
        logger.error("")
        logger.error("=" * 50)
        logger.error("❌ FAILED to retrieve token")
        logger.error("=" * 50)
        logger.error("")
        logger.error("Possible issues:")
        logger.error("1. CAPTCHA requirement")
        logger.error("2. Invalid credentials")
        logger.error("3. Page structure changed")
        logger.error("")
        logger.error("Check screenshots in /tmp/ for details:")
        logger.error("  - /tmp/zai_homepage.png")
        logger.error("  - /tmp/zai_signin_page.png")
        logger.error("  - /tmp/zai_before_submit.png")
        logger.error("  - /tmp/zai_after_submit.png")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

