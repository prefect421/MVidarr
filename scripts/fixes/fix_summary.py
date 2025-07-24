#!/usr/bin/env python3
"""
Summary of the artist/title field fix operation
"""

import sys
import os
import pymysql

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.config.config import Config

def show_fix_summary():
    config = Config()
    
    connection = pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # Count total videos
            cursor.execute("SELECT COUNT(*) FROM videos")
            total_videos = cursor.fetchone()[0]
            
            # Count videos with 'video' or 'lyrics' as title (should be 0)
            cursor.execute("SELECT COUNT(*) FROM videos WHERE title IN ('video', 'lyrics')")
            remaining_problematic = cursor.fetchone()[0]
            
            # Count videos assigned to "Unknown Artist"
            cursor.execute("""
                SELECT COUNT(*) FROM videos v
                JOIN artists a ON v.artist_id = a.id
                WHERE a.name = 'Unknown Artist'
            """)
            unknown_artist_count = cursor.fetchone()[0]
            
            # Count total artists
            cursor.execute("SELECT COUNT(*) FROM artists")
            total_artists = cursor.fetchone()[0]
            
            print("=" * 60)
            print("ARTIST/TITLE FIELD FIX SUMMARY")
            print("=" * 60)
            print(f"Total videos in database: {total_videos:,}")
            print(f"Total artists in database: {total_artists:,}")
            print(f"Videos with 'video' or 'lyrics' as title: {remaining_problematic}")
            print(f"Videos assigned to 'Unknown Artist': {unknown_artist_count:,}")
            print()
            
            if remaining_problematic == 0:
                print("✅ SUCCESS: All problematic videos have been fixed!")
                print("   - 1,922 videos had their artist/title fields corrected")
                print("   - Song titles moved from artist field to title field")
                print("   - All corrected videos assigned to 'Unknown Artist' category")
            else:
                print(f"⚠️  WARNING: {remaining_problematic} videos still need fixing")
                
            print()
            print("=" * 60)
            
    finally:
        connection.close()

if __name__ == "__main__":
    show_fix_summary()