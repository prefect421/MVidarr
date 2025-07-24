#!/usr/bin/env python3
"""
Migration script to add SSL/TLS enforcement setting
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

def add_ssl_tls_setting():
    """Add SSL/TLS enforcement setting to database"""
    
    try:
        # Initialize app and database
        from src.config.config import Config
        config = Config()
        
        from src.database.connection import init_db
        from flask import Flask
        app = Flask(__name__)
        app.config.from_object(config)
        init_db(app)
        
        # Load database settings
        config.load_from_database()
        
        # Add the SSL/TLS setting
        from src.services.settings_service import SettingsService
        
        # Check if setting already exists
        existing_value = SettingsService.get('ssl_required', None)
        
        if existing_value is None:
            # Add new setting
            SettingsService.set(
                'ssl_required', 
                'false',
                description='Enforce SSL/TLS connections by redirecting HTTP to HTTPS'
            )
            print("✅ Added ssl_required setting (default: false)")
        else:
            print(f"ℹ️  ssl_required setting already exists: {existing_value}")
        
        # Add related SSL settings
        ssl_settings = [
            ('ssl_port', '443', 'Default HTTPS port for SSL connections'),
            ('ssl_redirect_permanent', 'true', 'Use permanent (301) redirects for HTTP to HTTPS'),
            ('ssl_hsts_enabled', 'false', 'Enable HTTP Strict Transport Security headers'),
            ('ssl_hsts_max_age', '31536000', 'HSTS max age in seconds (1 year default)'),
        ]
        
        for key, default_value, description in ssl_settings:
            existing = SettingsService.get(key, None)
            if existing is None:
                SettingsService.set(key, default_value, description)
                print(f"✅ Added {key} setting (default: {default_value})")
            else:
                print(f"ℹ️  {key} setting already exists: {existing}")
        
        print("\n🔒 SSL/TLS configuration settings added successfully!")
        print("\nTo enable SSL enforcement:")
        print("1. Set ssl_required = 'true' in the settings")
        print("2. Ensure your reverse proxy or web server handles SSL termination")
        print("3. Restart the application")
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding SSL/TLS settings: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = add_ssl_tls_setting()
    sys.exit(0 if success else 1)