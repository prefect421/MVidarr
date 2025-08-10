#!/usr/bin/env python3
"""
Comprehensive MVidarr Application Test Suite
Tests all buttons, forms, and interactive elements across all pages
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright
from datetime import datetime

class MVidarrTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": [],
            "pages": {}
        }
        self.browser = None
        self.page = None
        
    async def setup(self):
        """Setup browser and page"""
        playwright = await async_playwright().__aenter__()
        self.browser = await playwright.chromium.launch(headless=True, devtools=False)
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        self.page = await context.new_page()
        
        # Listen for console errors and page errors
        self.page.on("console", self._handle_console)
        self.page.on("pageerror", self._handle_page_error)
        
    async def cleanup(self):
        """Cleanup browser"""
        if self.browser:
            await self.browser.close()
            
    def _handle_console(self, msg):
        """Handle console messages"""
        if msg.type == "error":
            print(f"Console Error: {msg.text}")
            
    def _handle_page_error(self, error):
        """Handle page errors"""
        print(f"Page Error: {error}")
        
    async def test_element(self, page_name, element_name, selector, action_type="click", test_data=None):
        """Test a single element"""
        test_name = f"{page_name}::{element_name}::{action_type}"
        self.test_results["total_tests"] += 1
        
        try:
            # Wait for element to be available
            await self.page.wait_for_selector(selector, timeout=5000)
            element = await self.page.query_selector(selector)
            
            if not element:
                raise Exception(f"Element not found: {selector}")
                
            # Perform the action
            if action_type == "click":
                await element.click()
                await asyncio.sleep(0.5)  # Wait for any effects
                
            elif action_type == "fill":
                if test_data:
                    await element.fill(test_data)
                    await asyncio.sleep(0.3)
                else:
                    raise Exception("No test data provided for fill action")
                    
            elif action_type == "select":
                if test_data:
                    await element.select_option(test_data)
                    await asyncio.sleep(0.3)
                    
            elif action_type == "check":
                await element.check()
                await asyncio.sleep(0.3)
                
            elif action_type == "hover":
                await element.hover()
                await asyncio.sleep(0.3)
                
            # Test passed
            self.test_results["passed_tests"] += 1
            print(f"✅ {test_name}")
            return True
            
        except Exception as e:
            # Test failed
            self.test_results["failed_tests"] += 1
            error_info = {
                "test": test_name,
                "selector": selector,
                "error": str(e),
                "action": action_type
            }
            self.test_results["errors"].append(error_info)
            print(f"❌ {test_name}: {e}")
            return False
            
    async def test_navigation(self):
        """Test basic navigation and page loading"""
        print("🧪 Testing Navigation...")
        
        pages_to_test = [
            ("Dashboard", "/"),
            ("Videos", "/videos"),
            ("Artists", "/artists"),
            ("MvTV", "/mvtv"),
            ("Settings", "/settings")
        ]
        
        for page_name, path in pages_to_test:
            try:
                print(f"\n📄 Loading {page_name} page...")
                await self.page.goto(self.base_url + path)
                await self.page.wait_for_load_state('networkidle', timeout=10000)
                
                # Check if page loaded successfully
                title = await self.page.title()
                if "MVidarr" not in title and page_name != "Dashboard":
                    raise Exception(f"Page title doesn't contain MVidarr: {title}")
                    
                self.test_results["pages"][page_name] = {
                    "loaded": True,
                    "tests": [],
                    "errors": []
                }
                
                print(f"✅ {page_name} page loaded successfully")
                
            except Exception as e:
                self.test_results["pages"][page_name] = {
                    "loaded": False,
                    "error": str(e),
                    "tests": [],
                    "errors": []
                }
                print(f"❌ Failed to load {page_name}: {e}")
                
    async def test_dashboard_page(self):
        """Test Dashboard page elements"""
        print("\\n🧪 Testing Dashboard Page...")
        
        await self.page.goto(self.base_url + "/")
        await self.page.wait_for_load_state('networkidle')
        
        # Test main action cards
        dashboard_tests = [
            ("Browse Videos Button", "a[href='/videos']", "click"),
            ("Browse Artists Button", "a[href='/artists']", "click"),
            ("User Profile Button", "a[href='/settings']", "click"),
            ("Settings Button", "a[href='/settings']", "click"),
        ]
        
        for test_name, selector, action in dashboard_tests:
            await self.test_element("Dashboard", test_name, selector, action)
            # Return to dashboard after each test
            await self.page.goto(self.base_url + "/")
            await asyncio.sleep(0.5)
            
    async def test_videos_page(self):
        """Test Videos page elements"""
        print("\\n🧪 Testing Videos Page...")
        
        await self.page.goto(self.base_url + "/videos")
        await self.page.wait_for_load_state('networkidle')
        
        # Test header actions
        videos_tests = [
            ("Add Video Button", "button[onclick*='showAddVideoModal']", "click"),
            ("Search & Filter Button", "button[onclick*='toggleSearchPanel']", "click"),
            ("Refresh Button", "button[onclick*='refreshVideos']", "click"),
            ("Refresh Thumbnails Button", "button[onclick*='refreshThumbnails']", "click"),
            ("Refresh Metadata Button", "button[onclick*='refreshAllMetadata']", "click"),
            ("Select All Checkbox", "#selectAllVideos", "check"),
            ("Bulk Actions Button", "button[onclick*='toggleBulkActionsPanel']", "click"),
        ]
        
        for test_name, selector, action in videos_tests:
            result = await self.test_element("Videos", test_name, selector, action)
            if not result:
                continue
                
            # Wait and close any modals that might have opened
            try:
                close_btn = await self.page.query_selector(".modal .close, .modal .btn:has-text('Cancel'), .modal .btn:has-text('Close')")
                if close_btn:
                    await close_btn.click()
                    await asyncio.sleep(0.3)
            except:
                pass
                
        # Test bulk actions (if panel is open)
        try:
            bulk_panel = await self.page.query_selector("#bulkActionsPanel")
            if bulk_panel:
                bulk_tests = [
                    ("Bulk Download", "button[onclick*='bulkDownloadSelected']", "click"),
                    ("Bulk Delete", "button[onclick*='bulkDeleteSelected']", "click"),
                    ("Bulk Check Quality", "button[onclick*='bulkCheckQuality']", "click"),
                    ("Bulk Upgrade Quality", "button[onclick*='bulkUpgradeQuality']", "click"),
                    ("Bulk Transcode", "button[onclick*='bulkTranscode']", "click"),
                ]
                
                for test_name, selector, action in bulk_tests:
                    await self.test_element("Videos", test_name, selector, action)
        except:
            pass
            
    async def test_artists_page(self):
        """Test Artists page elements"""
        print("\\n🧪 Testing Artists Page...")
        
        await self.page.goto(self.base_url + "/artists")
        await self.page.wait_for_load_state('networkidle')
        
        # Test header actions
        artists_tests = [
            ("Add Artist Button", "button[onclick*='showAddArtistModal']", "click"),
            ("Search & Filter Button", "button[onclick*='toggleArtistSearchPanel']", "click"),
            ("Refresh Button", "button[onclick*='refreshArtists']", "click"),
            ("Scan Missing Thumbnails", "button[onclick*='scanMissingThumbnails']", "click"),
            ("Select All Checkbox", "#selectAllArtists", "check"),
            ("Bulk Actions Button", "button[onclick*='toggleBulkArtistActionsPanel']", "click"),
        ]
        
        for test_name, selector, action in artists_tests:
            result = await self.test_element("Artists", test_name, selector, action)
            if not result:
                continue
                
            # Close any modals
            try:
                close_btn = await self.page.query_selector(".modal .close, .modal .btn:has-text('Cancel')")
                if close_btn:
                    await close_btn.click()
                    await asyncio.sleep(0.3)
            except:
                pass
                
        # Test bulk actions if available
        try:
            bulk_panel = await self.page.query_selector("#bulkActionsToolbar")
            if bulk_panel and await bulk_panel.is_visible():
                bulk_tests = [
                    ("Bulk Video Discovery", "button[onclick*='bulkVideoDiscovery']", "click"),
                    ("Bulk Refresh Metadata", "button[onclick*='bulkRefreshMetadata']", "click"),
                    ("Bulk IMVDb Link", "button[onclick*='bulkIMVDbLink']", "click"),
                ]
                
                for test_name, selector, action in bulk_tests:
                    await self.test_element("Artists", test_name, selector, action)
        except:
            pass
            
    async def test_mvtv_page(self):
        """Test MvTV page elements"""
        print("\\n🧪 Testing MvTV Page...")
        
        await self.page.goto(self.base_url + "/mvtv")
        await self.page.wait_for_load_state('networkidle')
        
        # Test MvTV controls
        mvtv_tests = [
            ("Play Button", "#playBtn", "click"),
            ("Shuffle Toggle", "#shuffleBtn", "click"),
            ("Cinematic Mode Button", "button[onclick*='toggleCinematicMode']", "click"),
        ]
        
        for test_name, selector, action in mvtv_tests:
            await self.test_element("MvTV", test_name, selector, action)
            await asyncio.sleep(0.5)
            
    async def test_settings_page(self):
        """Test Settings page elements"""
        print("\\n🧪 Testing Settings Page...")
        
        await self.page.goto(self.base_url + "/settings")
        await self.page.wait_for_load_state('networkidle')
        
        # Test settings tabs
        settings_tests = [
            ("General Tab", "button[onclick*='general-tab']", "click"),
            ("Security Tab", "button[onclick*='security-tab']", "click"), 
            ("Services Tab", "button[onclick*='services-tab']", "click"),
            ("Downloads Tab", "button[onclick*='downloads-tab']", "click"),
            ("Database Tab", "button[onclick*='database-tab']", "click"),
            ("System Tab", "button[onclick*='system-tab']", "click"),
            ("Themes Tab", "button[onclick*='themes-tab']", "click"),
        ]
        
        for test_name, selector, action in settings_tests:
            await self.test_element("Settings", test_name, selector, action)
            await asyncio.sleep(0.3)
            
        # Test some form elements (if visible)
        try:
            form_tests = [
                ("App Port Input", "#app_port", "fill", "5000"),
                ("Debug Mode Select", "#debug_mode", "select", "false"),
                ("Save Settings Button", "button[onclick*='saveSettings']", "click"),
            ]
            
            for test_name, selector, action, data in form_tests:
                if action == "fill" or action == "select":
                    await self.test_element("Settings", test_name, selector, action, data)
                else:
                    await self.test_element("Settings", test_name, selector, action)
        except:
            pass
            
    async def test_search_functionality(self):
        """Test search functionality across pages"""
        print("\\n🧪 Testing Search Functionality...")
        
        search_tests = [
            ("Videos", "/videos", "input[placeholder*='Search videos']", "test search"),
            ("Artists", "/artists", "input[placeholder*='Search artists']", "test artist"),
        ]
        
        for page_name, path, selector, test_data in search_tests:
            try:
                await self.page.goto(self.base_url + path)
                await self.page.wait_for_load_state('networkidle')
                
                # Try to open search panel first
                search_toggle = await self.page.query_selector("button[onclick*='toggleSearchPanel'], button[onclick*='toggleArtistSearchPanel']")
                if search_toggle:
                    await search_toggle.click()
                    await asyncio.sleep(0.5)
                
                await self.test_element(page_name, "Search Input", selector, "fill", test_data)
                
            except Exception as e:
                print(f"❌ Search test failed for {page_name}: {e}")
                
    async def run_comprehensive_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive MVidarr Application Test Suite")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Run all test suites
            await self.test_navigation()
            await self.test_dashboard_page()
            await self.test_videos_page()
            await self.test_artists_page()
            await self.test_mvtv_page()
            await self.test_settings_page()
            await self.test_search_functionality()
            
        except Exception as e:
            print(f"❌ Critical test error: {e}")
            
        finally:
            await self.cleanup()
            
        # Generate report
        self.generate_report()
        
    def generate_report(self):
        """Generate test report"""
        print("\\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']} ✅")
        print(f"Failed: {self.test_results['failed_tests']} ❌")
        
        if self.test_results['failed_tests'] > 0:
            print(f"\\n🚨 FAILED TESTS ({len(self.test_results['errors'])}):")
            print("-" * 40)
            
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"{i}. {error['test']}")
                print(f"   Selector: {error['selector']}")
                print(f"   Error: {error['error']}")
                print(f"   Action: {error['action']}")
                print()
        
        # Save detailed report to file
        report_file = f"/home/mike/mvidarr/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
            
        print(f"📄 Detailed report saved to: {report_file}")
        
        return self.test_results

async def main():
    """Main test runner"""
    tester = MVidarrTester()
    results = await tester.run_comprehensive_tests()
    return results

if __name__ == "__main__":
    asyncio.run(main())