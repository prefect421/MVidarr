#!/usr/bin/env python3
"""
Video organization script for MVidarr Enhanced
Cleans up filenames and organizes downloaded videos by artist
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.config.config import Config
from src.database.connection import init_db
from src.services.video_organization_service import video_organizer
from src.utils.logger import get_logger

logger = get_logger('mvidarr.video_organization_script')

class DummyApp:
    """Dummy app for database initialization"""
    def __init__(self):
        self.config = {}
        self.db_manager = None
        config = Config()
        for attr in dir(config):
            if not attr.startswith('_'):
                self.config[attr] = getattr(config, attr)
    
    def teardown_appcontext(self, func):
        """Dummy teardown function for Flask compatibility"""
        pass

def initialize_environment():
    """Initialize the application environment"""
    try:
        # Initialize database
        app = DummyApp() 
        init_db(app)
        logger.info("Environment initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize environment: {e}")
        return False

def organize_all_videos():
    """Organize all videos in downloads directory"""
    logger.info("Starting organization of all videos")
    
    try:
        # Show the paths being used
        downloads_path = video_organizer.get_downloads_path()
        music_videos_path = video_organizer.get_music_videos_path()
        
        print(f"\n🎵 Video Organization Process 🎵")
        print(f"Downloads path: {downloads_path}")
        print(f"Music videos path: {music_videos_path}")
        print("-" * 60)
        
        result = video_organizer.organize_all_downloads()
        
        print(f"\n🎵 Video Organization Complete 🎵")
        print(f"Total files found: {result['total_files']}")
        print(f"Successfully organized: {result['successful']}")
        print(f"Failed to organize: {result['failed']}")
        
        if result['successful'] > 0:
            print(f"\n✅ Successfully organized videos:")
            for item in result['results']:
                if item['success']:
                    print(f"  • {item['artist']} - {item['title']}")
        
        if result['failed'] > 0:
            print(f"\n❌ Failed to organize:")
            for item in result['results']:
                if not item['success']:
                    print(f"  • {Path(item['original_path']).name}: {item['error']}")
        
        return result['successful'] > 0
        
    except Exception as e:
        logger.error(f"Organization failed: {e}")
        print(f"❌ Organization failed: {e}")
        return False

def organize_single_video(filename):
    """Organize a specific video file"""
    logger.info(f"Organizing single video: {filename}")
    
    try:
        # Show the paths being used
        downloads_path = video_organizer.get_downloads_path()
        music_videos_path = video_organizer.get_music_videos_path()
        
        print(f"\n🎵 Single Video Organization 🎵")
        print(f"Downloads path: {downloads_path}")
        print(f"Music videos path: {music_videos_path}")
        print(f"Target file: {filename}")
        print("-" * 60)
        
        result = video_organizer.organize_single_file(filename)
        
        if result['success']:
            print(f"✅ Successfully organized: {result['artist']} - {result['title']}")
            print(f"   Moved to: {result['new_path']}")
            return True
        else:
            print(f"❌ Failed to organize {filename}: {result['error']}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to organize {filename}: {e}")
        print(f"❌ Failed to organize {filename}: {e}")
        return False

def show_path_configuration():
    """Show current path configuration from database settings"""
    try:
        downloads_path = video_organizer.get_downloads_path()
        music_videos_path = video_organizer.get_music_videos_path()
        
        print(f"\n⚙️  Path Configuration ⚙️")
        print("-" * 50)
        print(f"Downloads path:     {downloads_path}")
        print(f"Music videos path:  {music_videos_path}")
        print("-" * 50)
        
        # Check if directories exist
        downloads_exists = downloads_path.exists()
        music_videos_exists = music_videos_path.exists()
        
        print(f"Downloads directory exists:     {'✅' if downloads_exists else '❌'}")
        print(f"Music videos directory exists:  {'✅' if music_videos_exists else '❌'}")
        
        # Show pending videos
        if downloads_exists:
            video_files = video_organizer.scan_downloads_directory()
            print(f"Pending videos to organize:     {len(video_files)}")
        
        # Show organized artists
        if music_videos_exists:
            artists = video_organizer.get_artist_directories()
            total_videos = sum(artist['video_count'] for artist in artists)
            print(f"Organized artist directories:   {len(artists)}")
            print(f"Total organized videos:         {total_videos}")
        
    except Exception as e:
        logger.error(f"Failed to show path configuration: {e}")
        print(f"❌ Failed to show path configuration: {e}")

def show_artist_directories():
    """Show current artist directories and video counts"""
    try:
        artists = video_organizer.get_artist_directories()
        
        if not artists:
            print("📁 No artist directories found")
            return
        
        print(f"📁 Artist Directories ({len(artists)} total):")
        print("-" * 60)
        
        total_videos = 0
        for artist in artists:
            print(f"  {artist['name']:<40} {artist['video_count']:>3} videos")
            total_videos += artist['video_count']
        
        print("-" * 60)
        print(f"  Total videos organized: {total_videos}")
        
    except Exception as e:
        logger.error(f"Failed to show directories: {e}")
        print(f"❌ Failed to show directories: {e}")

def reorganize_existing_videos():
    """Reorganize existing videos in the music videos directory"""
    logger.info("Starting reorganization of existing music videos")
    
    try:
        # Show the paths being used
        music_videos_path = video_organizer.get_music_videos_path()
        
        print(f"\n🔄 Reorganizing Existing Music Videos 🔄")
        print(f"Music videos path: {music_videos_path}")
        print("-" * 60)
        
        result = video_organizer.reorganize_existing_videos()
        
        print(f"\n🔄 Reorganization Complete 🔄")
        print(f"Total files found: {result['total_files']}")
        print(f"Successfully reorganized: {result['successful']}")
        print(f"Already organized (skipped): {result['skipped']}")
        print(f"Failed to reorganize: {result['failed']}")
        
        if result['successful'] > 0:
            print(f"\n✅ Successfully reorganized videos:")
            for item in result['results']:
                if item['success'] and not item['skipped']:
                    action = item.get('action', 'organized')
                    print(f"  • {item['artist']} - {item['title']} ({action})")
        
        if result['skipped'] > 0:
            print(f"\n⏭️  Already properly organized (skipped):")
            for item in result['results']:
                if item['success'] and item['skipped']:
                    print(f"  • {item['artist']} - {item['title']}")
        
        if result['failed'] > 0:
            print(f"\n❌ Failed to reorganize:")
            for item in result['results']:
                if not item['success'] and not item['skipped']:
                    file_name = Path(item['original_path']).name
                    print(f"  • {file_name}: {item['error']}")
        
        return result['successful'] > 0
        
    except Exception as e:
        logger.error(f"Reorganization failed: {e}")
        print(f"❌ Reorganization failed: {e}")
        return False

def scan_existing_videos():
    """Scan and display existing videos in music videos directory"""
    try:
        music_videos_path = video_organizer.get_music_videos_path()
        video_files = video_organizer.scan_existing_music_videos()
        
        print(f"\n📁 Existing Music Videos Scan 📁")
        print(f"Music videos path: {music_videos_path}")
        print(f"Total video files found: {len(video_files)}")
        print("-" * 60)
        
        if video_files:
            print("Video files found:")
            for file_path in video_files[:20]:  # Show first 20 files
                try:
                    relative_path = file_path.relative_to(music_videos_path)
                    print(f"  • {relative_path}")
                except ValueError:
                    print(f"  • {file_path}")
            
            if len(video_files) > 20:
                print(f"  ... and {len(video_files) - 20} more files")
        else:
            print("No video files found in music videos directory")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to scan existing videos: {e}")
        print(f"❌ Failed to scan existing videos: {e}")
        return False

def cleanup_empty_directories():
    """Remove empty artist directories"""
    try:
        removed_count = video_organizer.cleanup_empty_directories()
        
        if removed_count > 0:
            print(f"🗑️  Removed {removed_count} empty directories")
        else:
            print("✨ No empty directories to clean up")
            
        return removed_count > 0
        
    except Exception as e:
        logger.error(f"Failed to cleanup directories: {e}")
        print(f"❌ Failed to cleanup directories: {e}")
        return False

def test_filename_cleanup():
    """Test the filename cleanup functionality"""
    from src.utils.filename_cleanup import FilenameCleanup
    
    test_cases = [
        "Taylor Swift - Anti-Hero [Official Music Video] [4K] (2022).mp4",
        "The Weeknd | Blinding Lights (Official Video) [1080p].mkv",
        "Billie Eilish – bad guy [YouTube Music Video] HD.mp4",
        "[Downloaded 2023-12-01] Ed Sheeran - Shape of You (Official).avi",
        "Dua Lipa: Levitating | Official Music Video [4K UHD].webm",
        "badly_formatted__file---name.mp4"
    ]
    
    print("🧪 Testing filename cleanup:")
    print("=" * 80)
    
    for original in test_cases:
        cleaned = FilenameCleanup.clean_filename(original)
        artist, title = FilenameCleanup.extract_artist_and_title(cleaned)
        
        print(f"Original: {original}")
        print(f"Cleaned:  {cleaned}")
        print(f"Artist:   {artist or 'Could not extract'}")
        print(f"Title:    {title or 'Could not extract'}")
        
        if artist and title:
            new_name = FilenameCleanup.generate_clean_filename(
                artist, title, Path(original).suffix
            )
            print(f"Final:    {new_name}")
        print("-" * 80)

def main():
    """Main script entry point"""
    parser = argparse.ArgumentParser(
        description='Organize downloaded music videos by artist',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --organize-all              # Organize all videos in downloads
  %(prog)s --organize "video.mp4"      # Organize specific video
  %(prog)s --reorganize-existing       # Reorganize existing music videos
  %(prog)s --scan-existing             # Scan existing music videos directory
  %(prog)s --show-artists              # Show current artist directories
  %(prog)s --show-paths                # Show current path configuration
  %(prog)s --cleanup                   # Remove empty directories
  %(prog)s --test                      # Test filename cleanup
        """
    )
    
    parser.add_argument('--organize-all', action='store_true',
                       help='Organize all videos in downloads directory')
    parser.add_argument('--organize', metavar='FILENAME',
                       help='Organize specific video file')
    parser.add_argument('--reorganize-existing', action='store_true',
                       help='Reorganize existing videos in music videos directory')
    parser.add_argument('--scan-existing', action='store_true',
                       help='Scan existing music videos directory for files')
    parser.add_argument('--show-artists', action='store_true',
                       help='Show current artist directories')
    parser.add_argument('--show-paths', action='store_true',
                       help='Show current path configuration from database')
    parser.add_argument('--cleanup', action='store_true',
                       help='Remove empty artist directories')
    parser.add_argument('--test', action='store_true',
                       help='Test filename cleanup functionality')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Show help if no arguments
    if not any(vars(args).values()):
        parser.print_help()
        return 0
    
    # Test mode doesn't require database
    if args.test:
        test_filename_cleanup()
        return 0
    
    # Initialize environment for database operations
    if not initialize_environment():
        print("❌ Failed to initialize environment")
        return 1
    
    success = True
    
    if args.organize_all:
        success = organize_all_videos() and success
    
    if args.organize:
        success = organize_single_video(args.organize) and success
    
    if args.reorganize_existing:
        success = reorganize_existing_videos() and success
    
    if args.scan_existing:
        scan_existing_videos()
    
    if args.show_artists:
        show_artist_directories()
    
    if args.show_paths:
        show_path_configuration()
    
    if args.cleanup:
        success = cleanup_empty_directories() and success
    
    return 0 if success else 1

if __name__ == '__main__':
    exit(main())