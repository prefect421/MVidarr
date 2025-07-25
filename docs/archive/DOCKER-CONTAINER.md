# MVidarr Docker Multi-Container Guide

This guide covers the multi-container Docker deployment of MVidarr with separated MariaDB database, using pre-built images from GitHub Container Registry.

## 📦 Pre-built Images

MVidarr provides pre-built Docker images hosted on GitHub Container Registry:

- **Production**: `ghcr.io/prefect421/mvidarr:latest`
- **Development**: `ghcr.io/prefect421/mvidarr:dev`
- **Tagged versions**: `ghcr.io/prefect421/mvidarr:v0.9`

## 🚀 Quick Start with Multi-Container Setup

### Architecture Overview

MVidarr uses a **multi-container architecture**:
- **MVidarr Application Container**: Main web application
- **MariaDB Database Container**: Dedicated database server
- **Shared Docker Network**: Secure container communication

### Using Docker Compose (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr
```

2. **Configure environment:**
```bash
# Copy the production template
cp .env.production.template .env

# Edit configuration (set passwords, API keys, paths)
nano .env
```

3. **Deploy the multi-container stack:**
```bash
# Production deployment
docker-compose -f docker-compose.production.yml up -d

# Check container status
docker-compose -f docker-compose.production.yml ps
```

### Manual Multi-Container Setup

**⚠️ Note**: Manual setup requires creating network and database container first.

```bash
# Create Docker network
docker network create mvidarr-network

# Start MariaDB container
docker run -d \
  --name mvidarr-mariadb \
  --network mvidarr-network \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=mvidarr \
  -e MYSQL_USER=mvidarr \
  -e MYSQL_PASSWORD=your_db_password \
  -v ./database/mariadb:/var/lib/mysql \
  mariadb:11.4

# Wait for database to be ready (30-60 seconds)
docker logs -f mvidarr-mariadb

# Start MVidarr application
docker run -d \
  --name mvidarr \
  --network mvidarr-network \
  -p 5000:5000 \
  -v ./data/musicvideos:/app/data/musicvideos \
  -v ./data/downloads:/app/data/downloads \
  -v ./data/thumbnails:/app/data/thumbnails \
  -v ./data/logs:/app/data/logs \
  -e DB_HOST=mvidarr-mariadb \
  -e DB_PASSWORD=your_db_password \
  -e SECRET_KEY=your_secret_key \
  ghcr.io/prefect421/mvidarr:latest
```

## 🏗️ Building Your Own Images

### Prerequisites for Building

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ available disk space
- Internet connection for dependencies

### Local Build

```bash
# Build production image
docker build -f Dockerfile.production -t mvidarr:local .

# Build with GitHub Container Registry tags
docker build -f Dockerfile.production \
  -t ghcr.io/prefect421/mvidarr:latest \
  -t ghcr.io/prefect421/mvidarr:v0.9 .
```

### Push to GitHub Container Registry

1. **Authenticate with GitHub Container Registry:**
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

2. **Push the images:**
```bash
docker push ghcr.io/prefect421/mvidarr:latest
docker push ghcr.io/prefect421/mvidarr:v0.9
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database hostname | `mariadb` |
| `DB_PORT` | Database port | `3306` |
| `DB_USER` | Database username | `mvidarr` |
| `DB_PASSWORD` | Database password | `secure_password` |
| `DB_NAME` | Database name | `mvidarr` |
| `SECRET_KEY` | Flask secret key | Generated |
| `YOUTUBE_API_KEY` | YouTube API key | None |
| `IMVDB_API_KEY` | IMVDb API key | None |
| `PORT` | Application port | `5000` |
| `DEBUG` | Debug mode | `false` |

### Volume Mounts

#### MVidarr Application Container
| Container Path | Description | Host Path Example |
|----------------|-------------|-------------------|
| `/app/data/downloads` | Temporary download files | `./downloads` |
| `/app/data/musicvideos` | Final music video collection | `./musicvideos` |
| `/app/data/thumbnails` | Video thumbnails | `./thumbnails` |
| `/app/data/logs` | Application logs | `./logs` |
| `/app/data/cache` | Cache files | `./cache` |
| `/app/config` | Configuration files | `./config` |

#### MariaDB Database Container
| Container Path | Description | Host Path Example |
|----------------|-------------|-------------------|
| `/var/lib/mysql` | MariaDB data directory | `./database/mariadb` |
| `/docker-entrypoint-initdb.d/` | Initialization scripts | `./docker/mariadb/` |

## 📋 Multi-Container Docker Compose Architecture

### Production (`docker-compose.production.yml`)
**Multi-container production setup:**
- **MVidarr Container**: Pre-built image from GitHub Container Registry
- **MariaDB Container**: Dedicated database server (MariaDB 11.4)
- **Docker Network**: Isolated `mvidarr-network` for secure communication
- **Health Checks**: Both containers have comprehensive health monitoring
- **Dependency Management**: MVidarr waits for MariaDB to be healthy
- **Persistent Storage**: Separated data volumes for app and database

### Development (`docker-compose.dev.yml`)
**Multi-container development setup:**
- **MVidarr Container**: Built locally with hot reload
- **MariaDB Container**: Development database with debug settings
- **PHPMyAdmin Container**: Database administration interface
- **Debug Mode**: Enhanced logging and development features

## 🔄 Automated Builds

The repository includes GitHub Actions workflow (`.github/workflows/docker-build.yml`) that automatically:

- Builds images on push to `main` and `develop` branches
- Creates tagged releases for version tags
- Pushes to GitHub Container Registry
- Uses build cache for faster builds

### Triggering Builds

- **Main branch push**: Creates `latest` tag
- **Develop branch push**: Creates `dev` tag  
- **Version tag push** (e.g., `v0.9`): Creates semantic version tags
- **Pull request**: Builds but doesn't push

## 🐛 Troubleshooting

### Multi-Container Troubleshooting

1. **MariaDB Connection Timeouts:**
```bash
# Check MariaDB container health
docker-compose -f docker-compose.production.yml logs mariadb

# Verify database is accepting connections
docker exec mvidarr-mariadb mysqladmin ping -h localhost -u root -p

# Restart database container
docker-compose -f docker-compose.production.yml restart mariadb
```

2. **Container Communication Issues:**
```bash
# Check network connectivity
docker network inspect mvidarr-network

# Test connection from app to database
docker exec mvidarr ping mvidarr-mariadb

# Verify environment variables
docker exec mvidarr env | grep DB_
```

3. **Permission denied errors:**
```bash
# Fix file permissions for all data directories
sudo chown -R 1000:1000 ./downloads ./musicvideos ./thumbnails ./logs ./cache
sudo chown -R 999:999 ./database/mariadb  # MariaDB user
```

4. **Database initialization issues:**
```bash
# Remove database volume and reinitialize
docker-compose -f docker-compose.production.yml down -v
docker volume prune
docker-compose -f docker-compose.production.yml up -d
```

### Multi-Container Logs and Debugging

```bash
# View all container logs
docker-compose -f docker-compose.production.yml logs -f

# View specific container logs
docker-compose -f docker-compose.production.yml logs -f mvidarr
docker-compose -f docker-compose.production.yml logs -f mariadb

# Enter containers for debugging
docker exec -it mvidarr bash
docker exec -it mvidarr-mariadb bash

# Check all container health and status
docker-compose -f docker-compose.production.yml ps

# Monitor resource usage
docker stats mvidarr mvidarr-mariadb
```

## 📝 Multi-Container Best Practices

### Security
1. **Use specific image tags** instead of `latest` in production
2. **Set strong passwords** for MariaDB root and user accounts
3. **Use Docker secrets** for sensitive information in production
4. **Isolate containers** with dedicated networks
5. **Run containers as non-root** users (already configured)

### Data Management
6. **Separate data volumes** for application and database
7. **Regular database backups**:
   ```bash
   docker exec mvidarr-mariadb mysqldump -u root -p mvidarr > backup.sql
   ```
8. **Persistent storage** for all data directories
9. **Monitor disk usage** for database growth

### Performance & Monitoring  
10. **Monitor container health** and resource usage
11. **Set appropriate memory limits** for containers
12. **Use multi-stage builds** to minimize image size
13. **Implement log rotation** to prevent disk filling

### Deployment
14. **Use environment files** (.env) for configuration
15. **Test database connectivity** before deploying application
16. **Implement health checks** for both containers
17. **Use restart policies** for automatic recovery

## 🔗 Related Documentation

- [Docker Quick Start Guide](DOCKER-QUICKSTART.md)
- [Installation Guide](INSTALLATION_GUIDE.md)
- [Main README](README.md)

---

For support and questions, please check the [GitHub Issues](https://github.com/prefect421/mvidarr/issues) page.