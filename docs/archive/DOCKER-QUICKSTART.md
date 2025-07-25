# MVidarr - Docker Quick Start

## 🚀 Ready to Deploy!

Your MVidarr Docker containerization is complete and production-ready!

### ✅ **CI/CD Tests Passed Successfully**
- **MariaDB Health Checks**: Fixed and working correctly
- **Code Quality**: All linting and formatting checks passed  
- **Security Scans**: No vulnerabilities detected
- **Container Integration**: MariaDB connectivity verified

### ✅ What's Been Built

1. **Production Dockerfile** (`Dockerfile.production`)
   - Multi-stage build for optimized image size
   - Python 3.12 with all dependencies
   - Non-root user for security
   - Health checks included
   - Image size: 1.35GB

2. **Docker Compose Configuration** (`docker-compose.production.yml`)
   - MVidarr application container
   - MariaDB 11.4 database container
   - Persistent volume mounts for data
   - Health monitoring and auto-restart
   - Secure networking

3. **Sample Configuration** (`docker-config.yml.sample`)
   - Complete environment variable template
   - Documented settings for easy customization
   - Security guidelines and best practices
   - Multiple deployment scenarios

4. **Documentation** (`README-Docker.md`)
   - Comprehensive deployment guide
   - Troubleshooting section
   - Security considerations
   - Maintenance procedures

### 🎯 Quick Start Deployment

#### Option 1: Simple Setup (Recommended for testing)
```bash
# 1. Clone and navigate
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr

# 2. Start with defaults
docker-compose up -d

# 3. Access application
open http://localhost:5001
```

#### Option 2: Production Setup
```bash
# 1. Copy and configure
cp docker-config.yml.sample docker-config.yml
nano docker-config.yml  # Edit your paths and API keys

# 2. Create directories
sudo mkdir -p /your/storage/{musicvideos,database,thumbnails,logs}
sudo chown -R 1001:1001 /your/storage/

# 3. Deploy
docker-compose --env-file docker-config.yml -f docker-compose.production.yml up -d

# 4. Access
open http://localhost:5001
```

### 📊 Container Details

**MVidarr Container:**
- **Base**: Python 3.12-slim
- **Size**: 1.35GB
- **User**: mvidarr (UID: 1001)
- **Port**: 5000 (mapped to host 5001)
- **Health Check**: `/api/health` endpoint
- **Features**: FFmpeg, yt-dlp, image processing, database connectivity

**MariaDB Container:**
- **Version**: 11.4
- **Port**: 3306 (configurable)
- **Database**: mvidarr_enhanced
- **Features**: UTF8MB4 support, optimized configuration

### 🔧 Key Features

✅ **Persistent Storage**: All data survives container restarts  
✅ **Health Monitoring**: Automatic failure detection and restart  
✅ **Security**: Non-root containers, isolated networking  
✅ **Performance**: Optimized for music video management workloads  
✅ **Flexibility**: Host directories or Docker volumes  
✅ **Documentation**: Complete deployment and maintenance guides  

### 📁 Required Configuration

Edit `docker-config.yml` with your settings:

```bash
# Essential settings
MUSIC_VIDEOS_PATH=/path/to/your/musicvideos
DATABASE_FOLDER=/path/to/your/database
DB_PASSWORD=your_secure_password
SECRET_KEY=your_long_random_secret

# API keys (optional but recommended)
IMVDB_API_KEY=your_imvdb_key
YOUTUBE_API_KEY=your_youtube_key
```

### 🌐 Remote Access

The Docker containers are configured for remote access:

```bash
# Application is accessible on all interfaces
http://YOUR_SERVER_IP:5001

# MariaDB is also accessible remotely (port 3307)
mysql -h YOUR_SERVER_IP -P 3307 -u mvidarr -p

# Configure firewall if needed
sudo ufw allow 5001/tcp comment "MVidarr Web Interface"
sudo ufw allow 3307/tcp comment "MVidarr MariaDB"
```

### 🏥 Health Status

After deployment, verify health:
```bash
# Check container status
docker-compose -f docker-compose.production.yml ps

# Test application health
curl http://localhost:5001/api/health

# View logs
docker-compose -f docker-compose.production.yml logs -f mvidarr
```

### 🆙 Next Steps

Your MVidarr is now ready for:
1. **Production Deployment** - All containers tested and working
2. **Data Migration** - Import existing music video collections
3. **API Integration** - Configure IMVDb and YouTube APIs
4. **User Management** - Set up your music video library
5. **Automation** - Schedule downloads and organization

### 📖 Documentation

- **Full Guide**: `README-Docker.md` - Complete deployment documentation
- **Configuration**: `docker-config.yml.sample` - All available settings
- **Troubleshooting**: See README-Docker.md troubleshooting section
- **Updates**: Standard Docker Compose update procedures

---

**🎉 Congratulations!** Your MVidarr music video management system is containerized and ready for production deployment. The Docker setup provides enterprise-grade reliability, security, and maintainability.