#!/bin/bash

# MVidarr Enhanced Database Setup Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[MVIDARR]${NC} $1"
}

# Load database configuration from .env
load_config() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
    else
        print_error ".env file not found. Please run './scripts/manage_service.sh install' first."
        exit 1
    fi
}

# Check if MySQL/MariaDB is running
check_mysql() {
    if ! systemctl is-active --quiet mariadb && ! systemctl is-active --quiet mysql; then
        print_error "MariaDB/MySQL is not running"
        print_error "Start it with: sudo systemctl start mariadb"
        exit 1
    fi
    print_status "MariaDB/MySQL is running"
}

# Setup database and user
setup_database() {
    print_header "MVidarr Database Setup"
    echo "This script will create the database and user for MVidarr Enhanced"
    echo ""
    
    load_config
    check_mysql
    
    print_status "Database configuration:"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    echo "  Host: $DB_HOST"
    echo ""
    
    # Prompt for root password
    echo -n "Enter MySQL/MariaDB root password: "
    read -s ROOT_PASSWORD
    echo ""
    
    # Test root connection
    if ! mysql -u root -p"$ROOT_PASSWORD" -e "SELECT 1;" &>/dev/null; then
        print_error "Failed to connect as root. Please check your password."
        exit 1
    fi
    
    print_status "Connected as root successfully"
    
    # Create database and user
    print_status "Creating database and user..."
    
    mysql -u root -p"$ROOT_PASSWORD" << EOF
-- Create database
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (drop if exists first)
DROP USER IF EXISTS '$DB_USER'@'$DB_HOST';
CREATE USER '$DB_USER'@'$DB_HOST' IDENTIFIED BY '$DB_PASSWORD';

-- Grant privileges
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'$DB_HOST';
FLUSH PRIVILEGES;

-- Show databases and users
SHOW DATABASES LIKE '$DB_NAME';
SELECT User, Host FROM mysql.user WHERE User = '$DB_USER';
EOF
    
    if [ $? -eq 0 ]; then
        print_status "Database and user created successfully!"
        
        # Test user connection
        print_status "Testing user connection..."
        if mysql -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" "$DB_NAME" -e "SELECT 1;" &>/dev/null; then
            print_status "User connection test successful!"
            echo ""
            print_status "You can now run: ./scripts/manage_service.sh init-db"
        else
            print_error "User connection test failed"
            exit 1
        fi
    else
        print_error "Failed to create database and user"
        exit 1
    fi
}

# Show current database status
show_status() {
    load_config
    
    print_header "Database Status"
    echo ""
    
    print_status "Configuration from .env:"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    echo "  Host: $DB_HOST"
    echo ""
    
    # Check if database exists
    if mysql -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" "$DB_NAME" -e "SELECT 1;" &>/dev/null; then
        print_status "Database connection: ✓ SUCCESS"
        
        # Check tables
        TABLE_COUNT=$(mysql -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" "$DB_NAME" -e "SHOW TABLES;" 2>/dev/null | wc -l)
        if [ $TABLE_COUNT -gt 1 ]; then
            print_status "Tables: ✓ $(($TABLE_COUNT - 1)) tables found"
        else
            print_warning "Tables: No tables found - run init-db"
        fi
    else
        print_error "Database connection: ✗ FAILED"
        print_warning "Run: $0 setup"
    fi
}

# Show help
show_help() {
    echo "MVidarr Enhanced Database Setup"
    echo "Usage: $0 {setup|status|help}"
    echo ""
    echo "Commands:"
    echo "  setup      Setup database and user"
    echo "  status     Show database status"
    echo "  help       Show this help message"
    echo ""
    echo "Prerequisites:"
    echo "  - MariaDB/MySQL installed and running"
    echo "  - .env file configured (run ./scripts/manage_service.sh install)"
    echo "  - MySQL root password"
}

# Main script logic
case "$1" in
    setup)
        setup_database
        ;;
    status)
        show_status
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