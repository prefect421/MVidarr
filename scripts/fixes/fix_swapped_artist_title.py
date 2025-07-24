#!/usr/bin/env python3
"""
Fix Swapped Artist/Title Fields in Videos

This script identifies and fixes videos where the artist and title fields appear to be swapped.
It looks for patterns where:
- Title field contains generic values like "video"
- Artist field contains song titles with typical markers like "Official Music Video", "feat", etc.

The script will:
1. Identify problematic videos
2. Extract actual song titles from the artist field
3. Find or create the correct artist entries
4. Update the video records with corrected data
"""

import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.database.connection import DatabaseManager
from src.database.models import Artist, Video, VideoStatus
from src.config.config import Config

class ArtistTitleFixer:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.config = Config()
        self.db_manager = DatabaseManager(self.config)
        self.session = None
        self.fixed_count = 0
        self.error_count = 0
        
    def __enter__(self):
        self.session_context = self.db_manager.get_session()
        self.session = self.session_context.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session_context:
            self.session_context.__exit__(exc_type, exc_val, exc_tb)
        
    def identify_problematic_videos(self) -> List[Dict]:
        """Identify videos with swapped artist/title fields"""
        print("Identifying problematic videos...")
        
        # Use SQLAlchemy ORM query for better compatibility
        query = self.session.query(
            Video.id,
            Video.title,
            Artist.name.label('artist_name'),
            Video.artist_id
        ).join(Artist).filter(
            (Video.title == 'video') |
            (Video.title.contains('video')) |
            (Artist.name.like('%Official Music Video%')) |
            (Artist.name.like('%feat%')) |
            (Artist.name.like('%remix%')) |
            (Artist.name.like('%cover%')) |
            (Artist.name.like('%live%')) |
            (Artist.name.like('%acoustic%'))
        ).order_by(Video.id).limit(10)  # Limit to first 10 for testing
        
        problematic_videos = []
        
        for row in query:
            video_data = {
                'id': row.id,
                'title': row.title,
                'artist_name': row.artist_name,
                'artist_id': row.artist_id
            }
            problematic_videos.append(video_data)
            
        print(f"Found {len(problematic_videos)} problematic videos")
        return problematic_videos
    
    def extract_song_title_and_artist(self, artist_name: str) -> Tuple[str, str]:
        """Extract the actual song title and artist name from the swapped field"""
        original = artist_name
        
        # Remove common video-related suffixes
        suffixes_to_remove = [
            r'\s*\(?\s*Official\s*Music\s*Video\s*\)?',
            r'\s*\(?\s*Official\s*Video\s*\)?',
            r'\s*\(?\s*Music\s*Video\s*\)?',
            r'\s*\(?\s*Official\s*\)?',
            r'\s*-?\s*Official\s*Music\s*Video',
            r'\s*-?\s*Official\s*Video',
            r'\s*-?\s*Music\s*Video',
            r'\s*video\s*$'
        ]
        
        cleaned_title = original
        for suffix in suffixes_to_remove:
            cleaned_title = re.sub(suffix, '', cleaned_title, flags=re.IGNORECASE)
        
        # Look for artist separators
        artist_patterns = [
            r'^(.+?)\s*-\s*(.+)$',  # Artist - Song
            r'^(.+?)\s*:\s*(.+)$',  # Artist : Song
            r'^(.+?)\s*\|\s*(.+)$', # Artist | Song
            r'^(.+?)\s*by\s+(.+)$', # Song by Artist
        ]
        
        for pattern in artist_patterns:
            match = re.match(pattern, cleaned_title.strip())
            if match:
                part1, part2 = match.groups()
                
                # Check if "by" pattern (song by artist)
                if 'by' in pattern:
                    return part1.strip(), part2.strip()  # song, artist
                else:
                    return part2.strip(), part1.strip()  # song, artist
        
        # Handle featuring/feat patterns
        feat_patterns = [
            r'^(.+?)\s*(?:feat\.?|featuring|ft\.?)\s*(.+)$',
        ]
        
        for pattern in feat_patterns:
            match = re.match(pattern, cleaned_title.strip(), flags=re.IGNORECASE)
            if match:
                main_part, feat_part = match.groups()
                # Try to extract artist from main part
                if ' - ' in main_part:
                    artist, song = main_part.split(' - ', 1)
                    return f"{song.strip()} (feat. {feat_part.strip()})", artist.strip()
                else:
                    # Assume the whole thing is the song title
                    return cleaned_title.strip(), "Unknown Artist"
        
        # If no clear pattern, return the cleaned title as song and try to guess artist
        return cleaned_title.strip(), "Unknown Artist"
    
    def find_or_create_artist(self, artist_name: str) -> Artist:
        """Find existing artist or create new one"""
        if artist_name == "Unknown Artist":
            artist_name = "Various Artists"
            
        # Look for existing artist (case insensitive)
        existing_artist = self.session.query(Artist).filter(
            Artist.name.ilike(artist_name)
        ).first()
        
        if existing_artist:
            return existing_artist
        
        # Create new artist
        new_artist = Artist(
            name=artist_name,
            monitored=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        if not self.dry_run:
            self.session.add(new_artist)
            self.session.flush()  # Get the ID
            
        return new_artist
    
    def fix_video(self, video_data: Dict) -> bool:
        """Fix a single video's artist/title fields"""
        try:
            video_id = video_data['id']
            current_title = video_data['title']
            current_artist_name = video_data['artist_name']
            
            # Extract the actual song title and artist
            song_title, artist_name = self.extract_song_title_and_artist(current_artist_name)
            
            # Skip if no meaningful extraction
            if not song_title or len(song_title.strip()) < 2:
                return False
            
            # Find or create the correct artist
            correct_artist = self.find_or_create_artist(artist_name)
            
            print(f"Video ID {video_id}:")
            print(f"  Current: Artist='{current_artist_name}' | Title='{current_title}'")
            print(f"  Fixed:   Artist='{correct_artist.name}' | Title='{song_title}'")
            
            if not self.dry_run:
                # Update the video record
                video = self.session.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.title = song_title
                    video.artist_id = correct_artist.id
                    video.updated_at = datetime.utcnow()
                    
            self.fixed_count += 1
            return True
            
        except Exception as e:
            print(f"Error fixing video {video_data['id']}: {str(e)}")
            self.error_count += 1
            return False
    
    def run_fixes(self):
        """Run the complete fix process"""
        print(f"Starting fix process (dry_run={self.dry_run})")
        print("=" * 50)
        
        try:
            # Get problematic videos
            problematic_videos = self.identify_problematic_videos()
            
            if not problematic_videos:
                print("No problematic videos found.")
                return
            
            # Process each video
            for video_data in problematic_videos:
                self.fix_video(video_data)
                
            # Commit changes if not dry run
            if not self.dry_run:
                self.session.commit()
                print(f"\nChanges committed to database.")
            else:
                print(f"\nDry run completed - no changes made to database.")
                
        except Exception as e:
            print(f"Error during fix process: {str(e)}")
            if not self.dry_run:
                self.session.rollback()
        finally:
            pass  # Session cleanup handled by context manager
            
        print("=" * 50)
        print(f"Fix Summary:")
        print(f"  Fixed videos: {self.fixed_count}")
        print(f"  Errors: {self.error_count}")
        print(f"  Total processed: {self.fixed_count + self.error_count}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix swapped artist/title fields in videos")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Run in dry-run mode (default: True)")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="Actually execute the fixes (overrides dry-run)")
    
    args = parser.parse_args()
    
    # If --execute is specified, disable dry-run
    dry_run = args.dry_run and not args.execute
    
    if not dry_run:
        print("WARNING: This will make actual changes to the database!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Aborted.")
            return
    
    with ArtistTitleFixer(dry_run=dry_run) as fixer:
        fixer.run_fixes()

if __name__ == "__main__":
    main()