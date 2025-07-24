#!/usr/bin/env python3
"""
Show problematic videos with swapped artist/title fields
"""

import sys
import os

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.database.connection import DatabaseManager
from src.database.models import Artist, Video
from src.config.config import Config

def show_problematic_videos():
    print("Finding problematic videos...")
    
    config = Config()
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_session() as session:
            # Simple query for videos with 'video' as title
            query = session.query(
                Video.id,
                Video.title,
                Artist.name.label('artist_name'),
                Video.artist_id
            ).join(Artist).filter(
                Video.title == 'video'
            ).order_by(Video.id).limit(10)
            
            print(f"{'ID':<5} {'Title':<20} {'Artist Name':<50}")
            print("-" * 80)
            
            for row in query:
                print(f"{row.id:<5} {row.title:<20} {row.artist_name:<50}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_problematic_videos()