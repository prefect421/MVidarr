# MVidarr Enhanced v2.0 - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Option 1: Automated Installation (Recommended)

#### Linux/macOS:
```bash
# Make installation script executable
chmod +x scripts/install.sh

# Run the installer
./scripts/install.sh
```

#### Windows:
```cmd
# Run the installer
scripts\install.bat
```

### Option 2: Manual Installation

#### Prerequisites
- **Python 3.8+** with pip
- **MariaDB 10.5+** (optional, app works without it)

#### Quick Install Commands

**1. Install Python Dependencies:**
```bash
# Core dependencies (required)
pip install flask==2.3.3 requests==2.31.0

# Recommended dependencies
pip install mysql-connector-python==8.1.0 bcrypt==4.0.1 flask-cors==4.0.0 python-dotenv==1.0.0

# Optional dependencies
pip install schedule==1.2.0 yt-dlp==2023.7.6
```

**2. Setup Environment:**
```bash
# Copy configuration template
cp .env.template .env

# Edit configuration (optional)
nano .env
```

**3. Create Directories:**
```bash
mkdir -p logs downloads/{music_videos,audio,thumbnails}
```

**4. Start the Application:**
```bash
python app.py
```

**5. Access the Application:**
- Open: http://localhost:5000
- Login: Admin / Admin
- **⚠️ Change the default password immediately!**

## 🏗️ Architecture Overview

### New Modular Structure
```
mvidarr/
├── app.py                 # Main application entry point
├── src/                   # Source code modules
│   ├── config/           # Configuration management
│   ├── database/         # Database layer
│   ├── services/         # Business logic (Users, Settings)
│   ├── api/              # API endpoints (future)
│   └── utils/            # Utility functions (future)
├── scripts/              # Installation and utility scripts
├── templates/            # HTML templates (future)
├── static/               # Static assets (future)
├── logs/                 # Application logs
├── downloads/            # Downloaded content
└── data/                 # Application data and backups
```

## 🔧 Key Features

### ✅ Completed in v2.0
- **Modular Architecture**: Clean separation of concerns
- **Configuration Management**: Environment-based config with fallbacks
- **Database Layer**: MariaDB with graceful fallbacks to mock mode
- **User Management**: Secure authentication with bcrypt
- **Settings System**: Database-persisted settings with caching
- **Dependency Management**: Graceful handling of missing dependencies
- **Installation Scripts**: Automated setup for Linux/macOS/Windows

### 🔄 From Previous Version
- **Settings Page**: Fixed 404 error, now fully functional
- **Default Credentials**: Hidden after password change
- **MariaDB Support**: Enhanced with optimized connection settings
- **Error Handling**: Comprehensive error handling throughout

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with your configuration:

```env
# MariaDB Configuration
MARIADB_HOST=localhost
MARIADB_PORT=3306
MARIADB_USER=mvidarr
MARIADB_PASSWORD=mvidarr123
MARIADB_DATABASE=mvidarr_db

# Application Settings
APP_SECRET_KEY=your-secret-key-here
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=5000

# MeTube Configuration (optional)
METUBE_URL=http://localhost:8081

# YouTube API (optional)
YOUTUBE_API_KEY=your-api-key-here

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mvidarr.log
```

### Database Setup (Optional)

If you want to use MariaDB instead of the mock database:

```sql
-- Connect to MariaDB as root
CREATE DATABASE mvidarr_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mvidarr'@'localhost' IDENTIFIED BY 'mvidarr123';
GRANT ALL PRIVILEGES ON mvidarr_db.* TO 'mvidarr'@'localhost';
FLUSH PRIVILEGES;
```

## 🚦 System Status

When you start the application, you'll see:

```
🎵 MVidarr Enhanced v2.0 - Refactored Music Video Downloader
======================================================================
🏗️  Modular Architecture:
   ✅ Configuration Management
   ✅ Database Layer with Connection Pooling
   ✅ Service Layer (Users, Settings)
   ✅ RESTful API Design
======================================================================
📊 Dependencies Status:
   MariaDB: ✅ Available / ❌ Missing (using mock)
   CORS: ✅ Available / ⚠️  Missing (manual headers)
======================================================================
🔧 Configuration:
   Database: localhost:3306
   App Port: 5000
   Debug Mode: False
   ✅ MariaDB connected (v10.6.12-MariaDB)
======================================================================
🚀 Server starting on http://0.0.0.0:5000
======================================================================
```

## 🔒 Security Notes

### Default Credentials
- **Default Login**: Admin / Admin
- **⚠️ CRITICAL**: Change the default password immediately after first login
- The system will prompt you to change the password on first login

### Database Security
- Change the default database password
- Use strong passwords for production
- Consider using environment variables for sensitive data

### Production Considerations
- Set `APP_DEBUG=false` in production
- Use a strong `APP_SECRET_KEY`
- Set up proper firewall rules
- Use HTTPS in production

## 🛠️ Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check if MariaDB is running
systemctl status mariadb  # Linux
brew services list | grep mariadb  # macOS

# Test connection manually
mysql -u mvidarr -p mvidarr_db
```

**2. Python Dependencies Missing**
```bash
# Reinstall dependencies
pip install -r requirements_enhanced.txt

# Or install individually
pip install flask requests mysql-connector-python bcrypt
```

**3. Permission Errors**
```bash
# Fix file permissions
chmod +x app.py
chmod 755 logs downloads
```

**4. Port Already in Use**
```bash
# Check what's using port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Or change port in .env file
echo "APP_PORT=8000" >> .env
```

### Getting Help

1. **Check Logs**: `tail -f logs/mvidarr.log`
2. **Test Installation**: Run the installation script again
3. **Health Check**: `curl http://localhost:5000/api/health`
4. **Documentation**: Check the detailed guides in the repository

## 📚 Next Steps

1. **🔧 Configuration**: Customize settings in the web interface
2. **🔑 API Keys**: Add YouTube API key for search functionality
3. **📺 MeTube**: Set up MeTube for video downloading
4. **🎵 Downloads**: Start downloading your favorite music videos
5. **⚙️ System Service**: Set up as a system service for auto-start

## 🎯 What's Different in v2.0

- **🏗️ Modular Design**: Clean, maintainable code structure
- **⚡ Better Performance**: Optimized database connections and caching
- **🛡️ Enhanced Security**: Improved authentication and error handling
- **🔧 Easy Setup**: Automated installation scripts
- **📊 Better Monitoring**: Comprehensive status reporting and health checks
- **🌐 API Ready**: Foundation for future API expansion

---

**Ready to start?** Run the installation script and you'll be up and running in minutes!

```bash
# Linux/macOS
./scripts/install.sh

# Windows
scripts\install.bat
```
