#!/bin/bash

# MVidarr Enhanced Docker Setup Script
# Automated Docker deployment setup for production and development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEPLOY_TYPE="production"
FORCE_SETUP=false
SKIP_BUILD=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "MVidarr Enhanced Docker Setup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE           Deployment type: production or development (default: production)"
    echo "  -f, --force              Force setup even if containers are running"
    echo "  -s, --skip-build         Skip Docker image building"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                       # Production setup"
    echo "  $0 -t development        # Development setup"
    echo "  $0 -f                    # Force production setup"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            DEPLOY_TYPE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_SETUP=true
            shift
            ;;
        -s|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate deployment type
if [[ "$DEPLOY_TYPE" != "production" && "$DEPLOY_TYPE" != "development" ]]; then
    print_error "Invalid deployment type: $DEPLOY_TYPE"
    print_error "Must be 'production' or 'development'"
    exit 1
fi

print_status "Starting MVidarr Enhanced Docker setup for $DEPLOY_TYPE environment"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

# Set compose file based on deployment type
if [[ "$DEPLOY_TYPE" == "development" ]]; then
    COMPOSE_FILE="docker-compose.dev.yml"
    ENV_FILE="docker-compose.env.example"
    CONTAINER_PREFIX="mvidarr-dev"
else
    COMPOSE_FILE="docker-compose.production.yml"
    ENV_FILE="docker-compose.env.example"
    CONTAINER_PREFIX="mvidarr"
fi

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    print_error "Docker Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    print_status "Creating .env file from template..."
    cp "$ENV_FILE" ".env"
    print_warning "Please edit .env file with your configuration before proceeding"
    print_warning "Pay special attention to passwords, API keys, and storage paths"
fi

# Check if containers are already running
if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    if [[ "$FORCE_SETUP" == "false" ]]; then
        print_warning "Containers are already running. Use -f/--force to override."
        exit 1
    else
        print_status "Stopping existing containers..."
        docker-compose -f "$COMPOSE_FILE" down
    fi
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/{database,musicvideos,thumbnails,logs,cache,backups}
mkdir -p docker/mariadb

# Set proper permissions
chmod 755 data/
chmod 755 data/*

# Create MariaDB configuration if it doesn't exist
if [[ ! -f "docker/mariadb/my.cnf" ]]; then
    print_status "Creating MariaDB configuration..."
    cat > docker/mariadb/my.cnf << 'EOF'
[mysqld]
# Character set and collation
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Connection settings
max_connections = 200
wait_timeout = 28800
interactive_timeout = 28800

# Performance tuning
innodb_buffer_pool_size = 256M
innodb_log_file_size = 64M
innodb_flush_method = O_DIRECT
innodb_file_per_table = 1

# Logging
general_log = 0
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# Security
bind-address = 0.0.0.0
EOF
fi

# Create MariaDB initialization script if it doesn't exist
if [[ ! -f "docker/mariadb/init.sql" ]]; then
    print_status "Creating MariaDB initialization script..."
    cat > docker/mariadb/init.sql << 'EOF'
-- MVidarr Enhanced Database Initialization Script

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS mvidarr_enhanced 
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create development database if needed
CREATE DATABASE IF NOT EXISTS mvidarr_dev 
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant privileges
GRANT ALL PRIVILEGES ON mvidarr_enhanced.* TO 'mvidarr'@'%';
GRANT ALL PRIVILEGES ON mvidarr_dev.* TO 'mvidarr'@'%';

-- Flush privileges
FLUSH PRIVILEGES;

-- Create indexes for performance
USE mvidarr_enhanced;

-- These tables will be created by the application, but we can pre-optimize

-- Optimize for artist searches
-- CREATE INDEX IF NOT EXISTS idx_artist_name ON artists(name);
-- CREATE INDEX IF NOT EXISTS idx_artist_created ON artists(created_at);

-- Optimize for video searches  
-- CREATE INDEX IF NOT EXISTS idx_video_title ON videos(title);
-- CREATE INDEX IF NOT EXISTS idx_video_artist ON videos(artist_id);
-- CREATE INDEX IF NOT EXISTS idx_video_status ON videos(status);
-- CREATE INDEX IF NOT EXISTS idx_video_created ON videos(created_at);

-- Optimize for authentication
-- CREATE INDEX IF NOT EXISTS idx_user_username ON users(username);
-- CREATE INDEX IF NOT EXISTS idx_session_token ON user_sessions(session_token);
-- CREATE INDEX IF NOT EXISTS idx_session_expires ON user_sessions(expires_at);
EOF
fi

# Build Docker images if not skipping
if [[ "$SKIP_BUILD" == "false" ]]; then
    print_status "Building Docker images..."
    
    if [[ "$DEPLOY_TYPE" == "development" ]]; then
        # Create development Dockerfile if it doesn't exist
        if [[ ! -f "Dockerfile.development" ]]; then
            print_status "Creating development Dockerfile..."
            cp Dockerfile.production Dockerfile.development
            # Modify for development (add hot reload, debug mode, etc.)
            sed -i 's/FLASK_ENV=production/FLASK_ENV=development/' Dockerfile.development
            sed -i 's/DEBUG=false/DEBUG=true/' Dockerfile.development
        fi
    fi
    
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    print_success "Docker images built successfully"
else
    print_status "Skipping Docker image build"
fi

# Start containers
print_status "Starting containers..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 10

# Check container health
MAX_RETRIES=30
RETRY_COUNT=0

while [[ $RETRY_COUNT -lt $MAX_RETRIES ]]; do
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "healthy\|Up"; then
        break
    fi
    
    print_status "Waiting for containers to be healthy... ($((RETRY_COUNT + 1))/$MAX_RETRIES)"
    sleep 5
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [[ $RETRY_COUNT -eq $MAX_RETRIES ]]; then
    print_error "Containers failed to become healthy within expected time"
    print_error "Check logs with: docker-compose -f $COMPOSE_FILE logs"
    exit 1
fi

# Initialize database
print_status "Initializing database..."
if [[ "$DEPLOY_TYPE" == "development" ]]; then
    CONTAINER_NAME="${CONTAINER_PREFIX}-dev"
else
    CONTAINER_NAME="${CONTAINER_PREFIX}-enhanced"
fi

# Run database initialization inside container
docker exec "$CONTAINER_NAME" python3 scripts/setup_database.sh || true
docker exec "$CONTAINER_NAME" python3 scripts/init_auth_database.py || true

# Show status
print_success "Setup completed successfully!"
print_status "Container status:"
docker-compose -f "$COMPOSE_FILE" ps

print_status "Application URLs:"
if [[ "$DEPLOY_TYPE" == "development" ]]; then
    echo "  - MVidarr Enhanced: http://localhost:5000"
    echo "  - PHPMyAdmin: http://localhost:8080"
    echo "  - MariaDB: localhost:3307"
else
    echo "  - MVidarr Enhanced: http://localhost:5000"
    echo "  - MariaDB: localhost:3306"
fi

print_status "Useful commands:"
echo "  - View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  - Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  - Restart services: docker-compose -f $COMPOSE_FILE restart"
echo "  - Enter container: docker exec -it $CONTAINER_NAME bash"

print_success "MVidarr Enhanced is now running in $DEPLOY_TYPE mode!"