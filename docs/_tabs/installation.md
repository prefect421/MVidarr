---
# the default layout is 'page'
icon: fas fa-download
order: 2
---

# Installation Guide

This guide provides comprehensive instructions for installing and configuring MVidarr in various environments.

## 🐳 Docker Deployment (Recommended)

Docker deployment is the recommended method for production use, offering consistent environments and easy maintenance.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr

# Checkout the latest stable release (v0.9.5 - recommended)
git checkout v0.9.5

# Start with Docker Compose
docker-compose up -d
```

**Access the application:**
- Open your browser to `http://localhost:5001`
- Default login: `admin` / `admin` (⚠️ **Change immediately**)

### Production Docker Image

For production deployments, use the pre-built Docker images:

```bash
# Use the latest stable release (v0.9.5)
docker pull ghcr.io/prefect421/mvidarr:v0.9.5

# Or use the latest tag
docker pull ghcr.io/prefect421/mvidarr:latest
```

### Docker Compose Configuration

Create a `docker-compose.yml` file for production:

```yaml
version: '3.8'
services:
  mvidarr:
    image: ghcr.io/prefect421/mvidarr:v0.9.5
    ports:
      - "5001:5000"
    environment:
      - DATABASE_URL=mysql://user:pass@db:3306/mvidarr
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    depends_on:
      - db
      
  db:
    image: mariadb:10.11
    environment:
      - MYSQL_DATABASE=mvidarr
      - MYSQL_USER=mvidarr
      - MYSQL_PASSWORD=secure_password
      - MYSQL_ROOT_PASSWORD=root_password
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
```

## 🐍 Python Installation

### Prerequisites

- Python 3.11 or 3.12
- MySQL or MariaDB server
- Git

### Step-by-Step Installation

```bash
# 1. Clone the repository
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr

# 2. Checkout stable release
git checkout v0.9.5

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 4. Install dependencies
pip install -r requirements-prod.txt

# 5. Configure environment
cp .env.template .env
# Edit .env with your database settings

# 6. Initialize database
python -m src.database.init_db

# 7. Run the application
python app.py
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=mysql://username:password@localhost:3306/mvidarr

# Application Settings
SECRET_KEY=your_secret_key_here
DEBUG=False
HOST=0.0.0.0
PORT=5000

# External API Keys (optional)
IMVDB_API_KEY=your_imvdb_api_key
YOUTUBE_API_KEY=your_youtube_api_key

# Security Settings
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=3
```

### Database Setup

#### MySQL/MariaDB Setup

```sql
-- Create database and user
CREATE DATABASE mvidarr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mvidarr'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON mvidarr.* TO 'mvidarr'@'localhost';
FLUSH PRIVILEGES;
```

## 🚀 Production Deployment

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 2GB
- **Storage**: 10GB + space for video files
- **Network**: Stable internet connection

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 4GB+
- **Storage**: 50GB+ SSD
- **Network**: High-speed internet for video downloads

### Security Hardening

1. **Change Default Credentials**
   ```bash
   # First login, change admin password immediately
   ```

2. **Configure HTTPS**
   ```bash
   # Use reverse proxy (nginx/Apache) with SSL certificates
   ```

3. **Database Security**
   ```bash
   # Use strong passwords
   # Restrict database access
   # Enable SSL connections
   ```

4. **Firewall Configuration**
   ```bash
   # Only open required ports
   # Restrict access to management interfaces
   ```

## 🔧 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :5001
# Kill the process or use a different port
```

#### Database Connection Issues
```bash
# Verify database is running
systemctl status mysql
# Check connection string in .env
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data
```

### Log Analysis

```bash
# View application logs
docker-compose logs mvidarr

# Follow logs in real-time
docker-compose logs -f mvidarr
```

## 📋 Upgrade Guide

### Upgrading from Previous Versions

```bash
# 1. Backup your data
docker-compose exec mvidarr python -c "import scripts.backup; scripts.backup.create_backup()"

# 2. Pull latest code
git fetch origin
git checkout v0.9.5

# 3. Update containers
docker-compose pull
docker-compose up -d

# 4. Run migrations if needed
docker-compose exec mvidarr python -m src.database.migrations
```

## ✅ Verification

After installation, verify everything is working:

1. **Web Interface**: Access `http://localhost:5001`
2. **API Health**: Check `http://localhost:5001/api/health`
3. **Database**: Verify tables are created
4. **Logs**: Check for any error messages

---

For additional help, visit our [GitHub Issues](https://github.com/prefect421/mvidarr/issues) page.