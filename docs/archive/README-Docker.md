# MVidarr Docker Deployment Guide

## 🐳 Overview

MVidarr is fully containerized and ready for production deployment with Docker and Docker Compose. This guide covers everything from quick testing to production deployment.

## ✅ Prerequisites

- Docker Engine 20.10+ 
- Docker Compose 2.0+
- 2GB+ RAM
- 10GB+ storage space

```bash
# Verify Docker installation
docker --version
docker-compose --version
```

## 🚀 Quick Start

### Option 1: Simple Setup (Great for Testing)

```bash
# 1. Clone the repository
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr

# 2. Start with default settings
docker-compose up -d

# 3. Access the application
open http://localhost:5000
```

### Option 2: Custom Configuration

```bash
# 1. Copy environment template
cp .env.docker.example .env

# 2. Edit configuration
nano .env

# 3. Start with custom settings
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

The easiest way to configure MVidarr is through environment variables in a `.env` file:

```bash
# Essential settings
MVIDARR_PORT=5000
DB_PASSWORD=your_secure_password
SECRET_KEY=your_long_random_secret_key

# Storage paths (can be absolute or relative)
MUSIC_VIDEOS_PATH=./music_videos
DOWNLOADS_PATH=./downloads
DATABASE_FOLDER=./database

# API keys (optional but recommended)
IMVDB_API_KEY=your_imvdb_api_key
YOUTUBE_API_KEY=your_youtube_api_key
```

### Directory Structure

MVidarr creates the following directory structure:

```
mvidarr/
├── music_videos/     # Organized music video files
├── downloads/        # Temporary download storage
├── database/         # MariaDB data files
├── thumbnails/       # Cached thumbnails
├── logs/            # Application logs
└── cache/           # Temporary cache files
```

### Storage Permissions

If using custom paths, ensure proper permissions:

```bash
# For custom storage locations
sudo mkdir -p /your/storage/{music_videos,downloads,database,thumbnails,logs,cache}
sudo chown -R 1001:1001 /your/storage/
```

## 🏗️ Production Deployment

### Using Production Compose File

For production deployments, use the dedicated production compose file:

```bash
# Copy and configure environment
cp .env.docker.example .env
nano .env  # Set your production values

# Deploy with production settings
docker-compose -f docker-compose.production.yml up -d
```

### Production Environment Variables

```bash
# Production settings
NODE_ENV=production
DEBUG=false

# Secure passwords
MYSQL_ROOT_PASSWORD=very_secure_root_password  
DB_PASSWORD=very_secure_db_password
SECRET_KEY=very_long_random_secret_key_64_chars_minimum

# Production storage paths
MUSIC_VIDEOS_PATH=/mnt/storage/musicvideos
DOWNLOADS_PATH=/mnt/storage/downloads
DATABASE_FOLDER=/mnt/storage/database
THUMBNAILS_PATH=/mnt/storage/thumbnails
LOGS_PATH=/var/log/mvidarr
```

## 🔍 Health Monitoring

### Container Health Checks

Both containers include health checks:

```bash
# Check container status
docker-compose ps

# View health status
docker inspect mvidarr --format='{{.State.Health.Status}}'
docker inspect mvidarr-mariadb --format='{{.State.Health.Status}}'

# Test application health manually
curl http://localhost:5000/api/health
```

### Log Monitoring

```bash
# View application logs
docker-compose logs -f mvidarr

# View database logs
docker-compose logs -f mariadb

# View all logs
docker-compose logs -f
```

## 🔧 Maintenance

### Updates

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d

# Clean up old images
docker image prune
```

### Backup

```bash
# Backup database
docker exec mvidarr-mariadb mysqldump -u root -p mvidarr > backup.sql

# Backup entire data directory
tar -czf mvidarr-backup-$(date +%Y%m%d).tar.gz music_videos/ database/ thumbnails/
```

### Restore

```bash
# Restore database
docker exec -i mvidarr-mariadb mysql -u root -p mvidarr < backup.sql

# Restore data directories
tar -xzf mvidarr-backup-YYYYMMDD.tar.gz
```

## 🛠️ Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check container logs
docker-compose logs mvidarr

# Common causes:
# - Port already in use
# - Insufficient permissions on storage directories
# - Invalid environment variables
```

#### Database Connection Issues

```bash
# Check MariaDB health
docker-compose exec mariadb mysqladmin ping -u root -p

# Check MariaDB logs
docker-compose logs mariadb

# Test connection from app container
docker-compose exec mvidarr mysql -h mariadb -u mvidarr -p -e "SELECT 1"
```

#### Permission Errors

```bash
# Fix ownership of data directories
sudo chown -R 1001:1001 ./music_videos ./database ./downloads ./thumbnails ./logs ./cache

# Check container user
docker-compose exec mvidarr id
```

#### Port Conflicts

```bash
# Check what's using port 5000
sudo lsof -i :5000

# Use different port
echo "MVIDARR_PORT=8080" >> .env
docker-compose up -d
```

### Debug Mode

Enable debug logging:

```bash
# Add to .env file
DEBUG=true

# Restart containers
docker-compose restart

# View debug logs
docker-compose logs -f mvidarr
```

## 🔒 Security Considerations

### Container Security

- Containers run as non-root user (UID 1001)
- Isolated network namespace
- No privileged access required
- Health checks for monitoring

### Data Security

- Database credentials via environment variables
- Secret key for session security
- Optional SSL/TLS termination with nginx
- File system permissions properly configured

### Network Security

```bash
# Use custom networks (already configured)
docker network ls | grep mvidarr

# Limit external access
# Only expose necessary ports in docker-compose.yml
```

## 📊 Performance Tuning

### Resource Limits

Add resource limits to docker-compose.yml:

```yaml
services:
  mvidarr:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

### Database Optimization

```bash
# Monitor database performance
docker-compose exec mariadb mysql -u root -p -e "SHOW PROCESSLIST;"

# Check database size
docker-compose exec mariadb mysql -u root -p mvidarr -e "
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'mvidarr'
ORDER BY (data_length + index_length) DESC;"
```

## 🆙 Advanced Configuration

### Reverse Proxy Setup

Enable nginx reverse proxy in docker-compose.production.yml:

```yaml
# Uncomment nginx service section
nginx:
  image: nginx:alpine
  container_name: mvidarr-nginx
  ports:
    - "80:80"
    - "443:443"
  # ... additional config
```

### SSL/TLS Configuration

```bash
# Generate SSL certificates
cd docker/nginx/ssl
./generate-certs.sh yourdomain.com

# Update nginx configuration
# Edit docker/nginx/nginx.conf for SSL settings
```

### External Database

Use external MariaDB/MySQL:

```yaml
services:
  mvidarr:
    environment:
      - DB_HOST=your-external-db-host
      - DB_PORT=3306
      - DB_USER=mvidarr
      - DB_PASSWORD=your_password
      - DB_NAME=mvidarr
    # Remove mariadb service and depends_on
```

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Docker and Docker Compose installed
- [ ] .env file configured with secure passwords
- [ ] Storage directories created with correct permissions
- [ ] API keys obtained (IMVDb, YouTube)
- [ ] Firewall rules configured
- [ ] Backup strategy planned

### Post-Deployment

- [ ] Application accessible at http://localhost:5000
- [ ] Health checks passing
- [ ] Database connectivity verified
- [ ] Log files being written
- [ ] Storage directories populated
- [ ] Initial admin user created
- [ ] API keys functional

## 📖 Additional Resources

- **Main Documentation**: [README.md](README.md)
- **Installation Guide**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- **Docker Quickstart**: [DOCKER-QUICKSTART.md](DOCKER-QUICKSTART.md)
- **Configuration Sample**: [.env.docker.example](.env.docker.example)

---

## 🎉 Success!

Your MVidarr music video management system is now running in Docker with:

- ✅ **Production-ready containers**
- ✅ **Persistent data storage**  
- ✅ **Health monitoring**
- ✅ **Automated restarts**
- ✅ **Secure configuration**
- ✅ **Easy maintenance**

Access your MVidarr instance at **http://localhost:5000** and start building your music video library!