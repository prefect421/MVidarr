#!/usr/bin/env python3
"""
Migration: Add light_theme_data column to custom_themes table
Version: 007
Date: 2025-01-08
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.database.connection import get_db
from src.utils.logger import get_logger
from sqlalchemy import text

logger = get_logger('mvidarr.migration_007')

def upgrade():
    """Add light_theme_data column to custom_themes table"""
    try:
        with get_db() as session:
            # Check if the column already exists
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'custom_themes' 
                AND column_name = 'light_theme_data'
            """)).fetchone()
            
            if not result:
                # Add the light_theme_data column
                session.execute(text("""
                    ALTER TABLE custom_themes 
                    ADD COLUMN light_theme_data JSON NULL
                """))
                session.commit()
                logger.info("Added light_theme_data column to custom_themes table")
            else:
                logger.info("light_theme_data column already exists in custom_themes table")
                
    except Exception as e:
        logger.error(f"Failed to add light_theme_data column: {e}")
        raise

def downgrade():
    """Remove light_theme_data column from custom_themes table"""
    try:
        with get_db() as session:
            # Check if the column exists
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'custom_themes' 
                AND column_name = 'light_theme_data'
            """)).fetchone()
            
            if result:
                # Remove the light_theme_data column
                session.execute(text("""
                    ALTER TABLE custom_themes 
                    DROP COLUMN light_theme_data
                """))
                session.commit()
                logger.info("Removed light_theme_data column from custom_themes table")
            else:
                logger.info("light_theme_data column does not exist in custom_themes table")
                
    except Exception as e:
        logger.error(f"Failed to remove light_theme_data column: {e}")
        raise

if __name__ == "__main__":
    # Run upgrade when script is executed directly
    upgrade()