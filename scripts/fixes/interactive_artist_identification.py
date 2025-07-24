#!/usr/bin/env python3
"""
Interactive Artist Identification for Unknown Artist videos
Allows searching and identifying individual videos one at a time
"""

import sys
import os
import pymysql
from datetime import datetime

# Add the project root directory to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.config.config import Config
from identify_artists_comprehensive import identify_artist_comprehensive, is_valid_artist_name

def search_unknown_videos(search_term="", limit=20):
    """Search for Unknown Artist videos"""
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
            if search_term:
                # Search by title
                cursor.execute("""
                    SELECT v.id, v.title, v.artist_id, v.local_path, v.year
                    FROM videos v
                    JOIN artists a ON v.artist_id = a.id
                    WHERE a.name = 'Unknown Artist'
                    AND v.title LIKE %s
                    ORDER BY v.title
                    LIMIT %s
                """, (f"%{search_term}%", limit))
            else:
                # Get recent Unknown Artist videos
                cursor.execute("""
                    SELECT v.id, v.title, v.artist_id, v.local_path, v.year
                    FROM videos v
                    JOIN artists a ON v.artist_id = a.id
                    WHERE a.name = 'Unknown Artist'
                    ORDER BY v.id DESC
                    LIMIT %s
                """, (limit,))
            
            return cursor.fetchall()
            
    finally:
        connection.close()

def get_video_details(video_id):
    """Get detailed information about a specific video"""
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
            cursor.execute("""
                SELECT v.id, v.title, v.artist_id, v.local_path, v.year, 
                       v.duration, v.created_at, v.status, a.name as artist_name
                FROM videos v
                JOIN artists a ON v.artist_id = a.id
                WHERE v.id = %s
            """, (video_id,))
            
            return cursor.fetchone()
            
    finally:
        connection.close()

def apply_identification(video_id, artist_name):
    """Apply artist identification to a specific video"""
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
            # Check if artist exists
            cursor.execute("SELECT id FROM artists WHERE name = %s", (artist_name,))
            existing_artist = cursor.fetchone()
            
            if existing_artist:
                target_artist_id = existing_artist[0]
                print(f"Using existing artist: {artist_name}")
            else:
                # Create new artist
                cursor.execute("""
                    INSERT INTO artists (name, monitored, created_at, updated_at)
                    VALUES (%s, %s, NOW(), NOW())
                """, (artist_name, True))
                target_artist_id = cursor.lastrowid
                print(f"Created new artist: {artist_name}")
            
            # Update video
            cursor.execute("""
                UPDATE videos
                SET artist_id = %s, updated_at = NOW()
                WHERE id = %s
            """, (target_artist_id, video_id))
            
            connection.commit()
            return True
            
    except Exception as e:
        print(f"Error applying identification: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()

def display_video_card(video_info):
    """Display detailed video information in a card format"""
    video_id, title, artist_id, local_path, year, duration, created_at, status, artist_name = video_info
    
    print("=" * 80)
    print(f"VIDEO CARD - ID: {video_id}")
    print("=" * 80)
    print(f"Title: {title}")
    print(f"Current Artist: {artist_name}")
    print(f"Year: {year or 'Unknown'}")
    print(f"Duration: {duration or 'Unknown'}")
    print(f"Status: {status}")
    print(f"Local Path: {local_path or 'Not downloaded'}")
    print(f"Added: {created_at}")
    print("-" * 80)

def display_identification_results(candidates):
    """Display identification candidates"""
    if not candidates:
        print("No identification candidates found.")
        return
    
    print("IDENTIFICATION CANDIDATES:")
    print("-" * 80)
    
    for i, candidate in enumerate(candidates, 1):
        print(f"{i}. {candidate['artist']} (confidence: {candidate['confidence']:.2f})")
        print(f"   Source: {candidate['source']}")
        print(f"   Reason: {candidate.get('match_reason', 'No additional info')}")
        print()

def interactive_mode():
    """Interactive mode for video identification"""
    print("Interactive Artist Identification Mode")
    print("=" * 60)
    print("Commands:")
    print("  search <term>  - Search for videos by title")
    print("  list          - List recent Unknown Artist videos")
    print("  identify <id> - Identify specific video by ID")
    print("  help          - Show this help")
    print("  quit          - Exit interactive mode")
    print("=" * 60)
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == 'quit' or command == 'q':
                print("Goodbye!")
                break
            
            elif command == 'help' or command == 'h':
                print("\nAvailable commands:")
                print("  search <term>  - Search for videos containing <term> in title")
                print("  list           - Show 20 most recent Unknown Artist videos")
                print("  identify <id>  - Show identification options for video ID")
                print("  quit           - Exit")
            
            elif command == 'list' or command == 'l':
                videos = search_unknown_videos(limit=20)
                if videos:
                    print(f"\n{'ID':<5} {'Title':<50} {'Year':<6}")
                    print("-" * 65)
                    for video in videos:
                        video_id, title, artist_id, local_path, year = video
                        title_display = title[:47] + "..." if len(title) > 50 else title
                        year_display = str(year) if year else ""
                        print(f"{video_id:<5} {title_display:<50} {year_display:<6}")
                else:
                    print("No Unknown Artist videos found.")
            
            elif command.startswith('search '):
                search_term = command[7:].strip()
                if search_term:
                    videos = search_unknown_videos(search_term, limit=20)
                    if videos:
                        print(f"\nSearch results for '{search_term}':")
                        print(f"{'ID':<5} {'Title':<50} {'Year':<6}")
                        print("-" * 65)
                        for video in videos:
                            video_id, title, artist_id, local_path, year = video
                            title_display = title[:47] + "..." if len(title) > 50 else title
                            year_display = str(year) if year else ""
                            print(f"{video_id:<5} {title_display:<50} {year_display:<6}")
                    else:
                        print(f"No videos found matching '{search_term}'.")
                else:
                    print("Please provide a search term: search <term>")
            
            elif command.startswith('identify '):
                try:
                    video_id = int(command[9:].strip())
                    
                    # Get video details
                    video_info = get_video_details(video_id)
                    if not video_info:
                        print(f"Video ID {video_id} not found.")
                        continue
                    
                    # Display video card
                    display_video_card(video_info)
                    
                    # Get identification candidates
                    title = video_info[1]  # title is second field
                    candidates = identify_artist_comprehensive(title, use_api=False)
                    
                    if candidates:
                        # Filter candidates with reasonable confidence
                        good_candidates = [c for c in candidates if c['confidence'] > 0.6]
                        
                        if good_candidates:
                            display_identification_results(good_candidates)
                            
                            # Interactive selection
                            while True:
                                choice = input("Select candidate (1-{}, 's' to skip, 'm' for manual): ".format(len(good_candidates))).strip().lower()
                                
                                if choice == 's':
                                    print("Skipped.")
                                    break
                                elif choice == 'm':
                                    manual_artist = input("Enter artist name manually: ").strip()
                                    if manual_artist and is_valid_artist_name(manual_artist):
                                        confirm = input(f"Apply artist '{manual_artist}' to video '{title}'? (y/n): ").strip().lower()
                                        if confirm == 'y':
                                            if apply_identification(video_id, manual_artist):
                                                print(f"✓ Applied: {manual_artist}")
                                            else:
                                                print("✗ Failed to apply identification")
                                    else:
                                        print("Invalid artist name.")
                                    break
                                else:
                                    try:
                                        choice_idx = int(choice) - 1
                                        if 0 <= choice_idx < len(good_candidates):
                                            selected = good_candidates[choice_idx]
                                            confirm = input(f"Apply artist '{selected['artist']}' to video '{title}'? (y/n): ").strip().lower()
                                            if confirm == 'y':
                                                if apply_identification(video_id, selected['artist']):
                                                    print(f"✓ Applied: {selected['artist']}")
                                                else:
                                                    print("✗ Failed to apply identification")
                                            break
                                        else:
                                            print("Invalid selection.")
                                    except ValueError:
                                        print("Invalid input. Enter number, 's', or 'm'.")
                        else:
                            print("No candidates with sufficient confidence found.")
                    else:
                        print("No identification candidates found.")
                        
                        # Offer manual entry
                        manual = input("Enter artist name manually (or press Enter to skip): ").strip()
                        if manual and is_valid_artist_name(manual):
                            confirm = input(f"Apply artist '{manual}' to video '{title}'? (y/n): ").strip().lower()
                            if confirm == 'y':
                                if apply_identification(video_id, manual):
                                    print(f"✓ Applied: {manual}")
                                else:
                                    print("✗ Failed to apply identification")
                        
                except ValueError:
                    print("Invalid video ID. Use: identify <number>")
            
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Interactive artist identification")
    parser.add_argument("--search", type=str, help="Search for videos by title")
    parser.add_argument("--identify", type=int, help="Identify specific video by ID")
    parser.add_argument("--interactive", action="store_true", default=True,
                        help="Interactive mode (default)")
    
    args = parser.parse_args()
    
    if args.search:
        videos = search_unknown_videos(args.search, limit=20)
        if videos:
            print(f"Search results for '{args.search}':")
            print(f"{'ID':<5} {'Title':<50} {'Year':<6}")
            print("-" * 65)
            for video in videos:
                video_id, title, artist_id, local_path, year = video
                title_display = title[:47] + "..." if len(title) > 50 else title
                year_display = str(year) if year else ""
                print(f"{video_id:<5} {title_display:<50} {year_display:<6}")
        else:
            print(f"No videos found matching '{args.search}'.")
    
    elif args.identify:
        video_info = get_video_details(args.identify)
        if video_info:
            display_video_card(video_info)
            title = video_info[1]
            candidates = identify_artist_comprehensive(title, use_api=False)
            display_identification_results(candidates)
        else:
            print(f"Video ID {args.identify} not found.")
    
    else:
        interactive_mode()

if __name__ == "__main__":
    main()