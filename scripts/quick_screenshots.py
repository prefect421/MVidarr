#!/usr/bin/env python3
"""
Quick Screenshot Capture for MVidarr Enhanced Documentation
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5000"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def quick_capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Comprehensive screenshots with shorter timeout
        captures = [
            # Main interface
            ("dashboard-overview.png", "/artists"),
            ("artist-management.png", "/artists"), 
            ("video-library-overview.png", "/videos"),
            ("video-cards.png", "/videos"),
            ("video-list.png", "/videos"),
            
            # Settings and configuration
            ("settings-overview.png", "/settings"),
            ("external-services.png", "/settings"),
            ("download-settings.png", "/settings"),
            ("ui-settings.png", "/settings"),
            ("system-settings.png", "/settings"),
            ("theme-selector.png", "/settings"),
            
            # System and health
            ("system-health.png", "/health"),
            ("health-dashboard.png", "/health"),
            ("performance-monitor.png", "/health"),
            
            # Video player and streaming
            ("mvtv-mode.png", "/mvtv"),
            ("video-player.png", "/mvtv"),
            ("streaming-interface.png", "/mvtv"),
            ("player-controls.png", "/mvtv"),
            
            # Search and filtering
            ("advanced-search.png", "/videos"),
            ("artist-list-view.png", "/artists"),
            ("status-indicators.png", "/videos"),
            
            # Installation and setup mockups
            ("installation-banner.png", "/artists"),
            ("welcome-screen.png", "/artists"),
            ("api-setup.png", "/settings"),
            ("storage-setup.png", "/settings"),
            ("theme-selection-setup.png", "/settings"),
        ]
        
        captured = 0
        
        for filename, path in captures:
            try:
                print(f"📸 {filename}")
                await page.goto(f"{BASE_URL}{path}", timeout=10000)
                await page.wait_for_timeout(2000)
                await page.screenshot(path=SCREENSHOTS_DIR / filename, full_page=True)
                captured += 1
                print(f"✅ {filename}")
            except Exception as e:
                print(f"❌ {filename}: {e}")
        
        # Mobile screenshots
        print(f"\n📱 Switching to mobile viewport...")
        await page.set_viewport_size({"width": 375, "height": 812})  # iPhone X
        
        mobile_captures = [
            ("mobile-overview.png", "/artists"),
            ("mobile-navigation.png", "/artists"),
            ("mobile-settings.png", "/settings"),
            ("mobile-interface.png", "/videos"),
            ("mobile-video-player.png", "/mvtv"),
        ]
        
        for filename, path in mobile_captures:
            try:
                print(f"📱 {filename}")
                await page.goto(f"{BASE_URL}{path}", timeout=10000)
                await page.wait_for_timeout(2000)
                await page.screenshot(path=SCREENSHOTS_DIR / filename, full_page=True)
                captured += 1
                print(f"✅ {filename}")
            except Exception as e:
                print(f"❌ {filename}: {e}")
        
        await browser.close()
        print(f"\n📊 Total captured: {captured} screenshots")
        print(f"📈 Progress: {captured}/147 screenshots ({captured/147*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(quick_capture())