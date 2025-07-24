#!/usr/bin/env python3
"""
Script to fix YouTube Video titles using the MVidarr API
"""

import requests
import json
import re
import sys
from typing import List, Dict, Optional
import time

class YouTubeVideoTitleFixer:
    """Fix YouTube Video titles using the MVidarr API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.fixed_count = 0
        self.error_count = 0
        
    def get_youtube_api_key(self) -> Optional[str]:
        """Get YouTube API key from settings"""
        try:
            response = self.session.get(f"{self.base_url}/api/settings/")
            response.raise_for_status()
            settings_data = response.json()
            settings = settings_data.get('settings', {})
            youtube_api_key = settings.get('youtube_api_key', {}).get('value')
            return youtube_api_key
        except Exception as e:
            print(f"Error getting YouTube API key: {e}")
            return None
    
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
    
    def get_youtube_video_details(self, youtube_id: str, api_key: str) -> Optional[Dict]:
        """Get video details from YouTube API"""
        try:
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'snippet,contentDetails,statistics',
                'id': youtube_id,
                'key': api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                print(f"No video found for YouTube ID: {youtube_id}")
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
            print(f"YouTube API request failed for ID {youtube_id}: {e}")
            return None
        except Exception as e:
            print(f"Failed to get YouTube video details for ID {youtube_id}: {e}")
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
        """Get all videos that start with 'YouTube Video' using the API"""
        try:
            # Search for videos starting with "YouTube Video"
            url = f"{self.base_url}/api/videos/search"
            params = {
                'q': 'YouTube Video',
                'page': 1,
                'per_page': 500  # Get a large batch
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get('videos', [])
            
            # Filter to only videos that start with "YouTube Video"
            youtube_videos = [v for v in videos if v.get('title', '').startswith('YouTube Video ')]
            
            return youtube_videos
            
        except Exception as e:
            print(f"Failed to get videos to fix: {e}")
            return []
    
    def update_video_details(self, video_id: int, youtube_details: Dict, youtube_id: str) -> bool:
        """Update video with YouTube details using the API"""
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
            
            # Prepare update data
            update_data = {
                'title': youtube_details.get('title'),
                'youtube_id': youtube_id,
                'youtube_url': f"https://www.youtube.com/watch?v={youtube_id}",
                'description': youtube_details.get('description'),
                'thumbnail_url': youtube_details.get('thumbnail_url'),
                'year': year,
                'duration': duration,
                'view_count': int(youtube_details.get('view_count', 0)) if youtube_details.get('view_count') else None,
                'like_count': int(youtube_details.get('like_count', 0)) if youtube_details.get('like_count') else None,
                'published_at': youtube_details.get('published_at'),
                'channel_title': youtube_details.get('channel_title'),
                'tags': youtube_details.get('tags', [])
            }
            
            # Update the video using the API
            url = f"{self.base_url}/api/videos/{video_id}"
            response = self.session.put(url, json=update_data)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"Failed to update video {video_id}: {e}")
            return False
    
    def fix_video_titles(self, dry_run: bool = False) -> Dict:
        """Fix all YouTube Video titles"""
        print(f"Starting YouTube Video title fix (dry_run={dry_run})")
        
        # Get YouTube API key
        api_key = self.get_youtube_api_key()
        if not api_key:
            print("ERROR: YouTube API key not configured")
            return {'error': 'YouTube API key not configured'}
        
        # Get videos to fix
        videos_to_fix = self.get_videos_to_fix()
        print(f"Found {len(videos_to_fix)} videos to fix")
        
        results = {
            'total_videos': len(videos_to_fix),
            'fixed_videos': 0,
            'errors': 0,
            'skipped': 0,
            'dry_run': dry_run,
            'video_updates': []
        }
        
        for i, video in enumerate(videos_to_fix, 1):
            try:
                print(f"Processing video {i}/{len(videos_to_fix)}: {video['id']} - {video['title']}")
                
                # Extract YouTube ID from title
                youtube_id = self.extract_youtube_id_from_title(video['title'])
                if not youtube_id:
                    print(f"Could not extract YouTube ID from title: {video['title']}")
                    results['skipped'] += 1
                    continue
                
                # Get YouTube video details
                youtube_details = self.get_youtube_video_details(youtube_id, api_key)
                if not youtube_details:
                    print(f"Could not get YouTube details for ID: {youtube_id}")
                    results['errors'] += 1
                    continue
                
                # Prepare update info
                update_info = {
                    'video_id': video['id'],
                    'old_title': video['title'],
                    'new_title': youtube_details.get('title'),
                    'youtube_id': youtube_id,
                    'artist_name': video.get('artist_name', 'Unknown')
                }
                
                if not dry_run:
                    # Update the video
                    if self.update_video_details(video['id'], youtube_details, youtube_id):
                        results['fixed_videos'] += 1
                        print(f"✓ Updated video {video['id']}: '{video['title']}' -> '{youtube_details.get('title')}'")
                    else:
                        results['errors'] += 1
                        print(f"✗ Failed to update video {video['id']}")
                else:
                    results['fixed_videos'] += 1
                    print(f"[DRY RUN] Would update video {video['id']}: '{video['title']}' -> '{youtube_details.get('title')}'")
                
                results['video_updates'].append(update_info)
                
                # Add a small delay to avoid hitting rate limits
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing video {video['id']}: {e}")
                results['errors'] += 1
        
        print(f"YouTube Video title fix completed: {results['fixed_videos']} fixed, {results['errors']} errors, {results['skipped']} skipped")
        
        return results

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix YouTube Video titles')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual changes)')
    parser.add_argument('--url', default='http://localhost:5000', help='MVidarr API base URL')
    
    args = parser.parse_args()
    
    fixer = YouTubeVideoTitleFixer(args.url)
    
    try:
        results = fixer.fix_video_titles(dry_run=args.dry_run)
        
        if 'error' in results:
            print(f"ERROR: {results['error']}")
            return 1
        
        print(f"\n=== YouTube Video Title Fix Results ===")
        print(f"Total videos found: {results['total_videos']}")
        print(f"Fixed videos: {results['fixed_videos']}")
        print(f"Errors: {results['errors']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Dry run: {results['dry_run']}")
        
        if results['video_updates']:
            print(f"\n=== Sample Video Updates ===")
            for update in results['video_updates'][:5]:  # Show first 5
                print(f"Video {update['video_id']} ({update['artist_name']}): '{update['old_title']}' -> '{update['new_title']}'")
            
            if len(results['video_updates']) > 5:
                print(f"... and {len(results['video_updates']) - 5} more")
        
        return 0 if results['errors'] == 0 else 1
        
    except Exception as e:
        print(f"Script failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())