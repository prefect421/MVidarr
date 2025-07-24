#!/usr/bin/env python3
"""
MVidarr Database Troubleshooting Script
Helps diagnose and fix common database issues
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import our modules
from config import get_config

try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("❌ mysql-connector-python not installed")
    print("   Install with: pip install mysql-connector-python")
    sys.exit(1)

def test_database_connection(config):
    """Test database connection and permissions"""
    print("🔍 Testing Database Connection...")
    print("=" * 50)
    
    db_config = config.get('database')
    connection_params = {
        'host': db_config['host'],
        'port': db_config['port'],
        'user': db_config['user'],
        'password': db_config['password'],
        'charset': db_config['charset'],
        'connect_timeout': 10
    }
    
    try:
        # Test connection without database
        print(f"📡 Connecting to {db_config['host']}:{db_config['port']}...")
        connection = mysql.connector.connect(**connection_params)
        print("✅ Basic connection successful")
        
        # Get server version
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ Server version: {version}")
        
        # Test database existence
        database_name = db_config['database']
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
        
        if database_name in databases:
            print(f"✅ Database '{database_name}' exists")
        else:
            print(f"❌ Database '{database_name}' does not exist")
            print(f"   Create with: CREATE DATABASE {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.close()
            connection.close()
            return False
        
        # Connect to the specific database
        cursor.close()
        connection.close()
        
        connection_params['database'] = database_name
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()
        print(f"✅ Connected to database '{database_name}'")
        
        # Test basic permissions
        print("\n🔑 Testing Permissions...")
        print("-" * 30)
        
        # Test SELECT
        try:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            print("✅ SELECT permission")
        except Error as e:
            print(f"❌ SELECT permission failed: {e}")
        
        # Test table listing
        try:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"✅ SHOW TABLES permission ({len(tables)} tables found)")
            if tables:
                table_names = [table[0] for table in tables]
                print(f"   Tables: {', '.join(table_names)}")
        except Error as e:
            print(f"❌ SHOW TABLES failed: {e}")
        
        # Test CREATE permission with a temporary table
        try:
            cursor.execute("CREATE TEMPORARY TABLE test_permissions (id INT)")
            cursor.execute("DROP TEMPORARY TABLE test_permissions")
            print("✅ CREATE permission")
        except Error as e:
            print(f"❌ CREATE permission failed: {e}")
            print("   Grant with: GRANT CREATE ON {}.* TO '{}'@'%';".format(database_name, db_config['user']))
        
        # Test INSERT/UPDATE/DELETE if we have tables
        if tables:
            try:
                # Try to create a test record in users table if it exists
                if any('users' in str(table) for table in tables):
                    # Test if we can describe the table structure
                    cursor.execute("DESCRIBE users")
                    print("✅ Table structure access (DESCRIBE)")
            except Error as e:
                print(f"⚠️ Table access limited: {e}")
        
        cursor.close()
        connection.close()
        print("\n✅ Database connection and basic permissions verified")
        return True
        
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        
        # Provide specific error guidance
        error_msg = str(e).lower()
        print("\n💡 Troubleshooting:")
        
        if "access denied" in error_msg:
            print("   - Check username and password in .env file")
            print("   - Verify user exists in MySQL: SELECT User FROM mysql.user;")
            print(f"   - Grant access: GRANT ALL ON {db_config['database']}.* TO '{db_config['user']}'@'{db_config['host']}';")
        elif "unknown database" in error_msg:
            print(f"   - Create database: CREATE DATABASE {db_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        elif "can't connect" in error_msg or "connection refused" in error_msg:
            print("   - Check if MySQL/MariaDB server is running")
            print("   - Verify host and port settings")
            print("   - Check firewall settings")
        elif "timeout" in error_msg:
            print("   - Check network connectivity")
            print("   - Verify server is not overloaded")
        
        return False

def check_table_structure(config):
    """Check existing table structure"""
    print("\n🏗️ Checking Table Structure...")
    print("=" * 50)
    
    db_config = config.get('database')
    connection_params = {
        'host': db_config['host'],
        'port': db_config['port'],
        'user': db_config['user'],
        'password': db_config['password'],
        'database': db_config['database'],
        'charset': db_config['charset']
    }
    
    try:
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor(dictionary=True)
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if not tables:
            print("📝 No tables found - first run will create them")
            return True
        
        table_key = list(tables[0].keys())[0]
        table_names = [row[table_key] for row in tables]
        
        print(f"📋 Found {len(table_names)} tables:")
        
        expected_tables = ['users', 'settings', 'downloaded_videos', 'download_queue', 'tracked_artists']
        
        for table_name in expected_tables:
            if table_name in table_names:
                print(f"✅ {table_name}")
                
                # Check table structure
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                print(f"   └─ {len(columns)} columns")
            else:
                print(f"❌ {table_name} (missing)")
        
        # Check for unexpected tables
        extra_tables = [t for t in table_names if t not in expected_tables]
        if extra_tables:
            print(f"\n📎 Additional tables: {', '.join(extra_tables)}")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Table structure check failed: {e}")
        return False

def fix_common_issues(config):
    """Attempt to fix common database issues"""
    print("\n🔧 Attempting to Fix Common Issues...")
    print("=" * 50)
    
    db_config = config.get('database')
    
    # Try to connect and fix issues
    try:
        # Connect without database first
        connection_params = {
            'host': db_config['host'],
            'port': db_config['port'],
            'user': db_config['user'],
            'password': db_config['password'],
            'charset': db_config['charset']
        }
        
        connection = mysql.connector.connect(**connection_params)
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        database_name = db_config['database']
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
        
        if database_name not in databases:
            print(f"🔨 Creating database '{database_name}'...")
            cursor.execute(f"CREATE DATABASE {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database created")
        
        cursor.close()
        connection.close()
        
        print("✅ Common issues check completed")
        return True
        
    except Error as e:
        print(f"❌ Could not fix issues automatically: {e}")
        
        if "access denied" in str(e).lower():
            print("\n💡 Manual fix required - run as database administrator:")
            print(f"   CREATE DATABASE IF NOT EXISTS {db_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print(f"   GRANT ALL PRIVILEGES ON {db_config['database']}.* TO '{db_config['user']}'@'%';")
            print("   FLUSH PRIVILEGES;")
        
        return False

def main():
    """Main troubleshooting function"""
    print("🎵 MVidarr Database Troubleshooting Tool")
    print("=" * 60)
    
    if not MYSQL_AVAILABLE:
        return
    
    # Load configuration
    try:
        config = get_config()
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        print("   Make sure .env file exists and is properly configured")
        return
    
    # Display current configuration
    db_config = config.get('database')
    print(f"\n📋 Current Database Configuration:")
    print(f"   Host: {db_config['host']}")
    print(f"   Port: {db_config['port']}")
    print(f"   Database: {db_config['database']}")
    print(f"   User: {db_config['user']}")
    print(f"   Password: {'*' * len(db_config['password'])}")
    
    # Run tests
    success = True
    
    # Test connection
    if not test_database_connection(config):
        success = False
        
        # Try to fix common issues
        if fix_common_issues(config):
            print("\n🔄 Retesting after fixes...")
            success = test_database_connection(config)
    
    if success:
        # Check table structure
        check_table_structure(config)
        
        print("\n🎉 Database troubleshooting completed successfully!")
        print("\n📋 Summary:")
        print("   ✅ Database connection working")
        print("   ✅ Permissions verified")
        print("   ✅ Table structure checked")
        print("\n🚀 You can now start MVidarr with: python3 app.py")
    else:
        print("\n❌ Database issues found that require manual intervention")
        print("\n🔧 Next steps:")
        print("   1. Check MariaDB/MySQL server is running")
        print("   2. Verify database credentials in .env file")
        print("   3. Create database and grant permissions (see error messages above)")
        print("   4. Run this script again to verify fixes")
        
        print("\n📚 For detailed setup instructions, see:")
        print("   - INSTALLATION_GUIDE.md")
        print("   - MARIADB_SETUP.md (if available)")

if __name__ == '__main__':
    main()
