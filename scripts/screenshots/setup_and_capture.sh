#!/bin/bash
# MVidarr Enhanced - Screenshot Capture Setup and Execution
set -e

echo "🚀 MVidarr Enhanced Screenshot Capture"
echo "======================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if MVidarr is running
check_mvidarr_running() {
    print_status "Checking if MVidarr Enhanced is running..."
    
    if curl -s -f http://localhost:5000/api/health > /dev/null 2>&1; then
        print_success "MVidarr Enhanced is running and healthy"
        return 0
    elif curl -s -f http://localhost:5000 > /dev/null 2>&1; then
        print_success "MVidarr Enhanced is running"
        return 0
    else
        print_error "MVidarr Enhanced is not running or not accessible at http://localhost:5000"
        print_status "Please start MVidarr Enhanced before running screenshot capture"
        print_status "Docker: docker-compose -f docker-compose.production.yml up -d"
        print_status "Local: python app.py"
        return 1
    fi
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Check if we're in a virtual environment
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "No virtual environment detected"
        print_status "Installing globally (you may need sudo)"
    fi
    
    pip install playwright
    
    print_status "Installing Playwright browsers..."
    playwright install chromium
    
    print_success "Dependencies installed successfully"
}

# Capture screenshots
capture_screenshots() {
    local priority="$1"
    local extra_args="$2"
    
    print_status "Starting screenshot capture..."
    print_status "Priority filter: ${priority:-all}"
    
    cd "$SCRIPT_DIR"
    
    # Build command
    local cmd="python capture_screenshots.py"
    
    if [[ -n "$priority" ]]; then
        cmd="$cmd --priority $priority"
    fi
    
    if [[ -n "$extra_args" ]]; then
        cmd="$cmd $extra_args"
    fi
    
    print_status "Running: $cmd"
    
    if $cmd; then
        print_success "Screenshot capture completed successfully"
        return 0
    else
        print_error "Screenshot capture failed"
        return 1
    fi
}

# Main function
main() {
    local priority=""
    local extra_args=""
    local skip_deps=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --priority)
                priority="$2"
                shift 2
                ;;
            --skip-deps)
                skip_deps=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --priority LEVEL    Capture only screenshots with specific priority (high/medium/low)"
                echo "  --skip-deps        Skip dependency installation"
                echo "  --help, -h         Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                           # Capture all screenshots"
                echo "  $0 --priority high          # Capture only high priority screenshots"
                echo "  $0 --skip-deps              # Skip dependency installation"
                exit 0
                ;;
            *)
                extra_args="$extra_args $1"
                shift
                ;;
        esac
    done
    
    print_status "Starting MVidarr Enhanced screenshot capture process"
    
    # Check if MVidarr is running
    if ! check_mvidarr_running; then
        exit 1
    fi
    
    # Install dependencies unless skipped
    if [[ "$skip_deps" != true ]]; then
        if ! install_dependencies; then
            print_error "Failed to install dependencies"
            exit 1
        fi
    else
        print_status "Skipping dependency installation"
    fi
    
    # Capture screenshots
    if capture_screenshots "$priority" "$extra_args"; then
        print_success "Screenshot capture process completed successfully!"
        print_status "Screenshots saved to: $PROJECT_ROOT/docs/screenshots/"
        print_status "Check capture_report.md for detailed results"
    else
        print_error "Screenshot capture process failed"
        exit 1
    fi
}

# Handle Ctrl+C gracefully
trap 'print_warning "Screenshot capture interrupted"; exit 130' INT

# Run main function
main "$@"