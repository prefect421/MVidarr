#!/usr/bin/env python3
"""
Check artists without folder paths
"""
import sys
sys.path.append('/home/mike/mvidarr')

from src.database.connection import get_db
from src.database.models import Artist
from src.utils.filename_cleanup import FilenameCleanup

def check_and_fix_folder_paths():
    """Check for artists without folder paths and fix them"""
    try:
        with get_db() as session:
            # Find artists without folder_path
            artists = session.query(Artist).all()
            
            artists_without_path = []
            artists_with_path = []
            
            for artist in artists:
                if not artist.folder_path or artist.folder_path.strip() == '':
                    artists_without_path.append(artist)
                else:
                    artists_with_path.append(artist)
            
            print(f'Artists without folder_path: {len(artists_without_path)}')
            print(f'Artists with folder_path: {len(artists_with_path)}')
            print(f'Total artists: {len(artists)}')
            
            if artists_without_path:
                print('\nArtists without folder paths:')
                for artist in artists_without_path[:10]:  # Show first 10
                    print(f'  - ID: {artist.id}, Name: "{artist.name}"')
                
                # Fix the folder paths
                print(f'\nFixing folder paths for {len(artists_without_path)} artists...')
                
                for artist in artists_without_path:
                    # Generate folder path using the same logic as other places
                    folder_path = FilenameCleanup.sanitize_folder_name(artist.name)
                    artist.folder_path = folder_path
                    print(f'  Fixed: "{artist.name}" -> "{folder_path}"')
                
                session.commit()
                print(f'✅ Fixed folder paths for {len(artists_without_path)} artists')
            else:
                print('✅ All artists already have folder paths')
                
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_and_fix_folder_paths()