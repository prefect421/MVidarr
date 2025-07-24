#!/usr/bin/env python3
"""
Check specific video assignment
"""

import sys
import os
import pymysql

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.config.config import Config

def check_video(video_id):
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
            cursor.execute("""
                SELECT v.id, v.title, a.name as artist_name
                FROM videos v
                JOIN artists a ON v.artist_id = a.id
                WHERE v.id = %s
            """, (video_id,))
            
            result = cursor.fetchone()
            if result:
                video_id, title, artist_name = result
                print(f"Video ID {video_id}: '{title}' -> Artist: '{artist_name}'")
            else:
                print(f"Video ID {video_id} not found")
                
    finally:
        connection.close()

if __name__ == "__main__":
    check_video(129)