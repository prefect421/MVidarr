#!/usr/bin/env python3
"""
Initialize Database and Authentication System for MVidarr Enhanced
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import init_db
from src.config.config import Config
from src.utils.logger import get_logger
import pymysql

logger = get_logger('mvidarr.init')

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        config = Config()
        logger.info(f"Checking database: {config.DB_NAME}")
        
        # Connect to MySQL without specifying database
        connection = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Check if database exists
            cursor.execute(f"SHOW DATABASES LIKE '{config.DB_NAME}'")
            result = cursor.fetchone()
            
            if not result:
                logger.info(f"Creating database: {config.DB_NAME}")
                cursor.execute(f"CREATE DATABASE {config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                logger.info("✅ Database created successfully")
            else:
                logger.info("ℹ️  Database already exists")
        
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False

def create_auth_tables():
    """Create authentication tables"""
    try:
        config = Config()
        logger.info("Creating authentication tables...")
        
        # Connect to the database
        connection = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create users table
            logger.info("Creating users table...")
            cursor.execute("""
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
            cursor.execute("""
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
                    INDEX idx_sessions_user_id (user_id),
                    INDEX idx_sessions_token (session_token),
                    INDEX idx_sessions_status (status)
                )
            """)
            
            # Create indexes
            logger.info("Creating indexes...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
            
            # Create default admin user
            logger.info("Creating default admin user...")
            
            # Check if admin user exists
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            if not cursor.fetchone():
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash("MVidarr@dmin123")
                
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, is_active, is_email_verified)
                    VALUES ('admin', 'admin@mvidarr.local', %s, 'ADMIN', TRUE, TRUE)
                """, (password_hash,))
                
                logger.info("✅ Default admin user created")
                logger.info("   Username: admin")
                logger.info("   Password: MVidarr@dmin123")
                logger.info("   ⚠️  CHANGE PASSWORD AFTER FIRST LOGIN!")
            else:
                logger.info("ℹ️  Admin user already exists")
        
        connection.commit()
        connection.close()
        
        logger.info("✅ Authentication tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create authentication tables: {e}")
        return False

def main():
    """Main initialization function"""
    try:
        print("🔐 MVidarr Enhanced - Database & Authentication Initialization")
        print("=" * 70)
        
        # Step 1: Create database
        print("📊 Step 1: Creating database if needed...")
        if not create_database_if_not_exists():
            print("❌ Failed to create database")
            return False
        
        # Step 2: Initialize database connection
        print("🔗 Step 2: Initializing database connection...")
        try:
            init_db()
            logger.info("✅ Database connection initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Continue anyway, we'll create tables manually
        
        # Step 3: Create authentication tables
        print("🔐 Step 3: Creating authentication tables...")
        if not create_auth_tables():
            print("❌ Failed to create authentication tables")
            return False
        
        print("\n🎉 Database and authentication system initialized successfully!")
        print("\n📝 Next Steps:")
        print("1. Start the application with authentication:")
        print("   python3 src/app_with_auth.py")
        print("\n2. Login with default admin credentials:")
        print("   Username: admin")
        print("   Password: MVidarr@dmin123")
        print("\n3. Change the default password immediately!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)