#!/usr/bin/env python3
"""
Secure Application Restart Script for MVidarr
This script provides admin-only restart functionality with proper security checks.
"""

import sys
import os
import signal
import subprocess
import time
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.auth_service import AuthService
from src.services.audit_service import AuditService
from src.config.config import Config
from src.utils.logger import get_logger

logger = get_logger('mvidarr.admin.restart')

class SecureRestartManager:
    """Manages secure application restarts with admin verification"""
    
    def __init__(self):
        self.config = Config()
        
    def verify_admin_user(self, username, password):
        """Verify that the user is an admin"""
        try:
            user = AuthService.authenticate_user(username, password)
            if not user:
                return False, "Invalid credentials"
            
            if not user.is_admin:
                return False, "User does not have admin privileges"
            
            if not user.is_active:
                return False, "User account is inactive"
            
            return True, user
            
        except Exception as e:
            logger.error(f"Admin verification error: {e}")
            return False, f"Verification failed: {e}"
    
    def log_restart_attempt(self, user, success=True, error_message=None):
        """Log restart attempt for audit trail"""
        try:
            additional_data = {
                "timestamp": time.time(),
                "process_id": os.getpid(),
                "success": success
            }
            
            if error_message:
                additional_data["error"] = error_message
            
            AuditService.log_admin_action(
                "restart_application_script",
                admin_user=user,
                additional_data=additional_data
            )
            
        except Exception as e:
            logger.error(f"Failed to log restart attempt: {e}")
    
    def restart_application(self, user):
        """Perform the actual application restart"""
        try:
            logger.warning(f"Application restart initiated by admin: {user.username}")
            
            current_pid = os.getpid()
            
            # Try different restart methods in order of preference
            restart_methods = [
                self._restart_via_systemctl,
                self._restart_via_script,
                self._restart_via_signal
            ]
            
            for method in restart_methods:
                try:
                    success, message = method()
                    if success:
                        self.log_restart_attempt(user, success=True)
                        return True, message
                except Exception as e:
                    logger.warning(f"Restart method {method.__name__} failed: {e}")
                    continue
            
            # If all methods failed
            error_msg = "All restart methods failed"
            self.log_restart_attempt(user, success=False, error_message=error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Restart failed: {e}"
            logger.error(error_msg)
            self.log_restart_attempt(user, success=False, error_message=error_msg)
            return False, error_msg
    
    def _restart_via_systemctl(self):
        """Restart using systemctl (production environment)"""
        try:
            # Check if service is managed by systemd
            result = subprocess.run(['systemctl', 'is-active', 'mvidarr'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Service is managed by systemd
                logger.info("Restarting via systemctl...")
                subprocess.run(['sudo', 'systemctl', 'restart', 'mvidarr'], 
                             timeout=10, check=True)
                return True, "Application restarted via systemctl"
            else:
                return False, "Service not managed by systemd"
                
        except subprocess.TimeoutExpired:
            return False, "Systemctl restart timeout"
        except subprocess.CalledProcessError as e:
            return False, f"Systemctl restart failed: {e}"
        except FileNotFoundError:
            return False, "Systemctl not available"
    
    def _restart_via_script(self):
        """Restart using the manage_service.sh script"""
        try:
            script_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'scripts', 'manage_service.sh'
            )
            
            if os.path.exists(script_path) and os.access(script_path, os.X_OK):
                logger.info("Restarting via manage_service.sh...")
                subprocess.run([script_path, 'restart'], timeout=10, check=True)
                return True, "Application restarted via manage_service.sh"
            else:
                return False, "manage_service.sh not available or not executable"
                
        except subprocess.TimeoutExpired:
            return False, "Script restart timeout"
        except subprocess.CalledProcessError as e:
            return False, f"Script restart failed: {e}"
    
    def _restart_via_signal(self):
        """Restart by sending signal to current process"""
        try:
            logger.info("Performing graceful process restart...")
            
            # Schedule the signal in a separate process to avoid self-termination issues
            def delayed_signal():
                time.sleep(1)  # Give time for response
                os.kill(os.getpid(), signal.SIGTERM)
            
            import threading
            signal_thread = threading.Thread(target=delayed_signal, daemon=True)
            signal_thread.start()
            
            return True, "Application restart signal sent"
            
        except Exception as e:
            return False, f"Signal restart failed: {e}"

def interactive_restart():
    """Interactive restart with admin authentication"""
    print("🔐 MVidarr - Secure Application Restart")
    print("=" * 50)
    
    restart_manager = SecureRestartManager()
    
    # Get admin credentials
    username = input("Admin Username: ").strip()
    if not username:
        print("❌ Username is required")
        return False
    
    import getpass
    password = getpass.getpass("Admin Password: ")
    if not password:
        print("❌ Password is required")
        return False
    
    # Verify admin credentials
    print("\n🔍 Verifying admin credentials...")
    is_admin, result = restart_manager.verify_admin_user(username, password)
    
    if not is_admin:
        print(f"❌ Access denied: {result}")
        return False
    
    user = result
    print(f"✅ Admin verified: {user.username}")
    
    # Confirm restart
    print(f"\n⚠️  Warning: This will restart the MVidarr application.")
    print("All users will be temporarily disconnected.")
    confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ Restart cancelled")
        return False
    
    # Perform restart
    print("\n🔄 Initiating application restart...")
    success, message = restart_manager.restart_application(user)
    
    if success:
        print(f"✅ {message}")
        print("The application should be back online shortly.")
        return True
    else:
        print(f"❌ Restart failed: {message}")
        return False

def programmatic_restart(username, password):
    """Programmatic restart for API use"""
    restart_manager = SecureRestartManager()
    
    # Verify admin credentials
    is_admin, result = restart_manager.verify_admin_user(username, password)
    if not is_admin:
        return False, result
    
    user = result
    
    # Perform restart
    return restart_manager.restart_application(user)

if __name__ == '__main__':
    try:
        if len(sys.argv) >= 3:
            # Programmatic mode with username and password
            username = sys.argv[1]
            password = sys.argv[2]
            success, message = programmatic_restart(username, password)
            if success:
                print(f"✅ {message}")
                sys.exit(0)
            else:
                print(f"❌ {message}")
                sys.exit(1)
        else:
            # Interactive mode
            success = interactive_restart()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n❌ Restart cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)