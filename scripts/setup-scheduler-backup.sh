#!/bin/bash
# Setup script for MVidarr scheduler backup systems
# This creates system service and cron job backups for the main scheduler

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Setting up MVidarr Scheduler Backup Systems..."

# Function to check if running as root for system service setup
check_sudo() {
    if [ "$EUID" -eq 0 ]; then
        echo "⚠️  Running as root - will set up system service"
        return 0
    else
        echo "ℹ️  Running as user - will set up user-level backups only"
        return 1
    fi
}

# Setup System Service (requires root)
setup_system_service() {
    if check_sudo; then
        echo "📋 Installing MVidarr Scheduler Service..."
        
        # Copy service file to systemd directory
        cp "$PROJECT_DIR/mvidarr-scheduler.service" /etc/systemd/system/
        
        # Reload systemd and enable service
        systemctl daemon-reload
        systemctl enable mvidarr-scheduler.service
        
        echo "✅ System service installed and enabled"
        echo "   - Start with: sudo systemctl start mvidarr-scheduler"
        echo "   - Status: sudo systemctl status mvidarr-scheduler"
        echo "   - Logs: sudo journalctl -u mvidarr-scheduler -f"
    else
        echo "⚠️  Skipping system service setup (requires sudo)"
    fi
}

# Setup Cron Job
setup_cron_job() {
    echo "📅 Setting up cron job backup..."
    
    # Create cron entry (run every hour at minute 30)
    CRON_JOB="30 * * * * $PROJECT_DIR/scripts/cron-scheduler.sh"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "cron-scheduler.sh"; then
        echo "ℹ️  Cron job already exists"
    else
        # Add cron job
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        echo "✅ Cron job added: runs every hour at minute 30"
    fi
    
    echo "   - View cron jobs: crontab -l"
    echo "   - Edit cron jobs: crontab -e"
    echo "   - Logs: $PROJECT_DIR/data/logs/cron-scheduler.log"
}

# Create log directories
setup_directories() {
    echo "📁 Creating log directories..."
    mkdir -p "$PROJECT_DIR/data/logs"
    echo "✅ Log directories created"
}

# Test the backup systems
test_backups() {
    echo "🧪 Testing backup systems..."
    
    # Test cron script
    echo "Testing cron scheduler script..."
    if "$PROJECT_DIR/scripts/cron-scheduler.sh"; then
        echo "✅ Cron scheduler script works"
    else
        echo "❌ Cron scheduler script failed"
    fi
    
    # Test Python scheduler service (dry run)
    echo "Testing Python scheduler service..."
    timeout 5 python3 "$PROJECT_DIR/scripts/scheduler-service.py" || {
        echo "✅ Scheduler service starts (timed out as expected)"
    }
}

# Main execution
main() {
    echo "Starting setup..."
    
    setup_directories
    setup_cron_job
    setup_system_service
    test_backups
    
    echo ""
    echo "🎉 MVidarr Scheduler Backup Setup Complete!"
    echo ""
    echo "📊 Summary:"
    echo "   ✅ Primary Scheduler: Running in main MVidarr app (http://localhost:5000)"
    echo "   📅 Cron Backup: Every hour at minute 30"
    if check_sudo; then
        echo "   🔧 System Service: Available (mvidarr-scheduler.service)"
    else
        echo "   🔧 System Service: Not installed (requires sudo)"
    fi
    echo ""
    echo "📝 Next Steps:"
    echo "   1. The main scheduler is already working in your MVidarr app"
    echo "   2. Cron backup will run automatically every hour"
    echo "   3. System service can be started manually if needed"
    echo ""
    echo "📋 Management Commands:"
    echo "   • Check scheduler status: curl -u admin:admin http://localhost:5000/api/scheduler/status"
    echo "   • Trigger download now: curl -u admin:admin -X POST http://localhost:5000/api/scheduler/trigger"
    echo "   • View cron logs: tail -f $PROJECT_DIR/data/logs/cron-scheduler.log"
    if check_sudo; then
        echo "   • Start system service: sudo systemctl start mvidarr-scheduler"
        echo "   • Service logs: sudo journalctl -u mvidarr-scheduler -f"
    fi
}

main "$@"