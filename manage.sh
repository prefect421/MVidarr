#!/bin/bash
# MVidarr Enhanced Management Script

show_help() {
    echo "MVidarr Enhanced Management Script"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the application"
    echo "  stop      Stop the application"
    echo "  restart   Restart the application"
    echo "  status    Show application status"
    echo "  logs      Show application logs"
    echo "  help      Show this help message"
    echo ""
    echo "URLs:"
    echo "  Application: http://localhost:5000"
    echo "  API Docs:    http://localhost:5000/api/docs"
    echo "  Health:      http://localhost:5000/api/health"
}

check_status() {
    if pgrep -f "python.*app" > /dev/null; then
        echo "✓ MVidarr Enhanced is running"
        PID=$(pgrep -f "python.*app")
        echo "  PID: $PID"
        
        # Check if port is listening
        if ss -tlnp | grep -q :5000; then
            echo "  Port 5000: Listening"
        else
            echo "  Port 5000: Not listening"
        fi
        
        # Test API health
        if curl -s http://localhost:5000/api/artists/ > /dev/null; then
            echo "  API Status: Responding"
        else
            echo "  API Status: Not responding"
        fi
        
        return 0
    else
        echo "✗ MVidarr Enhanced is not running"
        return 1
    fi
}

start_app() {
    echo "Starting MVidarr Enhanced..."
    
    if check_status > /dev/null 2>&1; then
        echo "Application is already running"
        return 0
    fi
    
    # Change to application directory
    cd "$(dirname "$0")"
    
    # Start the application using smart launcher
    python3 app_launcher.py > data/logs/app.log 2>&1 &
    PID=$!
    
    echo "Application started with PID: $PID"
    
    # Wait and check if it started successfully
    sleep 3
    
    if check_status > /dev/null 2>&1; then
        echo "✓ MVidarr Enhanced started successfully"
        echo "✓ Access at: http://localhost:5000"
        echo "✓ API Docs: http://localhost:5000/api/docs"
        return 0
    else
        echo "✗ Failed to start application"
        return 1
    fi
}

stop_app() {
    echo "Stopping MVidarr Enhanced..."
    
    if ! check_status > /dev/null 2>&1; then
        echo "Application is not running"
        return 0
    fi
    
    # Stop the application
    pkill -f "python.*app"
    
    # Wait for it to stop
    sleep 2
    
    if ! check_status > /dev/null 2>&1; then
        echo "✓ MVidarr Enhanced stopped successfully"
        return 0
    else
        echo "✗ Failed to stop application"
        return 1
    fi
}

restart_app() {
    echo "Restarting MVidarr Enhanced..."
    stop_app
    sleep 1
    start_app
}

show_logs() {
    echo "Showing MVidarr Enhanced logs..."
    echo "Press Ctrl+C to exit"
    echo "========================"
    
    if [ -f "data/logs/app.log" ]; then
        tail -f data/logs/app.log
    else
        echo "Log file not found: data/logs/app.log"
        return 1
    fi
}

# Main script logic
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        echo "No command specified. Use '$0 help' for usage information."
        check_status
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information."
        exit 1
        ;;
esac