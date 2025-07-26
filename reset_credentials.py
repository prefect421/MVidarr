#!/usr/bin/env python3
"""
Script to reset authentication credentials to default values
"""

import sys
import hashlib
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def reset_credentials():
    """Reset credentials to admin/mvidarr"""
    try:
        from src.services.simple_auth_service import SimpleAuthService
        
        # Reset to default credentials
        success, message = SimpleAuthService.set_credentials("admin", "mvidarr")
        
        if success:
            print("✅ Credentials reset successfully!")
            print("Username: admin")
            print("Password: mvidarr")
            
            # Verify the credentials work
            auth_success, auth_message = SimpleAuthService.authenticate("admin", "mvidarr")
            if auth_success:
                print("✅ Authentication test passed!")
            else:
                print(f"❌ Authentication test failed: {auth_message}")
        else:
            print(f"❌ Failed to reset credentials: {message}")
            
    except Exception as e:
        print(f"❌ Error resetting credentials: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Initialize database connection directly
    from src.config.config import Config
    from src.database.connection import DatabaseManager
    import src.database.connection as db_conn
    
    # Set up database manager
    config = Config()
    db_conn.db_manager = DatabaseManager(config)
    
    print("🔧 Resetting authentication credentials to defaults...")
    reset_credentials()