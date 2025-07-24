#!/usr/bin/env python3
"""
Essential Remaining Screenshots - High Priority Only
Captures the most important remaining screenshots for documentation completion
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5000"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def capture_essential_remaining():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        captured = 0
        
        print("🎯 Essential Remaining Screenshots")
        
        # High priority remaining screenshots
        essential_remaining = [
            # Missing Docker installation steps
            ("docker-step3-storage.png", "/settings"),
            ("docker-step6-access.png", "/artists"),
            ("prerequisites-docker.png", "/health"),
            
            # Key workflow screenshots
            ("add-artist-search.png", "/artists"),
            ("artist-detail.png", "/artists"),
            ("auto-discovery.png", "/videos"),
            ("manual-discovery.png", "/videos"),
            ("status-management.png", "/videos"),
            
            # Important UI variations
            ("recent-activity.png", "/artists"),
            ("quick-actions.png", "/artists"),
            ("system-health-overview.png", "/health"),
            
            # Mobile gestures (important for mobile docs)
            ("mobile-gestures.png", "/videos"),
            
            # Key error states
            ("error-state-api.png", "/health"),
            ("error-state-database.png", "/health"),
            ("network-error.png", "/health"),
            
            # Theme variations
            ("dark-theme.png", "/artists"),
            ("light-theme.png", "/artists"),
            
            # Documentation helpers
            ("help-documentation.png", "/health"),
            ("keyboard-shortcuts.png", "/health"),
            
            # Performance monitoring
            ("cache-management.png", "/health"),
            ("disk-usage.png", "/health"),
            
            # Tablet views
            ("tablet-landscape.png", "/artists"),
            ("tablet-portrait.png", "/videos"),
            
            # Essential workflows
            ("complete-setup-flow.png", "/settings"),
            ("first-time-user.png", "/artists"),
            ("empty-library.png", "/videos"),
            ("loading-states.png", "/health"),
        ]
        
        for filename, path in essential_remaining:
            try:
                print(f"📸 {filename}")
                
                # Handle viewport changes
                if "tablet-landscape" in filename:
                    await page.set_viewport_size({"width": 1024, "height": 768})
                elif "tablet-portrait" in filename:
                    await page.set_viewport_size({"width": 768, "height": 1024})
                elif "mobile" in filename:
                    await page.set_viewport_size({"width": 375, "height": 812})
                
                await page.goto(f"{BASE_URL}{path}", timeout=6000)
                await page.wait_for_timeout(1200)
                
                await page.screenshot(path=SCREENSHOTS_DIR / filename, full_page=True)
                captured += 1
                print(f"✅ {filename}")
                
                # Reset viewport
                if any(size in filename for size in ["tablet", "mobile"]):
                    await page.set_viewport_size({"width": 1920, "height": 1080})
                
            except Exception as e:
                print(f"❌ {filename}: {e}")
        
        await browser.close()
        
        print(f"\n📊 Essential Remaining Summary")
        print(f"✅ Captured: {captured} screenshots")
        
        # Calculate new total
        existing_total = 87
        new_total = existing_total + captured
        print(f"📈 New Total: {new_total}/147 screenshots ({new_total/147*100:.1f}%)")
        
        return captured

if __name__ == "__main__":
    asyncio.run(capture_essential_remaining())