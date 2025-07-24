#!/usr/bin/env python3
"""
Migration: Add video discovery fields to database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text, create_engine
from src.database.connection import DatabaseManager
from src.config.config import Config
from src.utils.logger import get_logger

logger = get_logger('mvidarr.migration.video_discovery')

def run_migration():
    """Add video discovery fields to database"""
    
    try:
        config = Config()
        db_manager = DatabaseManager(config)
        connection_url = db_manager.get_connection_url()
        engine = create_engine(connection_url)
        
        migrations = [
            # Add last_discovery field to artists table
            "ALTER TABLE artists ADD COLUMN last_discovery DATETIME NULL",
            
            # Add new fields to videos table
            "ALTER TABLE videos ADD COLUMN url VARCHAR(500) NULL",
            "ALTER TABLE videos ADD COLUMN release_date DATETIME NULL", 
            "ALTER TABLE videos ADD COLUMN description TEXT NULL",
            "ALTER TABLE videos ADD COLUMN view_count INTEGER NULL",
            "ALTER TABLE videos ADD COLUMN video_metadata JSON NULL",
            "ALTER TABLE videos ADD COLUMN discovered_date DATETIME NULL",
            
            # Copy video_url to url field if it exists
            "UPDATE videos SET url = video_url WHERE video_url IS NOT NULL",
            
            # Update status field to use enum values consistently
            "UPDATE videos SET status = 'wanted' WHERE status NOT IN ('wanted', 'downloaded', 'ignored', 'failed') OR status IS NULL",
            
            # Convert lowercase status values to uppercase for enum compatibility
            "UPDATE videos SET status = 'WANTED' WHERE status = 'wanted'",
            "UPDATE videos SET status = 'DOWNLOADED' WHERE status = 'downloaded'",
            "UPDATE videos SET status = 'IGNORED' WHERE status = 'ignored'",
            "UPDATE videos SET status = 'FAILED' WHERE status = 'failed'",
        ]
        
        with engine.connect() as connection:
            for migration_sql in migrations:
                try:
                    logger.info(f"Executing: {migration_sql}")
                    connection.execute(text(migration_sql))
                    connection.commit()
                except Exception as e:
                    if "Duplicate column name" in str(e) or "already exists" in str(e):
                        logger.info(f"Column already exists, skipping: {migration_sql}")
                    else:
                        logger.error(f"Migration failed: {migration_sql} - {e}")
                        raise
        
        logger.info("Video discovery migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("Running video discovery migration...")
    success = run_migration()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)