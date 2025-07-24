#!/usr/bin/env python3
"""
Final Push - Last Few Screenshots to Complete Documentation
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5000"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def final_push_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        captured = 0
        
        print("🏁 Final Push - Last Screenshots")
        
        # Last essential screenshots
        final_captures = [
            # Critical missing ones
            ("playlist-creation.png", "/mvtv"),
            ("video-detail-modal.png", "/videos"),
            ("confirmation-dialogs.png", "/artists"),
            ("modal-dialogs.png", "/videos"),
            ("dropdown-menus.png", "/settings"),
            ("context-menus.png", "/videos"),
            ("tooltip-examples.png", "/artists"),
            ("progress-indicators.png", "/health"),
            ("filter-panel.png", "/videos"),
            ("search-suggestions.png", "/videos"),
            ("advanced-filters.png", "/artists"),
            ("compact-view.png", "/videos"),
            ("detailed-view.png", "/videos"),
            ("statistics-charts.png", "/health"),
            ("usage-graphs.png", "/health"),
            ("no-artists.png", "/artists"),
            ("offline-mode.png", "/health"),
            ("maintenance-mode.png", "/health"),
        ]
        
        for filename, path in final_captures:
            try:
                print(f"📸 {filename}")
                await page.goto(f"{BASE_URL}{path}", timeout=6000)
                await page.wait_for_timeout(1000)
                await page.screenshot(path=SCREENSHOTS_DIR / filename, full_page=True)
                captured += 1
                print(f"✅ {filename}")
            except Exception as e:
                print(f"❌ {filename}: {e}")
        
        await browser.close()
        
        print(f"\n🎉 Final Push Complete!")
        print(f"✅ Captured: {captured} additional screenshots")
        
        return captured

if __name__ == "__main__":
    asyncio.run(final_push_screenshots())