#!/usr/bin/env python3
"""
Check for videos with 'lyrics' as title
"""

import sys
import os
import pymysql

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.config.config import Config

def check_lyrics_videos():
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
            # Find videos with 'lyrics' as title
            cursor.execute("""
                SELECT v.id, v.title, a.name as artist_name, v.artist_id
                FROM videos v
                JOIN artists a ON v.artist_id = a.id
                WHERE v.title = 'lyrics'
                ORDER BY v.id
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            
            # Count total
            cursor.execute("SELECT COUNT(*) FROM videos WHERE title = 'lyrics'")
            total_count = cursor.fetchone()[0]
            
            print(f"Found {total_count} videos with 'lyrics' as title")
            print(f"Showing first {len(results)} examples:")
            print(f"{'ID':<5} {'Title':<20} {'Artist Name':<50}")
            print("-" * 80)
            
            for row in results:
                print(f"{row[0]:<5} {row[1]:<20} {row[2]:<50}")
                
    finally:
        connection.close()

if __name__ == "__main__":
    check_lyrics_videos()