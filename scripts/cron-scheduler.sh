#!/bin/bash
# MVidarr Cron Scheduler Script
# Failsafe scheduler that runs via cron as backup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/data/logs/cron-scheduler.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log_message "=== MVidarr Cron Scheduler Started ==="

# Change to project directory
cd "$PROJECT_DIR" || {
    log_message "ERROR: Failed to change to project directory: $PROJECT_DIR"
    exit 1
}

# Check if MVidarr web app is running
if pgrep -f "python.*app" > /dev/null; then
    log_message "MVidarr web app is running, checking scheduler status via API"
    
    # Try to trigger downloads via API
    if command -v curl > /dev/null; then
        # Get admin credentials (this would need to be implemented)
        USERNAME=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.services.simple_auth_service import SimpleAuthService
    from src.database.connection import init_db_standalone
    init_db_standalone()
    username, _ = SimpleAuthService.get_credentials()
    print(username)
except Exception as e:
    print('admin')  # fallback
" 2>/dev/null)
        
        # Make API request
        RESPONSE=$(curl -s -w "%{http_code}" \
            -u "$USERNAME:$USERNAME" \
            -X POST \
            "http://localhost:5000/api/scheduler/trigger" \
            -H "Content-Type: application/json" \
            -d '{"source": "cron"}' 2>/dev/null)
        
        HTTP_CODE="${RESPONSE: -3}"
        
        if [ "$HTTP_CODE" = "200" ]; then
            log_message "Successfully triggered downloads via API"
            exit 0
        else
            log_message "API request failed with code: $HTTP_CODE"
        fi
    fi
fi

log_message "Falling back to direct Python execution"

# Fallback: Run scheduler directly
python3 -c "
import sys
sys.path.insert(0, '.')

try:
    from src.database.connection import init_db_standalone
    from src.services.settings_service import SettingsService
    
    # Initialize database
    init_db_standalone()
    SettingsService.load_cache()
    
    # Check if auto-download is enabled
    if not SettingsService.get_bool('auto_download_schedule_enabled', False):
        print('Auto-download scheduling is disabled')
        sys.exit(0)
    
    print('Auto-download is enabled - would run downloads here')
    # TODO: Implement direct download execution
    
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
" >> "$LOG_FILE" 2>&1

log_message "=== MVidarr Cron Scheduler Completed ==="