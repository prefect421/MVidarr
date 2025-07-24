#!/usr/bin/env python3
"""
Script to fix all videos marked as downloaded but with missing files
Sets them to wanted status and enables artist monitoring
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.video_recovery_service import video_recovery_service
from src.utils.logger import get_logger

logger = get_logger('mvidarr.scripts.fix_missing_videos')

def main():
    """Main function to fix missing downloaded videos"""
    print("MVidarr - Fix Missing Downloaded Videos")
    print("=" * 50)
    
    try:
        # Run the fix operation
        print("Scanning for videos marked as downloaded with missing files...")
        stats = video_recovery_service.fix_missing_downloaded_videos()
        
        # Display results
        print(f"\n📊 Results:")
        print(f"   Total downloaded videos checked: {stats['total_downloaded']}")
        print(f"   Videos with missing files: {stats['missing_files']}")
        print(f"   Videos recovered: {stats['recovered_videos']}")
        print(f"   Videos marked as wanted: {stats['marked_wanted']}")
        print(f"   Artists set to monitored: {stats['artists_monitored']}")
        
        if stats['missing_files'] > 0:
            print(f"\n✅ Successfully processed {stats['missing_files']} missing videos!")
            if stats['recovered_videos'] > 0:
                print(f"   🔄 {stats['recovered_videos']} videos were recovered and database updated")
            if stats['marked_wanted'] > 0:
                print(f"   📥 {stats['marked_wanted']} videos were marked as wanted for re-download")
            if stats['artists_monitored'] > 0:
                print(f"   👁️ {stats['artists_monitored']} artists were set to monitored")
        else:
            print("\n✅ No missing videos found! All downloaded videos have valid file paths.")
        
        print("\n🎉 Operation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during operation: {e}")
        logger.error(f"Error during fix missing videos operation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()