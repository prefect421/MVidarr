#!/usr/bin/env python3
"""
MVidarr - Screenshot Capture Script
Automated screenshot capture using Playwright for documentation
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class ScreenshotSpec:
    filename: str
    url: str
    description: str
    selector: Optional[str] = None
    wait_for: Optional[str] = None
    full_page: bool = False
    mobile: bool = False
    setup_actions: Optional[List[Dict]] = None
    priority: str = "medium"

class ScreenshotCapture:
    def __init__(self, base_url: str = "http://localhost:5000", output_dir: str = None):
        self.base_url = base_url
        self.output_dir = Path(output_dir or project_root / "docs" / "screenshots")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'screenshot_capture.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Screenshot specifications
        self.screenshots = self._define_screenshots()
        
    def _define_screenshots(self) -> List[ScreenshotSpec]:
        """Define all screenshots to capture"""
        return [
            # Priority Screenshots (Essential)
            ScreenshotSpec(
                filename="dashboard-overview.png",
                url="/",
                description="Main dashboard showing statistics and overview",
                full_page=True,
                priority="high"
            ),
            ScreenshotSpec(
                filename="artist-management.png",
                url="/artists",
                description="Artist management interface with thumbnails",
                full_page=True,
                priority="high"
            ),
            ScreenshotSpec(
                filename="video-discovery.png",
                url="/videos",
                description="Video discovery and import screen",
                full_page=True,
                priority="high"
            ),
            ScreenshotSpec(
                filename="system-health.png",
                url="/settings",
                description="System health dashboard",
                selector="#health-section",
                setup_actions=[
                    {"action": "click", "selector": "a[href*='health']"}
                ],
                priority="high"
            ),
            
            # Interface Screenshots - Dashboard
            ScreenshotSpec(
                filename="dashboard-main.png",
                url="/",
                description="Complete dashboard view",
                full_page=True
            ),
            ScreenshotSpec(
                filename="stats-cards.png",
                url="/",
                description="Statistics cards section",
                selector=".stats-container, .dashboard-stats, .metrics-cards",
            ),
            ScreenshotSpec(
                filename="quick-actions.png",
                url="/",
                description="Quick action buttons",
                selector=".quick-actions, .action-buttons, .dashboard-actions",
            ),
            ScreenshotSpec(
                filename="recent-activity.png",
                url="/",
                description="Recent activity panel",
                selector=".recent-activity, .activity-panel, .latest-activity",
            ),
            
            # Artist Management Screenshots
            ScreenshotSpec(
                filename="artist-list-view.png",
                url="/artists",
                description="Artist list with search and filters",
                full_page=True
            ),
            ScreenshotSpec(
                filename="add-artist-search.png",
                url="/artists",
                description="Artist search during addition",
                setup_actions=[
                    {"action": "click", "selector": "button:has-text('Add Artist'), .add-artist-btn"},
                    {"action": "wait", "timeout": 2000}
                ]
            ),
            ScreenshotSpec(
                filename="artist-detail.png",
                url="/artists",
                description="Artist detail page with tabs",
                setup_actions=[
                    {"action": "click", "selector": ".artist-item:first-child, .artist-row:first-child"},
                    {"action": "wait", "timeout": 2000}
                ],
                full_page=True
            ),
            ScreenshotSpec(
                filename="bulk-artist-operations.png",
                url="/artists",
                description="Bulk operations interface",
                setup_actions=[
                    {"action": "click", "selector": "input[type='checkbox']:first"},
                    {"action": "click", "selector": "input[type='checkbox']:nth-child(2)"},
                    {"action": "wait", "timeout": 1000}
                ]
            ),
            
            # Video Management Screenshots
            ScreenshotSpec(
                filename="video-library-overview.png",
                url="/videos",
                description="Complete video library",
                full_page=True
            ),
            ScreenshotSpec(
                filename="video-cards.png",
                url="/videos",
                description="Video card view",
                selector=".video-grid, .video-cards, .videos-container"
            ),
            ScreenshotSpec(
                filename="video-list.png",
                url="/videos",
                description="Video list view",
                setup_actions=[
                    {"action": "click", "selector": "button:has-text('List'), .view-list"}
                ],
                selector=".video-list, .videos-table"
            ),
            ScreenshotSpec(
                filename="video-detail.png",
                url="/videos",
                description="Video detail modal",
                setup_actions=[
                    {"action": "click", "selector": ".video-item:first-child .video-title, .video-card:first-child"},
                    {"action": "wait", "timeout": 2000}
                ]
            ),
            ScreenshotSpec(
                filename="advanced-search.png",
                url="/videos",
                description="Advanced search with filters",
                setup_actions=[
                    {"action": "click", "selector": "button:has-text('Search'), .search-btn, .advanced-search"}
                ]
            ),
            
            # Settings Screenshots
            ScreenshotSpec(
                filename="settings-overview.png",
                url="/settings",
                description="Main settings interface",
                full_page=True
            ),
            ScreenshotSpec(
                filename="external-services.png",
                url="/settings",
                description="API keys configuration",
                setup_actions=[
                    {"action": "click", "selector": "a[href*='external'], button:has-text('External')"}
                ]
            ),
            ScreenshotSpec(
                filename="download-settings.png",
                url="/settings",
                description="Download preferences",
                setup_actions=[
                    {"action": "click", "selector": "a[href*='download'], button:has-text('Download')"}
                ]
            ),
            ScreenshotSpec(
                filename="ui-settings.png",
                url="/settings",
                description="UI customization options",
                setup_actions=[
                    {"action": "click", "selector": "a[href*='ui'], button:has-text('Interface'), button:has-text('UI')"}
                ]
            ),
            
            # Theme Screenshots
            ScreenshotSpec(
                filename="theme-selector.png",
                url="/settings",
                description="Theme selection interface",
                setup_actions=[
                    {"action": "click", "selector": "a[href*='theme'], button:has-text('Theme'), .theme-selector"}
                ]
            ),
            
            # Mobile Screenshots
            ScreenshotSpec(
                filename="mobile-overview.png",
                url="/",
                description="Mobile interface overview",
                full_page=True,
                mobile=True
            ),
            ScreenshotSpec(
                filename="mobile-navigation.png",
                url="/",
                description="Mobile navigation",
                mobile=True,
                setup_actions=[
                    {"action": "click", "selector": ".mobile-menu, .hamburger, .nav-toggle"}
                ]
            ),
            ScreenshotSpec(
                filename="mobile-interface.png",
                url="/artists",
                description="Mobile artist interface",
                full_page=True,
                mobile=True
            ),
            
            # Health and Monitoring
            ScreenshotSpec(
                filename="health-dashboard.png",
                url="/settings",
                description="System health monitoring",
                setup_actions=[
                    {"action": "click", "selector": "a[href*='health'], button:has-text('Health')"}
                ],
                full_page=True
            ),
            ScreenshotSpec(
                filename="performance-monitor.png",
                url="/settings",
                description="Performance monitoring interface",
                setup_actions=[
                    {"action": "click", "selector": "a[href*='performance'], button:has-text('Performance')"}
                ]
            ),
            
            # Installation and Setup
            ScreenshotSpec(
                filename="initial-login.png",
                url="/",
                description="First time login screen",
                setup_actions=[
                    {"action": "evaluate", "script": "localStorage.clear(); sessionStorage.clear();"}
                ]
            ),
            ScreenshotSpec(
                filename="welcome-screen.png",
                url="/setup",
                description="Welcome/setup screen"
            ),
            ScreenshotSpec(
                filename="api-setup.png",
                url="/settings",
                description="API key configuration during setup",
                setup_actions=[
                    {"action": "click", "selector": "a[href*='api'], button:has-text('API')"}
                ]
            ),
        ]
    
    async def setup_browser_context(self, playwright, mobile=False):
        """Setup browser context with appropriate viewport"""
        if mobile:
            # Mobile viewport
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 375, 'height': 812},
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            )
        else:
            # Desktop viewport
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
        
        return browser, context
    
    async def perform_setup_actions(self, page, actions: List[Dict]):
        """Perform setup actions before taking screenshot"""
        for action in actions:
            try:
                action_type = action.get('action')
                
                if action_type == 'click':
                    selector = action.get('selector')
                    await page.click(selector, timeout=5000)
                    
                elif action_type == 'wait':
                    timeout = action.get('timeout', 1000)
                    await page.wait_for_timeout(timeout)
                    
                elif action_type == 'fill':
                    selector = action.get('selector')
                    value = action.get('value', '')
                    await page.fill(selector, value)
                    
                elif action_type == 'evaluate':
                    script = action.get('script')
                    await page.evaluate(script)
                    
                elif action_type == 'wait_for':
                    selector = action.get('selector')
                    await page.wait_for_selector(selector, timeout=10000)
                    
            except Exception as e:
                self.logger.warning(f"Setup action failed: {action_type} - {e}")
                # Continue with other actions
                pass
    
    async def capture_screenshot(self, page, spec: ScreenshotSpec) -> bool:
        """Capture a single screenshot"""
        try:
            # Navigate to URL
            full_url = f"{self.base_url}{spec.url}"
            self.logger.info(f"Capturing {spec.filename} from {full_url}")
            
            await page.goto(full_url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to be ready
            await page.wait_for_timeout(2000)
            
            # Perform setup actions if specified
            if spec.setup_actions:
                await self.perform_setup_actions(page, spec.setup_actions)
                await page.wait_for_timeout(1000)  # Allow time for UI changes
            
            # Wait for specific element if specified
            if spec.wait_for:
                await page.wait_for_selector(spec.wait_for, timeout=10000)
            
            # Prepare screenshot options
            screenshot_options = {
                'path': self.output_dir / spec.filename,
                'type': 'png'
            }
            
            if spec.full_page:
                screenshot_options['full_page'] = True
            
            # Take screenshot
            if spec.selector:
                # Screenshot specific element
                try:
                    element = await page.wait_for_selector(spec.selector, timeout=5000)
                    await element.screenshot(**screenshot_options)
                except:
                    # Fallback to full page if selector fails
                    await page.screenshot(**screenshot_options)
            else:
                # Screenshot full page or viewport
                await page.screenshot(**screenshot_options)
            
            self.logger.info(f"✅ Captured {spec.filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to capture {spec.filename}: {e}")
            return False
    
    async def check_app_health(self) -> bool:
        """Check if the MVidarr application is running and healthy"""
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Try to access the health endpoint
                try:
                    await page.goto(f"{self.base_url}/api/health", timeout=10000)
                    content = await page.content()
                    await browser.close()
                    return "healthy" in content.lower() or "status" in content.lower()
                except:
                    # Try main page as fallback
                    await page.goto(self.base_url, timeout=10000)
                    await browser.close()
                    return True
                    
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def capture_all_screenshots(self, priority_filter: str = None) -> Dict[str, int]:
        """Capture all screenshots with optional priority filtering"""
        if not await self.check_app_health():
            self.logger.error("❌ MVidarr application is not accessible. Please ensure it's running at {self.base_url}")
            return {"success": 0, "failed": 0, "skipped": 0}
        
        # Filter screenshots by priority if specified
        screenshots_to_capture = self.screenshots
        if priority_filter:
            screenshots_to_capture = [s for s in self.screenshots if s.priority == priority_filter]
        
        self.logger.info(f"🚀 Starting screenshot capture: {len(screenshots_to_capture)} screenshots")
        
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        async with async_playwright() as playwright:
            # Capture desktop screenshots
            desktop_screenshots = [s for s in screenshots_to_capture if not s.mobile]
            if desktop_screenshots:
                browser, context = await self.setup_browser_context(playwright, mobile=False)
                page = await context.new_page()
                
                for spec in desktop_screenshots:
                    success = await self.capture_screenshot(page, spec)
                    if success:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                
                await browser.close()
            
            # Capture mobile screenshots
            mobile_screenshots = [s for s in screenshots_to_capture if s.mobile]
            if mobile_screenshots:
                browser, context = await self.setup_browser_context(playwright, mobile=True)
                page = await context.new_page()
                
                for spec in mobile_screenshots:
                    success = await self.capture_screenshot(page, spec)
                    if success:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                
                await browser.close()
        
        self.logger.info(f"📊 Screenshot capture complete: {results['success']} success, {results['failed']} failed")
        return results
    
    def generate_summary_report(self, results: Dict[str, int]):
        """Generate a summary report of the screenshot capture"""
        total = sum(results.values())
        success_rate = (results['success'] / total * 100) if total > 0 else 0
        
        report = f"""
# Screenshot Capture Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Screenshots**: {total}
- **Successful**: {results['success']}
- **Failed**: {results['failed']}
- **Success Rate**: {success_rate:.1f}%

## Output Directory
`{self.output_dir}`

## Next Steps
{'✅ Review captured screenshots and update documentation' if success_rate > 80 else '❌ Fix application issues and retry failed screenshots'}

---
*Generated by MVidarr Screenshot Capture Tool*
"""
        
        with open(self.output_dir / 'capture_report.md', 'w') as f:
            f.write(report)
        
        return report

async def main():
    """Main function to run screenshot capture"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Capture MVidarr screenshots')
    parser.add_argument('--base-url', default='http://localhost:5000', help='Base URL of MVidarr application')
    parser.add_argument('--output-dir', help='Output directory for screenshots')
    parser.add_argument('--priority', choices=['high', 'medium', 'low'], help='Filter by priority level')
    parser.add_argument('--mobile-only', action='store_true', help='Capture only mobile screenshots')
    parser.add_argument('--desktop-only', action='store_true', help='Capture only desktop screenshots')
    
    args = parser.parse_args()
    
    # Create screenshot capture instance
    capture = ScreenshotCapture(base_url=args.base_url, output_dir=args.output_dir)
    
    # Run capture
    results = await capture.capture_all_screenshots(priority_filter=args.priority)
    
    # Generate report
    report = capture.generate_summary_report(results)
    print(report)
    
    return results['success'] > 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)