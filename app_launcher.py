#!/usr/bin/env python3
"""
MVidarr Smart Application Launcher
Automatically detects authentication settings and starts the appropriate application version
"""

import os
import sys
import sqlite3
import subprocess
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mvidarr.launcher')

class MVidarrLauncher:
    """Smart launcher for MVidarr applications"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.db_path = self.base_dir / 'data' / 'mvidarr.db'
        
        # Application entry points
        self.app_configs = {
            'simple_auth': {
                'file': 'src/app_with_simple_auth.py',
                'name': 'MVidarr with Simple Authentication',
                'description': 'Single-user authentication with username/password'
            },
            'full_auth': {
                'file': 'app.py',
                'name': 'MVidarr with Full Authentication',
                'description': 'Multi-user authentication with roles and OAuth'
            },
            'no_auth': {
                'file': 'app.py',  # Could be a separate no-auth version if needed
                'name': 'MVidarr without Authentication',
                'description': 'Open access without authentication'
            }
        }
    
    def get_auth_setting(self):
        """Get authentication setting from database"""
        try:
            # Check if database exists
            if not self.db_path.exists():
                logger.warning(f"Database not found at {self.db_path}")
                return 'simple_auth'  # Default to simple auth
            
            # Connect to database and check settings
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Check if settings table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='settings'
            """)
            
            if not cursor.fetchone():
                logger.warning("Settings table not found in database")
                conn.close()
                return 'simple_auth'
            
            # Get authentication setting
            cursor.execute("""
                SELECT value FROM settings 
                WHERE key = 'require_authentication'
            """)
            
            auth_required = cursor.fetchone()
            
            # Get authentication type if authentication is required
            if auth_required and auth_required[0].lower() in ['true', '1', 'yes']:
                cursor.execute("""
                    SELECT value FROM settings 
                    WHERE key = 'authentication_type'
                """)
                
                auth_type = cursor.fetchone()
                
                if auth_type:
                    auth_mode = auth_type[0].lower()
                    logger.info(f"Found authentication type: {auth_mode}")
                    
                    if auth_mode in ['simple', 'single_user']:
                        conn.close()
                        return 'simple_auth'
                    elif auth_mode in ['full', 'multi_user', 'oauth']:
                        conn.close()
                        return 'full_auth'
                
                # Default to simple auth if authentication is required but type not specified
                logger.info("Authentication required but type not specified, defaulting to simple auth")
                conn.close()
                return 'simple_auth'
            else:
                logger.info("Authentication not required")
                conn.close()
                return 'simple_auth'  # Still use simple auth as it can handle both modes
                
        except Exception as e:
            logger.error(f"Error reading database settings: {e}")
            logger.info("Defaulting to simple authentication")
            return 'simple_auth'
    
    def check_application_files(self):
        """Check if required application files exist"""
        missing_files = []
        
        for auth_type, config in self.app_configs.items():
            app_file = self.base_dir / config['file']
            if not app_file.exists():
                missing_files.append(f"{auth_type}: {config['file']}")
        
        if missing_files:
            logger.error("Missing application files:")
            for missing in missing_files:
                logger.error(f"  - {missing}")
            return False
        
        return True
    
    def launch_application(self, auth_mode=None):
        """Launch the appropriate application based on authentication mode"""
        
        # Auto-detect auth mode if not specified
        if auth_mode is None:
            auth_mode = self.get_auth_setting()
        
        # Validate auth mode
        if auth_mode not in self.app_configs:
            logger.error(f"Invalid authentication mode: {auth_mode}")
            logger.info(f"Available modes: {list(self.app_configs.keys())}")
            return False
        
        # Check if application files exist
        if not self.check_application_files():
            return False
        
        # Get application config
        app_config = self.app_configs[auth_mode]
        app_file = self.base_dir / app_config['file']
        
        logger.info("=" * 60)
        logger.info("MVidarr Smart Launcher")
        logger.info("=" * 60)
        logger.info(f"Selected Mode: {auth_mode}")
        logger.info(f"Application: {app_config['name']}")
        logger.info(f"Description: {app_config['description']}")
        logger.info(f"Entry Point: {app_config['file']}")
        logger.info("=" * 60)
        
        # Show authentication info for simple auth
        if auth_mode == 'simple_auth':
            logger.info("🔐 Simple Authentication Mode")
            logger.info("👤 Default credentials:")
            logger.info("   Username: admin")
            logger.info("   Password: mvidarr")
            logger.info("💡 Update credentials in Settings > General after first login!")
            logger.info("=" * 60)
        
        # Change to application directory
        os.chdir(self.base_dir)
        
        # Launch the application
        try:
            logger.info(f"Starting application: {app_file}")
            
            # Use exec to replace the current process with the application
            # This ensures the application gets the same PID and signals
            os.execv(sys.executable, [sys.executable, str(app_file)])
            
        except Exception as e:
            logger.error(f"Failed to launch application: {e}")
            return False
    
    def show_status(self):
        """Show current configuration and available applications"""
        print("\n" + "=" * 60)
        print("MVidarr Launcher Status")
        print("=" * 60)
        
        # Check database
        if self.db_path.exists():
            print(f"✅ Database: {self.db_path}")
            auth_mode = self.get_auth_setting()
            print(f"✅ Detected Auth Mode: {auth_mode}")
        else:
            print(f"❌ Database: {self.db_path} (not found)")
            auth_mode = 'simple_auth'
            print(f"⚠️  Default Auth Mode: {auth_mode}")
        
        print("\nAvailable Applications:")
        print("-" * 30)
        
        for mode, config in self.app_configs.items():
            app_file = self.base_dir / config['file']
            status = "✅" if app_file.exists() else "❌"
            marker = " [SELECTED]" if mode == auth_mode else ""
            print(f"{status} {mode}: {config['name']}{marker}")
            print(f"    File: {config['file']}")
            print(f"    Description: {config['description']}")
            print()
        
        print("=" * 60 + "\n")

def main():
    """Main entry point"""
    launcher = MVidarrLauncher()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            launcher.show_status()
            return
        elif command in launcher.app_configs:
            # Launch specific auth mode
            success = launcher.launch_application(command)
            if not success:
                sys.exit(1)
        elif command in ['help', '-h', '--help']:
            print("MVidarr Smart Launcher")
            print("\nUsage:")
            print("  python3 app_launcher.py [command]")
            print("\nCommands:")
            print("  (no args)    - Auto-detect and launch appropriate application")
            print("  status       - Show current configuration and available apps")
            print("  simple_auth  - Force launch simple authentication version")
            print("  full_auth    - Force launch full authentication version")
            print("  no_auth      - Force launch without authentication")
            print("  help         - Show this help message")
            print("\nExamples:")
            print("  python3 app_launcher.py")
            print("  python3 app_launcher.py status")
            print("  python3 app_launcher.py simple_auth")
            return
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Use 'help' to see available commands")
            sys.exit(1)
    else:
        # Auto-detect and launch
        success = launcher.launch_application()
        if not success:
            sys.exit(1)

if __name__ == '__main__':
    main()