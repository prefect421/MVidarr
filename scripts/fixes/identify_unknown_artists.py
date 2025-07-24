#!/usr/bin/env python3
"""
Identify and fix Unknown Artist videos using song title matching
"""

import sys
import os
import pymysql
from datetime import datetime

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.config.config import Config
from src.database.connection import DatabaseManager
from src.database.models import Artist, Video
from src.services.artist_identification_service import artist_identification_service

def show_identification_preview(limit=10):
    """Show a preview of what videos can be identified"""
    print("Artist Identification Preview")
    print("=" * 60)
    
    config = Config()
    db_manager = DatabaseManager(config)
    
    try:
        with db_manager.get_session() as session:
            # Get identification summary
            summary = artist_identification_service.get_identification_summary(session, limit)
            
            print(f"Total videos assigned to Unknown Artist: {summary['total_unknown_videos']:,}")
            print(f"Sampled videos: {summary['sampled_videos']}")
            print(f"Identifiable videos: {len(summary['identifiable_videos'])}")
            print(f"Identification rate: {summary['identification_rate']:.1%}")
            print()
            
            if summary['identifiable_videos']:
                print("Top identifiable videos:")
                print(f"{'ID':<5} {'Title':<40} {'Identified Artist':<25} {'Confidence':<10}")
                print("-" * 90)
                
                for item in summary['identifiable_videos'][:10]:
                    video_id = item['video_id']
                    title = item['title'][:37] + "..." if len(item['title']) > 40 else item['title']
                    artist = item['best_candidate']['artist_name']
                    confidence = f"{item['best_candidate']['confidence']:.2f}"
                    
                    print(f"{video_id:<5} {title:<40} {artist:<25} {confidence:<10}")
                    
                print()
                print("Use --execute to apply these identifications")
            else:
                print("No videos could be identified with sufficient confidence")
                
    except Exception as e:
        print(f"Error: {e}")

def apply_identifications(dry_run=True, confidence_threshold=0.7, limit=50):
    """Apply artist identifications to Unknown Artist videos"""
    config = Config()
    db_manager = DatabaseManager(config)
    
    fixed_count = 0
    created_artists = 0
    
    try:
        with db_manager.get_session() as session:
            # Get Unknown Artist
            unknown_artist = session.query(Artist).filter(
                Artist.name == 'Unknown Artist'
            ).first()
            
            if not unknown_artist:
                print("No Unknown Artist found in database")
                return
                
            print(f"Processing videos assigned to Unknown Artist...")
            print(f"Confidence threshold: {confidence_threshold}")
            print(f"Dry run: {dry_run}")
            print("=" * 60)
            
            # Get videos to process
            videos_to_process = session.query(Video).filter(
                Video.artist_id == unknown_artist.id
            ).limit(limit).all()
            
            for video in videos_to_process:
                # Get identification candidates
                candidates = artist_identification_service.identify_artist_from_title(video.title)
                
                if not candidates:
                    continue
                    
                best_candidate = candidates[0]
                
                # Only process if confidence is above threshold
                if best_candidate['confidence'] < confidence_threshold:
                    continue
                    
                artist_name = best_candidate['artist_name']
                
                print(f"Video ID {video.id}: '{video.title}'")
                print(f"  Current: Unknown Artist")
                print(f"  Identified: {artist_name} (confidence: {best_candidate['confidence']:.2f})")
                print(f"  Reason: {best_candidate['match_reason']}")
                
                if not dry_run:
                    # Find or create the artist
                    target_artist = session.query(Artist).filter(
                        Artist.name.ilike(artist_name)
                    ).first()
                    
                    if not target_artist:
                        # Create new artist
                        target_artist = Artist(
                            name=artist_name,
                            monitored=True,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        session.add(target_artist)
                        session.flush()  # Get the ID
                        created_artists += 1
                        print(f"  Created new artist: {artist_name}")
                    
                    # Update video
                    video.artist_id = target_artist.id
                    video.updated_at = datetime.utcnow()
                    
                    # Add IMVDb metadata if available
                    if 'metadata' in best_candidate and best_candidate['metadata']:
                        metadata = best_candidate['metadata']
                        if 'imvdb_id' in metadata and metadata['imvdb_id']:
                            video.imvdb_id = str(metadata['imvdb_id'])
                        if 'thumbnail_url' in metadata and metadata['thumbnail_url']:
                            video.thumbnail_url = metadata['thumbnail_url']
                    
                    fixed_count += 1
                
                print()
                
                # Show progress
                if fixed_count % 10 == 0 and fixed_count > 0:
                    print(f"... processed {fixed_count} videos")
                
            if not dry_run:
                print(f"Committing changes to database...")
                # Note: session.commit() is handled by the context manager
                
            print("=" * 60)
            print(f"Summary:")
            print(f"  Videos processed: {len(videos_to_process)}")
            print(f"  Artists identified: {fixed_count}")
            print(f"  New artists created: {created_artists}")
            
            if dry_run:
                print(f"  Dry run completed - no changes made")
            else:
                print(f"  Changes committed to database")
                
    except Exception as e:
        print(f"Error during identification: {e}")
        raise

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Identify artists for Unknown Artist videos")
    parser.add_argument("--preview", action="store_true", default=True,
                        help="Show preview of identifiable videos (default)")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="Execute the identifications")
    parser.add_argument("--confidence", type=float, default=0.7,
                        help="Minimum confidence threshold (default: 0.7)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Maximum number of videos to process (default: 50)")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Run in dry-run mode (default: True)")
    
    args = parser.parse_args()
    
    # If --execute is specified, disable preview and dry-run
    if args.execute:
        args.preview = False
        args.dry_run = False
        
        print("WARNING: This will make actual changes to the database!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Aborted.")
            return
    
    if args.preview:
        show_identification_preview(args.limit)
    else:
        apply_identifications(
            dry_run=args.dry_run,
            confidence_threshold=args.confidence,
            limit=args.limit
        )

if __name__ == "__main__":
    main()