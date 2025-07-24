#!/usr/bin/env python3
"""
Add genre columns to artists and videos tables
"""

import sys
import os

# Add the project root directory to the path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.database.connection import DatabaseManager
from src.config.config import Config
from src.utils.logger import get_logger

logger = get_logger('mvidarr.migrations.add_genre_columns')

def add_genre_columns():
    """Add genre columns to artists and videos tables"""
    config = Config()
    db_manager = DatabaseManager(config)
    engine = db_manager.create_engine()
    
    try:
        with engine.connect() as conn:
            # Add genres column to artists table
            try:
                from sqlalchemy import text
                conn.execute(text("ALTER TABLE artists ADD COLUMN genres JSON"))
                logger.info("Added genres column to artists table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    logger.info("genres column already exists in artists table")
                else:
                    raise e
            
            # Add genres column to videos table
            try:
                conn.execute(text("ALTER TABLE videos ADD COLUMN genres JSON"))
                logger.info("Added genres column to videos table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    logger.info("genres column already exists in videos table")
                else:
                    raise e
            
            conn.commit()
            logger.info("Genre columns migration completed successfully")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    
    return True

def remove_genre_columns():
    """Remove genre columns from artists and videos tables"""
    config = Config()
    db_manager = DatabaseManager(config)
    engine = db_manager.create_engine()
    
    try:
        with engine.connect() as conn:
            # Remove genres column from artists table
            try:
                from sqlalchemy import text
                conn.execute(text("ALTER TABLE artists DROP COLUMN genres"))
                logger.info("Removed genres column from artists table")
            except Exception as e:
                if "Can't DROP" in str(e) and "check that column/key exists" in str(e):
                    logger.info("genres column doesn't exist in artists table")
                else:
                    raise e
            
            # Remove genres column from videos table
            try:
                conn.execute(text("ALTER TABLE videos DROP COLUMN genres"))
                logger.info("Removed genres column from videos table")
            except Exception as e:
                if "Can't DROP" in str(e) and "check that column/key exists" in str(e):
                    logger.info("genres column doesn't exist in videos table")
                else:
                    raise e
            
            conn.commit()
            logger.info("Genre columns removal completed successfully")
            
    except Exception as e:
        logger.error(f"Migration rollback failed: {e}")
        return False
    
    return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add genre columns to database')
    parser.add_argument('--rollback', action='store_true', help='Remove genre columns')
    
    args = parser.parse_args()
    
    if args.rollback:
        success = remove_genre_columns()
        action = "rollback"
    else:
        success = add_genre_columns()
        action = "migration"
    
    if success:
        print(f"Genre columns {action} completed successfully")
        return 0
    else:
        print(f"Genre columns {action} failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())