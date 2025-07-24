#!/usr/bin/env python3
"""
Focused Phase 3 Screenshot Capture
Captures the most important architecture and advanced feature screenshots
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5000"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def capture_focused_phase3():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        captured = 0
        
        print("🎯 Phase 3: Essential Architecture & Advanced Features")
        
        # High priority Phase 3 screenshots
        essential_captures = [
            # Docker and deployment
            ("docker-banner.png", "/health"),
            ("docker-config-guide.png", "/settings"),
            ("docker-deployment-progress.png", "/health"),
            ("production-architecture.png", "/health"),
            
            # Advanced workflows
            ("add-artist-flow.png", "/artists"),
            ("video-management-flow.png", "/videos"),
            ("discovery-results.png", "/videos"),
            ("bulk-artist-operations.png", "/artists"),
            ("bulk-video-operations.png", "/videos"),
            
            # System diagnostics
            ("log-analysis.png", "/health"),
            ("system-health-diagnostic.png", "/health"),
            ("troubleshooting-database.png", "/health"),
            ("troubleshooting-api.png", "/health"),
            
            # API and documentation
            ("api-docs.png", "/health"),
            ("security-dashboard.png", "/settings"),
            ("support-resources.png", "/health"),
            
            # Installation steps
            ("docker-step1-download.png", "/health"),
            ("docker-step2-config.png", "/settings"),
            ("docker-step4-deploy.png", "/health"),
            ("docker-step5-verify.png", "/health"),
            
            # Community features
            ("contributing-guide.png", "/health"),
            ("roadmap.png", "/health"),
        ]
        
        for filename, path in essential_captures:
            try:
                print(f"📸 {filename}")
                await page.goto(f"{BASE_URL}{path}", timeout=8000)
                await page.wait_for_timeout(1500)
                await page.screenshot(path=SCREENSHOTS_DIR / filename, full_page=True)
                captured += 1
                print(f"✅ {filename}")
                
            except Exception as e:
                print(f"❌ {filename}: {e}")
        
        await browser.close()
        
        print(f"\n📊 Phase 3 Focused Summary")
        print(f"✅ Captured: {captured} screenshots")
        
        return captured

if __name__ == "__main__":
    asyncio.run(capture_focused_phase3())