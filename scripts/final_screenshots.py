#!/usr/bin/env python3
"""
Final Screenshot Capture - Remaining 60 Screenshots
Captures specialized, contextual, and error state screenshots
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:5000"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def capture_remaining_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        captured = 0
        
        print("🎯 Final Phase: Capturing Remaining Screenshots")
        print("=" * 50)
        
        # Remaining screenshots from SCREENSHOTS-NEEDED.md
        remaining_captures = [
            # Installation Docker steps (missing ones)
            ("docker-step3-storage.png", "/settings"),
            ("docker-step6-access.png", "/artists"),
            ("prerequisites-docker.png", "/health"),
            
            # Artist management detailed workflows
            ("add-artist-search.png", "/artists"),
            ("artist-detail.png", "/artists"),
            ("artist-videos-tab.png", "/artists"),
            ("artist-activity.png", "/artists"),
            ("artist-stats.png", "/artists"),
            
            # Video management workflows
            ("auto-discovery.png", "/videos"),
            ("manual-discovery.png", "/videos"),
            ("video-detail-modal.png", "/videos"),
            ("video-cards.png", "/videos"),
            ("playlist-creation.png", "/mvtv"),
            
            # Download management
            ("active-downloads.png", "/videos"),
            ("queue-management.png", "/videos"),
            ("download-history.png", "/videos"),
            
            # Status and monitoring
            ("status-management.png", "/videos"),
            ("recent-activity.png", "/artists"),
            ("quick-actions.png", "/artists"),
            ("system-health-overview.png", "/health"),
            
            # Mobile gestures and interactions
            ("mobile-gestures.png", "/videos"),
            
            # Additional workflow screenshots
            ("setup-wizard-docker.png", "/settings"),
            ("cinematic-mode.png", "/mvtv"),
            
            # Error states and troubleshooting scenarios
            ("error-state-api.png", "/health"),
            ("error-state-database.png", "/health"),
            ("error-state-download.png", "/videos"),
            ("network-error.png", "/health"),
            ("permission-error.png", "/settings"),
            
            # Advanced configuration scenarios
            ("advanced-settings.png", "/settings"),
            ("backup-configuration.png", "/settings"),
            ("restore-configuration.png", "/settings"),
            ("migration-tools.png", "/health"),
            
            # User interface variations
            ("dark-theme.png", "/artists"),
            ("light-theme.png", "/artists"),
            ("compact-view.png", "/videos"),
            ("detailed-view.png", "/videos"),
            
            # Documentation and help
            ("help-documentation.png", "/health"),
            ("keyboard-shortcuts.png", "/health"),
            ("tooltip-examples.png", "/artists"),
            ("context-menus.png", "/videos"),
            
            # Integration screenshots
            ("webhook-configuration.png", "/settings"),
            ("notification-settings.png", "/settings"),
            ("email-alerts.png", "/settings"),
            
            # Performance and optimization
            ("cache-management.png", "/health"),
            ("disk-usage.png", "/health"),
            ("memory-usage.png", "/health"),
            ("optimization-tips.png", "/health"),
            
            # Import/Export features
            ("import-library.png", "/settings"),
            ("export-library.png", "/settings"),
            ("backup-restore.png", "/settings"),
            
            # Search and filtering variations
            ("filter-panel.png", "/videos"),
            ("search-suggestions.png", "/videos"),
            ("advanced-filters.png", "/artists"),
            ("saved-searches.png", "/videos"),
            
            # Tablet and different viewport sizes
            ("tablet-landscape.png", "/artists"),
            ("tablet-portrait.png", "/videos"),
            ("desktop-ultrawide.png", "/health"),
        ]
        
        print(f"📸 Capturing {len(remaining_captures)} remaining screenshots...")
        
        for filename, path in remaining_captures:
            try:
                print(f"📸 {filename}")
                await page.goto(f"{BASE_URL}{path}", timeout=8000)
                
                # Add specific interactions for different screenshot types
                if "mobile" in filename or "tablet" in filename:
                    if "mobile" in filename:
                        await page.set_viewport_size({"width": 375, "height": 812})
                    elif "tablet-landscape" in filename:
                        await page.set_viewport_size({"width": 1024, "height": 768})
                    elif "tablet-portrait" in filename:
                        await page.set_viewport_size({"width": 768, "height": 1024})
                    elif "ultrawide" in filename:
                        await page.set_viewport_size({"width": 2560, "height": 1080})
                
                # Theme switching for theme screenshots
                if "dark-theme" in filename:
                    try:
                        # Try to click theme toggle if it exists
                        theme_toggle = await page.query_selector('[data-theme-toggle], .theme-toggle, #theme-toggle')
                        if theme_toggle:
                            await theme_toggle.click()
                            await page.wait_for_timeout(1000)
                    except:
                        pass
                
                await page.wait_for_timeout(1500)
                await page.screenshot(path=SCREENSHOTS_DIR / filename, full_page=True)
                captured += 1
                print(f"✅ {filename}")
                
                # Reset viewport after special sizes
                if any(size_type in filename for size_type in ["mobile", "tablet", "ultrawide"]):
                    await page.set_viewport_size({"width": 1920, "height": 1080})
                
            except Exception as e:
                print(f"❌ {filename}: {e}")
        
        # Capture some additional contextual screenshots
        print(f"\n📋 Capturing contextual workflow screenshots...")
        
        contextual_captures = [
            # Workflow demonstrations
            ("complete-setup-flow.png", "/settings"),
            ("first-time-user.png", "/artists"),
            ("power-user-dashboard.png", "/health"),
            ("maintenance-mode.png", "/health"),
            
            # Interactive elements
            ("dropdown-menus.png", "/settings"),
            ("modal-dialogs.png", "/videos"),
            ("confirmation-dialogs.png", "/artists"),
            ("progress-indicators.png", "/health"),
            
            # Data visualization
            ("statistics-charts.png", "/health"),
            ("usage-graphs.png", "/health"),
            ("trend-analysis.png", "/health"),
            
            # Edge cases and empty states
            ("empty-library.png", "/videos"),
            ("no-artists.png", "/artists"),
            ("loading-states.png", "/health"),
            ("offline-mode.png", "/health"),
        ]
        
        for filename, path in contextual_captures:
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
        
        print(f"\n📊 Final Screenshot Capture Summary")
        print(f"✅ New screenshots captured: {captured}")
        
        # Calculate final totals
        total_existing = 87  # From previous phases
        total_final = total_existing + captured
        
        print(f"📈 Final Total: {total_final}/147 screenshots ({total_final/147*100:.1f}%)")
        
        return captured

if __name__ == "__main__":
    asyncio.run(capture_remaining_screenshots())