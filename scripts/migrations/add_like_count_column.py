#!/usr/bin/env python3
"""
Migration: Add like_count column to videos table
"""

import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.connection import get_db
from src.utils.logger import get_logger
from sqlalchemy import text

logger = get_logger('mvidarr.migration.add_like_count')

def migrate():
    """Add like_count column to videos table"""
    try:
        with get_db() as session:
            # Check if column already exists
            result = session.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.columns 
                WHERE table_name = 'videos' 
                AND column_name = 'like_count'
                AND table_schema = DATABASE()
            """))
            
            column_exists = result.fetchone()[0] > 0
            
            if column_exists:
                logger.info("Column 'like_count' already exists in videos table")
                return True
            
            # Add the column
            session.execute(text("""
                ALTER TABLE videos 
                ADD COLUMN like_count INTEGER NULL 
                COMMENT 'Like count from video platforms'
            """))
            
            session.commit()
            logger.info("Successfully added like_count column to videos table")
            return True
            
    except Exception as e:
        logger.error(f"Failed to add like_count column: {e}")
        return False

def rollback():
    """Remove like_count column from videos table"""
    try:
        with get_db() as session:
            # Check if column exists
            result = session.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.columns 
                WHERE table_name = 'videos' 
                AND column_name = 'like_count'
                AND table_schema = DATABASE()
            """))
            
            column_exists = result.fetchone()[0] > 0
            
            if not column_exists:
                logger.info("Column 'like_count' does not exist in videos table")
                return True
            
            # Remove the column
            session.execute(text("""
                ALTER TABLE videos 
                DROP COLUMN like_count
            """))
            
            session.commit()
            logger.info("Successfully removed like_count column from videos table")
            return True
            
    except Exception as e:
        logger.error(f"Failed to remove like_count column: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Add like_count column to videos table')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
        action = "rollback"
    else:
        success = migrate()
        action = "migration"
    
    if success:
        print(f"✅ {action.capitalize()} completed successfully")
        sys.exit(0)
    else:
        print(f"❌ {action.capitalize()} failed")
        sys.exit(1)