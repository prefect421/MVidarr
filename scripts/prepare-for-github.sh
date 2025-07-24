#!/bin/bash
# MVidarr Enhanced - GitHub Release Preparation Script
# This script removes user-specific data and configurations for public release

set -e

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

echo "🚀 MVidarr Enhanced - GitHub Release Preparation"
echo "================================================="

# Check if we're in the correct directory
if [ ! -f "app.py" ]; then
    print_error "This script must be run from the MVidarr root directory"
    exit 1
fi

# Create backup of sensitive files
print_status "Creating backup of sensitive files..."
mkdir -p .github-prep-backup
cp -r data/ .github-prep-backup/ 2>/dev/null || true
cp .env .github-prep-backup/ 2>/dev/null || true

# Remove user-specific database file
print_status "Removing user-specific database file..."
if [ -f "data/mvidarr.db" ]; then
    rm -f data/mvidarr.db
    print_success "Removed user database file"
fi

# Remove downloaded music videos
print_status "Removing downloaded music videos..."
if [ -d "data/downloads" ]; then
    rm -rf data/downloads/*
    print_success "Cleared downloads directory"
fi

if [ -d "data/musicvideos" ]; then
    rm -rf data/musicvideos/*
    print_success "Cleared music videos directory"
fi

# Remove thumbnail cache
print_status "Removing thumbnail cache..."
if [ -d "data/thumbnails" ]; then
    rm -rf data/thumbnails/*
    print_success "Cleared thumbnails directory"
fi

# Remove log files
print_status "Removing log files..."
if [ -d "data/logs" ]; then
    rm -rf data/logs/*
    print_success "Cleared logs directory"
fi

# Remove cache files
print_status "Removing cache files..."
if [ -d "data/cache" ]; then
    rm -rf data/cache/*
    print_success "Cleared cache directory"
fi

# Remove backup files
print_status "Removing backup files..."
if [ -d "data/backups" ]; then
    rm -rf data/backups/*
    print_success "Cleared backups directory"
fi

# Remove environment file if it exists
print_status "Removing environment file..."
if [ -f ".env" ]; then
    rm -f .env
    print_success "Removed .env file"
fi

# Remove any temporary files
print_status "Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*.backup" -delete 2>/dev/null || true
find . -name "*.old" -delete 2>/dev/null || true

# Remove Python cache files
print_status "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove IDE files
print_status "Removing IDE files..."
rm -rf .vscode/ 2>/dev/null || true
rm -rf .idea/ 2>/dev/null || true
rm -f *.swp *.swo 2>/dev/null || true

# Remove OS-specific files
print_status "Removing OS-specific files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true

# Create placeholder files to maintain directory structure
print_status "Creating placeholder files for directory structure..."

# Create placeholder files for key directories
touch data/downloads/.gitkeep
touch data/thumbnails/.gitkeep
touch data/logs/.gitkeep
touch data/cache/.gitkeep
touch data/backups/.gitkeep

# Create example configuration files
print_status "Creating example configuration files..."

# Create example environment file
cat > .env.example << 'EOF'
# MVidarr Enhanced - Environment Configuration
# Copy this file to .env and configure your settings

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=mvidarr
DB_PASSWORD=your_secure_password_here
DB_NAME=mvidarr

# Application Configuration
SECRET_KEY=your_very_long_and_secure_secret_key_here
DEBUG=false
PORT=5000
HOST=localhost

# External API Keys
IMVDB_API_KEY=your_imvdb_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here

# Spotify Integration (optional)
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# Download Configuration
DOWNLOAD_DIRECTORY=data/downloads
THUMBNAIL_DIRECTORY=data/thumbnails
CACHE_DIRECTORY=data/cache

# MeTube Configuration
METUBE_HOST=localhost
METUBE_PORT=8081

# Theme Configuration
DEFAULT_THEME=default
THEME_PARK_ENABLED=true
EOF

# Create example Docker environment file
cat > .env.docker.example << 'EOF'
# MVidarr Enhanced - Docker Environment Configuration
# Copy this file to .env for Docker deployment

# Database Configuration
DB_PASSWORD=your_secure_db_password_here
MYSQL_ROOT_PASSWORD=your_secure_root_password_here

# Application Configuration
SECRET_KEY=your_very_long_and_secure_secret_key_here
DEBUG=false

# External API Keys
IMVDB_API_KEY=your_imvdb_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here

# Spotify Integration (optional)
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# Server Configuration
SERVER_HOST=localhost
SERVER_PORT=5000

# Security Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
ALLOWED_HOSTS=localhost,127.0.0.1

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/app/data/logs/mvidarr.log

# MeTube Configuration
METUBE_HOST=metube
METUBE_PORT=8081

# Theme Configuration
DEFAULT_THEME=default
THEME_PARK_ENABLED=true
EOF

# Create setup instructions
cat > SETUP.md << 'EOF'
# MVidarr Enhanced - Setup Instructions

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/prefect421/MVidarr.git
cd MVidarr
```

### 2. Choose Your Deployment Method

#### Option A: Docker Deployment (Recommended)
```bash
# Copy environment template
cp .env.docker.example .env

# Edit .env with your configuration
nano .env

# Run setup script
./docker-setup.sh prod
```

#### Option B: Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env

# Initialize database
python3 scripts/setup_database.sh

# Run application
python3 app.py
```

### 3. Configuration

#### Required Settings
- **Database**: Configure MariaDB/MySQL connection
- **Secret Key**: Generate a secure secret key
- **IMVDB API Key**: Get from https://imvdb.com/developers

#### Optional Settings
- **YouTube API Key**: For YouTube integration
- **Spotify Client ID/Secret**: For Spotify playlist import

### 4. Access the Application

- **Web Interface**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/docs

## For detailed documentation, see the README.md file.
EOF

# Remove any sensitive data from configuration files
print_status "Sanitizing configuration files..."

# Remove any API keys or sensitive data from source files
find src/ -name "*.py" -exec sed -i 's/client_id=[^,)]*/client_id="YOUR_CLIENT_ID_HERE"/g' {} \; 2>/dev/null || true
find src/ -name "*.py" -exec sed -i 's/client_secret=[^,)]*/client_secret="YOUR_CLIENT_SECRET_HERE"/g' {} \; 2>/dev/null || true
find src/ -name "*.py" -exec sed -i 's/api_key=[^,)]*/api_key="YOUR_API_KEY_HERE"/g' {} \; 2>/dev/null || true

# Clear sensitive API keys from database settings
print_status "Clearing sensitive API keys from database..."
curl -s -X PUT "http://localhost:5000/api/settings/spotify_client_id" \
  -H "Content-Type: application/json" \
  -d '{"value": ""}' > /dev/null 2>&1 || true
curl -s -X PUT "http://localhost:5000/api/settings/spotify_client_secret" \
  -H "Content-Type: application/json" \
  -d '{"value": ""}' > /dev/null 2>&1 || true
curl -s -X PUT "http://localhost:5000/api/settings/imvdb_api_key" \
  -H "Content-Type: application/json" \
  -d '{"value": ""}' > /dev/null 2>&1 || true
curl -s -X PUT "http://localhost:5000/api/settings/youtube_api_key" \
  -H "Content-Type: application/json" \
  -d '{"value": ""}' > /dev/null 2>&1 || true

# Update any hardcoded paths to use relative paths
find src/ -name "*.py" -exec sed -i 's|/home/[^/]*/mvidarr|/app|g' {} \; 2>/dev/null || true

# Create .gitignore for the release
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Application data
data/downloads/*
data/musicvideos/*
data/thumbnails/*
data/logs/*
data/cache/*
data/backups/*
*.db
*.sqlite
*.sqlite3

# Configuration
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# Temporary files
*.tmp
*.temp
*.bak
*.backup
*.old

# Media files
*.mp4
*.avi
*.mov
*.wmv
*.flv
*.webm
*.mkv
*.mp3
*.wav
*.flac
*.m4a

# Backup files
.github-prep-backup/
EOF

# Create release notes template
cat > RELEASE_NOTES.md << 'EOF'
# MVidarr Enhanced - Release Notes

## Version X.X.X - YYYY-MM-DD

### New Features
- List new features here

### Improvements
- List improvements here

### Bug Fixes
- List bug fixes here

### Breaking Changes
- List any breaking changes here

### Known Issues
- List any known issues here

### Installation Notes
- Any special installation instructions
EOF

print_success "GitHub release preparation completed!"
print_status "Summary of actions performed:"
echo "  ✅ Removed user-specific database file"
echo "  ✅ Cleared download directories"
echo "  ✅ Removed thumbnail cache"
echo "  ✅ Cleared log files"
echo "  ✅ Removed cache files"
echo "  ✅ Removed environment file"
echo "  ✅ Cleaned temporary files"
echo "  ✅ Removed Python cache files"
echo "  ✅ Created placeholder files"
echo "  ✅ Created example configuration files"
echo "  ✅ Created setup instructions"
echo "  ✅ Updated .gitignore"
echo "  ✅ Created release notes template"

print_warning "Backup of sensitive files created in .github-prep-backup/"
print_warning "Review all files before committing to GitHub"
print_warning "Update README.md with current feature list and installation instructions"

echo ""
print_status "Next steps:"
echo "1. Review and update README.md"
echo "2. Update version numbers in relevant files"
echo "3. Test the Docker setup with clean configuration"
echo "4. Create GitHub repository and push code"
echo "5. Set up GitHub Actions CI/CD pipeline"
echo "6. Create release tags and documentation"