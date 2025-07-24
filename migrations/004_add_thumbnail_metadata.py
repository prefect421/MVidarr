#!/usr/bin/env python3
"""
Database migration 004: Add thumbnail metadata and source tracking
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.database.connection import get_db
from src.utils.logger import get_logger

logger = get_logger('mvidarr.migration_004')

def upgrade():
    """Add thumbnail metadata and source tracking columns"""
    logger.info("Running migration 004: Add thumbnail metadata and source tracking")
    
    try:
        with get_db() as session:
            # Add thumbnail metadata columns to artists table
            session.execute("""
                ALTER TABLE artists 
                ADD COLUMN thumbnail_source VARCHAR(50) DEFAULT NULL,
                ADD COLUMN thumbnail_metadata JSON DEFAULT NULL,
                ADD COLUMN thumbnail_uploaded_at DATETIME DEFAULT NULL
            """)
            
            # Add thumbnail metadata columns to videos table
            session.execute("""
                ALTER TABLE videos 
                ADD COLUMN thumbnail_source VARCHAR(50) DEFAULT NULL,
                ADD COLUMN thumbnail_metadata JSON DEFAULT NULL,
                ADD COLUMN thumbnail_uploaded_at DATETIME DEFAULT NULL
            """)
            
            # Set default source for existing thumbnails
            session.execute("""
                UPDATE artists 
                SET thumbnail_source = 'imvdb' 
                WHERE thumbnail_url IS NOT NULL OR thumbnail_path IS NOT NULL
            """)
            
            session.execute("""
                UPDATE videos 
                SET thumbnail_source = 'imvdb' 
                WHERE thumbnail_url IS NOT NULL OR thumbnail_path IS NOT NULL
            """)
            
            session.commit()
            logger.info("Migration 004 completed successfully")
            
    except Exception as e:
        logger.error(f"Migration 004 failed: {e}")
        raise

def downgrade():
    """Remove thumbnail metadata and source tracking columns"""
    logger.info("Running downgrade for migration 004")
    
    try:
        with get_db() as session:
            # Remove thumbnail metadata columns from artists table
            session.execute("""
                ALTER TABLE artists 
                DROP COLUMN thumbnail_source,
                DROP COLUMN thumbnail_metadata,
                DROP COLUMN thumbnail_uploaded_at
            """)
            
            # Remove thumbnail metadata columns from videos table
            session.execute("""
                ALTER TABLE videos 
                DROP COLUMN thumbnail_source,
                DROP COLUMN thumbnail_metadata,
                DROP COLUMN thumbnail_uploaded_at
            """)
            
            session.commit()
            logger.info("Migration 004 downgrade completed successfully")
            
    except Exception as e:
        logger.error(f"Migration 004 downgrade failed: {e}")
        raise

if __name__ == '__main__':
    # Create Flask app context for database access
    import os
    os.chdir(Path(__file__).parent.parent)
    
    from app import create_app
    app = create_app()
    
    with app.app_context():
        upgrade()