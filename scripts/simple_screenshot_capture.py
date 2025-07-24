#!/usr/bin/env python3
"""
Simple Screenshot Capture Script for MVidarr Enhanced
Captures screenshots of specific pages without authentication issues
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

BASE_URL = "http://localhost:5000"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"

# Ensure screenshots directory exists
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def capture_single_screenshot(page, filename, url_path, wait_time=3000):
    """Capture a single screenshot"""
    try:
        print(f"📸 Capturing {filename}...")
        
        # Navigate to the specific URL
        full_url = f"{BASE_URL}{url_path}"
        print(f"   → Navigating to: {full_url}")
        
        await page.goto(full_url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(wait_time)
        
        # Take screenshot
        screenshot_path = SCREENSHOTS_DIR / filename
        await page.screenshot(path=screenshot_path, full_page=True)
        
        print(f"✅ Successfully captured {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to capture {filename}: {str(e)}")
        return False

async def main():
    print("🚀 MVidarr Enhanced Simple Screenshot Capture")
    print("=============================================")
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set viewport for consistent screenshots
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        captured = 0
        failed = 0
        
        # Define screenshots to capture with specific URLs
        screenshots = [
            # Main interface screenshots
            ("dashboard-overview.png", "/artists"),  # Since root redirects to artists
            ("artist-management.png", "/artists"),
            ("video-library-overview.png", "/videos"),
            ("video-cards.png", "/videos"),
            ("video-list.png", "/videos"),
            
            # Settings screenshots
            ("settings-overview.png", "/settings"),
            ("external-services.png", "/settings"),
            ("download-settings.png", "/settings"),
            ("ui-settings.png", "/settings"),
            ("system-settings.png", "/settings"),
            
            # Health and system
            ("system-health.png", "/health"),
            ("health-dashboard.png", "/health"),
            
            # MvTV and player
            ("mvtv-mode.png", "/mvtv"),
            ("video-player.png", "/mvtv"),
            ("streaming-interface.png", "/mvtv"),
            
            # Advanced search
            ("advanced-search.png", "/videos"),
            
            # Artist workflows
            ("artist-list-view.png", "/artists"),
            ("artist-configuration.png", "/artists"),
            
            # Video workflows  
            ("video-detail.png", "/videos"),
            ("status-indicators.png", "/videos"),
            
            # Theme and UI
            ("theme-selector.png", "/settings"),
        ]
        
        # Mobile screenshots (smaller viewport)
        mobile_screenshots = [
            ("mobile-overview.png", "/artists"),
            ("mobile-navigation.png", "/artists"),
            ("mobile-settings.png", "/settings"),
            ("mobile-interface.png", "/videos"),
        ]
        
        print(f"\n📱 Capturing desktop screenshots...")
        for filename, url_path in screenshots:
            if await capture_single_screenshot(page, filename, url_path):
                captured += 1
            else:
                failed += 1
        
        print(f"\n📱 Switching to mobile viewport for mobile screenshots...")
        await page.set_viewport_size({"width": 375, "height": 812})  # iPhone X size
        
        for filename, url_path in mobile_screenshots:
            if await capture_single_screenshot(page, filename, url_path):
                captured += 1
            else:
                failed += 1
        
        await browser.close()
        
        print(f"\n📊 Screenshot Capture Summary")
        print(f"✅ Successfully captured: {captured}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Progress: {captured}/147 screenshots ({captured/147*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())