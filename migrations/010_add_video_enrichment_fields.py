#!/usr/bin/env python3
"""
Migration 010: Add video enrichment fields (album, last_enriched)
Date: August 18, 2025
Purpose: Add missing fields to videos table for metadata enrichment functionality
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db
from src.utils.logger import get_logger
from sqlalchemy import text

logger = get_logger('mvidarr.migration_010')

def upgrade():
    """Add video enrichment fields"""
    try:
        with get_db() as session:
            logger.info("Starting migration 010: Adding video enrichment fields")
            
            # Add album field for track album information
            session.execute(text("""
                ALTER TABLE videos ADD COLUMN album VARCHAR(500)
            """))
            
            # Add last_enriched timestamp field  
            session.execute(text("""
                ALTER TABLE videos ADD COLUMN last_enriched DATETIME
            """))
            
            session.commit()
            logger.info("✅ Migration 010: Successfully added video enrichment fields")
            
    except Exception as e:
        logger.error(f"❌ Migration 010 failed: {e}")
        raise


def downgrade():
    """Remove video enrichment fields"""
    try:
        with get_db() as session:
            logger.info("Starting migration 010 downgrade: Removing video enrichment fields")
            
            # Remove added columns
            session.execute(text("""
                ALTER TABLE videos DROP COLUMN last_enriched
            """))
            
            session.execute(text("""
                ALTER TABLE videos DROP COLUMN album
            """))
            
            session.commit()
            logger.info("✅ Migration 010: Successfully removed video enrichment fields")
            
    except Exception as e:
        logger.error(f"❌ Migration 010 downgrade failed: {e}")
        raise


if __name__ == "__main__":
    # Run migration
    print("Migration 010: Add video enrichment fields")
    print("This migration adds album and last_enriched fields to the videos table")
    upgrade()