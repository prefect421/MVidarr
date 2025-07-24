#!/usr/bin/env python3
"""
MVidarr Database Reset Tool
Safely removes and recreates database tables
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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

def backup_data(connection, table_name):
    """Create a backup of important data"""
    cursor = connection.cursor(dictionary=True)
    
    try:
        if table_name == 'users':
            # Backup user data
            cursor.execute("SELECT username, email, password_hash, is_admin FROM users")
            return cursor.fetchall()
        elif table_name == 'settings':
            # Backup settings
            cursor.execute("SELECT category, setting_key, setting_value, setting_type, user_id FROM settings")
            return cursor.fetchall()
        else:
            return []
    except Error:
        return []
    finally:
        cursor.close()

def restore_data(connection, table_name, data):
    """Restore backed up data"""
    if not data:
        return True
        
    cursor = connection.cursor()
    
    try:
        if table_name == 'users':
            for user in data:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, is_admin) 
                    VALUES (%(username)s, %(email)s, %(password_hash)s, %(is_admin)s)
                """, user)
        elif table_name == 'settings':
            for setting in data:
                cursor.execute("""
                    INSERT INTO settings (category, setting_key, setting_value, setting_type, user_id)
                    VALUES (%(category)s, %(setting_key)s, %(setting_value)s, %(setting_type)s, %(user_id)s)
                """, setting)
        
        connection.commit()
        return True
    except Error as e:
        print(f"⚠️ Could not restore {table_name} data: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def reset_database_tables(config, preserve_data=True):
    """Reset database tables"""
    print("🔄 Resetting Database Tables...")
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
        cursor = connection.cursor()
        
        # Get existing tables
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("📝 No tables found to reset")
            cursor.close()
            connection.close()
            return True
        
        print(f"📋 Found tables to reset: {', '.join(tables)}")
        
        # Backup important data if requested
        backups = {}
        if preserve_data:
            print("\n💾 Backing up important data...")
            for table in ['users', 'settings']:
                if table in tables:
                    backup = backup_data(connection, table)
                    if backup:
                        backups[table] = backup
                        print(f"✅ Backed up {len(backup)} records from {table}")
        
        # Drop tables in reverse dependency order
        drop_order = ['tracked_artists', 'download_queue', 'downloaded_videos', 'settings', 'users']
        
        print("\n🗑️ Dropping existing tables...")
        for table in drop_order:
            if table in tables:
                try:
                    cursor.execute(f"DROP TABLE {table}")
                    print(f"✅ Dropped table: {table}")
                except Error as e:
                    print(f"⚠️ Could not drop {table}: {e}")
        
        cursor.close()
        connection.close()
        
        # Recreate tables using the application's table creation
        print("\n🏗️ Recreating tables...")
        from database import get_database
        
        db = get_database(config)
        db.connect()
        db.create_tables()
        
        # Restore backed up data
        if preserve_data and backups:
            print("\n📥 Restoring backed up data...")
            connection = mysql.connector.connect(**connection_params)
            
            for table_name, data in backups.items():
                if restore_data(connection, table_name, data):
                    print(f"✅ Restored {len(data)} records to {table_name}")
                else:
                    print(f"⚠️ Could not restore data to {table_name}")
            
            connection.close()
        
        print("\n✅ Database reset completed successfully!")
        return True
        
    except Error as e:
        print(f"❌ Database reset failed: {e}")
        return False

def main():
    """Main reset function"""
    print("🎵 MVidarr Database Reset Tool")
    print("=" * 50)
    print("⚠️ WARNING: This will remove and recreate all database tables!")
    print()
    
    if not MYSQL_AVAILABLE:
        return
    
    # Load configuration
    try:
        config = get_config()
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return
    
    # Get user confirmation
    print("\nOptions:")
    print("1. Reset tables and preserve user/settings data (recommended)")
    print("2. Reset tables completely (all data will be lost)")
    print("3. Cancel")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            preserve_data = True
            break
        elif choice == '2':
            confirm = input("Are you sure you want to delete ALL data? Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                preserve_data = False
                break
            else:
                print("❌ Reset cancelled")
                return
        elif choice == '3':
            print("❌ Reset cancelled")
            return
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
    
    # Perform reset
    if reset_database_tables(config, preserve_data):
        print("\n🎉 Database reset completed!")
        print("\n📋 Next steps:")
        print("1. Start MVidarr: python3 app.py")
        print("2. Login with default credentials if user data was reset")
        print("3. Change default password immediately")
    else:
        print("\n❌ Database reset failed")
        print("Check error messages above and ensure:")
        print("- Database server is running")
        print("- User has proper permissions")
        print("- No other applications are using the database")

if __name__ == '__main__':
    main()
