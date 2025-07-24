# MVidarr Docker Container Guide

This guide covers building, deploying, and using the MVidarr Docker container from GitHub Container Registry.

## 📦 Pre-built Images

MVidarr provides pre-built Docker images hosted on GitHub Container Registry:

- **Production**: `ghcr.io/prefect421/mvidarr:latest`
- **Development**: `ghcr.io/prefect421/mvidarr:dev`
- **Tagged versions**: `ghcr.io/prefect421/mvidarr:v0.9`

## 🚀 Quick Start with Pre-built Images

### Using Docker Compose (Recommended)

1. **Clone the repository:**
```bash
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr
```

2. **Run the setup script:**
```bash
# Production deployment
./docker-setup.sh

# Development deployment
./docker-setup.sh -t development
```

### Manual Docker Run

```bash
# Pull the image
docker pull ghcr.io/prefect421/mvidarr:latest

# Run with basic setup
docker run -d \
  --name mvidarr \
  -p 5000:5000 \
  -v ./data/musicvideos:/app/data/musicvideos \
  -v ./data/downloads:/app/data/downloads \
  -v ./data/thumbnails:/app/data/thumbnails \
  -v ./data/database:/app/data/database \
  -e DB_HOST=localhost \
  -e DB_NAME=mvidarr \
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

| Container Path | Description |
|----------------|-------------|
| `/app/data/downloads` | Temporary download files |
| `/app/data/musicvideos` | Final music video collection |
| `/app/data/thumbnails` | Video thumbnails |
| `/app/data/database` | SQLite database files |
| `/app/data/logs` | Application logs |
| `/app/data/cache` | Cache files |
| `/app/config` | Configuration files |

## 📋 Docker Compose Files

### Production (`docker-compose.production.yml`)
- Uses pre-built image from registry
- Includes MariaDB database
- Production-ready configuration
- Health checks enabled

### Development (`docker-compose.dev.yml`)
- Builds image locally
- Includes hot reload
- Debug mode enabled
- PHPMyAdmin included

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

### Common Issues

1. **Permission denied errors:**
```bash
# Fix file permissions
sudo chown -R 1000:1000 ./data/
```

2. **Database connection errors:**
```bash
# Check database container
docker-compose logs mariadb

# Restart database
docker-compose restart mariadb
```

3. **Build failures:**
```bash
# Clean build cache
docker builder prune

# Build without cache
docker build --no-cache -f Dockerfile.production -t mvidarr:local .
```

### Logs and Debugging

```bash
# View application logs
docker-compose logs -f mvidarr

# Enter container for debugging
docker exec -it mvidarr bash

# Check container health
docker-compose ps
```

## 📝 Best Practices

1. **Use specific tags** instead of `latest` in production
2. **Mount data volumes** to persistent storage
3. **Set strong passwords** for database and secret keys
4. **Regular backups** of data volumes
5. **Monitor container health** and resource usage
6. **Use secrets management** for API keys

## 🔗 Related Documentation

- [Docker Quick Start Guide](DOCKER-QUICKSTART.md)
- [Installation Guide](INSTALLATION_GUIDE.md)
- [Main README](README.md)

---

For support and questions, please check the [GitHub Issues](https://github.com/prefect421/mvidarr/issues) page.