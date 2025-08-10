# Enhanced Docker-Native Scheduler for MVidarr

## Overview

MVidarr includes an enhanced Docker-native scheduler service designed specifically for containerized deployments. This scheduler provides improved container support, environment variable configuration, graceful shutdown handling, and comprehensive health monitoring.

## Features

### Docker-Native Capabilities
- **Environment Variable Configuration**: Full configuration via environment variables
- **Signal Handling**: Graceful shutdown on SIGTERM, SIGINT, and SIGQUIT
- **Health Checks**: Built-in health monitoring endpoints for container orchestration
- **Logging**: Enhanced logging with emojis and comprehensive status reporting

### Enhanced Scheduling
- **Flexible Scheduling**: Support for hourly, daily, weekly, and custom intervals
- **Manual Triggers**: API endpoints for manual download and discovery triggers
- **Multiple Task Types**: Both download and discovery scheduling
- **Error Handling**: Robust error handling with detailed reporting

### Monitoring and Management
- **REST API**: Complete REST API for scheduler management
- **Status Reporting**: Comprehensive status and configuration information
- **Health Endpoints**: Dedicated health check endpoints (no auth required for monitoring)
- **Log Management**: Structured logging with configurable levels

## Configuration

### Environment Variables

The enhanced scheduler can be configured entirely through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MVIDARR_USE_ENHANCED_SCHEDULER` | `false` | Enable enhanced scheduler |
| `MVIDARR_AUTO_DOWNLOAD_ENABLED` | `true` | Enable automatic downloads |
| `MVIDARR_AUTO_DOWNLOAD_SCHEDULE` | `daily` | Download schedule frequency |
| `MVIDARR_AUTO_DOWNLOAD_TIME` | `03:30` | Download schedule time |
| `MVIDARR_AUTO_DISCOVERY_ENABLED` | `false` | Enable automatic video discovery |
| `MVIDARR_AUTO_DISCOVERY_SCHEDULE` | `daily` | Discovery schedule frequency |
| `MVIDARR_AUTO_DISCOVERY_TIME` | `06:00` | Discovery schedule time |
| `MVIDARR_MAX_DOWNLOADS_PER_RUN` | `10` | Maximum downloads per scheduled run |
| `MVIDARR_SCHEDULER_HEALTH_CHECK` | `true` | Enable periodic health checks |
| `MVIDARR_SCHEDULER_LOG_LEVEL` | `INFO` | Logging level |

### Schedule Frequency Options

- `hourly` - Run every hour
- `every_X_hours` - Run every X hours (e.g., `every_2_hours`, `every_6_hours`)
- `daily` - Run once per day
- `weekly` - Run once per week
- `monday,tuesday,friday` - Run on specific days (comma-separated)

## Usage

### Docker Compose

```yaml
version: '3.8'
services:
  mvidarr:
    image: mvidarr:latest
    environment:
      - MVIDARR_USE_ENHANCED_SCHEDULER=true
      - MVIDARR_AUTO_DOWNLOAD_ENABLED=true
      - MVIDARR_AUTO_DOWNLOAD_SCHEDULE=daily
      - MVIDARR_AUTO_DOWNLOAD_TIME=03:30
      - MVIDARR_SCHEDULER_HEALTH_CHECK=true
    volumes:
      - ./data:/app/data
    ports:
      - "5000:5000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/enhanced-scheduler/health"]
      interval: 5m
      timeout: 10s
      retries: 3
```

### Environment File

Create a `docker.env` file:

```bash
# Copy from docker.env.example
cp docker.env.example docker.env

# Edit configuration
nano docker.env
```

## API Endpoints

### Scheduler Management

- `GET /api/enhanced-scheduler/status` - Get comprehensive scheduler status
- `POST /api/enhanced-scheduler/start` - Start the scheduler service
- `POST /api/enhanced-scheduler/stop` - Stop the scheduler service
- `POST /api/enhanced-scheduler/reload` - Reload scheduler configuration

### Manual Triggers

- `POST /api/enhanced-scheduler/trigger/download` - Manually trigger downloads
- `POST /api/enhanced-scheduler/trigger/discovery` - Manually trigger video discovery

### Health Monitoring

- `GET /api/enhanced-scheduler/health` - Health check endpoint (no auth required)
- `GET /api/enhanced-scheduler/config` - Get environment configuration
- `GET /api/enhanced-scheduler/logs` - Get recent log entries (placeholder)

### Example API Usage

```bash
# Check scheduler status
curl -u admin:admin http://localhost:5000/api/enhanced-scheduler/status

# Manually trigger downloads
curl -u admin:admin -X POST http://localhost:5000/api/enhanced-scheduler/trigger/download

# Health check (no auth required)
curl http://localhost:5000/api/enhanced-scheduler/health
```

## Comparison with Standard Scheduler

| Feature | Standard Scheduler | Enhanced Scheduler |
|---------|-------------------|-------------------|
| Docker Support | Basic | Native |
| Environment Config | Database only | Environment variables |
| Signal Handling | Limited | Full SIGTERM/SIGINT/SIGQUIT |
| Health Checks | None | Built-in endpoints |
| Manual Triggers | Limited | Full REST API |
| Logging | Basic | Enhanced with emojis |
| Graceful Shutdown | Basic | Advanced with timeouts |

## Migration

### From Standard to Enhanced

1. **Set Environment Variable**:
   ```bash
   export MVIDARR_USE_ENHANCED_SCHEDULER=true
   ```

2. **Configure Environment Variables** (optional):
   ```bash
   export MVIDARR_AUTO_DOWNLOAD_TIME=04:00
   export MVIDARR_MAX_DOWNLOADS_PER_RUN=20
   ```

3. **Restart Application**:
   The enhanced scheduler will be used automatically.

### Database Settings Override

Environment variables take precedence over database settings when the enhanced scheduler is enabled. This ensures consistent behavior in containerized environments.

## Troubleshooting

### Check Scheduler Status

```bash
# Via API
curl -u admin:admin http://localhost:5000/api/enhanced-scheduler/status

# Via health endpoint
curl http://localhost:5000/api/enhanced-scheduler/health
```

### Common Issues

1. **Scheduler Not Starting**:
   - Check if `auto_download_schedule_enabled` is set to `true` in settings
   - Verify environment variables are properly set
   - Check application logs for error messages

2. **Downloads Not Running**:
   - Verify there are videos marked as "WANTED"
   - Check download schedule configuration
   - Use manual trigger to test functionality

3. **Health Check Failures**:
   - Ensure scheduler thread is alive
   - Check if jobs are properly scheduled
   - Verify environment configuration

### Log Messages

The enhanced scheduler uses emoji-enhanced logging for easy identification:

- 🔽 Starting scheduled download task
- 📭 No videos found for download
- 📋 Found X videos to download
- ⬇️ Downloading specific video
- ✅ Successfully started download
- ❌ Failed to download
- 📊 Task completion summary
- 🔍 Starting scheduled discovery
- 🏥 Health check operations
- ⚠️ Warning conditions

## Performance Considerations

- **Memory Usage**: Enhanced scheduler has minimal memory overhead
- **CPU Usage**: Efficient with configurable health check intervals
- **Network**: Health endpoints are lightweight
- **Storage**: Logs are managed by the application logger

## Security

- **Authentication**: All management endpoints require authentication
- **Health Checks**: Health endpoint accessible without auth for monitoring systems
- **Environment Variables**: Sensitive configuration via environment variables
- **Signal Handling**: Secure shutdown procedures

## Contributing

When modifying the enhanced scheduler:

1. Follow the existing emoji logging pattern
2. Maintain environment variable precedence over database settings
3. Ensure graceful shutdown behavior
4. Add appropriate health check indicators
5. Update documentation for new configuration options