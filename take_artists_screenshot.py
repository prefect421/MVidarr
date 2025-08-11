#!/usr/bin/env python3

import asyncio
from playwright.async_api import async_playwright

async def take_screenshot():
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()
        
        try:
            # Navigate to the Artists page
            print("Navigating to Artists page...")
            await page.goto('http://localhost:5000/artists')
            
            # Wait for page to load
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot
            screenshot_path = '/home/mike/mvidarr/artists_redesign_screenshot.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot saved to: {screenshot_path}")
            
        except Exception as e:
            print(f"Error taking screenshot: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(take_screenshot())