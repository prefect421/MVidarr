#!/usr/bin/env python3
"""
Fix Download Queue Display Issue
Resolves inconsistency between video status and download queue display
"""

import subprocess
import sys
from pathlib import Path

def run_mysql_command(sql_command, database="mvidarr"):
    """Execute MySQL command"""
    try:
        cmd = ["sudo", "mysql", database, "-e", sql_command]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def get_stuck_downloads():
    """Get videos stuck in DOWNLOADING status"""
    
    success, result = run_mysql_command("""
        SELECT v.id, v.title, a.name as artist_name, v.status, v.created_at 
        FROM videos v 
        LEFT JOIN artists a ON v.artist_id = a.id 
        WHERE v.status = 'DOWNLOADING' 
        ORDER BY v.created_at DESC;
    """)
    
    if not success:
        print(f"❌ Error querying stuck downloads: {result}")
        return []
    
    # Parse the result
    lines = result.strip().split('\n')
    if len(lines) <= 1:  # Only header or empty
        return []
    
    downloads = []
    for line in lines[1:]:  # Skip header
        parts = line.split('\t')
        if len(parts) >= 5:
            downloads.append({
                'id': parts[0],
                'title': parts[1],
                'artist': parts[2] if parts[2] != 'NULL' else 'Unknown',
                'status': parts[3],
                'created_at': parts[4]
            })
    
    return downloads

def fix_stuck_downloads():
    """Fix videos stuck in DOWNLOADING status"""
    
    print("🔍 Checking for videos stuck in DOWNLOADING status...")
    
    stuck_downloads = get_stuck_downloads()
    
    if not stuck_downloads:
        print("✅ No videos found stuck in DOWNLOADING status")
        return True
    
    print(f"📋 Found {len(stuck_downloads)} videos stuck in DOWNLOADING status:")
    for download in stuck_downloads:
        print(f"   - {download['title']} by {download['artist']} (ID: {download['id']})")
    
    print()
    print("⚠️  These videos show as 'downloading' but are not in the active download queue.")
    print("   This happens when the application restarts while downloads are active.")
    print("   Options:")
    print("   1. Reset to WANTED - Videos will be available for download again")
    print("   2. Reset to DISCOVERED - Videos will be marked as discovered but not wanted")
    print("   3. Cancel - Leave as is")
    print()
    
    choice = input("Choose an option (1/2/3): ").strip()
    
    if choice == '1':
        new_status = 'WANTED'
        description = "reset to WANTED status"
    elif choice == '2':
        new_status = 'DISCOVERED'  
        description = "reset to DISCOVERED status"
    else:
        print("❌ Operation cancelled")
        return True
    
    print(f"\n🔧 Updating {len(stuck_downloads)} videos to {new_status} status...")
    
    # Update the video statuses
    video_ids = [d['id'] for d in stuck_downloads]
    ids_string = ','.join(video_ids)
    
    update_sql = f"""
        UPDATE videos 
        SET status = '{new_status}', updated_at = NOW() 
        WHERE id IN ({ids_string});
    """
    
    success, result = run_mysql_command(update_sql)
    
    if not success:
        print(f"❌ Error updating video statuses: {result}")
        return False
    
    print(f"✅ Successfully {description} for {len(stuck_downloads)} videos")
    
    # Also clean up any orphaned download entries
    print("\n🧹 Cleaning up any orphaned download entries...")
    cleanup_sql = "DELETE FROM downloads WHERE status IN ('downloading', 'pending') AND metube_id IS NULL;"
    
    success, result = run_mysql_command(cleanup_sql)
    if success:
        print("✅ Cleaned up orphaned download entries")
    else:
        print(f"⚠️  Could not clean up download entries: {result}")
    
    return True

def verify_fix():
    """Verify the fix worked"""
    
    print("\n🔍 Verifying fix...")
    
    # Check for remaining DOWNLOADING videos
    stuck_downloads = get_stuck_downloads()
    if stuck_downloads:
        print(f"⚠️  Still found {len(stuck_downloads)} videos in DOWNLOADING status")
        return False
    
    # Check download queue via API would require Flask context
    print("✅ No videos found stuck in DOWNLOADING status")
    return True

def main():
    """Main execution function"""
    
    print("=" * 60)
    print("MVidarr Enhanced - Fix Download Queue Display Issue")
    print("=" * 60)
    
    # Test MySQL connection
    success, result = run_mysql_command("SELECT 1;")
    if not success:
        print(f"❌ Cannot connect to MariaDB: {result}")
        sys.exit(1)
    
    # Fix stuck downloads
    if not fix_stuck_downloads():
        print("❌ Failed to fix download queue issue!")
        sys.exit(1)
    
    # Verify fix
    if not verify_fix():
        print("⚠️  Fix may not have been completely successful")
    
    print("\n" + "=" * 60)
    print("✅ Download queue fix completed!")
    print("=" * 60)
    print("📋 Next steps:")
    print("  1. Refresh the dashboard: http://localhost:5000")
    print("  2. Check the download queue - should now be empty")
    print("  3. Videos should no longer show as 'downloading'")
    print("  4. Try downloading videos again to test the fix")

if __name__ == "__main__":
    main()