#!/usr/bin/env python3
"""
Clear MariaDB Content Script
Removes all video and artist entries from the MVidarr MariaDB database
"""

import subprocess
import sys
import os
from pathlib import Path

def run_mysql_command(sql_command, database="mvidarr"):
    """Execute MySQL command"""
    try:
        cmd = ["sudo", "mysql", database, "-e", sql_command]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def get_table_counts():
    """Get current counts of data"""
    counts = {}
    
    tables = ["artists", "videos", "downloads"]
    for table in tables:
        success, result = run_mysql_command(f"SELECT COUNT(*) as count FROM {table};")
        if success:
            # Parse the result to get the count
            lines = result.strip().split('\n')
            if len(lines) >= 2:
                counts[table] = int(lines[1])
            else:
                counts[table] = 0
        else:
            counts[table] = 0
    
    return counts

def clear_database_content():
    """Clear all video and artist entries from MariaDB"""
    
    print("🔍 Checking current database content...")
    
    # Get current counts
    counts = get_table_counts()
    
    print(f"📊 Current database content:")
    print(f"   - Artists: {counts.get('artists', 0)}")
    print(f"   - Videos: {counts.get('videos', 0)}")
    print(f"   - Downloads: {counts.get('downloads', 0)}")
    
    total_records = sum(counts.values())
    
    if total_records == 0:
        print("✅ Database is already empty of content")
        return True
    
    print(f"\n⚠️  WARNING: This will permanently delete {total_records} records!")
    print("   - All video records will be removed")
    print("   - All artist records will be removed") 
    print("   - All download records will be removed")
    print("   - Thumbnail files will be removed")
    print("   - Video files will remain (manual cleanup required)")
    print()
    
    confirm = input("Are you sure you want to continue? (type 'yes' to confirm): ")
    
    if confirm.lower() != 'yes':
        print("❌ Operation cancelled by user")
        return False
    
    print("\n🗄️  Clearing database content...")
    
    # Clear tables in order (respecting foreign key constraints)
    tables_to_clear = ["downloads", "videos", "artists"]
    
    for table in tables_to_clear:
        print(f"   Clearing {table} table...")
        success, result = run_mysql_command(f"DELETE FROM {table};")
        if not success:
            print(f"❌ Error clearing {table}: {result}")
            return False
    
    # Reset auto-increment counters
    print("   Resetting auto-increment sequences...")
    for table in tables_to_clear:
        run_mysql_command(f"ALTER TABLE {table} AUTO_INCREMENT = 1;")
    
    print("✅ Database content cleared successfully!")
    print(f"   - Removed {counts.get('videos', 0)} videos")
    print(f"   - Removed {counts.get('artists', 0)} artists") 
    print(f"   - Removed {counts.get('downloads', 0)} downloads")
    print("   - Reset ID sequences")
    
    return True

def clear_thumbnail_files():
    """Clear thumbnail files from filesystem"""
    
    base_dir = Path(__file__).parent.parent
    thumbnail_dirs = [
        base_dir / 'data' / 'thumbnails' / 'artists',
        base_dir / 'data' / 'thumbnails' / 'videos',
        base_dir / 'data' / 'thumbnails' / 'uploads'
    ]
    
    total_removed = 0
    
    for thumb_dir in thumbnail_dirs:
        if thumb_dir.exists():
            files = list(thumb_dir.glob('*'))
            # Keep .gitkeep files
            files = [f for f in files if f.name != '.gitkeep']
            
            print(f"   Removing {len(files)} files from {thumb_dir.name}")
            
            for file in files:
                try:
                    if file.is_file():
                        file.unlink()
                        total_removed += 1
                except Exception as e:
                    print(f"   ⚠️  Failed to remove {file.name}: {e}")
    
    print(f"✅ Removed {total_removed} thumbnail files")
    return total_removed

def main():
    """Main execution function"""
    
    print("=" * 60)
    print("MVidarr Enhanced - Database Content Clearing")
    print("=" * 60)
    
    # Test MySQL connection
    success, result = run_mysql_command("SELECT 1;")
    if not success:
        print(f"❌ Cannot connect to MariaDB: {result}")
        print("   Make sure MariaDB is running and you have sudo access")
        sys.exit(1)
    
    # Clear database content  
    if not clear_database_content():
        print("❌ Database clearing failed!")
        sys.exit(1)
    
    # Clear thumbnail files
    print("\n🖼️  Clearing thumbnail files...")
    clear_thumbnail_files()
    
    print("\n" + "=" * 60)
    print("✅ Database clearing completed successfully!")
    print("=" * 60)
    print("Next steps:")
    print("  1. Restart the application: ./manage.sh restart")
    print("  2. Manually remove video files from data/musicvideos/ if desired")
    print("  3. Start fresh with new artist imports")
    print("  4. Access the application at: http://localhost:5000")

if __name__ == "__main__":
    main()