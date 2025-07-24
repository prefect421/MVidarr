#!/usr/bin/env python3
"""
Extract YouTube IDs from videos with 'YouTube Video' titles for manual fixing
"""

import requests
import json
import re
import sys
from typing import List, Dict, Optional

def extract_youtube_id_from_title(title: str) -> Optional[str]:
    """Extract YouTube ID from 'YouTube Video {id}' format"""
    if not title or not title.startswith('YouTube Video '):
        return None
        
    # Extract the part after 'YouTube Video '
    youtube_id = title.replace('YouTube Video ', '').strip()
    
    # Validate YouTube ID format (11 characters, alphanumeric and -_)
    if len(youtube_id) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', youtube_id):
        return youtube_id
    
    return None

def get_videos_to_fix(base_url: str = "http://localhost:5000") -> List[Dict]:
    """Get all videos that start with 'YouTube Video' using the API"""
    try:
        # Search for videos starting with "YouTube Video"
        url = f"{base_url}/api/videos/search"
        params = {
            'q': 'YouTube Video',
            'page': 1,
            'per_page': 500  # Get a large batch
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        videos = data.get('videos', [])
        
        # Filter to only videos that start with "YouTube Video"
        youtube_videos = [v for v in videos if v.get('title', '').startswith('YouTube Video ')]
        
        return youtube_videos
        
    except Exception as e:
        print(f"Failed to get videos to fix: {e}")
        return []

def main():
    print("Extracting YouTube IDs from videos with 'YouTube Video' titles...")
    
    videos = get_videos_to_fix()
    print(f"Found {len(videos)} videos to fix")
    
    if not videos:
        print("No videos found that need fixing.")
        return
    
    # Extract YouTube IDs and prepare data
    video_data = []
    for video in videos:
        youtube_id = extract_youtube_id_from_title(video['title'])
        if youtube_id:
            video_data.append({
                'video_id': video['id'],
                'title': video['title'],
                'youtube_id': youtube_id,
                'youtube_url': f"https://www.youtube.com/watch?v={youtube_id}",
                'artist_name': video.get('artist_name', 'Unknown'),
                'artist_id': video.get('artist_id')
            })
    
    print(f"Successfully extracted {len(video_data)} YouTube IDs")
    
    # Save to file
    output_file = 'youtube_videos_to_fix.json'
    with open(output_file, 'w') as f:
        json.dump(video_data, f, indent=2)
    
    print(f"Saved video data to {output_file}")
    
    # Print sample of what we found
    print("\nSample of videos that need fixing:")
    for video in video_data[:10]:
        print(f"  Video {video['video_id']}: {video['title']} -> https://www.youtube.com/watch?v={video['youtube_id']}")
    
    if len(video_data) > 10:
        print(f"  ... and {len(video_data) - 10} more videos")
    
    print(f"\nTo manually fix these videos, visit each YouTube URL and update the video title in MVidarr")
    print(f"Or configure a YouTube API key and run the automated fix script")

if __name__ == '__main__':
    main()