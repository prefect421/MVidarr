#!/usr/bin/env python3
"""
Investigate theme deletion and frontend issues
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def login_session():
    """Create an authenticated session"""
    session = requests.Session()
    
    # Login
    login_response = session.post(f"{BASE_URL}/simple-login", 
                                data={"username": "admin", "password": "mvidarr"},
                                allow_redirects=False)
    
    if login_response.status_code == 302:
        print("✓ Login successful")
        return session
    else:
        print(f"✗ Login failed: {login_response.status_code}")
        return None

def test_theme_deletion():
    """Test theme deletion functionality"""
    print("\n=== Testing Theme Deletion ===")
    
    session = login_session()
    if not session:
        return
    
    # First, create a test theme to delete
    test_theme = {
        "name": "delete_test_theme",
        "display_name": "Delete Test Theme",
        "description": "A test theme for deletion testing",
        "theme_data": {
            "--bg-primary": "#ff0000",
            "--text-primary": "#ffffff"
        },
        "is_public": False
    }
    
    print("1. Creating test theme for deletion...")
    create_response = session.post(f"{BASE_URL}/api/themes", 
                                 json=test_theme,
                                 headers={'Content-Type': 'application/json'})
    
    if create_response.status_code == 201:
        theme_data = create_response.json()
        theme_id = theme_data.get('id')
        print(f"✓ Test theme created with ID: {theme_id}")
        
        # Now try to delete it
        print("2. Attempting to delete test theme...")
        delete_response = session.delete(f"{BASE_URL}/api/themes/{theme_id}")
        
        print(f"Delete response status: {delete_response.status_code}")
        print(f"Delete response: {delete_response.text}")
        
        # Check if theme still exists
        print("3. Checking if theme was actually deleted...")
        get_response = session.get(f"{BASE_URL}/api/themes/{theme_id}")
        print(f"Get theme status: {get_response.status_code}")
        
        if get_response.status_code == 404:
            print("✓ Theme was successfully deleted from database")
        else:
            print("✗ Theme still exists in database")
            
    else:
        print(f"✗ Failed to create test theme: {create_response.status_code}")
        print(f"Response: {create_response.text}")

def test_frontend_integration():
    """Test frontend integration"""
    print("\n=== Testing Frontend Integration ===")
    
    session = login_session()
    if not session:
        return
    
    # Get themes page
    themes_response = session.get(f"{BASE_URL}/themes")
    
    if themes_response.status_code == 200:
        content = themes_response.text
        
        # Check for export/import functionality
        checks = [
            ('Export All button', 'exportAllThemes()'),
            ('Import button', 'showImportDialog()'),
            ('Export Current button', 'exportCurrentTheme()'),
            ('Import modal', 'id="import-modal"'),
            ('File upload functionality', 'handleFileSelect'),
            ('Export All onclick', 'onclick="exportAllThemes()"'),
            ('Import onclick', 'onclick="showImportDialog()"')
        ]
        
        print("Frontend element checks:")
        for name, pattern in checks:
            if pattern in content:
                print(f"✓ {name} found")
            else:
                print(f"✗ {name} missing")
        
        # Check if the buttons are in the correct locations
        if '<button onclick="exportAllThemes()"' in content:
            print("✓ Export All button properly integrated")
        else:
            print("✗ Export All button not properly integrated")
            
        if '<button onclick="showImportDialog()"' in content:
            print("✓ Import button properly integrated") 
        else:
            print("✗ Import button not properly integrated")
            
    else:
        print(f"✗ Failed to get themes page: {themes_response.status_code}")

def main():
    """Run all investigations"""
    print("🔍 MVidarr Theme Issues Investigation")
    print("=" * 50)
    
    test_theme_deletion()
    test_frontend_integration()
    
    print("\n" + "=" * 50)
    print("Investigation complete!")

if __name__ == "__main__":
    main()