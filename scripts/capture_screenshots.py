#!/usr/bin/env python3
"""
Screenshot Capture Script for MVidarr Documentation
Captures all required screenshots systematically using Playwright
"""

import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright
import time
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

BASE_URL = "http://localhost:5000"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "docs" / "screenshots"

# Ensure screenshots directory exists
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

class ScreenshotCapture:
    def __init__(self):
        self.browser = None
        self.page = None
        self.captured = []
        self.failed = []
        
    async def setup(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        
        # Set viewport for consistent screenshots
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Wait for application to be ready
        await self.page.goto(BASE_URL)
        await self.page.wait_for_timeout(2000)
        
        # Handle authentication if login page is shown
        await self.handle_authentication()
        
    async def handle_authentication(self):
        """Handle authentication if required"""
        try:
            # First, capture the login screen for documentation
            current_url = self.page.url
            if "/login" in current_url or "login" in (await self.page.title()).lower():
                print("🔐 Found login page - capturing for documentation...")
                await self.capture_screenshot("auth-login-screen.png")
                
                print("🔐 Attempting authentication...")
                
                # Wait a bit more for the page to fully load
                await self.page.wait_for_timeout(2000)
                
                # Try multiple selector combinations for username
                username_selectors = [
                    'input[name="username"]',
                    'input[id="username"]', 
                    'input[type="text"]',
                    'input[placeholder*="username" i]',
                    'input[placeholder*="user" i]',
                    '#username',
                    '.username input'
                ]
                
                username_input = None
                for selector in username_selectors:
                    username_input = await self.page.query_selector(selector)
                    if username_input:
                        print(f"✅ Found username input with selector: {selector}")
                        break
                
                # Try multiple selector combinations for password
                password_selectors = [
                    'input[name="password"]',
                    'input[id="password"]',
                    'input[type="password"]',
                    'input[placeholder*="password" i]',
                    '#password',
                    '.password input'
                ]
                
                password_input = None
                for selector in password_selectors:
                    password_input = await self.page.query_selector(selector)
                    if password_input:
                        print(f"✅ Found password input with selector: {selector}")
                        break
                
                if username_input and password_input:
                    # Clear any existing values and fill
                    await username_input.clear()
                    await password_input.clear()
                    
                    await username_input.type("admin", delay=100)
                    await password_input.type("MVidarr@dmin123", delay=100)
                    
                    print("🔐 Credentials entered, looking for submit button...")
                    
                    # Try multiple selector combinations for submit button
                    submit_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("Login")',
                        'button:has-text("Sign In")',
                        'button:has-text("Submit")',
                        '.login-button',
                        '#login-button',
                        'form button',
                        'button'  # fallback
                    ]
                    
                    login_button = None
                    for selector in submit_selectors:
                        login_button = await self.page.query_selector(selector)
                        if login_button:
                            print(f"✅ Found login button with selector: {selector}")
                            break
                    
                    if login_button:
                        await login_button.click()
                        print("🔐 Login button clicked, waiting for response...")
                        
                        # Wait for navigation or page change
                        try:
                            await self.page.wait_for_load_state('networkidle', timeout=10000)
                        except:
                            await self.page.wait_for_timeout(5000)
                        
                        # Check if login was successful
                        new_url = self.page.url
                        page_content = await self.page.content()
                        
                        if "/login" not in new_url and "login" not in (await self.page.title()).lower():
                            print("✅ Authentication successful - can now capture app screenshots")
                            return True
                        else:
                            print("❌ Still on login page - authentication may have failed")
                            print(f"Current URL: {new_url}")
                            # Check for error messages
                            error_elements = await self.page.query_selector_all('.error, .alert-danger, .error-message')
                            for error in error_elements:
                                error_text = await error.inner_text()
                                if error_text.strip():
                                    print(f"Error message: {error_text}")
                    else:
                        print("❌ Could not find login button")
                        # Debug: print all buttons
                        all_buttons = await self.page.query_selector_all('button')
                        print(f"Found {len(all_buttons)} buttons on page")
                        for i, btn in enumerate(all_buttons[:5]):  # Show first 5
                            text = await btn.inner_text()
                            print(f"Button {i+1}: '{text.strip()}'")
                else:
                    print("❌ Could not find username or password inputs")
                    # Debug: print all input elements
                    all_inputs = await self.page.query_selector_all('input')
                    print(f"Found {len(all_inputs)} input elements:")
                    for i, inp in enumerate(all_inputs):
                        inp_type = await inp.get_attribute('type')
                        inp_name = await inp.get_attribute('name')
                        inp_id = await inp.get_attribute('id')
                        placeholder = await inp.get_attribute('placeholder')
                        print(f"Input {i+1}: type='{inp_type}', name='{inp_name}', id='{inp_id}', placeholder='{placeholder}'")
                        
            return False
        except Exception as e:
            print(f"❌ Authentication handling failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    async def cleanup(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def capture_screenshot(self, filename, url_path="", wait_selector=None, wait_time=2000):
        """Capture a single screenshot"""
        try:
            print(f"📸 Capturing {filename}...")
            
            # Navigate to the page
            full_url = f"{BASE_URL}{url_path}" if url_path else BASE_URL
            await self.page.goto(full_url)
            
            # Wait for page to load
            await self.page.wait_for_timeout(wait_time)
            
            # Wait for specific selector if provided
            if wait_selector:
                try:
                    await self.page.wait_for_selector(wait_selector, timeout=10000)
                except:
                    print(f"⚠️  Selector {wait_selector} not found for {filename}")
            
            # Take screenshot
            screenshot_path = SCREENSHOTS_DIR / filename
            await self.page.screenshot(path=screenshot_path, full_page=True)
            
            self.captured.append(filename)
            print(f"✅ Captured {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to capture {filename}: {str(e)}")
            self.failed.append((filename, str(e)))
            return False
    
    async def capture_phase1_essentials(self):
        """Capture Phase 1 essential screenshots"""
        print("\n🎯 Phase 1: Essential Screenshots")
        
        # Main README.md screenshots
        await self.capture_screenshot("dashboard-overview.png", "/", ".dashboard-container")
        await self.capture_screenshot("artist-management.png", "/artists", ".artists-container")
        
        # Check if we have any artists to show video discovery
        try:
            await self.page.goto(f"{BASE_URL}/artists")
            await self.page.wait_for_timeout(2000)
            
            # Look for artist cards
            artist_cards = await self.page.query_selector_all(".artist-card")
            if artist_cards:
                # Click on first artist
                await artist_cards[0].click()
                await self.page.wait_for_timeout(2000)
                await self.capture_screenshot("video-discovery.png")
        except:
            print("⚠️  No artists found for video discovery screenshot")
        
        await self.capture_screenshot("advanced-search.png", "/videos?search=true")
        
        # Try to capture system health
        await self.capture_screenshot("system-health.png", "/health")
        
        # Dashboard components
        await self.capture_screenshot("dashboard-main.png", "/")
        await self.capture_screenshot("stats-cards.png", "/", ".stats-section")
        
    async def capture_phase1_interface(self):
        """Capture interface screenshots"""
        print("\n🎨 Interface Screenshots")
        
        # Artist management
        await self.capture_screenshot("artist-list-view.png", "/artists")
        
        # Try video library
        await self.capture_screenshot("video-library-overview.png", "/videos")
        await self.capture_screenshot("video-cards.png", "/videos?view=cards")
        await self.capture_screenshot("video-list.png", "/videos?view=list")
        
    async def capture_phase1_config(self):
        """Capture configuration screenshots"""
        print("\n⚙️ Configuration Screenshots")
        
        await self.capture_screenshot("settings-overview.png", "/settings")
        await self.capture_screenshot("external-services.png", "/settings?tab=api")
        await self.capture_screenshot("download-settings.png", "/settings?tab=download")
        await self.capture_screenshot("ui-settings.png", "/settings?tab=ui")
        await self.capture_screenshot("system-settings.png", "/settings?tab=system")
        
    async def capture_phase1_additional(self):
        """Capture additional Phase 1 screenshots"""
        print("\n🔧 Additional Interface Screenshots")
        
        # Try to capture login screen (if authentication is enabled)
        try:
            await self.page.goto(f"{BASE_URL}/login")
            await self.page.wait_for_timeout(2000)
            await self.capture_screenshot("initial-login.png")
        except:
            print("⚠️  Login page not accessible or not configured")
        
        # Health dashboard
        await self.capture_screenshot("health-dashboard.png", "/health")
        
        # MvTV if available
        try:
            await self.capture_screenshot("mvtv-mode.png", "/mvtv")
        except:
            print("⚠️  MvTV page not accessible")
            
        # Download queue if available
        try:
            await self.capture_screenshot("download-queue.png", "/downloads")
        except:
            print("⚠️  Downloads page not accessible")
            
        # Theme selector
        await self.capture_screenshot("theme-selector.png", "/settings?tab=ui")
        
    async def capture_artist_workflow(self):
        """Capture artist management workflow screenshots"""
        print("\n👤 Artist Management Workflow")
        
        # Try to add a new artist
        try:
            await self.page.goto(f"{BASE_URL}/artists")
            await self.page.wait_for_timeout(2000)
            
            # Look for "Add Artist" button or similar
            add_buttons = await self.page.query_selector_all("button, a")
            for button in add_buttons:
                text = await button.inner_text()
                if "add" in text.lower() and "artist" in text.lower():
                    await button.click()
                    await self.page.wait_for_timeout(2000)
                    await self.capture_screenshot("add-artist-search.png")
                    break
        except:
            print("⚠️  Could not capture add artist workflow")
            
        # Artist configuration and discovery
        await self.capture_screenshot("artist-configuration.png", "/artists?view=config")
        
    async def capture_video_workflow(self):
        """Capture video management workflow screenshots"""
        print("\n🎥 Video Management Workflow")
        
        await self.capture_screenshot("video-detail.png", "/videos?detail=true")
        await self.capture_screenshot("status-indicators.png", "/videos")
        
        # Try to capture video player if videos exist
        try:
            await self.page.goto(f"{BASE_URL}/videos")
            await self.page.wait_for_timeout(2000)
            
            # Look for video elements
            video_elements = await self.page.query_selector_all(".video-card, .video-item")
            if video_elements and len(video_elements) > 0:
                await video_elements[0].click()
                await self.page.wait_for_timeout(2000)
                await self.capture_screenshot("video-player.png")
        except:
            print("⚠️  Could not capture video player")
        
    async def run_phase1(self):
        """Run Phase 1 screenshot capture"""
        await self.setup()
        
        try:
            await self.capture_phase1_essentials()
            await self.capture_phase1_interface()
            await self.capture_phase1_config()
            await self.capture_phase1_additional()
            await self.capture_artist_workflow()
            await self.capture_video_workflow()
            
        finally:
            await self.cleanup()
            
        return self.captured, self.failed
    
    async def capture_mobile_screenshots(self):
        """Capture mobile-responsive screenshots"""
        print("\n📱 Mobile Interface Screenshots")
        
        # Set mobile viewport
        await self.page.set_viewport_size({"width": 375, "height": 812})  # iPhone X size
        
        await self.capture_screenshot("mobile-overview.png", "/")
        await self.capture_screenshot("mobile-navigation.png", "/artists")
        await self.capture_screenshot("mobile-settings.png", "/settings")
        await self.capture_screenshot("mobile-interface.png", "/videos")
        
        # Reset to desktop viewport
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        
    async def capture_troubleshooting_screenshots(self):
        """Capture troubleshooting and diagnostic screenshots"""
        print("\n🔧 Troubleshooting Screenshots")
        
        await self.capture_screenshot("performance-monitor.png", "/health")
        await self.capture_screenshot("log-viewer.png", "/health?view=logs")
        await self.capture_screenshot("system-health-diagnostic.png", "/health?diagnostic=true")
        
    async def capture_installation_screenshots(self):
        """Capture installation-related screenshots"""
        print("\n🚀 Installation Screenshots")
        
        # These would be mock/example screenshots for documentation
        await self.capture_screenshot("installation-banner.png", "/")
        await self.capture_screenshot("welcome-screen.png", "/setup")
        await self.capture_screenshot("api-setup.png", "/settings?tab=api")
        await self.capture_screenshot("storage-setup.png", "/settings?tab=system")
        await self.capture_screenshot("theme-selection-setup.png", "/settings?tab=ui")
        
    async def capture_workflow_screenshots(self):
        """Capture complete workflow screenshots"""
        print("\n📋 Workflow Screenshots")
        
        # Complete workflows
        await self.capture_screenshot("add-artist-flow.png", "/artists?action=add")
        await self.capture_screenshot("video-management-flow.png", "/videos?workflow=true")
        
        # Player and streaming
        await self.capture_screenshot("video-player.png", "/mvtv")
        await self.capture_screenshot("player-controls.png", "/mvtv?controls=true")
        await self.capture_screenshot("streaming-interface.png", "/mvtv")
        
    async def run_phase2(self):
        """Run Phase 2 screenshot capture"""
        await self.setup()
        
        try:
            await self.capture_mobile_screenshots()
            await self.capture_troubleshooting_screenshots()
            await self.capture_installation_screenshots()
            await self.capture_workflow_screenshots()
            
        finally:
            await self.cleanup()
            
        return self.captured, self.failed
    
    async def run_comprehensive(self):
        """Run comprehensive screenshot capture (Phase 1 + 2)"""
        await self.setup()
        
        try:
            # Phase 1
            await self.capture_phase1_essentials()
            await self.capture_phase1_interface()
            await self.capture_phase1_config()
            await self.capture_phase1_additional()
            await self.capture_artist_workflow()
            await self.capture_video_workflow()
            
            # Phase 2
            await self.capture_mobile_screenshots()
            await self.capture_troubleshooting_screenshots()
            await self.capture_installation_screenshots()
            await self.capture_workflow_screenshots()
            
        finally:
            await self.cleanup()
            
        return self.captured, self.failed
    
    def print_summary(self):
        """Print capture summary"""
        print(f"\n📊 Screenshot Capture Summary")
        print(f"✅ Successfully captured: {len(self.captured)}")
        print(f"❌ Failed: {len(self.failed)}")
        
        if self.captured:
            print(f"\n📸 Captured files:")
            for filename in self.captured:
                print(f"  • {filename}")
                
        if self.failed:
            print(f"\n❌ Failed captures:")
            for filename, error in self.failed:
                print(f"  • {filename}: {error}")

async def main():
    print("🚀 MVidarr Screenshot Capture")
    print("=====================================")
    
    # Check if application is running
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL) as response:
                if response.status not in [200, 302]:
                    print(f"❌ Application not responding at {BASE_URL}")
                    return
    except:
        print(f"❌ Application not reachable at {BASE_URL}")
        print("Please ensure MVidarr is running with: python3 app.py")
        return
    
    print(f"✅ Application detected at {BASE_URL}")
    
    # Start comprehensive capture (Phase 1 + 2)
    capture = ScreenshotCapture()
    captured, failed = await capture.run_comprehensive()
    capture.print_summary()
    
    # Update progress
    total_screenshots = 147  # From SCREENSHOTS-NEEDED.md
    progress = len(captured)
    print(f"\n📈 Progress: {progress}/{total_screenshots} screenshots ({progress/total_screenshots*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())