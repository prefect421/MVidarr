#!/usr/bin/env python3
"""
Simple fix for swapped artist/title fields
"""

import sys
import os
import pymysql
import re

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.config.config import Config

def fix_swapped_fields(dry_run=True):
    config = Config()
    
    # Direct MySQL connection
    connection = pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # Find problematic videos where title is 'video' or 'lyrics' and artist_name looks like a song
            cursor.execute("""
                SELECT v.id, v.title, a.name as artist_name, v.artist_id
                FROM videos v
                JOIN artists a ON v.artist_id = a.id
                WHERE v.title IN ('video', 'lyrics')
                ORDER BY v.id
            """)
            
            results = cursor.fetchall()
            
            print(f"Found {len(results)} videos with 'video' or 'lyrics' as title")
            print(f"Running in {'DRY RUN' if dry_run else 'LIVE'} mode")
            print("=" * 80)
            
            fixed_count = 0
            
            for row in results:
                video_id, title, artist_name, artist_id = row
                
                # Extract song title from artist name (which contains the actual song title)
                song_title = artist_name.strip()
                
                # Skip if the artist name looks like an actual artist name (very short or common patterns)
                if len(song_title) < 3 or song_title.lower() in ['unknown', 'various', 'artist']:
                    continue
                
                # Look for or create "Unknown Artist" entry
                cursor.execute("SELECT id FROM artists WHERE name = %s", ('Unknown Artist',))
                unknown_artist = cursor.fetchone()
                
                if not unknown_artist:
                    if not dry_run:
                        cursor.execute("""
                            INSERT INTO artists (name, monitored, created_at, updated_at)
                            VALUES (%s, %s, NOW(), NOW())
                        """, ('Unknown Artist', True))
                        unknown_artist_id = cursor.lastrowid
                    else:
                        unknown_artist_id = 9999  # Placeholder for dry run
                else:
                    unknown_artist_id = unknown_artist[0]
                
                print(f"Video ID {video_id}:")
                print(f"  Current: Artist='{artist_name}' | Title='{title}'")
                print(f"  Fixed:   Artist='Unknown Artist' | Title='{song_title}'")
                
                if not dry_run:
                    # Update the video record
                    cursor.execute("""
                        UPDATE videos
                        SET title = %s, artist_id = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (song_title, unknown_artist_id, video_id))
                
                fixed_count += 1
                
                # Show progress every 100 records
                if fixed_count % 100 == 0:
                    print(f"  ... processed {fixed_count} records so far")
                
            if not dry_run:
                connection.commit()
                print(f"\nCommitted {fixed_count} fixes to database")
            else:
                print(f"\nDry run completed - {fixed_count} videos would be fixed")
                
    except Exception as e:
        print(f"Error: {e}")
        if not dry_run:
            connection.rollback()
    finally:
        connection.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix swapped artist/title fields")
    parser.add_argument("--execute", action="store_true", help="Execute fixes (default is dry run)")
    
    args = parser.parse_args()
    
    if args.execute:
        print("WARNING: This will make actual changes to the database!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Aborted.")
            return
    
    fix_swapped_fields(dry_run=not args.execute)

if __name__ == "__main__":
    main()