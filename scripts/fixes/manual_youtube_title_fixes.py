#!/usr/bin/env python3
"""
Manual fixes for YouTube Video titles with known correct titles
"""

import requests
import json
import sys

# Manual title mappings for some common videos
KNOWN_TITLES = {
    'q7yCLn-O-Y0': 'Fun.: Carry On [OFFICIAL VIDEO]',
    'dO6WmM7w93I': 'Fun.: Some Nights [OFFICIAL VIDEO]',
    'qQkBeOisNM0': 'Fun.: We Are Young ft. Janelle Monáe [OFFICIAL VIDEO]',
    '_-xLsGOekk8': 'Meat Puppets - Backwater',
    '-0kcet4aPpQ': 'Pink Floyd - Wish You Were Here (Official Music Video)',
    '-9yYJ6ZAYns': 'Ozzy Osbourne - "Crazy Train" (Official Video)',
    '-p8GXZcdrIk': 'Lynyrd Skynyrd - Free Bird (Official Music Video)',
    '-s-K2_sFBos': 'Elvis Costello & The Imposters - "Heart Shaped Bruise" (Official Video)',
    '0J1Ux73NrGA': 'Otis Gibbs - "Thanksgiving" (Official Video)',
    '2AsLRPzqdpc': 'Ozzy Osbourne - "Shot In The Dark" (Official Video)',
    '2uYs0gJD-LE': 'M.I.A. - "Paper Planes" (Official Video)',
    '3aqi23-BBLA': 'Authority Zero - "Revolution" (Official Video)',
    '4EkXnXe4Rfk': 'Seven Mary Three - "Cumbersome" (Official Video)',
    '4l4gdhPqh3E': 'Colter Wall - "Sleeping on the Blacktop" (Official Video)',
    '4rTbInqWC54': 'Mike Ness - "Cheating at Solitaire" (Official Video)',
    '4SHIEKeubCM': 'Agent Orange - "Bloodstains" (Official Video)',
    '4XeWngFZaa8': 'Pink Floyd - "Time" (Official Video)',
    '5iaHS-skmM4': 'Wax - "Rosana" (Official Video)',
    '5x5fgblnwJg': 'Dwarves - "Must Die" (Official Video)',
    '632QWw2Pz6g': 'Stiff Little Fingers - "Alternative Ulster" (Official Video)',
    '6ChlNsxFHjE': 'Otis Gibbs - "Grandpa Was A Carpenter" (Official Video)',
    '7-f18YAeZkU': 'Laura Jane Grace & The Devouring Mothers - "The Apology Song" (Official Video)',
    '74xGXdgnk8M': 'Generation X - "Dancing With Myself" (Official Video)',
    '78N-JOrX6ys': 'Shovels & Rope - "Swimmin\' Time" (Official Video)',
    '7BVCxuY14fE': 'Hayes Carll - "Chances Are" (Official Video)',
    '7tUzhodl_rw': 'Lucinda Williams - "Car Wheels on a Gravel Road" (Official Video)',
    '7V-OX0lbX1w': 'Justin Townes Earle - "Harlem River Blues" (Official Video)',
    '8laLLKw98WM': 'Laura Jane Grace - "The Swimming Pool Song" (Official Video)',
    '8qQQGcRGWcY': 'Buck Owens - "Act Naturally" (Official Video)',
    '9hC9Mg_YzGw': 'Laura Jane Grace - "Anna Is A Stool Pigeon" (Official Video)',
    '9LMcZRL1Pfs': 'Laura Jane Grace - "Bought to Rot" (Official Video)',
    '9Qtyw84F5DM': 'Serj Tankian - "Empty Walls" (Official Video)',
    '9V-vcXOpG9g': 'Prince & The New Power Generation - "Cream" (Official Video)',
    '9VdrtFnt1R0': 'Laura Jane Grace - "Stabitha Christie" (Official Video)'
}

def update_video_title(video_id: int, new_title: str, base_url: str = "http://localhost:5000") -> bool:
    """Update a video's title using the API"""
    try:
        url = f"{base_url}/api/videos/{video_id}"
        update_data = {
            'title': new_title
        }
        
        response = requests.put(url, json=update_data)
        response.raise_for_status()
        
        return True
        
    except Exception as e:
        print(f"Failed to update video {video_id}: {e}")
        return False

def load_video_data(filename: str = "youtube_videos_to_fix.json") -> list:
    """Load video data from the extraction file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File {filename} not found. Run extract_youtube_ids.py first.")
        return []
    except Exception as e:
        print(f"Error loading video data: {e}")
        return []

def main():
    print("Manual YouTube Video Title Fixes")
    print("="*50)
    
    # Load video data
    video_data = load_video_data()
    if not video_data:
        return 1
    
    # Find videos we can fix
    fixable_videos = []
    for video in video_data:
        youtube_id = video['youtube_id']
        if youtube_id in KNOWN_TITLES:
            fixable_videos.append({
                'video_id': video['video_id'],
                'old_title': video['title'],
                'new_title': KNOWN_TITLES[youtube_id],
                'youtube_id': youtube_id,
                'artist_name': video['artist_name']
            })
    
    print(f"Found {len(fixable_videos)} videos with known titles to fix")
    
    if not fixable_videos:
        print("No videos found with known titles. Add more mappings to KNOWN_TITLES.")
        return 0
    
    # Show what we're going to fix
    print("\nVideos to fix:")
    for video in fixable_videos:
        print(f"  Video {video['video_id']} ({video['artist_name']}): '{video['old_title']}' -> '{video['new_title']}'")
    
    # Ask for confirmation
    response = input(f"\nFix {len(fixable_videos)} videos? (y/n): ").lower()
    if response != 'y':
        print("Cancelled.")
        return 0
    
    # Fix the videos
    success_count = 0
    error_count = 0
    
    for video in fixable_videos:
        print(f"Fixing video {video['video_id']}...")
        if update_video_title(video['video_id'], video['new_title']):
            success_count += 1
            print(f"  ✓ Updated: '{video['old_title']}' -> '{video['new_title']}'")
        else:
            error_count += 1
            print(f"  ✗ Failed to update video {video['video_id']}")
    
    print(f"\nResults: {success_count} fixed, {error_count} errors")
    
    return 0 if error_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())