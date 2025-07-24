#!/bin/bash
# Production Security Setup Script for MVidarr Enhanced

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="/var/log/mvidarr_security_setup.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
   exit 1
fi

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

log "Starting MVidarr Enhanced Production Security Setup"
log "Project directory: $PROJECT_DIR"

# Function to generate secure random strings
generate_secret() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Function to setup file permissions
setup_file_permissions() {
    log "Setting up secure file permissions..."
    
    # Set restrictive permissions on sensitive files
    if [[ -f .env ]]; then
        chmod 600 .env
        success "Set .env permissions to 600"
    fi
    
    if [[ -f data/mvidarr.db ]]; then
        chmod 600 data/mvidarr.db
        success "Set database permissions to 600"
    fi
    
    # Set log directory permissions
    if [[ -d data/logs ]]; then
        chmod 750 data/logs
        find data/logs -type f -name "*.log" -exec chmod 640 {} \;
        success "Set log directory and file permissions"
    fi
    
    # Set backup directory permissions
    if [[ -d data/backups ]]; then
        chmod 750 data/backups
        find data/backups -type f -exec chmod 600 {} \;
        success "Set backup directory permissions"
    fi
    
    # Secure configuration files
    find src/config -type f -name "*.py" -exec chmod 644 {} \;
    success "Set configuration file permissions"
}

# Function to setup environment variables
setup_environment() {
    log "Setting up secure environment configuration..."
    
    if [[ ! -f .env ]]; then
        if [[ -f .env.example ]]; then
            cp .env.example .env
            chmod 600 .env
            log "Created .env from template"
        else
            error ".env.example not found!"
            exit 1
        fi
    fi
    
    # Generate secure values if they're still defaults
    if grep -q "CHANGE_ME_TO_A_VERY_LONG_RANDOM_STRING" .env; then
        SECRET_KEY=$(generate_secret 64)
        sed -i "s/SECRET_KEY=CHANGE_ME_TO_A_VERY_LONG_RANDOM_STRING_FOR_PRODUCTION_USE/SECRET_KEY=$SECRET_KEY/" .env
        success "Generated secure SECRET_KEY"
    fi
    
    if grep -q "CHANGE_ME_TO_A_VERY_STRONG_DATABASE_PASSWORD" .env; then
        DB_PASSWORD=$(generate_secret 32)
        sed -i "s/DB_PASSWORD=CHANGE_ME_TO_A_VERY_STRONG_DATABASE_PASSWORD/DB_PASSWORD=$DB_PASSWORD/" .env
        success "Generated secure DB_PASSWORD"
    fi
    
    # Ensure production settings
    sed -i 's/FLASK_ENV=development/FLASK_ENV=production/' .env
    sed -i 's/FLASK_DEBUG=true/FLASK_DEBUG=false/' .env
    
    success "Environment configuration secured"
}

# Function to setup SSL/TLS (nginx configuration)
setup_ssl_config() {
    log "Setting up SSL/TLS configuration template..."
    
    mkdir -p docker/nginx/ssl
    
    cat > docker/nginx/ssl/ssl.conf << 'EOF'
# SSL Configuration for MVidarr Enhanced
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;

# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; media-src 'self' blob:; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'" always;

# Hide server information
server_tokens off;
EOF

    success "Created SSL configuration template"
}

# Function to setup database security
setup_database_security() {
    log "Setting up database security configuration..."
    
    # Create database security configuration
    cat > scripts/setup/secure_mariadb.sql << 'EOF'
-- MVidarr Enhanced MariaDB Security Configuration

-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';

-- Remove remote root access
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');

-- Drop test database
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';

-- Create MVidarr database and user with minimal privileges
CREATE DATABASE IF NOT EXISTS mvidarr_enhanced CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (replace password with the one from .env)
-- CREATE USER 'mvidarr'@'localhost' IDENTIFIED BY 'your_secure_password_here';
-- GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON mvidarr_enhanced.* TO 'mvidarr'@'localhost';

-- Reload privilege tables
FLUSH PRIVILEGES;
EOF

    success "Created database security configuration"
}

# Function to setup monitoring
setup_security_monitoring() {
    log "Setting up security monitoring..."
    
    # Create fail2ban configuration for MVidarr
    cat > scripts/setup/mvidarr-fail2ban.conf << 'EOF'
[mvidarr]
enabled = true
port = 5000
filter = mvidarr
logpath = /home/*/mvidarr/data/logs/mvidarr.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

    # Create fail2ban filter
    cat > scripts/setup/mvidarr-filter.conf << 'EOF'
[Definition]
failregex = .*Rate limit exceeded.*from.*<HOST>
            .*Invalid.*from.*<HOST>
            .*Authentication failed.*from.*<HOST>
            .*Suspicious activity.*from.*<HOST>
ignoreregex =
EOF

    success "Created security monitoring configuration"
}

# Function to setup backup security
setup_backup_security() {
    log "Setting up secure backup configuration..."
    
    mkdir -p scripts/backup
    
    cat > scripts/backup/secure_backup.sh << 'EOF'
#!/bin/bash
# Secure backup script for MVidarr Enhanced

BACKUP_DIR="/secure/backup/location"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="mvidarr_backup_$DATE.tar.gz.enc"

# Create encrypted backup
tar czf - data/ src/config/ .env | \
    gpg --symmetric --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
        --s2k-digest-algo SHA512 --s2k-count 65536 --force-mdc \
        --output "$BACKUP_DIR/$BACKUP_FILE"

# Set secure permissions
chmod 600 "$BACKUP_DIR/$BACKUP_FILE"

# Clean old backups (keep 7 days)
find "$BACKUP_DIR" -name "mvidarr_backup_*.tar.gz.enc" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
EOF

    chmod +x scripts/backup/secure_backup.sh
    success "Created secure backup script"
}

# Function to create security checklist
create_security_checklist() {
    log "Creating security deployment checklist..."
    
    cat > SECURITY_CHECKLIST.md << 'EOF'
# MVidarr Enhanced Security Deployment Checklist

## Pre-Deployment Security Checklist

### Environment Security
- [ ] Strong SECRET_KEY generated (64+ characters)
- [ ] Strong DB_PASSWORD set (32+ characters)
- [ ] FLASK_ENV set to 'production'
- [ ] FLASK_DEBUG set to 'false'
- [ ] All API keys configured with minimal required permissions
- [ ] .env file permissions set to 600
- [ ] .env file added to .gitignore (never commit to version control)

### File System Security
- [ ] Database file permissions set to 600
- [ ] Log directory permissions set to 750
- [ ] Log file permissions set to 640
- [ ] Backup directory secured with 750 permissions
- [ ] Application runs as non-root user
- [ ] Sensitive directories not world-readable

### Database Security
- [ ] MariaDB anonymous users removed
- [ ] MariaDB remote root access disabled
- [ ] Test database removed
- [ ] Application user has minimal required privileges
- [ ] Database password is strong and unique
- [ ] Database connection uses SSL/TLS

### Network Security
- [ ] SSL/TLS certificate installed and configured
- [ ] HTTPS enforcement enabled
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] Non-default port configured (optional)
- [ ] Firewall rules configured to allow only required ports
- [ ] Rate limiting enabled

### Application Security
- [ ] Input validation enabled on all endpoints
- [ ] File upload restrictions configured
- [ ] Security headers applied to all responses
- [ ] Error pages don't reveal sensitive information
- [ ] Debug mode disabled
- [ ] Unnecessary features disabled

### Monitoring and Logging
- [ ] Security logging enabled
- [ ] Log rotation configured
- [ ] Fail2ban configured for brute force protection
- [ ] Monitoring alerts configured
- [ ] Backup monitoring in place

### Backup Security
- [ ] Automated backups configured
- [ ] Backups encrypted
- [ ] Backup retention policy implemented
- [ ] Backup restoration tested
- [ ] Offsite backup storage configured

### Dependency Security
- [ ] All dependencies updated to latest secure versions
- [ ] Vulnerability scanning enabled
- [ ] Dependency update monitoring configured
- [ ] Security advisories subscribed

### Post-Deployment
- [ ] Security scan performed
- [ ] Penetration testing completed
- [ ] Security incident response plan in place
- [ ] Security training provided to administrators
- [ ] Regular security review schedule established

## Security Contacts
- Security Team: security@yourorganization.com
- Incident Response: incident@yourorganization.com
- System Administrator: admin@yourorganization.com

## Emergency Procedures
1. In case of security breach:
   - Immediately isolate the system
   - Contact security team
   - Preserve logs and evidence
   - Follow incident response plan

2. For critical security updates:
   - Test in staging environment first
   - Schedule maintenance window
   - Apply updates promptly
   - Verify security posture post-update
EOF

    success "Created security deployment checklist"
}

# Main execution
main() {
    log "=== MVidarr Enhanced Production Security Setup ==="
    
    # Run all setup functions
    setup_file_permissions
    setup_environment
    setup_ssl_config
    setup_database_security
    setup_security_monitoring
    setup_backup_security
    create_security_checklist
    
    # Final security check
    log "Running final security validation..."
    python3 src/utils/security_assessment.py > security_validation.log 2>&1 || true
    
    success "=== Security setup completed ==="
    
    echo ""
    echo "================================================================"
    echo "🛡️  MVidarr Enhanced Production Security Setup Complete"
    echo "================================================================"
    echo ""
    echo "Next steps:"
    echo "1. Review and customize .env file"
    echo "2. Set up SSL certificates"
    echo "3. Configure MariaDB security (run scripts/setup/secure_mariadb.sql)"
    echo "4. Set up fail2ban (copy configurations to /etc/fail2ban/)"
    echo "5. Review SECURITY_CHECKLIST.md and complete all items"
    echo "6. Run security assessment: python3 src/utils/security_assessment.py"
    echo ""
    echo "⚠️  IMPORTANT: Review all generated configurations before deployment!"
    echo ""
    echo "Security logs: $LOG_FILE"
    echo "Security validation: security_validation.log"
    echo ""
}

# Run main function
main "$@"