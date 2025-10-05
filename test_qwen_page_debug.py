#!/usr/bin/env python
"""Debug script to see what's on the Qwen page"""

import asyncio
from playwright.async_api import async_playwright


async def debug_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print("Navigating to https://chat.qwen.ai...")
        await page.goto("https://chat.qwen.ai", wait_until='networkidle', timeout=30000)
        
        print("\nTaking screenshot...")
        await page.screenshot(path="/tmp/qwen_page.png", full_page=True)
        
        print("\nPage title:", await page.title())
        print("\nPage URL:", page.url)
        
        print("\nPage HTML (first 2000 chars):")
        html = await page.content()
        print(html[:2000])
        
        print("\n\nLooking for inputs...")
        inputs = await page.query_selector_all('input')
        print(f"Found {len(inputs)} input elements")
        
        for i, inp in enumerate(inputs[:10]):
            input_type = await inp.get_attribute('type')
            input_name = await inp.get_attribute('name')
            input_placeholder = await inp.get_attribute('placeholder')
            input_id = await inp.get_attribute('id')
            print(f"  Input {i}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}")
        
        print("\nLooking for buttons...")
        buttons = await page.query_selector_all('button')
        print(f"Found {len(buttons)} button elements")
        
        for i, btn in enumerate(buttons[:10]):
            text = await btn.text_content()
            btn_type = await btn.get_attribute('type')
            print(f"  Button {i}: type={btn_type}, text={text}")
        
        await browser.close()
        print("\nScreenshot saved to /tmp/qwen_page.png")


if __name__ == "__main__":
    asyncio.run(debug_page())

