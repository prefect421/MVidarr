#!/usr/bin/env python3
"""
Check Database Status
Check what data exists in the current database
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from src.database.connection import get_db
    from src.database.models import Artist, Video, Download
    
    print("✅ Using application database connection")
    
    with get_db() as db_session:
        artist_count = db_session.query(Artist).count()
        video_count = db_session.query(Video).count() 
        download_count = db_session.query(Download).count()
        
        print(f"📊 Database Status:")
        print(f"   - Artists: {artist_count}")
        print(f"   - Videos: {video_count}")
        print(f"   - Downloads: {download_count}")
        
        if artist_count > 0:
            artists = db_session.query(Artist).limit(5).all()
            print(f"\n🎵 Sample Artists:")
            for artist in artists:
                print(f"   - {artist.name} (ID: {artist.id})")
        
        if video_count > 0:
            videos = db_session.query(Video).limit(5).all()
            print(f"\n🎬 Sample Videos:")
            for video in videos:
                print(f"   - {video.title} by {video.artist} (ID: {video.id})")

except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("Trying SQLite fallback...")
    
    # Fallback to direct SQLite
    import sqlite3
    db_path = Path(__file__).parent.parent / 'data' / 'mvidarr.db'
    
    if db_path.exists() and db_path.stat().st_size > 0:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 SQLite Tables: {[t[0] for t in tables]}")
        
        conn.close()
    else:
        print("📂 No valid database found")