#!/usr/bin/env python3
"""
Script to fix YouTube Video titles by extracting YouTube IDs and fetching actual titles
"""

import sys
import os
import re
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional

# Add the project root directory to the path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.database.connection import get_db
from src.database.models import Video, Artist
from src.services.settings_service import settings
from src.services.youtube_search_service import YouTubeSearchService
from src.utils.logger import get_logger

logger = get_logger('mvidarr.scripts.fix_youtube_titles')

class YouTubeVideoTitleFixer:
    """Fix YouTube Video titles by fetching actual titles from YouTube API"""
    
    def __init__(self):
        self.db = get_db()
        self.youtube_service = YouTubeSearchService()
        self.fixed_count = 0
        self.error_count = 0
        
    def extract_youtube_id_from_title(self, title: str) -> Optional[str]:
        """Extract YouTube ID from 'YouTube Video {id}' format"""
        if not title or not title.startswith('YouTube Video '):
            return None
            
        # Extract the part after 'YouTube Video '
        youtube_id = title.replace('YouTube Video ', '').strip()
        
        # Validate YouTube ID format (11 characters, alphanumeric and -_)
        if len(youtube_id) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', youtube_id):
            return youtube_id
        
        return None
    
    def get_youtube_video_details(self, youtube_id: str) -> Optional[Dict]:
        """Get video details from YouTube API"""
        if not self.youtube_service.api_key:
            logger.error("YouTube API key not configured")
            return None
            
        try:
            url = f"{self.youtube_service.base_url}/videos"
            params = {
                'part': 'snippet,contentDetails,statistics',
                'id': youtube_id,
                'key': self.youtube_service.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                logger.warning(f"No video found for YouTube ID: {youtube_id}")
                return None
                
            video = items[0]
            snippet = video.get('snippet', {})
            content_details = video.get('contentDetails', {})
            statistics = video.get('statistics', {})
            
            return {
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'channel_title': snippet.get('channelTitle'),
                'published_at': snippet.get('publishedAt'),
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                'duration': content_details.get('duration'),
                'view_count': statistics.get('viewCount'),
                'like_count': statistics.get('likeCount'),
                'tags': snippet.get('tags', [])
            }
            
        except requests.RequestException as e:
            logger.error(f"YouTube API request failed for ID {youtube_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get YouTube video details for ID {youtube_id}: {e}")
            return None
    
    def parse_youtube_duration(self, duration_str: str) -> Optional[int]:
        """Parse YouTube duration string to seconds"""
        if not duration_str:
            return None
        
        try:
            # YouTube returns duration in ISO 8601 format (PT4M13S)
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 3600 + minutes * 60 + seconds
        except:
            pass
        
        return None
    
    def get_videos_to_fix(self) -> List[Dict]:
        """Get all videos that start with 'YouTube Video'"""
        try:
            query = """
                SELECT v.id, v.title, v.artist_id, v.youtube_id, v.youtube_url, 
                       v.video_metadata, a.name as artist_name
                FROM videos v
                LEFT JOIN artists a ON v.artist_id = a.id
                WHERE v.title LIKE 'YouTube Video %'
                ORDER BY v.id
            """
            
            result = self.db.execute(query)
            videos = []
            
            for row in result:
                videos.append({
                    'id': row[0],
                    'title': row[1],
                    'artist_id': row[2],
                    'youtube_id': row[3],
                    'youtube_url': row[4],
                    'video_metadata': json.loads(row[5]) if row[5] else {},
                    'artist_name': row[6]
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Failed to get videos to fix: {e}")
            return []
    
    def update_video_details(self, video_id: int, youtube_details: Dict, youtube_id: str) -> bool:
        """Update video with YouTube details"""
        try:
            # Extract year from published_at
            year = None
            if youtube_details.get('published_at'):
                try:
                    year = int(youtube_details['published_at'][:4])
                except:
                    pass
            
            # Parse duration
            duration = None
            if youtube_details.get('duration'):
                duration = self.parse_youtube_duration(youtube_details['duration'])
            
            # Prepare updated metadata
            updated_metadata = {
                'youtube_data': {
                    'published_at': youtube_details.get('published_at'),
                    'channel_title': youtube_details.get('channel_title'),
                    'like_count': youtube_details.get('like_count'),
                    'tags': youtube_details.get('tags', []),
                    'updated_at': datetime.utcnow().isoformat(),
                    'title_fixed': True
                }
            }
            
            # Update the video
            update_query = """
                UPDATE videos 
                SET title = ?, 
                    youtube_id = ?, 
                    youtube_url = ?, 
                    description = ?, 
                    thumbnail_url = ?, 
                    year = ?, 
                    duration = ?, 
                    view_count = ?, 
                    like_count = ?, 
                    video_metadata = ?
                WHERE id = ?
            """
            
            params = [
                youtube_details.get('title'),
                youtube_id,
                f"https://www.youtube.com/watch?v={youtube_id}",
                youtube_details.get('description'),
                youtube_details.get('thumbnail_url'),
                year,
                duration,
                youtube_details.get('view_count'),
                youtube_details.get('like_count'),
                json.dumps(updated_metadata),
                video_id
            ]
            
            self.db.execute(update_query, params)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update video {video_id}: {e}")
            return False
    
    def fix_video_titles(self, dry_run: bool = False) -> Dict:
        """Fix all YouTube Video titles"""
        logger.info(f"Starting YouTube Video title fix (dry_run={dry_run})")
        
        videos_to_fix = self.get_videos_to_fix()
        logger.info(f"Found {len(videos_to_fix)} videos to fix")
        
        results = {
            'total_videos': len(videos_to_fix),
            'fixed_videos': 0,
            'errors': 0,
            'skipped': 0,
            'dry_run': dry_run,
            'video_updates': []
        }
        
        for video in videos_to_fix:
            try:
                logger.info(f"Processing video {video['id']}: {video['title']}")
                
                # Extract YouTube ID from title
                youtube_id = self.extract_youtube_id_from_title(video['title'])
                if not youtube_id:
                    logger.warning(f"Could not extract YouTube ID from title: {video['title']}")
                    results['skipped'] += 1
                    continue
                
                # Get YouTube video details
                youtube_details = self.get_youtube_video_details(youtube_id)
                if not youtube_details:
                    logger.error(f"Could not get YouTube details for ID: {youtube_id}")
                    results['errors'] += 1
                    continue
                
                # Prepare update info
                update_info = {
                    'video_id': video['id'],
                    'old_title': video['title'],
                    'new_title': youtube_details.get('title'),
                    'youtube_id': youtube_id,
                    'artist_name': video['artist_name']
                }
                
                if not dry_run:
                    # Update the video
                    if self.update_video_details(video['id'], youtube_details, youtube_id):
                        results['fixed_videos'] += 1
                        logger.info(f"Updated video {video['id']}: '{video['title']}' -> '{youtube_details.get('title')}'")
                    else:
                        results['errors'] += 1
                        logger.error(f"Failed to update video {video['id']}")
                else:
                    results['fixed_videos'] += 1
                    logger.info(f"[DRY RUN] Would update video {video['id']}: '{video['title']}' -> '{youtube_details.get('title')}'")
                
                results['video_updates'].append(update_info)
                
            except Exception as e:
                logger.error(f"Error processing video {video['id']}: {e}")
                results['errors'] += 1
        
        logger.info(f"YouTube Video title fix completed: {results['fixed_videos']} fixed, {results['errors']} errors, {results['skipped']} skipped")
        
        return results
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix YouTube Video titles')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual changes)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
    
    fixer = YouTubeVideoTitleFixer()
    
    try:
        results = fixer.fix_video_titles(dry_run=args.dry_run)
        
        print(f"\n=== YouTube Video Title Fix Results ===")
        print(f"Total videos found: {results['total_videos']}")
        print(f"Fixed videos: {results['fixed_videos']}")
        print(f"Errors: {results['errors']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Dry run: {results['dry_run']}")
        
        if results['video_updates']:
            print(f"\n=== Video Updates ===")
            for update in results['video_updates'][:10]:  # Show first 10
                print(f"Video {update['video_id']} ({update['artist_name']}): '{update['old_title']}' -> '{update['new_title']}'")
            
            if len(results['video_updates']) > 10:
                print(f"... and {len(results['video_updates']) - 10} more")
        
        return 0 if results['errors'] == 0 else 1
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        return 1
    finally:
        fixer.close()

if __name__ == '__main__':
    sys.exit(main())