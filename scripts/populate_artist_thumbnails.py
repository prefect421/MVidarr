#!/usr/bin/env python3
"""
Script to populate artist thumbnails from IMVDb
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import get_db, DatabaseManager
from src.database.models import Artist
from src.services.imvdb_service import imvdb_service
from src.services.thumbnail_service import thumbnail_service
from src.config.config import Config
from src.utils.logger import get_logger

logger = get_logger('mvidarr.populate_thumbnails')

# Initialize database
config = Config()
db_manager = DatabaseManager(config)

def populate_artist_thumbnails(limit=None):
    """
    Populate artist thumbnails from IMVDb
    
    Args:
        limit: Limit number of artists to process (None for all)
    """
    try:
        # Initialize database connection
        db_manager.create_database_if_not_exists()
        
        with db_manager.get_session() as session:
            # Get artists without thumbnails
            query = session.query(Artist).filter(Artist.thumbnail_url.is_(None))
            
            if limit:
                query = query.limit(limit)
            
            artists = query.all()
            
            if not artists:
                logger.info("No artists found without thumbnails")
                return
            
            logger.info(f"Found {len(artists)} artists without thumbnails")
            
            updated_count = 0
            
            for artist in artists:
                try:
                    logger.info(f"Processing artist: {artist.name}")
                    
                    # Search for artist on IMVDb (get all results for better matching)
                    artist_results = imvdb_service.search_artist(artist.name, return_multiple=True)
                    
                    thumbnail_url = None
                    best_match = None
                    
                    if artist_results:
                        # Try to find the best match by name similarity
                        for artist_data in artist_results:
                            artist_imvdb_name = artist_data.get('name', '').lower()
                            our_artist_name = artist.name.lower()
                            
                            # Look for exact match first
                            if artist_imvdb_name == our_artist_name:
                                best_match = artist_data
                                break
                            # Look for close matches (contains)
                            elif our_artist_name in artist_imvdb_name or artist_imvdb_name in our_artist_name:
                                if not best_match:  # Keep first close match
                                    best_match = artist_data
                        
                        # If no good match found, use first result
                        if not best_match:
                            best_match = artist_results[0]
                        
                        # Extract thumbnail URL from best match
                        if best_match and 'image' in best_match:
                            if isinstance(best_match['image'], dict):
                                # Try different image sizes
                                thumbnail_url = (best_match['image'].get('l') or 
                                               best_match['image'].get('m') or 
                                               best_match['image'].get('s'))
                            elif isinstance(best_match['image'], str):
                                thumbnail_url = best_match['image']
                        
                        if thumbnail_url:
                            # Download and save thumbnail
                            thumbnail_path = thumbnail_service.download_artist_thumbnail(
                                artist.name, 
                                thumbnail_url
                            )
                            
                            if thumbnail_path:
                                # Update artist with thumbnail info
                                artist.thumbnail_url = thumbnail_url
                                artist.thumbnail_path = thumbnail_path
                                artist.imvdb_id = best_match.get('id')
                                
                                session.add(artist)
                                updated_count += 1
                                
                                logger.info(f"Updated thumbnail for {artist.name} (matched with: {best_match.get('name')})")
                            else:
                                logger.warning(f"Failed to download thumbnail for {artist.name}")
                        else:
                            logger.info(f"No thumbnail available for matched artist: {best_match.get('name') if best_match else 'None'}")
                    else:
                        logger.info(f"No artist results found on IMVDb for: {artist.name}")
                        
                except Exception as e:
                    logger.error(f"Failed to process artist {artist.name}: {e}")
                    continue
            
            session.commit()
            logger.info(f"Updated thumbnails for {updated_count} artists")
            
    except Exception as e:
        logger.error(f"Failed to populate artist thumbnails: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate artist thumbnails from IMVDb')
    parser.add_argument('--limit', type=int, help='Limit number of artists to process')
    
    args = parser.parse_args()
    
    print("Populating artist thumbnails...")
    populate_artist_thumbnails(args.limit)
    print("Done!")