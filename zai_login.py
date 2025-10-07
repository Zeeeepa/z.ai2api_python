#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Z.AI Automated Login Script
Automates login to Z.AI and extracts authentication token

Usage:
    python zai_login.py --email your@email.com --password yourpassword
    python zai_login.py --email your@email.com --password yourpassword --headless
    python zai_login.py --email your@email.com --password yourpassword --save-env
"""

import asyncio
import argparse
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeout
except ImportError:
    print("❌ Error: playwright library not installed!")
    print("Install with: pip install playwright")
    print("Then run: playwright install chromium")
    exit(1)


# ============================================================================
# Configuration
# ============================================================================

LOGIN_URL = "https://chat.z.ai/auth"
HOMEPAGE_URL = "https://chat.z.ai/"
DEFAULT_TIMEOUT = 30000  # 30 seconds


# ============================================================================
# Colors
# ============================================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_info(msg: str):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")


def print_step(step: int, msg: str):
    print(f"{Colors.BOLD}{Colors.CYAN}[{step}] {msg}{Colors.END}")


# ============================================================================
# Slider Solver
# ============================================================================

async def solve_slider_captcha(page: Page) -> bool:
    """
    Solve the slider CAPTCHA by dragging the slider to the right
    
    Returns:
        bool: True if solved successfully, False otherwise
    """
    try:
        print_info("Waiting for slider CAPTCHA...")
        
        # Wait for slider wrapper to appear
        slider_wrapper = await page.wait_for_selector(
            "#aliyunCaptcha-sliding-wrapper",
            timeout=10000
        )
        
        if not slider_wrapper:
            print_warning("No slider CAPTCHA detected")
            return True
        
        print_info("Slider CAPTCHA detected, attempting to solve...")
        
        # Find the draggable button
        slider_button_selector = "div.aliyunCaptcha-sliding-bg-wrapper div.aliyunCaptcha-sliding-button"
        slider_button = await page.wait_for_selector(slider_button_selector, timeout=5000)
        
        if not slider_button:
            print_error("Could not find slider button")
            return False
        
        # Get the bounding boxes
        button_box = await slider_button.bounding_box()
        wrapper_box = await slider_wrapper.bounding_box()
        
        if not button_box or not wrapper_box:
            print_error("Could not get element dimensions")
            return False
        
        # Calculate drag distance (almost to the end, leave some margin)
        drag_distance = wrapper_box['width'] - button_box['width'] - 10
        
        print_info(f"Dragging slider {drag_distance:.0f}px to the right...")
        
        # Move to button center
        start_x = button_box['x'] + button_box['width'] / 2
        start_y = button_box['y'] + button_box['height'] / 2
        
        # Move mouse to button
        await page.mouse.move(start_x, start_y)
        await asyncio.sleep(0.2)
        
        # Press mouse button
        await page.mouse.down()
        await asyncio.sleep(0.1)
        
        # Drag in steps to simulate human behavior
        steps = 20
        step_distance = drag_distance / steps
        
        for i in range(steps):
            current_x = start_x + (step_distance * (i + 1))
            await page.mouse.move(current_x, start_y)
            await asyncio.sleep(0.02)  # Small delay between steps
        
        # Release mouse button
        await page.mouse.up()
        
        print_success("Slider dragged successfully")
        
        # Wait a bit for validation
        await asyncio.sleep(1)
        
        # Check if CAPTCHA was solved by seeing if it disappears or changes
        try:
            await page.wait_for_selector(
                "#aliyunCaptcha-sliding-wrapper",
                state="hidden",
                timeout=3000
            )
            print_success("Slider CAPTCHA solved!")
            return True
        except PlaywrightTimeout:
            # CAPTCHA might still be visible but could be solved
            # Check for success indicators
            success_indicator = await page.query_selector(".aliyunCaptcha-success")
            if success_indicator:
                print_success("Slider CAPTCHA solved!")
                return True
            else:
                print_warning("Slider CAPTCHA state unclear, continuing anyway...")
                return True
                
    except PlaywrightTimeout:
        print_warning("Slider CAPTCHA timeout, may not be required")
        return True
    except Exception as e:
        print_error(f"Error solving slider CAPTCHA: {e}")
        return False


# ============================================================================
# Login Flow
# ============================================================================

async def perform_login(
    page: Page,
    email: str,
    password: str
) -> bool:
    """
    Perform the complete login flow
    
    Args:
        page: Playwright page object
        email: User email
        password: User password
        
    Returns:
        bool: True if login successful, False otherwise
    """
    
    # Step 1: Navigate to login page
    print_step(1, f"Navigating to {LOGIN_URL}")
    try:
        await page.goto(LOGIN_URL, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        print_success("Login page loaded")
    except Exception as e:
        print_error(f"Failed to load login page: {e}")
        return False
    
    await asyncio.sleep(2)
    
    # Step 2: Click "Continue with Email" button
    print_step(2, "Clicking 'Continue with Email' button")
    try:
        # Try multiple selectors
        selectors = [
            "button:has-text('Continue with Email')",
            "form button:nth-child(3)",
            ".loginFormUni button:nth-child(3)"
        ]
        
        button_clicked = False
        for selector in selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000)
                if button:
                    await button.click()
                    print_success("Clicked 'Continue with Email'")
                    button_clicked = True
                    break
            except:
                continue
        
        if not button_clicked:
            print_error("Could not find 'Continue with Email' button")
            return False
            
    except Exception as e:
        print_error(f"Failed to click 'Continue with Email': {e}")
        return False
    
    await asyncio.sleep(2)
    
    # Step 3: Enter email
    print_step(3, f"Entering email: {email}")
    try:
        # Try multiple selectors for email input
        email_selectors = [
            "input[type='email']",
            "input[placeholder*='Email' i]",
            "input[placeholder*='email' i]",
            ".loginForm input:first-child"
        ]
        
        email_entered = False
        for selector in email_selectors:
            try:
                email_input = await page.wait_for_selector(selector, timeout=5000)
                if email_input:
                    await email_input.click()
                    await email_input.fill(email)
                    print_success("Email entered")
                    email_entered = True
                    break
            except:
                continue
        
        if not email_entered:
            print_error("Could not find email input field")
            return False
            
    except Exception as e:
        print_error(f"Failed to enter email: {e}")
        return False
    
    await asyncio.sleep(1)
    
    # Step 4: Enter password
    print_step(4, "Entering password")
    try:
        # Try multiple selectors for password input
        password_selectors = [
            "input[type='password']",
            "input[placeholder*='Password' i]",
            "input[placeholder*='password' i]",
            ".loginForm input[type='password']"
        ]
        
        password_entered = False
        for selector in password_selectors:
            try:
                password_input = await page.wait_for_selector(selector, timeout=5000)
                if password_input:
                    await password_input.click()
                    await password_input.fill(password)
                    print_success("Password entered")
                    password_entered = True
                    break
            except:
                continue
        
        if not password_entered:
            print_error("Could not find password input field")
            return False
            
    except Exception as e:
        print_error(f"Failed to enter password: {e}")
        return False
    
    await asyncio.sleep(1)
    
    # Step 5: Solve slider CAPTCHA if present
    print_step(5, "Checking for slider CAPTCHA")
    captcha_solved = await solve_slider_captcha(page)
    if not captcha_solved:
        print_error("Failed to solve slider CAPTCHA")
        return False
    
    await asyncio.sleep(3)
    
    # Step 6: Click Sign In button
    print_step(6, "Clicking 'Sign In' button")
    try:
        # Try multiple selectors for sign in button
        signin_selectors = [
            "button:has-text('Sign In')",
            "button:has-text('sign in')",
            ".loginForm button:first-child",
            "form button[type='submit']"
        ]
        
        button_clicked = False
        for selector in signin_selectors:
            try:
                signin_button = await page.wait_for_selector(selector, timeout=5000)
                if signin_button:
                    await signin_button.click()
                    print_success("Clicked 'Sign In'")
                    button_clicked = True
                    break
            except:
                continue
        
        if not button_clicked:
            print_error("Could not find 'Sign In' button")
            return False
            
    except Exception as e:
        print_error(f"Failed to click 'Sign In': {e}")
        return False
    
    # Step 7: Wait for navigation and verify login
    print_step(7, "Waiting for login to complete")
    try:
        # Wait for navigation or URL change
        await page.wait_for_url(f"{HOMEPAGE_URL}**", timeout=15000)
        print_success("Successfully navigated to homepage!")
        return True
    except PlaywrightTimeout:
        # Check if we're still on auth page (login failed)
        current_url = page.url
        if "auth" in current_url:
            print_error("Login failed - still on auth page")
            
            # Try to capture error message
            try:
                error_elem = await page.query_selector(".error, .alert, [role='alert']")
                if error_elem:
                    error_text = await error_elem.inner_text()
                    print_error(f"Error message: {error_text}")
            except:
                pass
            
            return False
        else:
            print_success("Login appears successful (page changed)")
            return True
    except Exception as e:
        print_error(f"Error during login verification: {e}")
        return False


# ============================================================================
# Token Extraction
# ============================================================================

async def extract_token(context: BrowserContext) -> Optional[str]:
    """
    Extract the authentication token from cookies or localStorage
    
    Args:
        context: Playwright browser context
        
    Returns:
        Optional[str]: The token if found, None otherwise
    """
    print_info("Extracting authentication token...")
    
    # Try to get token from cookies
    cookies = await context.cookies()
    
    for cookie in cookies:
        if cookie['name'] == 'token':
            token = cookie['value']
            print_success(f"Token found in cookies!")
            return token
    
    # If not in cookies, try localStorage
    try:
        pages = context.pages
        if pages:
            page = pages[0]
            token = await page.evaluate("() => localStorage.getItem('token')")
            if token:
                print_success(f"Token found in localStorage!")
                return token
    except Exception as e:
        print_warning(f"Could not access localStorage: {e}")
    
    print_error("Token not found in cookies or localStorage")
    return None


async def save_cookies(context: BrowserContext, filename: str = "zai_cookies.json"):
    """
    Save browser cookies to a file
    
    Args:
        context: Playwright browser context
        filename: Output filename for cookies
    """
    cookies = await context.cookies()
    
    with open(filename, 'w') as f:
        json.dump(cookies, f, indent=2)
    
    print_success(f"Cookies saved to: {filename}")


def save_token_to_env(token: str, env_file: str = ".env"):
    """
    Save token to .env file
    
    Args:
        token: The authentication token
        env_file: Path to .env file
    """
    env_path = Path(env_file)
    
    # Read existing .env content
    env_content = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_content[key.strip()] = value.strip()
    
    # Update AUTH_TOKEN
    env_content['AUTH_TOKEN'] = token
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.write("# Z.AI Authentication Token\n")
        f.write(f"# Generated: {Path(env_file).stat().st_mtime if env_path.exists() else 'now'}\n\n")
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")
    
    print_success(f"Token saved to {env_file} as AUTH_TOKEN")


# ============================================================================
# Main Function
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="Automated Z.AI login and token extraction"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Z.AI account email"
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Z.AI account password"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--save-env",
        action="store_true",
        help="Save token to .env file"
    )
    parser.add_argument(
        "--save-cookies",
        action="store_true",
        help="Save cookies to file"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds (default: 30)"
    )
    
    args = parser.parse_args()
    
    # Banner
    print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║              Z.AI Automated Login Script                    ║
║                                                              ║
║  This script automates the Z.AI login process and           ║
║  extracts the authentication token for API usage            ║
╚══════════════════════════════════════════════════════════════╝{Colors.END}
    """)
    
    print_info(f"Email: {args.email}")
    print_info(f"Headless mode: {args.headless}")
    print_info(f"Timeout: {args.timeout}s")
    print()
    
    async with async_playwright() as p:
        # Launch browser
        print_info("Launching browser...")
        browser = await p.chromium.launch(
            headless=args.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
        
        # Create context with realistic user agent
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Create page
        page = await context.new_page()
        
        try:
            # Perform login
            success = await perform_login(page, args.email, args.password)
            
            if not success:
                print_error("Login failed!")
                await browser.close()
                return 1
            
            print()
            print_success("Login successful!")
            print()
            
            # Extract token
            token = await extract_token(context)
            
            if token:
                print()
                print(f"{Colors.BOLD}{Colors.GREEN}╔══════════════════════════════════════════════════════════════╗{Colors.END}")
                print(f"{Colors.BOLD}{Colors.GREEN}║                    TOKEN EXTRACTED                           ║{Colors.END}")
                print(f"{Colors.BOLD}{Colors.GREEN}╚══════════════════════════════════════════════════════════════╝{Colors.END}")
                print()
                print(f"{Colors.BOLD}Token:{Colors.END}")
                print(f"{Colors.CYAN}{token}{Colors.END}")
                print()
                
                # Save to .env if requested
                if args.save_env:
                    save_token_to_env(token)
                
                # Save cookies if requested
                if args.save_cookies:
                    await save_cookies(context)
                
                print()
                print_success("✨ All done! You can now use this token with the API server.")
                print()
                print(f"{Colors.BOLD}Usage:{Colors.END}")
                print(f"  export AUTH_TOKEN='{token}'")
                print(f"  python main.py --port 8080")
                print()
                
                return 0
            else:
                print_error("Failed to extract token")
                return 1
                
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            if not args.headless:
                print_info("Browser will stay open for 5 seconds...")
                await asyncio.sleep(5)
            
            await browser.close()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print()
        print_warning("Interrupted by user")
        exit(130)

