#!/bin/bash
"""
Automated video organization script for MVidarr Enhanced
This script can be run as a cron job to automatically organize downloaded videos
"""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Log file for automation
LOG_FILE="$PROJECT_DIR/data/logs/auto_organize.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "Starting automatic video organization"

# Change to project directory
cd "$PROJECT_DIR" || {
    log_message "ERROR: Could not change to project directory: $PROJECT_DIR"
    exit 1
}

# Get current downloads path from database and check for video files
DOWNLOADS_PATH=$(python3 -c "
import sys
sys.path.insert(0, 'src')
from src.config.config import Config
from src.database.connection import init_db
from src.services.video_organization_service import video_organizer

class DummyApp:
    def __init__(self):
        self.config = {}
        self.db_manager = None
        config = Config()
        for attr in dir(config):
            if not attr.startswith('_'):
                self.config[attr] = getattr(config, attr)
    def teardown_appcontext(self, func): pass

try:
    app = DummyApp()
    init_db(app)
    print(video_organizer.get_downloads_path())
except:
    print('data/downloads')
" 2>/dev/null || echo "data/downloads")

VIDEO_COUNT=$(find "$DOWNLOADS_PATH" -name "*.mp4" -o -name "*.mkv" -o -name "*.avi" -o -name "*.mov" -o -name "*.wmv" -o -name "*.flv" -o -name "*.webm" -o -name "*.m4v" 2>/dev/null | wc -l)

if [ "$VIDEO_COUNT" -eq 0 ]; then
    log_message "No video files found in downloads directory"
    exit 0
fi

log_message "Found $VIDEO_COUNT video files to organize"

# Run the organization script
if python3 scripts/organize_videos.py --organize-all > /tmp/organize_output.log 2>&1; then
    # Count results
    SUCCESSFUL=$(grep -o "Successfully organized:" /tmp/organize_output.log | wc -l)
    FAILED=$(grep -o "Failed to organize:" /tmp/organize_output.log | wc -l)
    
    log_message "Organization completed: $SUCCESSFUL successful, $FAILED failed"
    
    # Log any failures for review
    if [ "$FAILED" -gt 0 ]; then
        log_message "Failed video details:"
        grep "Failed to organize:" /tmp/organize_output.log | tee -a "$LOG_FILE"
    fi
    
    # Clean up empty directories
    if python3 scripts/organize_videos.py --cleanup >> /tmp/organize_output.log 2>&1; then
        CLEANED=$(grep -o "Removed.*empty" /tmp/organize_output.log | tail -1)
        if [ -n "$CLEANED" ]; then
            log_message "Cleanup: $CLEANED"
        fi
    fi
    
else
    log_message "ERROR: Organization script failed"
    cat /tmp/organize_output.log | tee -a "$LOG_FILE"
    exit 1
fi

# Clean up temp log
rm -f /tmp/organize_output.log

log_message "Auto-organization completed successfully"

# Optional: Send notification if configured
if command -v notify-send >/dev/null 2>&1 && [ "$VIDEO_COUNT" -gt 0 ]; then
    notify-send "MVidarr" "Organized $SUCCESSFUL music videos"
fi