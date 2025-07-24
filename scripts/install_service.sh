#!/bin/bash

# MVidarr Enhanced Systemd Service Installation Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_NAME="mvidarr"
SERVICE_FILE="$PROJECT_DIR/$SERVICE_NAME.service"
SYSTEMD_DIR="/etc/systemd/system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Install the systemd service
install_service() {
    print_status "Installing MVidarr systemd service..."
    
    # Check if service file exists
    if [ ! -f "$SERVICE_FILE" ]; then
        print_error "Service file not found: $SERVICE_FILE"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        print_warning "Virtual environment not found. Creating..."
        sudo -u mike python3 -m venv "$PROJECT_DIR/venv"
        sudo -u mike "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
        print_status "Virtual environment created"
    fi
    
    # Check if app_launcher.py exists
    if [ ! -f "$PROJECT_DIR/app_launcher.py" ]; then
        print_error "Application launcher not found: $PROJECT_DIR/app_launcher.py"
        exit 1
    fi
    
    # Create data directories with proper permissions
    print_status "Creating data directories..."
    mkdir -p "$PROJECT_DIR/data/logs" "$PROJECT_DIR/data/downloads" "$PROJECT_DIR/data/thumbnails" "$PROJECT_DIR/data/cache" "$PROJECT_DIR/data/backups"
    chown -R mike:mike "$PROJECT_DIR/data"
    chmod -R 755 "$PROJECT_DIR/data"
    
    # Copy service file to systemd directory
    cp "$SERVICE_FILE" "$SYSTEMD_DIR/"
    
    # Set proper permissions
    chmod 644 "$SYSTEMD_DIR/$SERVICE_NAME.service"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service for autostart
    systemctl enable "$SERVICE_NAME.service"
    
    print_status "Service installed and enabled for autostart"
    print_status "Service file: $SYSTEMD_DIR/$SERVICE_NAME.service"
    print_status ""
    print_status "You can now use:"
    print_status "  sudo systemctl start mvidarr    # Start the service"
    print_status "  sudo systemctl stop mvidarr     # Stop the service"  
    print_status "  sudo systemctl restart mvidarr  # Restart the service"
    print_status "  sudo systemctl status mvidarr   # Check service status"
    print_status "  sudo journalctl -u mvidarr -f   # View live logs"
    
    # Show service status
    systemctl status "$SERVICE_NAME.service" --no-pager
}

# Uninstall the systemd service
uninstall_service() {
    print_status "Uninstalling MVidarr systemd service..."
    
    # Stop service if running
    if systemctl is-active --quiet "$SERVICE_NAME.service"; then
        print_status "Stopping service..."
        systemctl stop "$SERVICE_NAME.service"
    fi
    
    # Disable service
    if systemctl is-enabled --quiet "$SERVICE_NAME.service"; then
        print_status "Disabling service..."
        systemctl disable "$SERVICE_NAME.service"
    fi
    
    # Remove service file
    if [ -f "$SYSTEMD_DIR/$SERVICE_NAME.service" ]; then
        rm "$SYSTEMD_DIR/$SERVICE_NAME.service"
        print_status "Service file removed"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Service uninstalled successfully"
}

# Start the service
start_service() {
    print_status "Starting MVidarr service..."
    systemctl start "$SERVICE_NAME.service"
    
    # Check if service started successfully
    if systemctl is-active --quiet "$SERVICE_NAME.service"; then
        print_status "Service started successfully"
    else
        print_error "Failed to start service"
        print_error "Check logs with: sudo journalctl -u $SERVICE_NAME.service"
    fi
}

# Stop the service
stop_service() {
    print_status "Stopping MVidarr service..."
    systemctl stop "$SERVICE_NAME.service"
    
    if ! systemctl is-active --quiet "$SERVICE_NAME.service"; then
        print_status "Service stopped successfully"
    else
        print_error "Failed to stop service"
    fi
}

# Restart the service
restart_service() {
    print_status "Restarting MVidarr service..."
    systemctl restart "$SERVICE_NAME.service"
    
    if systemctl is-active --quiet "$SERVICE_NAME.service"; then
        print_status "Service restarted successfully"
    else
        print_error "Failed to restart service"
        print_error "Check logs with: sudo journalctl -u $SERVICE_NAME.service"
    fi
}

# Show service status
status_service() {
    print_status "MVidarr service status:"
    systemctl status "$SERVICE_NAME.service" --no-pager
}

# Show service logs
logs_service() {
    if [ "$1" = "follow" ]; then
        journalctl -u "$SERVICE_NAME.service" -f
    else
        journalctl -u "$SERVICE_NAME.service" -n 50
    fi
}

# Enable service for autostart
enable_service() {
    print_status "Enabling MVidarr service for autostart..."
    systemctl enable "$SERVICE_NAME.service"
    
    if systemctl is-enabled --quiet "$SERVICE_NAME.service"; then
        print_status "Service enabled for autostart"
    else
        print_error "Failed to enable service"
    fi
}

# Disable service autostart
disable_service() {
    print_status "Disabling MVidarr service autostart..."
    systemctl disable "$SERVICE_NAME.service"
    
    if ! systemctl is-enabled --quiet "$SERVICE_NAME.service"; then
        print_status "Service autostart disabled"
    else
        print_error "Failed to disable service"
    fi
}

# Show help
show_help() {
    echo "MVidarr Enhanced Systemd Service Management"
    echo "Usage: sudo $0 {install|uninstall|start|stop|restart|status|logs|enable|disable|help}"
    echo ""
    echo "Commands:"
    echo "  install    Install and enable the systemd service"
    echo "  uninstall  Stop, disable, and remove the systemd service"
    echo "  start      Start the service"
    echo "  stop       Stop the service"
    echo "  restart    Restart the service"
    echo "  status     Show service status"
    echo "  logs       Show recent service logs"
    echo "  logs-f     Follow service logs (journalctl -f)"
    echo "  enable     Enable service for autostart"
    echo "  disable    Disable service autostart"
    echo "  help       Show this help message"
    echo ""
    echo "Note: This script must be run as root (use sudo)"
}

# Main script logic
case "$1" in
    install)
        check_root
        install_service
        ;;
    uninstall)
        check_root
        uninstall_service
        ;;
    start)
        check_root
        start_service
        ;;
    stop)
        check_root
        stop_service
        ;;
    restart)
        check_root
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        logs_service
        ;;
    logs-f)
        logs_service follow
        ;;
    enable)
        check_root
        enable_service
        ;;
    disable)
        check_root
        disable_service
        ;;
    help)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

exit $?