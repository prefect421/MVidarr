#!/usr/bin/env python3
"""
Simple Authentication Tables Migration for MVidarr
Creates authentication tables using direct database connection.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import get_db
from src.services.auth_service import AuthService
from src.database.models import UserRole
from src.utils.logger import get_logger

logger = get_logger('mvidarr.migration.simple')

def create_authentication_tables():
    """Create authentication tables using SQL"""
    try:
        logger.info("Creating authentication tables...")
        
        with get_db() as session:
            # Create users table
            logger.info("Creating users table...")
            session.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('ADMIN', 'MANAGER', 'USER', 'READONLY') DEFAULT 'USER' NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    is_email_verified BOOLEAN DEFAULT FALSE NOT NULL,
                    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
                    locked_until DATETIME NULL,
                    last_login DATETIME NULL,
                    last_login_ip VARCHAR(45) NULL,
                    password_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    email_verification_token VARCHAR(255) NULL,
                    password_reset_token VARCHAR(255) NULL,
                    password_reset_expires DATETIME NULL,
                    two_factor_secret VARCHAR(32) NULL,
                    two_factor_enabled BOOLEAN DEFAULT FALSE NOT NULL,
                    backup_codes JSON NULL,
                    preferences JSON NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Create user_sessions table
            logger.info("Creating user_sessions table...")
            session.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    status ENUM('ACTIVE', 'EXPIRED', 'REVOKED') DEFAULT 'ACTIVE' NOT NULL,
                    ip_address VARCHAR(45) NULL,
                    user_agent TEXT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            logger.info("Creating indexes...")
            session.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            session.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            session.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
            session.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token)")
            session.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)")
            session.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON user_sessions(status)")
            
            session.commit()
            logger.info("✅ Authentication tables created successfully")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to create authentication tables: {e}")
        return False

def create_default_admin():
    """Create default admin user"""
    try:
        logger.info("Creating default admin user...")
        
        success, message, admin_user = AuthService.create_user(
            username="admin",
            email="admin@mvidarr.local",
            password="MVidarr@dmin123",
            role=UserRole.ADMIN
        )
        
        if success:
            logger.info("✅ Default admin user created successfully")
            logger.info("   Username: admin")
            logger.info("   Password: MVidarr@dmin123")
            logger.info("   ⚠️  IMPORTANT: Change the default password immediately!")
            return True
        else:
            if "already exists" in message:
                logger.info("ℹ️  Admin user already exists")
                return True
            else:
                logger.error(f"❌ Failed to create admin user: {message}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Error creating admin user: {e}")
        return False

def main():
    """Main migration function"""
    try:
        print("🔐 MVidarr - Simple Authentication Migration")
        print("=" * 60)
        
        # Step 1: Create tables
        print("📊 Step 1: Creating authentication tables...")
        if not create_authentication_tables():
            print("❌ Failed to create tables")
            return False
        
        # Step 2: Create admin user
        print("👤 Step 2: Creating default admin user...")
        if not create_default_admin():
            print("❌ Failed to create admin user")
            return False
        
        print("\n✅ Authentication migration completed successfully!")
        print("🔐 Authentication system is ready to use")
        print("\n📝 Default Admin Credentials:")
        print("   Username: admin")
        print("   Password: MVidarr@dmin123")
        print("   ⚠️  Change password after first login!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)