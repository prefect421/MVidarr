#!/usr/bin/env python3
"""
Fix missing database settings in the settings table
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.services.settings_service import SettingsService

def add_missing_database_settings():
    """Add missing database settings to the settings table"""
    
    # Database settings that should exist
    db_settings = {
        'db_host': ('localhost', 'Database host'),
        'db_port': ('3306', 'Database port'),
        'db_name': ('mvidarr', 'Database name'),
        'db_user': ('mvidarr', 'Database user'),
        'db_password': ('mvidarr', 'Database password'),
        'db_pool_size': ('10', 'Database connection pool size'),
        'db_pool_overflow': ('20', 'Database connection pool max overflow'),
        'db_pool_recycle': ('3600', 'Database connection pool recycle time'),
        'db_pool_timeout': ('30', 'Database connection pool timeout'),
    }
    
    print("Adding missing database settings...")
    
    for key, (default_value, description) in db_settings.items():
        try:
            # Check if setting already exists
            current_value = SettingsService.get(key)
            if current_value:
                print(f"✓ {key} already exists: {current_value}")
            else:
                # Add the setting
                if SettingsService.set(key, default_value, description):
                    print(f"✓ Added {key} = {default_value}")
                else:
                    print(f"✗ Failed to add {key}")
        except Exception as e:
            print(f"✗ Error with {key}: {e}")
    
    print("Database settings fix completed!")

if __name__ == "__main__":
    add_missing_database_settings()