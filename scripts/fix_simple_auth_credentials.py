#!/usr/bin/env python3
"""
Fix Simple Auth Credentials
Sets the correct bcrypt-hashed credentials for simple authentication
"""

import subprocess
import sys
import bcrypt
from pathlib import Path

def run_mysql_command(sql_command, database="mvidarr"):
    """Execute MySQL command"""
    try:
        cmd = ["sudo", "mysql", database, "-e", sql_command]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def set_simple_auth_credentials():
    """Set proper bcrypt credentials for simple authentication"""
    
    print("🔧 Setting proper simple authentication credentials...")
    
    # Default credentials
    username = "admin"
    password = "mvidarr"
    
    # Create bcrypt hash (matching the SimpleAuthService expectation)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    password_hash_str = password_hash.decode('utf-8')
    
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   Hash: {password_hash_str[:30]}...")
    
    # Update the correct settings keys that SimpleAuthService uses
    credentials_sql = f"""
    INSERT INTO settings (`key`, value) VALUES 
    ('auth_username', '{username}'),
    ('auth_password_hash', '{password_hash_str}')
    ON DUPLICATE KEY UPDATE 
    value = VALUES(value),
    updated_at = NOW();
    """
    
    success, result = run_mysql_command(credentials_sql)
    if not success:
        print(f"❌ Error setting credentials: {result}")
        return False
    
    # Also set authentication settings
    auth_settings_sql = """
    INSERT INTO settings (`key`, value) VALUES 
    ('require_authentication', 'true'),
    ('authentication_type', 'simple')
    ON DUPLICATE KEY UPDATE 
    value = VALUES(value),
    updated_at = NOW();
    """
    
    success, result = run_mysql_command(auth_settings_sql)
    if not success:
        print(f"❌ Error setting auth settings: {result}")
        return False
    
    print("✅ Simple authentication credentials set successfully!")
    return True

def check_simple_login_template():
    """Check if the simple login template shows default credentials warning"""
    
    template_path = Path(__file__).parent.parent / 'frontend' / 'templates' / 'auth' / 'simple_login.html'
    
    if template_path.exists():
        with open(template_path, 'r') as f:
            content = f.read()
            
        if 'show_default_credentials' in content:
            print("✅ Login template has default credentials warning capability")
            return True
        else:
            print("⚠️  Login template missing default credentials warning")
            return False
    else:
        print("❌ Simple login template not found")
        return False

def main():
    """Main execution function"""
    
    print("=" * 60)
    print("MVidarr Enhanced - Fix Simple Auth Credentials")
    print("=" * 60)
    
    # Test MySQL connection
    success, result = run_mysql_command("SELECT 1;")
    if not success:
        print(f"❌ Cannot connect to MariaDB: {result}")
        sys.exit(1)
    
    # Set proper credentials
    if not set_simple_auth_credentials():
        print("❌ Failed to set credentials!")
        sys.exit(1)
    
    # Check template
    print("\n🔍 Checking login template...")
    check_simple_login_template()
    
    # Clear any existing sessions
    print("\n🔧 Clearing user sessions...")
    run_mysql_command("DELETE FROM user_sessions;")
    
    print("\n" + "=" * 60)
    print("✅ Simple auth credentials fixed successfully!")
    print("=" * 60)
    print("🔑 Login Credentials:")
    print("   Username: admin")
    print("   Password: mvidarr")
    print()
    print("📋 Next steps:")
    print("  1. Restart the application: ./manage.sh restart")
    print("  2. Access: http://localhost:5000")
    print("  3. Login with credentials above")
    print("  4. The default credentials warning should now appear")

if __name__ == "__main__":
    main()