#!/usr/bin/env python3
"""
Z.AI Browser-Based Login Automation with Playwright
Handles CAPTCHA, dynamic loading, and token extraction
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>")


async def browser_login() -> str:
    """
    Automate Z.AI login using Playwright browser automation.
    
    Returns:
        str: Authentication token extracted from browser
    """
    email = os.environ.get('ZAI_EMAIL')
    password = os.environ.get('ZAI_PASSWORD')
    
    if not email or not password:
        logger.error("❌ ZAI_EMAIL and ZAI_PASSWORD must be set!")
        return None
    
    logger.info("🌐 Starting browser automation...")
    logger.info(f"📧 Email: {email}")
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None
    
    async with async_playwright() as p:
        logger.info("🚀 Launching browser...")
        
        # Launch browser with better defaults
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Step 1: Navigate directly to auth page
            logger.info("🔗 Navigating directly to https://chat.z.ai/auth...")
            
            try:
                await page.goto('https://chat.z.ai/auth', wait_until='domcontentloaded', timeout=15000)
            except Exception as e:
                logger.warning(f"Direct auth page load failed: {e}, trying via homepage...")
                await page.goto('https://chat.z.ai/', wait_until='domcontentloaded', timeout=15000)
                
                # Click sign-in to get to auth page
                try:
                    await page.click('text=Sign in', timeout=5000)
                    await page.wait_for_url('**/auth', timeout=10000)
                except Exception:
                    logger.warning("⚠️ Couldn't click sign-in, assuming on login page")
            
            # Wait for auth page to fully load
            await page.wait_for_timeout(3000)
            
            # Take screenshot
            await page.screenshot(path='/tmp/zai_step1_auth_page.png')
            logger.info("📸 Auth page screenshot: /tmp/zai_step1_auth_page.png")
            
            # Step 2: Click "Continue with Email" button
            logger.info("📧 Looking for 'Continue with Email' button...")
            
            try:
                # Find button with "Email" text
                email_button = await page.wait_for_selector('button:has-text("Email")', timeout=5000)
                if email_button:
                    logger.info("✅ Found 'Continue with Email' button")
                    await email_button.click()
                    logger.info("🖱️  Clicked 'Continue with Email'")
                    await page.wait_for_timeout(2000)
                    await page.screenshot(path='/tmp/zai_step2_email_clicked.png')
                    logger.info("📸 After email button click: /tmp/zai_step2_email_clicked.png")
            except Exception as e:
                logger.warning(f"⚠️ Could not click 'Continue with Email': {e}")
            
            # Step 3: Fill email field
            logger.info("📧 Looking for email input field...")
            
            # Give extra time for form to render
            await page.wait_for_timeout(2000)
            
            email_filled = False
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[name="username"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="Email" i]',
                'input[id*="email"]',
                'input[autocomplete="email"]',
                'input[autocomplete="username"]',
                'input.email',
                'input#email',
                'input#username',
            ]
            
            # Try each selector
            for selector in email_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000, state='visible')
                    if element:
                        logger.info(f"✅ Found email field: {selector}")
                        await element.click()
                        await page.wait_for_timeout(500)
                        await element.fill(email)
                        await page.wait_for_timeout(500)
                        email_filled = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # If still not found, try to find any visible input
            if not email_filled:
                logger.warning("⚠️ Trying to find ANY visible input field...")
                try:
                    all_inputs = await page.query_selector_all('input[type="text"], input:not([type]), input[type="email"]')
                    for input_el in all_inputs:
                        is_visible = await input_el.is_visible()
                        if is_visible:
                            logger.info(f"✅ Found visible input, trying as email field")
                            await input_el.click()
                            await page.wait_for_timeout(500)
                            await input_el.fill(email)
                            email_filled = True
                            break
                except Exception as e:
                    logger.debug(f"Generic input search failed: {e}")
            
            if not email_filled:
                logger.error("❌ Could not find email input field")
                await page.screenshot(path='/tmp/zai_error_no_email.png')
                return None
            
            # Step 4: Fill password field
            logger.info("🔐 Looking for password input...")
            
            password_filled = False
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="Password" i]',
                'input[id*="password"]',
            ]
            
            for selector in password_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000, state='visible')
                    if element:
                        logger.info(f"✅ Found password field: {selector}")
                        await element.click()
                        await element.fill(password)
                        password_filled = True
                        break
                except Exception:
                    continue
            
            if not password_filled:
                logger.error("❌ Could not find password input field")
                await page.screenshot(path='/tmp/zai_error_no_password.png')
                return None
            
            await page.wait_for_timeout(1000)
            await page.screenshot(path='/tmp/zai_step3_credentials_filled.png')
            logger.info("📸 Credentials filled: /tmp/zai_step3_credentials_filled.png")
            
            # Step 5: Check for CAPTCHA
            logger.info("🤖 Checking for CAPTCHA...")
            
            captcha_detected = False
            captcha_selectors = [
                'iframe[src*="captcha"]',
                'iframe[src*="recaptcha"]',
                'iframe[title*="captcha" i]',
                '[class*="captcha"]',
                '[id*="captcha"]',
                '.g-recaptcha',
                '#captcha',
            ]
            
            for selector in captcha_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        captcha_detected = True
                        logger.warning(f"⚠️ CAPTCHA detected: {selector}")
                        break
                except Exception:
                    continue
            
            if captcha_detected:
                logger.warning("⚠️ CAPTCHA present - waiting 30 seconds for manual solve...")
                logger.warning("   If running headless, you need to solve CAPTCHA manually")
                logger.warning("   Consider using headless=False for debugging")
                await page.wait_for_timeout(30000)
            else:
                logger.info("✅ No CAPTCHA detected")
            
            # Step 6: Submit form
            logger.info("📤 Submitting login form...")
            
            submit_clicked = False
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign in")',
                'button:has-text("Login")',
                'button:has-text("Continue")',
                'button:has-text("Submit")',
                'input[type="submit"]',
                '[data-testid*="submit"]',
            ]
            
            for selector in submit_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000, state='visible')
                    if element:
                        logger.info(f"✅ Found submit button: {selector}")
                        await element.click()
                        submit_clicked = True
                        break
                except Exception:
                    continue
            
            if not submit_clicked:
                logger.warning("⚠️ No submit button found, trying Enter key...")
                await page.keyboard.press('Enter')
            
            # Step 7: Wait for navigation after login
            logger.info("⏳ Waiting for login to complete...")
            
            try:
                # Wait for URL change or specific elements
                await page.wait_for_url('**/chat**', timeout=15000)
                logger.info("✅ URL changed to chat page")
            except Exception:
                logger.warning("⚠️ URL didn't change, waiting for dashboard elements...")
                await page.wait_for_timeout(5000)
            
            await page.screenshot(path='/tmp/zai_step4_after_login.png')
            logger.info("📸 After login: /tmp/zai_step4_after_login.png")
            
            # Step 8: Extract token from localStorage
            logger.info("🔑 Extracting authentication token...")
            
            # Try multiple token keys
            token_keys = [
                'token',
                'auth_token',
                'authToken', 
                'access_token',
                'accessToken',
                'jwt',
                'bearer',
                'user_token',
            ]
            
            token = None
            for key in token_keys:
                try:
                    token = await page.evaluate(f'localStorage.getItem("{key}")')
                    if token and len(token) > 20:
                        logger.info(f"✅ Token found in localStorage['{key}']")
                        logger.info(f"   Token preview: {token[:30]}...")
                        break
                except Exception:
                    continue
            
            # Try cookies if localStorage didn't work
            if not token:
                logger.info("🍪 Trying to extract token from cookies...")
                cookies = await context.cookies()
                for cookie in cookies:
                    if any(keyword in cookie['name'].lower() for keyword in ['token', 'auth', 'jwt', 'bearer']):
                        token = cookie['value']
                        logger.info(f"✅ Token found in cookie: {cookie['name']}")
                        logger.info(f"   Token preview: {token[:30]}...")
                        break
            
            if not token:
                logger.error("❌ Could not extract token from browser")
                logger.info("💡 Check screenshots in /tmp/ for debugging")
                
                # Dump localStorage for debugging
                all_storage = await page.evaluate('JSON.stringify(localStorage)')
                logger.debug(f"localStorage contents: {all_storage}")
                
                return None
            
            # Step 9: Store token in database
            logger.info("💾 Storing token in database...")
            
            from app.services.token_dao import TokenDAO
            dao = TokenDAO()
            await dao.init_database()
            
            token_id = await dao.add_token(
                provider="zai",
                token=token,
                token_type="user",
                priority=10,
                validate=False
            )
            
            if token_id:
                logger.success(f"✅ Token stored successfully! ID: {token_id}")
            else:
                logger.error("❌ Failed to store token in database")
                return None
            
            return token
            
        except Exception as e:
            logger.error(f"❌ Browser automation error: {e}")
            await page.screenshot(path='/tmp/zai_error_final.png')
            logger.info("📸 Error screenshot: /tmp/zai_error_final.png")
            import traceback
            logger.debug(traceback.format_exc())
            return None
            
        finally:
            logger.info("🔒 Browser closed")
            await browser.close()


async def main() -> int:
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("🌐 Z.AI Browser Login Automation")
    logger.info("=" * 50)
    logger.info("")
    
    try:
        token = await browser_login()
        
        if token:
            logger.success("=" * 50)
            logger.success("✅ Login Successful!")
            logger.success("=" * 50)
            logger.success("")
            logger.success(f"Token: {token[:50]}...")
            logger.success("")
            logger.success("Next steps:")
            logger.success("  1. Server will use this token automatically")
            logger.success("  2. Run: bash scripts/start.sh")
            logger.success("  3. Test: bash scripts/send_request.sh")
            return 0
        else:
            logger.error("=" * 50)
            logger.error("❌ Login Failed")
            logger.error("=" * 50)
            logger.error("")
            logger.error("Possible reasons:")
            logger.error("  1. CAPTCHA blocking (try headless=False)")
            logger.error("  2. Wrong credentials")
            logger.error("  3. Page structure changed")
            logger.error("")
            logger.error("Check screenshots in /tmp/ for debugging")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
