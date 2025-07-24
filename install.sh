#!/bin/bash

# MVidarr Enhanced Installation Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

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

print_header "MVidarr Enhanced Installation"
echo "=============================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root"
    exit 1
fi

# Check system requirements
print_status "Checking system requirements..."

# Check Python 3
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    print_error "Please install Python 3: sudo apt install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_status "Python version: $PYTHON_VERSION"

# Check pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed"
    print_error "Please install pip3: sudo apt install python3-pip"
    exit 1
fi

# Install dependencies
print_status "Installing Python dependencies..."

# Try different installation methods
if pip3 install --break-system-packages -r requirements.txt 2>/dev/null; then
    print_status "Dependencies installed with --break-system-packages"
elif pip3 install --user -r requirements.txt 2>/dev/null; then
    print_status "Dependencies installed with --user"
elif python3 -m venv venv 2>/dev/null && source venv/bin/activate && pip install -r requirements.txt; then
    print_status "Dependencies installed in virtual environment"
else
    print_error "Failed to install dependencies"
    print_error "Please try manually:"
    print_error "pip3 install --break-system-packages -r requirements.txt"
    exit 1
fi

# Create necessary directories
print_status "Creating application directories..."
mkdir -p data/{logs,downloads,thumbnails,cache,backups}
mkdir -p frontend/static

# Check for MariaDB/MySQL
print_status "Checking database requirements..."
if command -v mysql &> /dev/null; then
    print_status "MySQL/MariaDB client found"
else
    print_warning "MySQL/MariaDB client not found"
    print_warning "Install with: sudo apt install mariadb-client"
fi

# Make scripts executable
print_status "Setting script permissions..."
chmod +x scripts/manage_service.sh

# Create environment file template
if [ ! -f .env ]; then
    print_status "Creating environment configuration template..."
    cat > .env << 'EOF'
# MVidarr Enhanced Configuration

# Database configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mvidarr
DB_USER=mvidarr
DB_PASSWORD=change_me_to_your_password

# Application settings
PORT=5000
DEBUG=false
SECRET_KEY=change_me_to_random_string_for_production

# External services
IMVDB_API_KEY=
YOUTUBE_API_KEY=
METUBE_HOST=localhost
METUBE_PORT=8081

# Logging
LOG_LEVEL=INFO
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Database connection pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
EOF
    print_status "Environment file created: .env"
    print_warning "Please edit .env file with your database credentials"
else
    print_status "Environment file already exists"
fi

# Installation complete
print_header "Installation Complete!"
echo "=============================================="
print_status "MVidarr Enhanced has been installed successfully"
echo ""
print_status "Next steps:"
echo "1. Install MariaDB/MySQL if not already installed:"
echo "   sudo apt install mariadb-server"
echo ""
echo "2. Create database and user:"
echo "   sudo mysql -u root -p"
echo "   CREATE DATABASE mvidarr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "   CREATE USER 'mvidarr'@'localhost' IDENTIFIED BY 'your_password';"
echo "   GRANT ALL PRIVILEGES ON mvidarr.* TO 'mvidarr'@'localhost';"
echo "   FLUSH PRIVILEGES;"
echo "   EXIT;"
echo ""
echo "3. Edit .env file with your database credentials"
echo ""
echo "4. Initialize database:"
echo "   ./scripts/manage_service.sh init-db"
echo ""
echo "5. Start the service:"
echo "   ./scripts/manage_service.sh start"
echo ""
echo "6. Access the web interface:"
echo "   http://localhost:5000"
echo ""
print_status "For help: ./scripts/manage_service.sh help"