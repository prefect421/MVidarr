#!/usr/bin/env python3
"""
Fix Download Completion Issue
Adds database updates to ytdlp service and fixes existing downloaded videos
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

def find_downloaded_files():
    """Find video files that were downloaded but not marked as DOWNLOADED in database"""
    
    print("🔍 Scanning for downloaded video files...")
    
    # Get videos that show as DOWNLOADING but may have files
    success, result = run_mysql_command("""
        SELECT v.id, v.title, a.name as artist_name, v.status, v.local_path 
        FROM videos v 
        LEFT JOIN artists a ON v.artist_id = a.id 
        WHERE v.status = 'DOWNLOADING' 
        ORDER BY v.created_at DESC;
    """)
    
    if not success:
        print(f"❌ Error querying videos: {result}")
        return []
    
    # Parse results
    lines = result.strip().split('\n')
    if len(lines) <= 1:
        print("✅ No videos found in DOWNLOADING status")
        return []
    
    downloaded_videos = []
    music_videos_path = Path("data/musicvideos")
    
    print(f"📋 Checking {len(lines)-1} videos in DOWNLOADING status...")
    
    for line in lines[1:]:  # Skip header
        parts = line.split('\t')
        if len(parts) >= 5:
            video_id = parts[0]
            title = parts[1]
            artist = parts[2] if parts[2] != 'NULL' else 'Unknown'
            status = parts[3]
            local_path = parts[4] if parts[4] != 'NULL' else None
            
            # Look for the file in the expected location
            artist_folder = music_videos_path / artist.replace('/', '_')
            
            if artist_folder.exists():
                # Look for files matching the video title
                video_files = []
                for ext in ['mp4', 'mkv', 'webm', 'avi']:
                    pattern = f"*{title}*.{ext}"
                    matches = list(artist_folder.glob(pattern))
                    video_files.extend(matches)
                
                # Also check for files with simplified patterns
                if not video_files:
                    for ext in ['mp4', 'mkv', 'webm', 'avi']:
                        all_files = list(artist_folder.glob(f"*.{ext}"))
                        # Look for files that might match
                        for file in all_files:
                            if any(word in file.name.lower() for word in title.lower().split()[:3]):
                                video_files.append(file)
                                break
                
                if video_files:
                    # Found a downloaded file
                    video_file = video_files[0]  # Use first match
                    file_size = video_file.stat().st_size if video_file.exists() else 0
                    
                    downloaded_videos.append({
                        'id': video_id,
                        'title': title,
                        'artist': artist,
                        'file_path': str(video_file),
                        'file_size': file_size
                    })
                    
                    print(f"   ✅ Found: {title} by {artist}")
                    print(f"      File: {video_file}")
                else:
                    print(f"   ❌ Missing: {title} by {artist}")
    
    return downloaded_videos

def update_downloaded_videos(downloaded_videos):
    """Update database to mark videos as DOWNLOADED with file paths"""
    
    if not downloaded_videos:
        print("✅ No videos need database updates")
        return True
    
    print(f"\n🔧 Updating {len(downloaded_videos)} videos to DOWNLOADED status...")
    
    for video in downloaded_videos:
        # Update video status and file path
        update_sql = f"""
            UPDATE videos 
            SET status = 'DOWNLOADED', 
                local_path = '{video['file_path']}',
                updated_at = NOW()
            WHERE id = {video['id']};
        """
        
        success, result = run_mysql_command(update_sql)
        if success:
            print(f"   ✅ Updated: {video['title']}")
        else:
            print(f"   ❌ Failed to update {video['title']}: {result}")
            return False
    
    return True

def add_database_sync_to_ytdlp():
    """Add database synchronization to ytdlp service"""
    
    print("\n🔧 Adding database synchronization to ytdlp service...")
    
    ytdlp_service_path = Path("src/services/ytdlp_service.py")
    
    if not ytdlp_service_path.exists():
        print(f"❌ ytdlp service not found: {ytdlp_service_path}")
        return False
    
    # Read the current file
    with open(ytdlp_service_path, 'r') as f:
        content = f.read()
    
    # Check if database sync is already added
    if "update_video_status_in_database" in content:
        print("✅ Database synchronization already present in ytdlp service")
        return True
    
    # Add imports at the top
    import_addition = """from src.database.connection import get_db
from src.database.models import Video"""
    
    if "from src.database.connection import get_db" not in content:
        # Find the imports section and add our imports
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('from src.') or line.startswith('import '):
                insert_pos = i + 1
        
        lines.insert(insert_pos, "from src.database.connection import get_db")
        lines.insert(insert_pos + 1, "from src.database.models import Video")
        content = '\n'.join(lines)
    
    # Add database update method
    db_method = '''
    def _update_video_status_in_database(self, video_id: int, status: str, file_path: str = None, file_size: int = None):
        """Update video status in database"""
        if not video_id:
            return
        
        try:
            with get_db() as session:
                video = session.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = status
                    if file_path:
                        video.local_path = file_path
                    if status == 'DOWNLOADED':
                        # Ensure we have the file info
                        if file_path and os.path.exists(file_path):
                            video.local_path = file_path
                            if not file_size:
                                file_size = os.path.getsize(file_path)
                    session.commit()
                    logger.info(f"Updated video {video_id} status to {status} in database")
                else:
                    logger.warning(f"Video {video_id} not found in database")
        except Exception as e:
            logger.error(f"Failed to update video {video_id} status in database: {e}")
'''
    
    # Find where to insert the method (before get_queue method)
    get_queue_pos = content.find("def get_queue(self)")
    if get_queue_pos == -1:
        print("❌ Could not find get_queue method to insert database sync")
        return False
    
    # Insert the method before get_queue
    content = content[:get_queue_pos] + db_method + "\n    " + content[get_queue_pos:]
    
    # Add database sync calls in the download completion logic
    # Find the successful completion section
    success_pattern = "download_entry['status'] = 'completed'"
    success_pos = content.find(success_pattern)
    
    if success_pos != -1:
        # Find the end of this section
        lines = content[success_pos:].split('\n')
        insert_line = -1
        for i, line in enumerate(lines):
            if 'logger.info' in line and 'completed successfully' in line:
                insert_line = i + 1
                break
        
        if insert_line != -1:
            # Insert database sync after the success logging
            sync_call = "                        # Sync to database\n                        self._update_video_status_in_database(video_id, 'DOWNLOADED', download_entry.get('file_path'), download_entry.get('file_size'))"
            
            before_lines = content[:success_pos].split('\n')
            after_lines = content[success_pos:].split('\n')
            
            after_lines.insert(insert_line, sync_call)
            content = '\n'.join(before_lines + after_lines)
            
            print("✅ Added database sync for successful downloads")
    
    # Add database sync for failed downloads
    fail_pattern = "download_entry['status'] = 'failed'"
    content = content.replace(
        fail_pattern,
        fail_pattern + "\n                self._update_video_status_in_database(video_id, 'FAILED')"
    )
    
    # Write the updated file
    with open(ytdlp_service_path, 'w') as f:
        f.write(content)
    
    print("✅ Database synchronization added to ytdlp service")
    return True

def main():
    """Main execution function"""
    
    print("=" * 60)
    print("MVidarr - Fix Download Completion Issue")
    print("=" * 60)
    
    # Test MySQL connection
    success, result = run_mysql_command("SELECT 1;")
    if not success:
        print(f"❌ Cannot connect to MariaDB: {result}")
        sys.exit(1)
    
    # Find downloaded files that need database updates
    downloaded_videos = find_downloaded_files()
    
    # Update database for existing downloaded files
    if not update_downloaded_videos(downloaded_videos):
        print("❌ Failed to update video statuses!")
        sys.exit(1)
    
    # Add database synchronization to ytdlp service
    if not add_database_sync_to_ytdlp():
        print("❌ Failed to add database synchronization!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Download completion fix applied successfully!")
    print("=" * 60)
    print("📋 Changes made:")
    print(f"  - Updated {len(downloaded_videos)} videos to DOWNLOADED status")
    print("  - Added database synchronization to ytdlp service")
    print("  - Future downloads will properly update video status")
    print()
    print("📋 Next steps:")
    print("  1. Restart the application: ./manage.sh restart")
    print("  2. Check video statuses are now correct")
    print("  3. Test new downloads to verify database sync works")

if __name__ == "__main__":
    main()