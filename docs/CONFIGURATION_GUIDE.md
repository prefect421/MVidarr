# MVidarr Configuration Guide

## Overview

This guide provides comprehensive instructions for configuring MVidarr, including settings management, API integrations, security configuration, and optimization options. MVidarr uses a flexible database-driven configuration system with web UI management and environment variable support.

## 🏗️ Configuration Architecture

### Configuration Hierarchy
1. **Database Settings** (Primary) - Managed via web UI, stored in database
2. **Environment Variables** (Fallback) - Used when database is unavailable  
3. **Default Values** - Built-in application defaults

### Settings Management
- **Web Interface**: `Settings` page with tabbed organization
- **API Access**: RESTful endpoints for programmatic access
- **Caching System**: In-memory cache with automatic invalidation
- **Dynamic Reloading**: Services automatically reload when settings change

## 🔧 Core Application Settings

### General Settings

#### Basic Configuration
| Setting | Default | Description |
|---------|---------|-------------|
| `app_port` | 5000 | Port for web interface |
| `app_host` | 0.0.0.0 | Host binding address |
| `debug_mode` | false | Enable debug logging |
| `secret_key` | auto-generated | Flask session secret |
| `language` | en | Application language |
| `ui_theme` | default | User interface theme |

**Configuration Example:**
```bash
# Environment variables
export PORT=5001
export DEBUG=false
export SECRET_KEY="your-secure-random-key"
```

### File System Paths

#### Directory Configuration
| Setting | Default | Description |
|---------|---------|-------------|
| `downloads_path` | data/downloads | Temporary downloads location |
| `music_videos_path` | data/musicvideos | Organized video library |
| `thumbnails_path` | data/thumbnails | Thumbnail cache directory |

**Best Practices:**
```bash
# Recommended directory structure
/mvidarr-data/
├── downloads/          # Temporary processing
├── musicvideos/       # Final organized library  
├── thumbnails/        # Generated thumbnails
└── database/          # SQLite database files
```

**Permissions Setup:**
```bash
# Set appropriate permissions
sudo chown -R $(id -u):$(id -g) /path/to/mvidarr-data
chmod -R 755 /path/to/mvidarr-data
chmod -R 777 /path/to/mvidarr-data/downloads  # Needs write access
```

## 🔐 Authentication & Security

### Simple Authentication

#### Enable Authentication
```bash
# Via web interface: Settings → General → Authentication
require_authentication=true
simple_auth_username="admin"
simple_auth_password="secure_password_hash"  # SHA-256 hashed
```

#### Password Hashing
```python
# Generate password hash
import hashlib
password = "your_secure_password"
hash_value = hashlib.sha256(password.encode()).hexdigest()
print(f"Password hash: {hash_value}")
```

### SSL/HTTPS Configuration

#### SSL Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `ssl_required` | false | Force HTTPS redirects |
| `ssl_port` | 443 | HTTPS port |
| `ssl_hsts_enabled` | false | HTTP Strict Transport Security |
| `ssl_hsts_max_age` | 31536000 | HSTS max age (1 year) |
| `ssl_redirect_permanent` | false | Use 301 vs 302 redirects |

**SSL Configuration Example:**
```bash
# Enable SSL with HSTS
ssl_required=true
ssl_port=443
ssl_hsts_enabled=true
ssl_hsts_max_age=31536000
```

**Reverse Proxy Setup (Nginx):**
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🌐 External Service Integration

### IMVDB Integration

#### API Key Configuration
```bash
# Get API key from https://imvdb.com/developers
imvdb_api_key="your_imvdb_api_key"
```

**Features Enabled:**
- Artist metadata enrichment
- Music video discovery
- Album artwork and biographies
- Video metadata validation

### YouTube Integration

#### YouTube API Setup
```bash
# Get API key from Google Cloud Console
youtube_api_key="your_youtube_api_key"
youtube_enabled=true
youtube_auto_download=false
youtube_playlist_sync_interval=60  # minutes
```

**Required Google Cloud APIs:**
- YouTube Data API v3
- YouTube Analytics API (optional)

**Usage Quotas:**
- Free tier: 10,000 units/day
- Search operations: ~100 units each
- Monitor usage in Google Cloud Console

### MeTube Integration

#### MeTube Server Configuration
```bash
# MeTube server settings
metube_host="localhost"
metube_port=8081
```

**Docker Compose Setup:**
```yaml
version: '3.8'
services:
  mvidarr:
    image: mvidarr:latest
    ports:
      - "5000:5000"
    depends_on:
      - metube
      
  metube:
    image: ghcr.io/alexta69/metube
    ports:
      - "8081:8081"
    volumes:
      - ./downloads:/downloads
```

### Spotify Integration

#### OAuth Configuration
```bash
# Create Spotify app at https://developer.spotify.com
spotify_enabled=true
spotify_client_id="your_spotify_client_id"
spotify_client_secret="your_spotify_client_secret"
spotify_redirect_uri="http://localhost:5000/api/spotify/callback"
```

**Spotify App Setup:**
1. Create app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Add redirect URI: `http://your-domain.com/api/spotify/callback`
3. Copy Client ID and Client Secret to MVidarr settings

### Lidarr Integration

#### Lidarr Connection
```bash
# Lidarr server configuration
lidarr_enabled=true
lidarr_server_url="http://localhost:8686"
lidarr_api_key="your_lidarr_api_key"
lidarr_sync_interval=6  # hours
```

**Features:**
- Artist synchronization
- Album monitoring
- Quality profile matching
- Automatic music video downloads for monitored artists

## 📥 Download & Processing Settings

### Download Configuration

#### Quality and Processing
```bash
# Video quality preferences
video_quality_preference="best"  # Options: best, worst, 1080p, 720p, 480p
max_concurrent_downloads=3
auto_organize_downloads=true
```

**Quality Options:**
- `best` - Highest available quality
- `worst` - Lowest available quality  
- `1080p`, `720p`, `480p` - Specific resolutions
- `bestaudio` - Audio only
- `bestvideo` - Video only (no audio)

### Automated Scheduling

#### Auto-Download Schedule
```bash
# Scheduled download configuration
auto_download_schedule_enabled=true
auto_download_schedule_time="02:00"
auto_download_schedule_days="daily"  # Options: hourly, daily, weekly
auto_download_max_videos=10
```

#### Auto-Discovery Schedule  
```bash
# Automated discovery configuration
auto_discovery_schedule_enabled=true
auto_discovery_schedule_time="06:00"
auto_discovery_schedule_days="daily"
auto_discovery_max_videos_per_artist=5
```

**Schedule Options:**
- `hourly` - Every hour at specified minute
- `daily` - Every day at specified time
- `weekly` - Every week on specified day/time
- `monthly` - Every month on specified date/time

## 🗄️ Database Configuration

### Connection Settings

#### Database Connection
```bash
# MySQL/MariaDB configuration
db_host="localhost"
db_port=3306
db_name="mvidarr"
db_user="mvidarr_user"
db_password="secure_db_password"
```

#### Connection Pool Settings
```bash
# Performance optimization
db_pool_size=10
db_max_overflow=20
db_pool_timeout=30
```

**Database Setup:**
```sql
-- Create database and user
CREATE DATABASE mvidarr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mvidarr_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON mvidarr.* TO 'mvidarr_user'@'localhost';
FLUSH PRIVILEGES;
```

### SQLite Configuration (Alternative)

#### SQLite Setup
```bash
# For smaller deployments
db_host="sqlite"
db_name="/app/database/mvidarr.db"
```

**SQLite Optimization:**
```sql
-- Performance settings (applied automatically)
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=1000;
PRAGMA temp_store=memory;
```

## 📊 Logging & Monitoring

### Logging Configuration

#### Log Level Settings
```bash
# Logging configuration
log_level="INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_max_size=10485760  # 10MB
log_backup_count=5
```

**Log Levels Explained:**
- `DEBUG` - Detailed diagnostic information
- `INFO` - General application flow
- `WARNING` - Warning messages
- `ERROR` - Error messages  
- `CRITICAL` - Critical system errors

#### Log File Locations
```bash
# Docker deployment
/app/logs/mvidarr.log

# Local installation
~/.local/share/mvidarr/logs/mvidarr.log
/var/log/mvidarr/mvidarr.log  # System-wide install
```

### Notifications

#### System Notifications
```bash
# Enable notifications
enable_notifications=true
```

**Notification Types:**
- Download completions
- Error alerts
- System status changes
- Scheduled task results

## 🐳 Docker Configuration

### Environment Variables

#### Complete Docker Environment
```bash
# docker-compose.env
# Core Application
PORT=5000
DEBUG=false
SECRET_KEY=your-secure-secret-key

# Database
DB_HOST=db
DB_PORT=3306
DB_NAME=mvidarr
DB_USER=mvidarr
DB_PASSWORD=secure-password

# External Services
IMVDB_API_KEY=your-imvdb-api-key
YOUTUBE_API_KEY=your-youtube-api-key

# MeTube Integration
METUBE_HOST=metube
METUBE_PORT=8081

# Paths (container paths)
DOWNLOADS_PATH=/app/downloads
MUSIC_VIDEOS_PATH=/app/musicvideos
THUMBNAILS_PATH=/app/thumbnails

# Scheduling
MVIDARR_USE_ENHANCED_SCHEDULER=true
MVIDARR_AUTO_DOWNLOAD_ENABLED=true
MVIDARR_AUTO_DOWNLOAD_SCHEDULE=daily
```

### Docker Compose Configuration

#### Complete docker-compose.yml
```yaml
version: '3.8'

services:
  mvidarr:
    image: mvidarr:latest
    container_name: mvidarr-app
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - ./config:/app/config
      - ./downloads:/app/downloads
      - ./musicvideos:/app/musicvideos
      - ./thumbnails:/app/thumbnails
      - ./database:/app/database
      - ./logs:/app/logs
    environment:
      - DB_HOST=db
      - DB_NAME=mvidarr
      - DB_USER=mvidarr
      - DB_PASSWORD=${DB_PASSWORD}
      - IMVDB_API_KEY=${IMVDB_API_KEY}
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
    env_file:
      - .env
    depends_on:
      - db
      - metube
    networks:
      - mvidarr-network

  db:
    image: mariadb:10.11
    container_name: mvidarr-db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=mvidarr
      - MYSQL_USER=mvidarr
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql
      - ./database/backup:/backup
    networks:
      - mvidarr-network

  metube:
    image: ghcr.io/alexta69/metube
    container_name: mvidarr-metube
    restart: unless-stopped
    ports:
      - "8081:8081"
    volumes:
      - ./downloads:/downloads
    networks:
      - mvidarr-network

volumes:
  db_data:

networks:
  mvidarr-network:
    driver: bridge
```

## ⚡ Performance Optimization

### Resource Configuration

#### Memory and CPU Settings
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```

### Database Optimization

#### Connection Pool Tuning
```bash
# For high-traffic deployments
db_pool_size=20
db_max_overflow=40
db_pool_timeout=60
```

#### Index Optimization
```sql
-- Performance indexes (applied automatically)
CREATE INDEX idx_videos_artist_id ON videos(artist_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_downloads_status ON downloads(status);
```

## 🔄 Configuration Management

### Settings API

#### Programmatic Access
```bash
# Get all settings
curl http://localhost:5000/api/settings/

# Get specific setting
curl http://localhost:5000/api/settings/imvdb_api_key

# Update setting
curl -X PUT http://localhost:5000/api/settings/max_concurrent_downloads \
  -H "Content-Type: application/json" \
  -d '{"value": "5"}'

# Bulk update
curl -X PUT http://localhost:5000/api/settings/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "imvdb_api_key": "new-key",
    "max_concurrent_downloads": "3",
    "video_quality_preference": "720p"
  }'
```

### Configuration Backup

#### Export Settings
```bash
# Export all settings
curl http://localhost:5000/api/settings/ > mvidarr-settings-backup.json

# Create full backup
docker exec mvidarr-app sqlite3 /app/database/mvidarr.db ".backup /app/backup/full-backup.db"
```

#### Import Settings
```bash
# Import settings via API
curl -X PUT http://localhost:5000/api/settings/bulk \
  -H "Content-Type: application/json" \
  -d @mvidarr-settings-backup.json
```

## 🚨 Security Considerations

### API Key Security

#### Best Practices
- Store API keys in environment variables
- Use different keys for development/production
- Regularly rotate API keys
- Monitor API usage quotas

#### Key Storage
```bash
# Secure environment file (.env)
# Never commit this to version control
IMVDB_API_KEY=abc123def456
YOUTUBE_API_KEY=xyz789uvw012
DB_PASSWORD=secure-random-password
```

### Access Control

#### Network Security
```bash
# Firewall configuration (example)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5000/tcp   # Block direct access (use reverse proxy)
```

## 📋 Configuration Checklist

### Initial Setup
- [ ] Configure file system paths
- [ ] Set up database connection
- [ ] Configure authentication (if required)
- [ ] Add IMVDB API key
- [ ] Add YouTube API key (if using)
- [ ] Configure MeTube connection
- [ ] Set video quality preferences
- [ ] Configure download scheduling

### Security Setup
- [ ] Enable authentication
- [ ] Configure SSL/HTTPS
- [ ] Set up reverse proxy
- [ ] Configure firewall rules
- [ ] Secure API key storage
- [ ] Enable HSTS (if using SSL)

### Performance Optimization
- [ ] Tune database connection pool
- [ ] Configure resource limits
- [ ] Set up log rotation
- [ ] Enable appropriate caching
- [ ] Monitor resource usage

### Integration Setup
- [ ] Configure Spotify (if using)
- [ ] Set up Lidarr integration (if using)
- [ ] Configure scheduled tasks
- [ ] Test external service connections
- [ ] Set up monitoring and alerts

## 🔗 Related Documentation

- **Installation Guide**: See `INSTALLATION-GUIDE.md`
- **Docker Troubleshooting**: See `TROUBLESHOOTING_DOCKER.md`
- **System Monitoring**: See `MONITORING.md`
- **API Documentation**: See `API_DOCUMENTATION.md`
- **User Guide**: See `USER-GUIDE.md`

This configuration guide provides comprehensive coverage of all MVidarr configuration options and best practices for optimal performance and security.