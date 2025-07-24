#!/usr/bin/env python3
"""
MVidarr - Manual Testing Checklist
Interactive checklist for manual testing procedures.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

class ManualTestChecklist:
    """Interactive manual testing checklist"""
    
    def __init__(self):
        self.checklist_items = []
        self.completed_items = []
        self.failed_items = []
        self.notes = []
    
    def run_checklist(self):
        """Run the interactive manual testing checklist"""
        print("🧪 MVidarr - Manual Testing Checklist")
        print("=" * 60)
        print("This interactive checklist will guide you through manual testing.")
        print("For each item, press 'p' for pass, 'f' for fail, 's' for skip, or 'q' to quit.")
        print("=" * 60)
        
        self._load_checklist()
        
        for i, item in enumerate(self.checklist_items, 1):
            self._test_item(i, item)
        
        self._generate_report()
    
    def _load_checklist(self):
        """Load the manual testing checklist"""
        self.checklist_items = [
            # Core Functionality
            ("Core", "Navigate to Dashboard - Should load without errors"),
            ("Core", "Navigate to Artists page - Should show pagination controls"),
            ("Core", "Test artist search - Enter 'test' and verify search works"),
            ("Core", "Navigate to Videos page - Should show video list with pagination"),
            ("Core", "Test video search - Enter search term and verify results"),
            ("Core", "Navigate to MvTV page - Should load video player interface"),
            ("Core", "Navigate to Settings page - Should show all configuration tabs"),
            
            # Left Sidebar Navigation
            ("UI", "Toggle sidebar - Click hamburger menu to collapse/expand"),
            ("UI", "Test sidebar on mobile - Resize browser to mobile width and test overlay"),
            ("UI", "Test all sidebar navigation links - Each should navigate correctly"),
            ("UI", "Test theme toggle - Click theme button to switch day/night mode"),
            ("UI", "Test sidebar user menu - Should show when authenticated"),
            
            # Authentication & User Management
            ("Auth", "Access admin interface - Navigate to /admin/users (may require auth)"),
            ("Auth", "Test authentication status - Check /auth/check endpoint"),
            ("Auth", "Test user management visibility - Admin users should see user mgmt option"),
            ("Auth", "Test session management - Login/logout functionality"),
            
            # Artist Management
            ("Artists", "Artist pagination - Test different page sizes (25, 50, 100, 200)"),
            ("Artists", "Artist search - Test search with various terms"),
            ("Artists", "Artist details - Click on an artist to view details"),
            ("Artists", "Artist metadata editing - Test editing artist information"),
            ("Artists", "Artist thumbnail management - Test thumbnail operations"),
            
            # Video Management  
            ("Videos", "Video pagination - Test page navigation and page size selection"),
            ("Videos", "Video search and filters - Test multi-criteria search"),
            ("Videos", "Video metadata editing - Test editing video information including genre"),
            ("Videos", "Video thumbnail management - Test thumbnail search and upload"),
            ("Videos", "Video streaming - Test video playback functionality"),
            
            # Download System
            ("Downloads", "Individual video download - Test downloading a single video"),
            ("Downloads", "Download All Wanted - Test bulk download (check for 19 failed error)"),
            ("Downloads", "Download queue - Verify download progress tracking"),
            ("Downloads", "Download settings - Test caption/subtitle download options"),
            
            # MvTV Player
            ("MvTV", "Continuous playback - Test video player auto-advance"),
            ("MvTV", "Artist dropdown - Test scrollable, searchable artist selection"),
            ("MvTV", "Cinematic mode - Test full-screen mode with overlay controls"),
            ("MvTV", "Keyboard shortcuts - Test player keyboard controls"),
            ("MvTV", "Playlist management - Test playlist creation and management"),
            
            # Theme System
            ("Theme", "Day/Night toggle - Test theme switching persistence"),
            ("Theme", "Bauhaus theme - Verify theme application across pages"),
            ("Theme", "Responsive design - Test on different screen sizes"),
            ("Theme", "Theme persistence - Refresh page and verify theme remains"),
            
            # Settings & Configuration
            ("Settings", "Database settings - Test settings load and save"),
            ("Settings", "Scheduler settings - Test auto-download configuration"),
            ("Settings", "Security settings - Test authentication requirements"),
            ("Settings", "System health - Test health diagnostics"),
            
            # Error Handling
            ("Errors", "404 pages - Navigate to non-existent page"),
            ("Errors", "API error handling - Test with network disconnected"),
            ("Errors", "Form validation - Test invalid input handling"),
            ("Errors", "Database connectivity - Test behavior during DB issues"),
            
            # Performance
            ("Performance", "Page load times - All pages should load within 2 seconds"),
            ("Performance", "Large dataset handling - Test with 100+ artists/videos"),
            ("Performance", "Search performance - Search should complete within 1 second"),
            ("Performance", "Memory usage - Monitor browser memory during testing"),
            
            # Security
            ("Security", "Role-based access - Test different user role permissions"),
            ("Security", "Admin interface protection - Non-admin users blocked"),
            ("Security", "Session security - Test session timeout and invalidation"),
            ("Security", "Input validation - Test SQL injection prevention"),
        ]
    
    def _test_item(self, number, item):
        """Test individual checklist item"""
        category, description = item
        
        print(f"\n[{number}/{len(self.checklist_items)}] {category}: {description}")
        print("-" * 80)
        
        while True:
            response = input("Result [p=pass, f=fail, s=skip, n=note, q=quit]: ").lower().strip()
            
            if response == 'p':
                self.completed_items.append(item)
                print("✅ PASSED")
                break
            elif response == 'f':
                self.failed_items.append(item)
                note = input("Failure details (optional): ")
                if note:
                    self.notes.append(f"FAILED - {category}: {description} - {note}")
                else:
                    self.notes.append(f"FAILED - {category}: {description}")
                print("❌ FAILED")
                break
            elif response == 's':
                print("⚠️ SKIPPED")
                break
            elif response == 'n':
                note = input("Enter note: ")
                self.notes.append(f"NOTE - {category}: {description} - {note}")
                print(f"📝 Note added: {note}")
                continue
            elif response == 'q':
                print("Testing stopped by user.")
                self._generate_report()
                sys.exit(0)
            else:
                print("Invalid input. Please enter 'p', 'f', 's', 'n', or 'q'.")
    
    def _generate_report(self):
        """Generate testing report"""
        print("\n" + "=" * 60)
        print("📊 MANUAL TESTING REPORT")
        print("=" * 60)
        
        total_items = len(self.checklist_items)
        passed_items = len(self.completed_items)
        failed_items = len(self.failed_items)
        tested_items = passed_items + failed_items
        
        if tested_items > 0:
            pass_rate = (passed_items / tested_items) * 100
        else:
            pass_rate = 0
        
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Items: {total_items}")
        print(f"Tested Items: {tested_items}")
        print(f"Passed: {passed_items} ✅")
        print(f"Failed: {failed_items} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        # Category breakdown
        if self.completed_items or self.failed_items:
            print("\n📋 Results by Category:")
            categories = {}
            
            for item in self.completed_items:
                category = item[0]
                categories[category] = categories.get(category, {'passed': 0, 'failed': 0})
                categories[category]['passed'] += 1
            
            for item in self.failed_items:
                category = item[0]
                categories[category] = categories.get(category, {'passed': 0, 'failed': 0})
                categories[category]['failed'] += 1
            
            for category, results in categories.items():
                total_cat = results['passed'] + results['failed']
                cat_rate = (results['passed'] / total_cat * 100) if total_cat > 0 else 0
                print(f"  {category}: {results['passed']}/{total_cat} ({cat_rate:.1f}%)")
        
        # Failed items
        if self.failed_items:
            print("\n❌ Failed Items:")
            for item in self.failed_items:
                print(f"  - {item[0]}: {item[1]}")
        
        # Notes
        if self.notes:
            print("\n📝 Notes:")
            for note in self.notes:
                print(f"  - {note}")
        
        # Save report
        report_path = Path(__file__).parent.parent.parent / 'data' / 'logs' / 'manual_test_report.txt'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write("MVidarr - Manual Testing Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Items: {total_items}\n")
            f.write(f"Tested Items: {tested_items}\n")
            f.write(f"Passed: {passed_items}\n")
            f.write(f"Failed: {failed_items}\n")
            f.write(f"Pass Rate: {pass_rate:.1f}%\n\n")
            
            if self.failed_items:
                f.write("Failed Items:\n")
                for item in self.failed_items:
                    f.write(f"  - {item[0]}: {item[1]}\n")
                f.write("\n")
            
            if self.notes:
                f.write("Notes:\n")
                for note in self.notes:
                    f.write(f"  - {note}\n")
        
        print(f"\n📝 Report saved to: {report_path}")
        
        # Overall assessment
        if pass_rate >= 95:
            print("\n🎉 EXCELLENT - System appears to be working very well!")
        elif pass_rate >= 85:
            print("\n👍 GOOD - Minor issues identified, but overall functional")
        elif pass_rate >= 70:
            print("\n⚠️ ACCEPTABLE - Several issues need attention")
        else:
            print("\n❌ NEEDS WORK - Significant issues require resolution")

def main():
    """Main entry point"""
    checklist = ManualTestChecklist()
    checklist.run_checklist()

if __name__ == '__main__':
    main()