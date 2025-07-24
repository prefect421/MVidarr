#!/usr/bin/env python3
"""
Clear Database Content Script
Removes all video and artist entries from the MVidarr database while preserving structure
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import sqlite3

def get_db_path():
    """Get database path"""
    return str(Path(__file__).parent.parent / 'data' / 'mvidarr.db')

def get_logger(name):
    """Simple logger"""
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logging.getLogger(name)

logger = get_logger('mvidarr.clear_database')

def clear_database_content():
    """Clear all video and artist entries from the database"""
    
    db_path = get_db_path()
    logger.info(f"Connecting to database: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get counts before deletion
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM artists")
        artist_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM downloads")
        download_count = cursor.fetchone()[0]
        
        logger.info(f"Found {video_count} videos, {artist_count} artists, {download_count} downloads")
        
        if video_count == 0 and artist_count == 0 and download_count == 0:
            logger.info("Database is already empty of content")
            conn.close()
            return True
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Clear related tables first (foreign key constraints)
        logger.info("Clearing downloads table...")
        cursor.execute("DELETE FROM downloads")
        
        logger.info("Clearing videos table...")
        cursor.execute("DELETE FROM videos")
        
        logger.info("Clearing artists table...")
        cursor.execute("DELETE FROM artists")
        
        # Reset auto-increment counters
        logger.info("Resetting auto-increment sequences...")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('videos', 'artists', 'downloads')")
        
        # Commit transaction
        cursor.execute("COMMIT")
        conn.close()
        
        logger.info("✅ Database content cleared successfully!")
        logger.info(f"   - Removed {video_count} videos")
        logger.info(f"   - Removed {artist_count} artists") 
        logger.info(f"   - Removed {download_count} downloads")
        logger.info("   - Reset ID sequences")
        
        return True
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        try:
            cursor.execute("ROLLBACK")
            conn.close()
        except:
            pass
        return False

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
            
            logger.info(f"Removing {len(files)} files from {thumb_dir}")
            
            for file in files:
                try:
                    if file.is_file():
                        file.unlink()
                        total_removed += 1
                except Exception as e:
                    logger.warning(f"Failed to remove {file}: {e}")
    
    logger.info(f"✅ Removed {total_removed} thumbnail files")
    return total_removed

def clear_video_files():
    """Clear video files from filesystem (optional - commented out for safety)"""
    
    logger.info("Video file cleanup is disabled for safety")
    logger.info("To remove video files manually:")
    logger.info("  - Check: data/musicvideos/ or data/downloads/")
    logger.info("  - Remove individual artist folders as needed")
    
    # Uncomment below to enable video file removal (USE WITH CAUTION)
    """
    base_dir = Path(__file__).parent.parent
    video_dirs = [
        base_dir / 'data' / 'musicvideos',
        base_dir / 'data' / 'downloads'
    ]
    
    total_removed = 0
    
    for video_dir in video_dirs:
        if video_dir.exists():
            for artist_dir in video_dir.iterdir():
                if artist_dir.is_dir():
                    logger.info(f"Removing artist directory: {artist_dir}")
                    shutil.rmtree(artist_dir)
                    total_removed += 1
    
    logger.info(f"✅ Removed {total_removed} artist video directories")
    """

def main():
    """Main execution function"""
    
    logger.info("=" * 60)
    logger.info("MVidarr Enhanced - Database Content Clearing")
    logger.info("=" * 60)
    
    # Confirm operation
    print("\n⚠️  WARNING: This will permanently delete all videos and artists from the database!")
    print("   - All video records will be removed")
    print("   - All artist records will be removed") 
    print("   - All download records will be removed")
    print("   - Thumbnail files will be removed")
    print("   - Video files will remain (manual cleanup required)")
    print()
    
    confirm = input("Are you sure you want to continue? (type 'yes' to confirm): ")
    
    if confirm.lower() != 'yes':
        logger.info("Operation cancelled by user")
        return
    
    # Clear database content
    logger.info("\n🗄️  Clearing database content...")
    if not clear_database_content():
        logger.error("Database clearing failed!")
        sys.exit(1)
    
    # Clear thumbnail files
    logger.info("\n🖼️  Clearing thumbnail files...")
    clear_thumbnail_files()
    
    # Info about video files
    logger.info("\n📹 Video file information:")
    clear_video_files()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Database clearing completed successfully!")
    logger.info("=" * 60)
    logger.info("Next steps:")
    logger.info("  1. Restart the application if needed")
    logger.info("  2. Manually remove video files from data/musicvideos/ if desired")
    logger.info("  3. Start fresh with new artist imports")

if __name__ == "__main__":
    main()