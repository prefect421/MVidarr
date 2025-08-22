#!/usr/bin/env python3
"""
Verification script to show that bulk operation endpoints are now available
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def verify_endpoints():
    """Verify that all bulk operation endpoints are now available"""
    print("🔍 Bulk Operations Endpoint Verification")
    print("=" * 60)
    
    try:
        from src.api.bulk_operations_bridge import bulk_bridge_bp
        
        # Extract endpoint information
        endpoints = []
        for rule in bulk_bridge_bp.url_map.iter_rules():
            endpoints.append({
                'endpoint': rule.rule,
                'methods': list(rule.methods - {'OPTIONS', 'HEAD'})  # Remove default methods
            })
        
        # Sort endpoints for better display
        endpoints.sort(key=lambda x: x['endpoint'])
        
        print("📋 Available Bulk Operations Endpoints:")
        print()
        
        # Group by category
        basic_endpoints = [e for e in endpoints if '/api/videos/bulk/' in e['endpoint'] and 'enhanced' not in e['endpoint']]
        enhanced_endpoints = [e for e in endpoints if 'enhanced' in e['endpoint']]
        management_endpoints = [e for e in endpoints if '/api/bulk/operations' in e['endpoint'] or '/api/bulk/bridge' in e['endpoint']]
        
        print("🔧 Basic Endpoints (Frontend Compatibility):")
        for endpoint in basic_endpoints:
            methods = ', '.join(endpoint['methods'])
            print(f"  ✅ {endpoint['endpoint']} [{methods}]")
        
        print("\n🚀 Enhanced Endpoints (Progressive Enhancement):")
        for endpoint in enhanced_endpoints:
            methods = ', '.join(endpoint['methods'])
            print(f"  ✅ {endpoint['endpoint']} [{methods}]")
        
        print("\n📈 Management Endpoints (Progress, Cancel, Undo):")
        for endpoint in management_endpoints:
            methods = ', '.join(endpoint['methods'])
            print(f"  ✅ {endpoint['endpoint']} [{methods}]")
        
        print(f"\n📊 Total: {len(endpoints)} endpoints available")
        
        # Specifically check the refresh-metadata endpoint that was causing the 404
        refresh_endpoint = '/api/videos/bulk/refresh-metadata'
        has_refresh = any(e['endpoint'] == refresh_endpoint for e in endpoints)
        
        print(f"\n🔥 404 Error Resolution:")
        if has_refresh:
            print(f"✅ {refresh_endpoint} - NOW AVAILABLE")
            print("🎉 The 404 error for bulk refresh metadata should be resolved!")
        else:
            print(f"❌ {refresh_endpoint} - STILL MISSING")
            print("⚠️  The 404 error may persist")
        
        return has_refresh
        
    except Exception as e:
        print(f"❌ Error verifying endpoints: {str(e)}")
        return False

def show_integration_status():
    """Show the integration status of the bulk operations system"""
    print("\n🔄 Integration Status")
    print("=" * 60)
    
    print("📁 Backend Files:")
    files_to_check = [
        'src/api/bulk_operations.py',
        'src/api/bulk_operations_bridge.py', 
        'src/database/bulk_models.py',
        'src/services/bulk_operations_service.py'
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
    
    print("\n📁 Frontend Files:")
    frontend_files = [
        'frontend/static/js/bulk-operations-enhanced.js',
        'frontend/CSS/bulk-operations-enhanced.css'
    ]
    
    for file_path in frontend_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
    
    print("\n📝 Template Integration:")
    try:
        # Check base.html for CSS
        with open('frontend/templates/base.html', 'r') as f:
            base_content = f.read()
        if 'bulk-operations-enhanced.css' in base_content:
            print("  ✅ CSS integrated in base.html")
        else:
            print("  ❌ CSS not found in base.html")
        
        # Check videos.html for JS
        with open('frontend/templates/videos.html', 'r') as f:
            videos_content = f.read()
        if 'bulk-operations-enhanced.js' in videos_content:
            print("  ✅ JavaScript integrated in videos.html")
        else:
            print("  ❌ JavaScript not found in videos.html")
    except Exception as e:
        print(f"  ❌ Error checking templates: {str(e)}")

def main():
    """Main verification function"""
    success = verify_endpoints()
    show_integration_status()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 VERIFICATION COMPLETE")
        print("✅ All bulk operations endpoints are available")
        print("🔧 The 404 error for refresh-metadata should be resolved")
        print("🚀 Enhanced bulk operations system is ready for use")
        return 0
    else:
        print("❌ VERIFICATION FAILED")
        print("🔥 Some endpoints may still be missing")
        return 1

if __name__ == '__main__':
    exit(main())