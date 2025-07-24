"""
Simple single-user authentication service for MVidarr Enhanced
Replaces complex multi-user system with simple username/password authentication
"""

from typing import Tuple, Optional
from flask import session as flask_session
from src.services.settings_service import SettingsService
from src.utils.logger import get_logger
import bcrypt

logger = get_logger('mvidarr.simple_auth')

class SimpleAuthService:
    """Simple single-user authentication service"""
    
    @staticmethod
    def set_credentials(username: str, password: str) -> Tuple[bool, str]:
        """
        Set username and password for single-user authentication
        
        Args:
            username: Username to set
            password: Password to set (will be hashed)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not username or not password:
                return False, "Username and password are required"
            
            if len(username) < 3:
                return False, "Username must be at least 3 characters long"
                
            if len(password) < 6:
                return False, "Password must be at least 6 characters long"
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Store in settings
            SettingsService.set('auth_username', username)
            SettingsService.set('auth_password_hash', password_hash.decode('utf-8'))
            
            logger.info(f"Credentials updated for user: {username}")
            return True, "Credentials updated successfully"
            
        except Exception as e:
            logger.error(f"Error setting credentials: {e}")
            return False, "Failed to update credentials"
    
    @staticmethod
    def authenticate(username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate user with username and password
        
        Args:
            username: Username to authenticate
            password: Password to authenticate
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not username or not password:
                return False, "Username and password are required"
            
            # Get stored credentials
            stored_username = SettingsService.get('auth_username')
            stored_password_hash = SettingsService.get('auth_password_hash')
            
            if not stored_username or not stored_password_hash:
                return False, "No credentials configured"
            
            # Check username
            if username != stored_username:
                logger.warning(f"Failed login attempt with username: {username}")
                return False, "Invalid username or password"
            
            # Check password
            if not bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                logger.warning(f"Failed login attempt for user: {username}")
                return False, "Invalid username or password"
            
            logger.info(f"User authenticated: {username}")
            return True, "Authentication successful"
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return False, "Authentication failed"
    
    @staticmethod
    def login_user(username: str) -> bool:
        """
        Set user as logged in using Flask session
        
        Args:
            username: Username to log in
            
        Returns:
            True if successful
        """
        try:
            flask_session['authenticated'] = True
            flask_session['username'] = username
            flask_session.permanent = True
            logger.info(f"User logged in: {username}")
            return True
        except Exception as e:
            logger.error(f"Error logging in user: {e}")
            return False
    
    @staticmethod
    def logout_user() -> bool:
        """
        Log out current user by clearing Flask session
        
        Returns:
            True if successful
        """
        try:
            username = flask_session.get('username', 'unknown')
            flask_session.clear()
            logger.info(f"User logged out: {username}")
            return True
        except Exception as e:
            logger.error(f"Error logging out user: {e}")
            return False
    
    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if current user is authenticated
        
        Returns:
            True if authenticated, False otherwise
        """
        return flask_session.get('authenticated', False)
    
    @staticmethod
    def get_current_username() -> Optional[str]:
        """
        Get current logged in username
        
        Returns:
            Username if authenticated, None otherwise
        """
        if SimpleAuthService.is_authenticated():
            return flask_session.get('username')
        return None
    
    @staticmethod
    def get_credentials() -> Tuple[Optional[str], bool]:
        """
        Get current stored username and whether credentials are configured
        
        Returns:
            Tuple of (username, has_credentials)
        """
        username = SettingsService.get('auth_username')
        password_hash = SettingsService.get('auth_password_hash')
        has_credentials = bool(username and password_hash)
        return username, has_credentials
    
    @staticmethod
    def _is_default_password() -> bool:
        """
        Check if current password is still the default 'mvidarr'
        
        Returns:
            True if password is still default, False otherwise
        """
        try:
            stored_password_hash = SettingsService.get('auth_password_hash')
            if not stored_password_hash:
                return True  # No password set, assume default
            
            # Test if default password matches stored hash
            return bcrypt.checkpw('mvidarr'.encode('utf-8'), stored_password_hash.encode('utf-8'))
            
        except Exception:
            return True  # Assume default on error
    
    @staticmethod
    def initialize_default_credentials() -> Tuple[bool, str, str, str]:
        """
        Initialize default credentials if none exist
        
        Returns:
            Tuple of (created, username, password, message)
        """
        try:
            username, has_credentials = SimpleAuthService.get_credentials()
            
            if has_credentials:
                return False, username, "", "Credentials already configured"
            
            # Create default credentials
            default_username = "admin"
            default_password = "mvidarr"
            
            success, message = SimpleAuthService.set_credentials(default_username, default_password)
            
            if success:
                logger.info("Default credentials initialized")
                return True, default_username, default_password, "Default credentials created"
            else:
                return False, "", "", message
                
        except Exception as e:
            logger.error(f"Error initializing default credentials: {e}")
            return False, "", "", "Failed to initialize credentials"