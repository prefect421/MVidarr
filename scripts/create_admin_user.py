#!/usr/bin/env python3
"""
Create admin user with proper password hash
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from werkzeug.security import generate_password_hash
import pymysql
from src.config.config import Config

def create_admin_user():
    """Create admin user with proper credentials"""
    try:
        config = Config()
        
        # Generate password hash
        password_hash = generate_password_hash("MVidarr@dmin123")
        
        # Connect to database
        connection = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Delete existing admin user if any
            cursor.execute("DELETE FROM users WHERE username = 'admin'")
            
            # Insert new admin user
            cursor.execute("""
                INSERT INTO users (
                    username, email, password_hash, role, 
                    is_active, is_email_verified, is_admin
                ) VALUES (
                    'admin', 'admin@mvidarr.local', %s, 'ADMIN', 
                    TRUE, TRUE, TRUE
                )
            """, (password_hash,))
        
        connection.commit()
        connection.close()
        
        print("✅ Admin user created successfully!")
        print("   Username: admin")
        print("   Password: MVidarr@dmin123")
        print("   ⚠️  Change password after first login!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        return False

if __name__ == '__main__':
    create_admin_user()