#!/usr/bin/env python3
"""
Migration 005: Fix Missing Artist Folder Paths

This migration addresses Issue #16 by ensuring all artists have proper folder paths.
Artists imported from YouTube or other sources may be missing folder paths.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.connection import get_db
from src.database.models import Artist
from src.utils.filename_cleanup import FilenameCleanup
from src.utils.logger import get_logger

logger = get_logger("mvidarr.migration.005")


def migrate_artist_folder_paths():
    """
    Fix missing folder paths for all artists
    
    This addresses the issue where artists imported from YouTube or other sources
    may not have folder_path values set, making it unclear where files will be stored.
    """
    
    try:
        with get_db() as session:
            logger.info("Starting migration 005: Fix missing artist folder paths")
            
            # Find all artists
            all_artists = session.query(Artist).all()
            logger.info(f"Found {len(all_artists)} total artists")
            
            # Find artists without folder paths
            artists_without_paths = []
            artists_with_empty_paths = []
            
            for artist in all_artists:
                if not artist.folder_path:
                    artists_without_paths.append(artist)
                elif artist.folder_path.strip() == '':
                    artists_with_empty_paths.append(artist)
            
            total_to_fix = len(artists_without_paths) + len(artists_with_empty_paths)
            
            if total_to_fix == 0:
                logger.info("✅ All artists already have folder paths - no migration needed")
                return True
            
            logger.info(f"Found {len(artists_without_paths)} artists with NULL folder_path")
            logger.info(f"Found {len(artists_with_empty_paths)} artists with empty folder_path")
            logger.info(f"Total artists to fix: {total_to_fix}")
            
            # Fix artists without folder paths
            fixed_count = 0
            
            for artist in artists_without_paths + artists_with_empty_paths:
                try:
                    # Generate folder path using the same logic as create_artist
                    folder_path = FilenameCleanup.sanitize_folder_name(artist.name)
                    
                    # Update the artist
                    artist.folder_path = folder_path
                    
                    logger.info(f"Fixed artist ID {artist.id}: '{artist.name}' -> '{folder_path}'")
                    fixed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to fix artist {artist.id} '{artist.name}': {e}")
                    continue
            
            # Commit all changes
            session.commit()
            
            logger.info(f"✅ Migration 005 completed successfully")
            logger.info(f"✅ Fixed folder paths for {fixed_count}/{total_to_fix} artists")
            
            # Verify the fix
            remaining_without_paths = session.query(Artist).filter(
                (Artist.folder_path.is_(None)) | (Artist.folder_path == '')
            ).count()
            
            if remaining_without_paths == 0:
                logger.info("✅ Verification passed: All artists now have folder paths")
                return True
            else:
                logger.warning(f"⚠️  {remaining_without_paths} artists still without folder paths")
                return False
                
    except Exception as e:
        logger.error(f"❌ Migration 005 failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def rollback_migration():
    """
    Rollback migration (not applicable for this migration since we're only adding data)
    """
    logger.info("Migration 005 rollback: No rollback needed (only added missing data)")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migration 005: Fix missing artist folder paths")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_migration()
    else:
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            # Implementation for dry run would go here
            success = True
        else:
            success = migrate_artist_folder_paths()
    
    sys.exit(0 if success else 1)