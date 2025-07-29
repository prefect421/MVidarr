#!/usr/bin/env python3
"""
Script to fix missing artist folder paths

This script addresses Issue #16 by ensuring all artists have folder_path values.
Can be run manually or integrated into the application startup.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def fix_artist_folder_paths():
    """Fix missing folder paths for all artists"""
    try:
        # Import here to ensure proper initialization
        from src.database.connection import get_db
        from src.database.models import Artist
        from src.utils.filename_cleanup import FilenameCleanup
        
        print("🔧 Fixing missing artist folder paths...")
        
        with get_db() as session:
            # Find artists without folder paths
            artists_needing_fix = session.query(Artist).filter(
                (Artist.folder_path.is_(None)) | (Artist.folder_path == '')
            ).all()
            
            if not artists_needing_fix:
                print("✅ All artists already have folder paths - no fixes needed!")
                return True
            
            print(f"📋 Found {len(artists_needing_fix)} artists without folder paths:")
            
            fixed_count = 0
            for artist in artists_needing_fix:
                try:
                    # Generate folder path
                    folder_path = FilenameCleanup.sanitize_folder_name(artist.name)
                    artist.folder_path = folder_path
                    
                    print(f"  ✅ Fixed: '{artist.name}' -> '{folder_path}'")
                    fixed_count += 1
                    
                except Exception as e:
                    print(f"  ❌ Failed to fix '{artist.name}': {e}")
                    continue
            
            # Commit all changes
            session.commit()
            
            print(f"\n🎉 Successfully fixed folder paths for {fixed_count} artists!")
            print("📁 Artists will now display proper folder paths in the UI")
            
            return True
            
    except Exception as e:
        print(f"❌ Error fixing folder paths: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_artist_folder_paths()
    sys.exit(0 if success else 1)