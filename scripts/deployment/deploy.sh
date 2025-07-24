#!/bin/bash
"""
MVidarr Enhanced - Automated Deployment Script
Handles deployment to staging and production environments.
"""

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCKER_REGISTRY="ghcr.io"
IMAGE_NAME="mvidarr-enhanced"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
MVidarr Enhanced Deployment Script

Usage: $0 <environment> [options]

Environments:
    staging     Deploy to staging environment
    production  Deploy to production environment
    local       Deploy locally for testing

Options:
    -t, --tag <tag>         Docker image tag to deploy (default: latest)
    -f, --force             Force deployment without confirmation
    -r, --rollback          Rollback to previous deployment
    -h, --help              Show this help message
    --health-check          Perform health check only
    --backup-db             Backup database before deployment
    --migrate-db            Run database migrations

Examples:
    $0 staging
    $0 production --tag v1.2.0 --backup-db
    $0 local --force
    $0 production --rollback

EOF
}

# Parse arguments
ENVIRONMENT=""
IMAGE_TAG="latest"
FORCE_DEPLOY=false
ROLLBACK=false
HEALTH_CHECK_ONLY=false
BACKUP_DB=false
MIGRATE_DB=false

while [[ $# -gt 0 ]]; do
    case $1 in
        staging|production|local)
            ENVIRONMENT="$1"
            shift
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_DEPLOY=true
            shift
            ;;
        -r|--rollback)
            ROLLBACK=true
            shift
            ;;
        --health-check)
            HEALTH_CHECK_ONLY=true
            shift
            ;;
        --backup-db)
            BACKUP_DB=true
            shift
            ;;
        --migrate-db)
            MIGRATE_DB=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment is required"
    show_help
    exit 1
fi

# Load environment-specific configuration
load_environment_config() {
    case "$ENVIRONMENT" in
        local)
            COMPOSE_FILE="docker-compose.dev.yml"
            APP_URL="http://localhost:5000"
            DB_BACKUP_DIR="./backups"
            ;;
        staging)
            COMPOSE_FILE="docker-compose.staging.yml"
            APP_URL="${STAGING_URL:-http://staging.mvidarr.local:5000}"
            DB_BACKUP_DIR="/var/backups/mvidarr-staging"
            ;;
        production)
            COMPOSE_FILE="docker-compose.production.yml"
            APP_URL="${PRODUCTION_URL:-https://mvidarr.example.com}"
            DB_BACKUP_DIR="/var/backups/mvidarr-production"
            ;;
    esac
    
    FULL_IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    log_info "Configuration loaded:"
    log_info "  Environment: $ENVIRONMENT"
    log_info "  Compose file: $COMPOSE_FILE"
    log_info "  Image: $FULL_IMAGE_NAME"
    log_info "  App URL: $APP_URL"
}

# Health check function
perform_health_check() {
    log_info "Performing health check..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -sf "$APP_URL/api/health" > /dev/null 2>&1; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 10s..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Database backup function
backup_database() {
    if [[ "$BACKUP_DB" != true ]]; then
        return 0
    fi
    
    log_info "Creating database backup..."
    
    # Create backup directory
    mkdir -p "$DB_BACKUP_DIR"
    
    # Generate backup filename with timestamp
    local backup_file="$DB_BACKUP_DIR/mvidarr-backup-$(date +%Y%m%d-%H%M%S).sql"
    
    # Create backup using docker-compose
    if docker-compose -f "$COMPOSE_FILE" exec -T db mysqldump -u root -p"${MYSQL_ROOT_PASSWORD:-mvidarr}" mvidarr > "$backup_file"; then
        log_success "Database backup created: $backup_file"
        
        # Keep only last 10 backups
        find "$DB_BACKUP_DIR" -name "mvidarr-backup-*.sql" -type f -printf '%T@ %p\n' | sort -rn | tail -n +11 | cut -d' ' -f2- | xargs -r rm
        
        return 0
    else
        log_error "Database backup failed"
        return 1
    fi
}

# Database migration function
migrate_database() {
    if [[ "$MIGRATE_DB" != true ]]; then
        return 0
    fi
    
    log_info "Running database migrations..."
    
    # Run migrations using the app container
    if docker-compose -f "$COMPOSE_FILE" exec -T app python scripts/migrations/add_authentication_tables.py && \
       docker-compose -f "$COMPOSE_FILE" exec -T app python scripts/migrations/add_genre_columns.py; then
        log_success "Database migrations completed"
        return 0
    else
        log_error "Database migrations failed"
        return 1
    fi
}

# Rollback function
perform_rollback() {
    log_info "Performing rollback..."
    
    # Get previous image tag
    local previous_tag
    previous_tag=$(docker-compose -f "$COMPOSE_FILE" images app | awk 'NR==2 {print $3}' | sed 's/.*://')
    
    if [[ -z "$previous_tag" ]]; then
        log_error "No previous deployment found for rollback"
        return 1
    fi
    
    log_info "Rolling back to tag: $previous_tag"
    
    # Set rollback tag and deploy
    IMAGE_TAG="$previous_tag"
    FULL_IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    deploy_application
}

# Main deployment function
deploy_application() {
    log_info "Starting deployment..."
    
    # Pull latest image
    log_info "Pulling Docker image: $FULL_IMAGE_NAME"
    if ! docker pull "$FULL_IMAGE_NAME"; then
        log_error "Failed to pull Docker image"
        return 1
    fi
    
    # Update docker-compose file with new image
    export MVIDARR_IMAGE="$FULL_IMAGE_NAME"
    
    # Stop services gracefully
    log_info "Stopping services..."
    docker-compose -f "$COMPOSE_FILE" stop app
    
    # Start services
    log_info "Starting services with new image..."
    if docker-compose -f "$COMPOSE_FILE" up -d; then
        log_success "Services started successfully"
    else
        log_error "Failed to start services"
        return 1
    fi
    
    # Wait for services to be ready
    sleep 30
    
    # Run health check
    if perform_health_check; then
        log_success "Deployment completed successfully"
        
        # Clean up old images
        log_info "Cleaning up old Docker images..."
        docker image prune -f
        
        return 0
    else
        log_error "Deployment failed health check"
        return 1
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if docker-compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker compose file not found: $COMPOSE_FILE"
        return 1
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        return 1
    fi
    
    # Check if we can access the registry
    if ! docker pull hello-world > /dev/null 2>&1; then
        log_error "Cannot access Docker registry"
        return 1
    fi
    
    log_success "Pre-deployment checks passed"
    return 0
}

# Confirmation prompt
confirm_deployment() {
    if [[ "$FORCE_DEPLOY" == true ]]; then
        return 0
    fi
    
    echo
    log_warning "You are about to deploy to: $ENVIRONMENT"
    log_warning "Image: $FULL_IMAGE_NAME"
    log_warning "This will restart the application services."
    echo
    
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
}

# Main execution
main() {
    log_info "MVidarr Enhanced Deployment Script"
    echo "======================================"
    
    # Load configuration
    load_environment_config
    
    # Handle health check only mode
    if [[ "$HEALTH_CHECK_ONLY" == true ]]; then
        perform_health_check
        exit $?
    fi
    
    # Handle rollback
    if [[ "$ROLLBACK" == true ]]; then
        confirm_deployment
        perform_rollback
        exit $?
    fi
    
    # Run pre-deployment checks
    if ! pre_deployment_checks; then
        exit 1
    fi
    
    # Confirm deployment
    confirm_deployment
    
    # Backup database if requested
    if ! backup_database; then
        log_error "Database backup failed, deployment aborted"
        exit 1
    fi
    
    # Deploy application
    if deploy_application; then
        # Run migrations if requested
        if ! migrate_database; then
            log_warning "Database migrations failed, but deployment was successful"
        fi
        
        log_success "Deployment to $ENVIRONMENT completed successfully!"
        log_info "Application is available at: $APP_URL"
    else
        log_error "Deployment failed!"
        exit 1
    fi
}

# Run main function
main "$@"