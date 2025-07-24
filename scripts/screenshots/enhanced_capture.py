#!/usr/bin/env python3
"""
MVidarr - Advanced Screenshot Capture
Enhanced screenshot capture with intelligent element detection and data seeding
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
import random
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class ScreenshotTask:
    filename: str
    url: str
    description: str
    selectors: List[str]  # Multiple selectors to try
    full_page: bool = False
    mobile: bool = False
    setup_steps: Optional[List[Dict]] = None
    priority: str = "medium"
    wait_conditions: Optional[List[str]] = None
    data_seed: Optional[Dict] = None

class EnhancedScreenshotCapture:
    def __init__(self, base_url: str = "http://localhost:5000", output_dir: str = None):
        self.base_url = base_url
        self.output_dir = Path(output_dir or project_root / "docs" / "screenshots")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        log_file = self.output_dir / f'screenshot_capture_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Screenshot tasks
        self.tasks = self._define_screenshot_tasks()
        
    def _define_screenshot_tasks(self) -> List[ScreenshotTask]:
        """Define comprehensive screenshot tasks with multiple selector fallbacks"""
        return [
            # High Priority - Essential Screenshots
            ScreenshotTask(
                filename="dashboard-overview.png",
                url="/",
                description="Main dashboard showing statistics and overview",
                selectors=[".dashboard-container", ".main-content", "main", "body"],
                full_page=True,
                priority="high",
                wait_conditions=["networkidle", "load"]
            ),
            
            ScreenshotTask(
                filename="artist-management.png",
                url="/artists",
                description="Artist management interface with thumbnails",
                selectors=[".artists-container", ".artist-list", ".artists-page", "main"],
                full_page=True,
                priority="high",
                wait_conditions=["networkidle"]
            ),
            
            ScreenshotTask(
                filename="video-discovery.png",
                url="/videos",
                description="Video discovery and import screen",
                selectors=[".videos-container", ".video-library", ".videos-page", "main"],
                full_page=True,
                priority="high",
                wait_conditions=["networkidle"]
            ),
            
            ScreenshotTask(
                filename="system-health.png",
                url="/settings/health",
                description="System health dashboard",
                selectors=[".health-dashboard", ".system-health", ".health-status", ".settings-content"],
                full_page=True,
                priority="high",
                setup_steps=[
                    {"type": "navigation", "url": "/settings"},
                    {"type": "click", "selectors": ["a[href*='health']", "button:has-text('Health')", ".health-tab"]},
                    {"type": "wait", "duration": 2000}
                ]
            ),
            
            # Dashboard Components
            ScreenshotTask(
                filename="stats-cards.png",
                url="/",
                description="Statistics cards section",
                selectors=[
                    ".stats-container", ".dashboard-stats", ".metrics-cards", 
                    ".statistics", ".stat-cards", ".overview-stats"
                ],
                wait_conditions=["networkidle"]
            ),
            
            ScreenshotTask(
                filename="quick-actions.png",
                url="/",
                description="Quick action buttons",
                selectors=[
                    ".quick-actions", ".action-buttons", ".dashboard-actions",
                    ".primary-actions", ".main-actions", ".action-bar"
                ]
            ),
            
            # Artist Management Detailed
            ScreenshotTask(
                filename="artist-list-view.png",
                url="/artists",
                description="Artist list with search and filters",
                selectors=[".artist-list", ".artists-grid", ".artists-container"],
                full_page=True
            ),
            
            ScreenshotTask(
                filename="add-artist-search.png",
                url="/artists",
                description="Artist search during addition",
                selectors=[".add-artist-modal", ".artist-search", ".modal-content"],
                setup_steps=[
                    {"type": "click", "selectors": ["button:has-text('Add Artist')", ".add-artist-btn", ".btn-add-artist"]},
                    {"type": "wait", "duration": 2000}
                ]
            ),
            
            ScreenshotTask(
                filename="artist-detail.png",
                url="/artists",
                description="Artist detail page with tabs",
                selectors=[".artist-detail", ".artist-page", ".artist-info"],
                full_page=True,
                setup_steps=[
                    {"type": "click", "selectors": [".artist-item:first-child", ".artist-card:first-child", ".artist-row:first-child"]},
                    {"type": "wait", "duration": 3000}
                ]
            ),
            
            # Video Management
            ScreenshotTask(
                filename="video-library-overview.png",
                url="/videos",
                description="Complete video library",
                selectors=[".video-library", ".videos-container", ".video-grid"],
                full_page=True
            ),
            
            ScreenshotTask(
                filename="video-cards.png",
                url="/videos",
                description="Video card view",
                selectors=[".video-grid", ".video-cards", ".videos-grid", ".video-list"]
            ),
            
            ScreenshotTask(
                filename="advanced-search.png",
                url="/videos",
                description="Advanced search with filters",
                selectors=[".search-panel", ".filters", ".advanced-search"],
                setup_steps=[
                    {"type": "click", "selectors": ["button:has-text('Search')", ".search-btn", ".filter-btn"]},
                    {"type": "wait", "duration": 1500}
                ]
            ),
            
            # Settings Screenshots
            ScreenshotTask(
                filename="settings-overview.png",
                url="/settings",
                description="Main settings interface",
                selectors=[".settings-container", ".settings-page", "main"],
                full_page=True
            ),
            
            ScreenshotTask(
                filename="external-services.png",
                url="/settings",
                description="API keys configuration",
                selectors=[".external-services", ".api-settings", ".settings-content"],
                setup_steps=[
                    {"type": "click", "selectors": ["a[href*='external']", "button:has-text('External')", ".external-tab"]},
                    {"type": "wait", "duration": 2000}
                ]
            ),
            
            ScreenshotTask(
                filename="theme-selector.png",
                url="/settings",
                description="Theme selection interface",
                selectors=[".theme-selector", ".ui-settings", ".appearance-settings"],
                setup_steps=[
                    {"type": "click", "selectors": ["a[href*='theme']", "button:has-text('Theme')", ".theme-tab"]},
                    {"type": "wait", "duration": 2000}
                ]
            ),
            
            # Mobile Screenshots
            ScreenshotTask(
                filename="mobile-overview.png",
                url="/",
                description="Mobile interface overview",
                selectors=["body"],
                full_page=True,
                mobile=True
            ),
            
            ScreenshotTask(
                filename="mobile-navigation.png",
                url="/",
                description="Mobile navigation",
                selectors=[".mobile-nav", ".nav-menu", ".sidebar"],
                mobile=True,
                setup_steps=[
                    {"type": "click", "selectors": [".mobile-menu", ".hamburger", ".nav-toggle", ".menu-btn"]},
                    {"type": "wait", "duration": 1000}
                ]
            ),
            
            # Performance and Health
            ScreenshotTask(
                filename="health-dashboard.png",
                url="/settings/health",
                description="System health monitoring",
                selectors=[".health-dashboard", ".system-status", ".diagnostics"],
                full_page=True
            ),
            
            ScreenshotTask(
                filename="performance-monitor.png",
                url="/settings",
                description="Performance monitoring interface",
                selectors=[".performance-metrics", ".system-monitor", ".stats-panel"],
                setup_steps=[
                    {"type": "click", "selectors": ["a[href*='performance']", "button:has-text('Performance')", ".performance-tab"]},
                    {"type": "wait", "duration": 2000}
                ]
            ),
        ]
    
    async def setup_browser_context(self, playwright, mobile=False, theme="light"):
        """Setup browser context with appropriate settings"""
        browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context_options = {
            'ignore_https_errors': True,
            'java_script_enabled': True,
        }
        
        if mobile:
            context_options.update({
                'viewport': {'width': 375, 'height': 812},
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
                'device_scale_factor': 2,
                'is_mobile': True,
                'has_touch': True
            })
        else:
            context_options.update({
                'viewport': {'width': 1920, 'height': 1080},
                'device_scale_factor': 1
            })
        
        context = await browser.new_context(**context_options)
        return browser, context
    
    async def execute_setup_steps(self, page, steps: List[Dict]):
        """Execute setup steps before capturing screenshot"""
        for i, step in enumerate(steps):
            try:
                step_type = step.get('type')
                self.logger.debug(f"Executing step {i+1}: {step_type}")
                
                if step_type == 'click':
                    selectors = step.get('selectors', [])
                    clicked = False
                    
                    for selector in selectors:
                        try:
                            await page.click(selector, timeout=3000)
                            clicked = True
                            self.logger.debug(f"Clicked: {selector}")
                            break
                        except:
                            continue
                    
                    if not clicked:
                        self.logger.warning(f"Could not click any selector: {selectors}")
                
                elif step_type == 'wait':
                    duration = step.get('duration', 1000)
                    await page.wait_for_timeout(duration)
                
                elif step_type == 'navigation':
                    url = step.get('url')
                    if url:
                        await page.goto(f"{self.base_url}{url}", wait_until='networkidle')
                
                elif step_type == 'fill':
                    selectors = step.get('selectors', [])
                    value = step.get('value', '')
                    
                    for selector in selectors:
                        try:
                            await page.fill(selector, value)
                            break
                        except:
                            continue
                
                elif step_type == 'scroll':
                    selector = step.get('selector')
                    if selector:
                        await page.evaluate(f"document.querySelector('{selector}').scrollIntoView()")
                    else:
                        await page.evaluate("window.scrollBy(0, 500)")
                
            except Exception as e:
                self.logger.warning(f"Setup step {i+1} failed: {e}")
                continue
    
    async def find_best_selector(self, page, selectors: List[str]) -> Optional[str]:
        """Find the best selector that exists on the page"""
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    # Check if element is visible
                    is_visible = await element.is_visible()
                    if is_visible:
                        self.logger.debug(f"Found visible element: {selector}")
                        return selector
            except:
                continue
        
        # If no visible elements found, try any existing element
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    self.logger.debug(f"Found element (may not be visible): {selector}")
                    return selector
            except:
                continue
        
        return None
    
    async def capture_screenshot(self, page, task: ScreenshotTask) -> bool:
        """Capture a single screenshot with intelligent element detection"""
        try:
            # Navigate to URL
            full_url = f"{self.base_url}{task.url}"
            self.logger.info(f"📸 Capturing {task.filename} from {full_url}")
            
            await page.goto(full_url, wait_until='networkidle', timeout=30000)
            
            # Wait for page stability
            await page.wait_for_timeout(2000)
            
            # Execute setup steps
            if task.setup_steps:
                await self.execute_setup_steps(page, task.setup_steps)
                await page.wait_for_timeout(1500)  # Allow UI to settle
            
            # Wait for specific conditions
            if task.wait_conditions:
                for condition in task.wait_conditions:
                    if condition == "networkidle":
                        await page.wait_for_load_state('networkidle')
                    elif condition == "load":
                        await page.wait_for_load_state('load')
            
            # Prepare screenshot options
            screenshot_path = self.output_dir / task.filename
            screenshot_options = {
                'path': screenshot_path,
                'type': 'png',
                'quality': 90
            }
            
            # Determine screenshot target
            if task.full_page:
                # Full page screenshot
                screenshot_options['full_page'] = True
                await page.screenshot(**screenshot_options)
                self.logger.info(f"✅ Full page screenshot: {task.filename}")
                
            else:
                # Element-specific screenshot
                best_selector = await self.find_best_selector(page, task.selectors)
                
                if best_selector:
                    try:
                        element = await page.query_selector(best_selector)
                        await element.screenshot(**screenshot_options)
                        self.logger.info(f"✅ Element screenshot ({best_selector}): {task.filename}")
                    except Exception as e:
                        self.logger.warning(f"Element screenshot failed, using viewport: {e}")
                        del screenshot_options['full_page']
                        await page.screenshot(**screenshot_options)
                        self.logger.info(f"✅ Viewport screenshot: {task.filename}")
                else:
                    # Fallback to viewport screenshot
                    await page.screenshot(**screenshot_options)
                    self.logger.info(f"✅ Viewport screenshot (no element found): {task.filename}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to capture {task.filename}: {e}")
            return False
    
    async def check_application_health(self) -> bool:
        """Check if MVidarr is running and responsive"""
        try:
            async with async_playwright() as playwright:
                browser, context = await self.setup_browser_context(playwright)
                page = await context.new_page()
                
                # Try health endpoint first
                try:
                    response = await page.goto(f"{self.base_url}/api/health", timeout=10000)
                    if response.status == 200:
                        await browser.close()
                        return True
                except:
                    pass
                
                # Try main page
                try:
                    response = await page.goto(self.base_url, timeout=10000)
                    if response.status == 200:
                        await browser.close()
                        return True
                except:
                    pass
                
                await browser.close()
                return False
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def capture_all_screenshots(self, priority: str = None, limit: int = None) -> Dict[str, int]:
        """Capture all screenshots with optional filtering"""
        
        # Health check
        if not await self.check_application_health():
            self.logger.error(f"❌ MVidarr is not accessible at {self.base_url}")
            self.logger.info("Please ensure the application is running:")
            self.logger.info("  Docker: docker-compose -f docker-compose.production.yml up -d")
            self.logger.info("  Local: python app.py")
            return {"success": 0, "failed": 0, "total": 0}
        
        # Filter tasks
        tasks = self.tasks
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        if limit:
            tasks = tasks[:limit]
        
        self.logger.info(f"🚀 Starting screenshot capture: {len(tasks)} tasks")
        
        results = {"success": 0, "failed": 0, "total": len(tasks)}
        
        async with async_playwright() as playwright:
            # Capture desktop screenshots
            desktop_tasks = [t for t in tasks if not t.mobile]
            if desktop_tasks:
                self.logger.info(f"📱 Capturing {len(desktop_tasks)} desktop screenshots")
                browser, context = await self.setup_browser_context(playwright, mobile=False)
                page = await context.new_page()
                
                for task in desktop_tasks:
                    if await self.capture_screenshot(page, task):
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                    
                    # Small delay between captures
                    await asyncio.sleep(0.5)
                
                await browser.close()
            
            # Capture mobile screenshots
            mobile_tasks = [t for t in tasks if t.mobile]
            if mobile_tasks:
                self.logger.info(f"📱 Capturing {len(mobile_tasks)} mobile screenshots")
                browser, context = await self.setup_browser_context(playwright, mobile=True)
                page = await context.new_page()
                
                for task in mobile_tasks:
                    if await self.capture_screenshot(page, task):
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                    
                    await asyncio.sleep(0.5)
                
                await browser.close()
        
        success_rate = (results["success"] / results["total"] * 100) if results["total"] > 0 else 0
        self.logger.info(f"📊 Capture complete: {results['success']}/{results['total']} successful ({success_rate:.1f}%)")
        
        return results
    
    def create_capture_report(self, results: Dict[str, int]) -> str:
        """Create detailed capture report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_rate = (results["success"] / results["total"] * 100) if results["total"] > 0 else 0
        
        # List captured files
        captured_files = []
        if self.output_dir.exists():
            captured_files = [f.name for f in self.output_dir.glob("*.png")]
        
        report = f"""# MVidarr Screenshot Capture Report

**Generated**: {timestamp}  
**Output Directory**: `{self.output_dir}`

## Summary Statistics
- **Total Screenshots**: {results["total"]}
- **Successfully Captured**: {results["success"]}
- **Failed**: {results["failed"]}
- **Success Rate**: {success_rate:.1f}%

## Captured Screenshots ({len(captured_files)} files)
{chr(10).join(f"- ✅ {filename}" for filename in sorted(captured_files))}

## Status
{"✅ **SUCCESS**: Screenshot capture completed successfully!" if success_rate >= 80 else "⚠️ **PARTIAL**: Some screenshots failed - check application state"}

## Next Steps
1. Review captured screenshots in `{self.output_dir}`
2. Update documentation references as needed
3. {"Consider re-running failed captures" if results["failed"] > 0 else "Deploy updated documentation"}

## Troubleshooting
If screenshots are missing or incomplete:
1. Ensure MVidarr is fully loaded with sample data
2. Check browser console for JavaScript errors
3. Verify all UI components are properly rendered
4. Consider running with `--priority high` for essential screenshots only

---
*Generated by MVidarr Screenshot Capture Tool*
"""
        
        report_path = self.output_dir / f"capture_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        return report

async def main():
    """Enhanced main function with comprehensive options"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enhanced MVidarr Screenshot Capture',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_capture.py                    # Capture all screenshots
  python enhanced_capture.py --priority high   # High priority only
  python enhanced_capture.py --limit 10        # First 10 screenshots
  python enhanced_capture.py --mobile-only     # Mobile screenshots only
        """
    )
    
    parser.add_argument('--base-url', default='http://localhost:5000', 
                       help='Base URL of MVidarr application')
    parser.add_argument('--output-dir', 
                       help='Output directory for screenshots')
    parser.add_argument('--priority', choices=['high', 'medium', 'low'], 
                       help='Filter by priority level')
    parser.add_argument('--limit', type=int, 
                       help='Maximum number of screenshots to capture')
    parser.add_argument('--mobile-only', action='store_true', 
                       help='Capture only mobile screenshots')
    parser.add_argument('--desktop-only', action='store_true', 
                       help='Capture only desktop screenshots')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create capture instance
    capture = EnhancedScreenshotCapture(
        base_url=args.base_url, 
        output_dir=args.output_dir
    )
    
    # Run capture
    results = await capture.capture_all_screenshots(
        priority=args.priority,
        limit=args.limit
    )
    
    # Generate report
    report = capture.create_capture_report(results)
    print("\n" + "="*60)
    print(report)
    
    return results["success"] > 0

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Screenshot capture interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Screenshot capture failed: {e}")
        sys.exit(1)