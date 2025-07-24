#!/usr/bin/env python3
"""
Database migration to add external integration columns
"""

import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db, engine
from sqlalchemy import text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_external_integration_columns():
    """Add columns for external service integration"""
    
    migrations = [
        # Add spotify_id column to artists table
        "ALTER TABLE artists ADD COLUMN spotify_id VARCHAR(100) NULL",
        
        # Add lastfm_name column to artists table  
        "ALTER TABLE artists ADD COLUMN lastfm_name VARCHAR(255) NULL",
        
        # Add source column to artists table if it doesn't exist
        "ALTER TABLE artists ADD COLUMN source VARCHAR(50) NULL",
        
        # Add last_discovery column to artists table if it doesn't exist
        "ALTER TABLE artists ADD COLUMN last_discovery DATETIME NULL",
        
        # Add youtube_id column to videos table
        "ALTER TABLE videos ADD COLUMN youtube_id VARCHAR(100) NULL",
        
        # Add youtube_url column to videos table
        "ALTER TABLE videos ADD COLUMN youtube_url VARCHAR(500) NULL",
        
        # Add playlist_id column to videos table
        "ALTER TABLE videos ADD COLUMN playlist_id VARCHAR(100) NULL",
        
        # Add playlist_position column to videos table
        "ALTER TABLE videos ADD COLUMN playlist_position INTEGER NULL",
        
        # Add source column to videos table if it doesn't exist
        "ALTER TABLE videos ADD COLUMN source VARCHAR(50) NULL",
        
        # Add discovered_date column to videos table
        "ALTER TABLE videos ADD COLUMN discovered_date DATETIME NULL",
        
        # Add indexes for performance
        "CREATE INDEX idx_artist_spotify_id ON artists(spotify_id)",
        "CREATE INDEX idx_artist_lastfm_name ON artists(lastfm_name)",
        "CREATE INDEX idx_artist_source ON artists(source)",
        "CREATE INDEX idx_video_youtube_id ON videos(youtube_id)",
        "CREATE INDEX idx_video_playlist_id ON videos(playlist_id)",
        "CREATE INDEX idx_video_source ON videos(source)"
    ]
    
    with get_db() as session:
        for migration in migrations:
            try:
                logger.info(f"Running migration: {migration}")
                session.execute(text(migration))
                session.commit()
                logger.info(f"Migration successful: {migration}")
                
            except Exception as e:
                # Check if it's a "column already exists" error
                if "Duplicate column name" in str(e) or "already exists" in str(e):
                    logger.info(f"Column already exists, skipping: {migration}")
                    session.rollback()
                else:
                    logger.error(f"Migration failed: {migration} - {e}")
                    session.rollback()
                    raise

def main():
    """Main migration function"""
    try:
        logger.info("Starting database migration for external integrations...")
        add_external_integration_columns()
        logger.info("Database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()