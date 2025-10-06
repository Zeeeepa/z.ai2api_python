#!/usr/bin/env python
"""Debug localStorage after login"""

import asyncio
import os
from playwright.async_api import async_playwright


async def debug_localStorage():
    email = os.getenv("QWEN_EMAIL", "developer@pixelium.uk")
    password = os.getenv("QWEN_PASSWORD", "")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print("Navigating to https://chat.qwen.ai...")
        await page.goto("https://chat.qwen.ai", wait_until='networkidle', timeout=30000)
        
        # Click login
        print("Clicking 'Log in' button...")
        login_btn = await page.wait_for_selector('button:has-text("Log in")', timeout=5000)
        await login_btn.click()
        await page.wait_for_load_state('networkidle', timeout=10000)
        
        # Fill form
        print("Filling form...")
        await page.wait_for_selector('input[type="email"], input[type="text"]', timeout=10000)
        email_input = await page.query_selector('input[type="email"], input[type="text"]')
        await email_input.fill(email)
        
        password_input = await page.query_selector('input[type="password"]')
        await password_input.fill(password)
        
        # Submit
        print("Submitting...")
        submit_btn = await page.query_selector('button[type="submit"]')
        await submit_btn.click()
        
        # Wait for navigation
        try:
            await page.wait_for_url('**/chat**', timeout=20000)
            print("✅ Login successful!")
        except:
            await page.wait_for_load_state('networkidle', timeout=20000)
            print("✅ Login completed (networkidle)")
        
        print("\nCurrent URL:", page.url)
        
        # Get ALL localStorage keys
        print("\n📦 All localStorage keys:")
        all_keys = await page.evaluate('''() => {
            const keys = [];
            for (let i = 0; i < localStorage.length; i++) {
                keys.push(localStorage.key(i));
            }
            return keys;
        }''')
        
        for key in all_keys:
            value = await page.evaluate(f'''() => {{
                return localStorage.getItem('{key}');
            }}''')
            print(f"  {key}: {value[:100] if value and len(value) > 100 else value}")
        
        # Get all cookies
        print("\n🍪 All cookies:")
        cookies = await context.cookies()
        for cookie in cookies:
            print(f"  {cookie['name']}: {cookie['value'][:50]}...")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_localStorage())

