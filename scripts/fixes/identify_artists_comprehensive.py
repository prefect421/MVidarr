#!/usr/bin/env python3
"""
Comprehensive artist identification for Unknown Artist videos
"""

import sys
import os
import pymysql
import requests
import json
from datetime import datetime

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.config.config import Config

def identify_artist_comprehensive(song_title, use_api=False):
    """Comprehensive artist identification"""
    candidates = []
    
    # Method 1: Title parsing
    parsed_artist = parse_title_for_artist(song_title)
    if parsed_artist:
        candidates.append({
            'artist': parsed_artist,
            'confidence': 0.8,
            'source': 'title_parsing'
        })
    
    # Method 2: Database lookup for similar titles
    db_artist = lookup_similar_titles(song_title)
    if db_artist:
        candidates.append({
            'artist': db_artist,
            'confidence': 0.9,
            'source': 'database_match'
        })
    
    # Method 3: Simple web search (if enabled)
    if use_api:
        web_artist = search_web_for_artist(song_title)
        if web_artist:
            candidates.append({
                'artist': web_artist,
                'confidence': 0.7,
                'source': 'web_search'
            })
    
    # Return best candidate
    if candidates:
        best = max(candidates, key=lambda x: x['confidence'])
        return best
    
    return None

def parse_title_for_artist(title):
    """Parse title for embedded artist information"""
    import re
    
    # Enhanced patterns
    patterns = [
        (r'^(.+?)\s*-\s*(.+)$', 'first'),  # Artist - Song
        (r'^(.+?)\s*:\s*(.+)$', 'first'),  # Artist : Song
        (r'^(.+?)\s*\|\s*(.+)$', 'first'), # Artist | Song
        (r'^(.+?)\s*by\s+(.+)$', 'second'), # Song by Artist
        (r'^(.+?)\s*\((.+?)\)$', 'second'), # Song (Artist)
        (r'^(.+?)\s*\[(.+?)\]$', 'second'), # Song [Artist]
        (r'^(.+?)\s*feat\.?\s+(.+)$', 'first'), # Song feat Artist
        (r'^(.+?)\s*featuring\s+(.+)$', 'first'), # Song featuring Artist
        (r'^(.+?)\s*ft\.?\s+(.+)$', 'first'), # Song ft Artist
        (r'^(.+?)\s*vs\.?\s+(.+)$', 'first'), # Artist vs Artist
        (r'^(.+?)\s*&\s+(.+)$', 'first'), # Artist & Artist
        (r'^(.+?)\s*and\s+(.+)$', 'first'), # Artist and Artist
    ]
    
    for pattern, which_part in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            part1, part2 = match.groups()
            
            potential_artist = part1.strip() if which_part == 'first' else part2.strip()
            
            # Enhanced validation
            if is_valid_artist_name(potential_artist):
                return potential_artist
    
    return None

def lookup_similar_titles(song_title):
    """Look up similar titles in the database"""
    config = Config()
    
    connection = pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # Look for similar titles from known artists
            cursor.execute("""
                SELECT a.name, v.title
                FROM videos v
                JOIN artists a ON v.artist_id = a.id
                WHERE a.name != 'Unknown Artist'
                AND v.title LIKE %s
                LIMIT 1
            """, (f"%{song_title}%",))
            
            result = cursor.fetchone()
            if result:
                return result[0]  # Return artist name
                
    finally:
        connection.close()
    
    return None

def search_web_for_artist(song_title):
    """Search web for artist information (placeholder)"""
    # This is a placeholder for web search functionality
    # In a real implementation, you might use:
    # - Last.fm API
    # - Spotify API
    # - YouTube API
    # - Lyrics APIs
    # - Web scraping (with proper rate limiting)
    
    return None

def is_valid_artist_name(name):
    """Enhanced artist name validation"""
    name = name.strip()
    
    # Basic validation
    if len(name) < 2 or len(name) > 100:
        return False
        
    # Skip obvious non-artist terms
    invalid_terms = [
        'video', 'lyrics', 'official', 'music', 'live', 'acoustic', 
        'remix', 'cover', 'instrumental', 'karaoke', 'version',
        'hd', 'hq', 'full', 'complete', 'extended', 'radio', 'edit',
        'remaster', 'remastered', 'clean', 'explicit', 'censored',
        'single', 'album', 'ep', 'demo', 'bootleg', 'rare'
    ]
    
    name_lower = name.lower()
    for term in invalid_terms:
        if term in name_lower:
            return False
    
    # Check for reasonable character composition
    alpha_ratio = sum(c.isalpha() or c.isspace() for c in name) / len(name)
    if alpha_ratio < 0.6:  # Allow more special characters
        return False
    
    # Skip very common words that aren't artists
    common_words = ['the', 'and', 'or', 'but', 'for', 'with', 'to', 'of', 'in', 'on', 'at', 'my', 'your', 'our', 'their', 'his', 'her', 'its', 'we', 'you', 'they', 'i', 'me', 'us', 'them', 'him', 'she', 'it']
    words = name_lower.split()
    if len(words) == 1 and words[0] in common_words:
        return False
    
    # Skip obvious non-artist phrases
    non_artist_phrases = [
        'to party', 'and i feel fine', 'say so much', 'in my hands', 'out tonight',
        'the sweater song', 'time of your life', 'only the good die young',
        'youve got it', 'we salute you', 'and ill go mine', 'the ecstasy',
        'not constantinople', 'dance floor anthem', 'one last kiss',
        'hotel baby', 'of the unknown', 'better off dead', 'shut up and kiss me',
        'death to pop', 'hey oh', 'james murphy)', 'lloyd)', 'go )', 'ghosts )'
    ]
    
    for phrase in non_artist_phrases:
        if phrase in name_lower:
            return False
    
    # Skip single letters or very short words
    if len(words) == 1 and len(words[0]) < 3:
        return False
        
    return True

def test_comprehensive_identification():
    """Test comprehensive identification"""
    config = Config()
    
    connection = pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # Get some Unknown Artist videos
            cursor.execute("""
                SELECT v.id, v.title
                FROM videos v
                JOIN artists a ON v.artist_id = a.id
                WHERE a.name = 'Unknown Artist'
                LIMIT 20
            """)
            
            videos = cursor.fetchall()
            
            print(f"Comprehensive Artist Identification Test")
            print(f"Testing on {len(videos)} videos:")
            print(f"{'ID':<5} {'Title':<40} {'Identified Artist':<25} {'Confidence':<10} {'Source':<15}")
            print("-" * 100)
            
            identified_count = 0
            
            for video_id, title in videos:
                result = identify_artist_comprehensive(title, use_api=False)
                
                if result:
                    identified_count += 1
                    artist = result['artist'][:22] + "..." if len(result['artist']) > 25 else result['artist']
                    confidence = f"{result['confidence']:.2f}"
                    source = result['source']
                    
                    print(f"{video_id:<5} {title[:37] + '...' if len(title) > 40 else title:<40} {artist:<25} {confidence:<10} {source:<15}")
                else:
                    print(f"{video_id:<5} {title[:37] + '...' if len(title) > 40 else title:<40} {'(no match)':<25} {'0.00':<10} {'none':<15}")
            
            print("-" * 100)
            print(f"Identification rate: {identified_count}/{len(videos)} ({identified_count/len(videos)*100:.1f}%)")
                    
    finally:
        connection.close()

def apply_identifications(dry_run=True, confidence_threshold=0.7, limit=None):
    """Apply artist identifications"""
    config = Config()
    
    connection = pymysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset='utf8mb4'
    )
    
    fixed_count = 0
    created_artists = 0
    processed_count = 0
    
    try:
        with connection.cursor() as cursor:
            # Get total count first
            cursor.execute("""
                SELECT COUNT(*)
                FROM videos v
                JOIN artists a ON v.artist_id = a.id
                WHERE a.name = 'Unknown Artist'
            """)
            total_count = cursor.fetchone()[0]
            
            # Get Unknown Artist videos
            query = """
                SELECT v.id, v.title, v.artist_id
                FROM videos v
                JOIN artists a ON v.artist_id = a.id
                WHERE a.name = 'Unknown Artist'
                ORDER BY v.id
            """
            
            if limit:
                query += f" LIMIT {limit}"
                
            cursor.execute(query)
            
            videos = cursor.fetchall()
            
            print(f"Applying artist identifications...")
            print(f"Total Unknown Artist videos: {total_count:,}")
            print(f"Processing: {len(videos):,} videos")
            print(f"Confidence threshold: {confidence_threshold}")
            print(f"Dry run: {dry_run}")
            print("=" * 80)
            
            for video_id, title, current_artist_id in videos:
                processed_count += 1
                result = identify_artist_comprehensive(title, use_api=False)
                
                if not result or result['confidence'] < confidence_threshold:
                    continue
                
                artist_name = result['artist']
                
                print(f"Video ID {video_id}: '{title}'")
                print(f"  Identified: {artist_name} (confidence: {result['confidence']:.2f})")
                print(f"  Source: {result['source']}")
                
                if not dry_run:
                    # Check if artist exists
                    cursor.execute("SELECT id FROM artists WHERE name = %s", (artist_name,))
                    existing_artist = cursor.fetchone()
                    
                    if existing_artist:
                        target_artist_id = existing_artist[0]
                    else:
                        # Create new artist
                        cursor.execute("""
                            INSERT INTO artists (name, monitored, created_at, updated_at)
                            VALUES (%s, %s, NOW(), NOW())
                        """, (artist_name, True))
                        target_artist_id = cursor.lastrowid
                        created_artists += 1
                        print(f"  Created new artist: {artist_name}")
                    
                    # Update video
                    cursor.execute("""
                        UPDATE videos
                        SET artist_id = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (target_artist_id, video_id))
                    
                    fixed_count += 1
                else:
                    # Count as identified even in dry run
                    fixed_count += 1
                
                print()
                
                # Show progress every 100 videos
                if processed_count % 100 == 0:
                    print(f"Progress: {processed_count:,}/{len(videos):,} videos processed, {fixed_count} identified...")
            
            if not dry_run:
                connection.commit()
                print(f"Committed {fixed_count} fixes to database")
            else:
                print(f"Dry run completed - {fixed_count} videos would be fixed")
                
            print("=" * 80)
            print(f"Summary:")
            print(f"  Total Unknown Artist videos: {total_count:,}")
            print(f"  Videos processed: {len(videos):,}")
            print(f"  Artists identified: {fixed_count}")
            print(f"  New artists created: {created_artists}")
            print(f"  Identification rate: {fixed_count/len(videos)*100:.1f}%")
                    
    finally:
        connection.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive artist identification")
    parser.add_argument("--test", action="store_true", default=True,
                        help="Test identification (default)")
    parser.add_argument("--apply", action="store_true", default=False,
                        help="Apply identifications")
    parser.add_argument("--confidence", type=float, default=0.7,
                        help="Minimum confidence threshold")
    parser.add_argument("--execute", action="store_true", default=False,
                        help="Execute changes (not dry run)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of videos to process (default: all)")
    parser.add_argument("--all", action="store_true", default=False,
                        help="Process entire database (removes default limit)")
    
    args = parser.parse_args()
    
    # Handle --all flag
    if args.all:
        args.limit = None
    
    if args.apply:
        dry_run = not args.execute
        
        if args.execute:
            print("WARNING: This will make actual changes to the database!")
            if args.limit is None:
                print("This will process ALL Unknown Artist videos in the database!")
            else:
                print(f"This will process up to {args.limit} Unknown Artist videos!")
            response = input("Are you sure you want to proceed? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Aborted.")
                return
        
        apply_identifications(
            dry_run=dry_run, 
            confidence_threshold=args.confidence,
            limit=args.limit
        )
    else:
        test_comprehensive_identification()

if __name__ == "__main__":
    main()