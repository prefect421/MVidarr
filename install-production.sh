#!/bin/bash

# MVidarr Enhanced Production Installation Script
# Automated production deployment for Ubuntu/Debian systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
INSTALL_DIR="/opt/mvidarr"
SERVICE_USER="mvidarr"
DB_NAME="mvidarr_enhanced"
DB_USER="mvidarr"
WEB_PORT="5000"
DOMAIN_NAME=""
USE_SSL=false
INSTALL_NGINX=false

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
    echo "MVidarr Enhanced Production Installation Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --directory DIR       Installation directory (default: /opt/mvidarr)"
    echo "  -u, --user USER          Service user (default: mvidarr)"
    echo "  -p, --port PORT          Web port (default: 5000)"
    echo "  -n, --domain DOMAIN      Domain name for SSL setup"
    echo "  -s, --ssl                Enable SSL/HTTPS"
    echo "  -r, --reverse-proxy      Install and configure Nginx reverse proxy"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Basic installation"
    echo "  $0 -d /home/user/mvidarr             # Custom directory"
    echo "  $0 -n mvidarr.example.com -s -r     # Full production with SSL"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--directory)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -u|--user)
            SERVICE_USER="$2"
            shift 2
            ;;
        -p|--port)
            WEB_PORT="$2"
            shift 2
            ;;
        -n|--domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        -s|--ssl)
            USE_SSL=true
            shift
            ;;
        -r|--reverse-proxy)
            INSTALL_NGINX=true
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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Starting MVidarr Enhanced production installation"
print_status "Installation directory: $INSTALL_DIR"
print_status "Service user: $SERVICE_USER"
print_status "Web port: $WEB_PORT"

# Detect OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS=$NAME
else
    print_error "Cannot detect OS version"
    exit 1
fi

print_status "Detected OS: $OS"

# Update system packages
print_status "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    ffmpeg \
    supervisor \
    mariadb-server \
    mariadb-client \
    libmariadb-dev \
    pkg-config \
    build-essential \
    ufw \
    certbot

# Install Nginx if requested
if [[ "$INSTALL_NGINX" == "true" ]]; then
    print_status "Installing Nginx..."
    apt-get install -y nginx
    systemctl enable nginx
fi

# Create service user
if ! id "$SERVICE_USER" &>/dev/null; then
    print_status "Creating service user: $SERVICE_USER"
    useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
else
    print_status "Service user $SERVICE_USER already exists"
fi

# Create installation directory
print_status "Creating installation directory..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"/{data,logs,config,backups}
mkdir -p "$INSTALL_DIR"/data/{musicvideos,thumbnails,cache,database}

# Clone or copy application
if [[ -f "app.py" ]]; then
    print_status "Copying application files..."
    cp -r . "$INSTALL_DIR"/
else
    print_error "Application files not found in current directory"
    print_error "Please run this script from the MVidarr Enhanced source directory"
    exit 1
fi

# Set ownership
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Create Python virtual environment
print_status "Creating Python virtual environment..."
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"

# Install Python dependencies
print_status "Installing Python dependencies..."
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Configure MariaDB
print_status "Configuring MariaDB..."
systemctl start mariadb
systemctl enable mariadb

# Secure MariaDB installation
mysql_secure_installation

# Generate database password
DB_PASSWORD=$(openssl rand -base64 32)

# Create database and user
print_status "Creating database and user..."
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

# Create configuration file
print_status "Creating configuration file..."
cat > "$INSTALL_DIR/.env" << EOF
# MVidarr Enhanced Production Configuration

# Database configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD

# Application settings
PORT=$WEB_PORT
DEBUG=false
SECRET_KEY=$(openssl rand -base64 64)

# External services (add your API keys)
IMVDB_API_KEY=
YOUTUBE_API_KEY=

# Logging
LOG_LEVEL=INFO
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Database connection pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
EOF

chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
chmod 600 "$INSTALL_DIR/.env"

# Initialize database
print_status "Initializing database..."
cd "$INSTALL_DIR"
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" scripts/setup_database.sh
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" scripts/init_auth_database.py

# Create systemd service
print_status "Creating systemd service..."
cat > "/etc/systemd/system/mvidarr.service" << EOF
[Unit]
Description=MVidarr Enhanced Music Video Management System
After=network.target mariadb.service
Requires=mariadb.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python app.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mvidarr

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable mvidarr
systemctl start mvidarr

# Configure firewall
print_status "Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow "$WEB_PORT"

if [[ "$INSTALL_NGINX" == "true" ]]; then
    ufw allow 'Nginx Full'
fi

# Configure Nginx if requested
if [[ "$INSTALL_NGINX" == "true" ]]; then
    print_status "Configuring Nginx reverse proxy..."
    
    cat > "/etc/nginx/sites-available/mvidarr" << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME:-localhost};
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;  
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static {
        alias $INSTALL_DIR/frontend/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:$WEB_PORT/api/health;
        access_log off;
    }
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/mvidarr /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    nginx -t
    systemctl restart nginx
    
    # Setup SSL if requested
    if [[ "$USE_SSL" == "true" && -n "$DOMAIN_NAME" ]]; then
        print_status "Setting up SSL certificate..."
        certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --email admin@"$DOMAIN_NAME"
    fi
fi

# Create admin user
print_status "Creating admin user..."
cd "$INSTALL_DIR"
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" scripts/create_admin_user.py

# Create backup script
print_status "Creating backup script..."
cat > "$INSTALL_DIR/backup.sh" << 'EOF'
#!/bin/bash
# MVidarr Enhanced Backup Script

BACKUP_DIR="/var/backups/mvidarr"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > "$BACKUP_DIR/database_$DATE.sql"

# Backup configuration
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C /opt/mvidarr .env config/

# Backup thumbnails
tar -czf "$BACKUP_DIR/thumbnails_$DATE.tar.gz" -C /opt/mvidarr data/thumbnails/

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x "$INSTALL_DIR/backup.sh"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/backup.sh"

# Add backup cron job
print_status "Setting up automated backups..."
(crontab -u "$SERVICE_USER" -l 2>/dev/null; echo "0 2 * * * $INSTALL_DIR/backup.sh") | crontab -u "$SERVICE_USER" -

# Final status check
sleep 5
systemctl status mvidarr --no-pager

print_success "Installation completed successfully!"
print_status "MVidarr Enhanced has been installed and started"
print_status ""
print_status "Service status: $(systemctl is-active mvidarr)"
print_status "Installation directory: $INSTALL_DIR"
print_status "Configuration file: $INSTALL_DIR/.env"
print_status "Log files: $INSTALL_DIR/data/logs/"
print_status ""
print_status "Web interface: http://localhost:$WEB_PORT"
if [[ "$INSTALL_NGINX" == "true" && -n "$DOMAIN_NAME" ]]; then
    if [[ "$USE_SSL" == "true" ]]; then
        print_status "Public URL: https://$DOMAIN_NAME"
    else
        print_status "Public URL: http://$DOMAIN_NAME"
    fi
fi
print_status ""
print_status "Database credentials stored in: $INSTALL_DIR/.env"
print_status "Admin user created - check logs for credentials"
print_status ""
print_status "Useful commands:"
echo "  - Check status: sudo systemctl status mvidarr"
echo "  - View logs: sudo journalctl -u mvidarr -f"
echo "  - Restart service: sudo systemctl restart mvidarr"
echo "  - Run backup: sudo -u $SERVICE_USER $INSTALL_DIR/backup.sh"
print_status ""
print_success "MVidarr Enhanced is now running in production mode!"