# Automatic Downloads - Issue #100

## Overview
MVidarr now supports automatic downloading of videos marked as "WANTED" through a comprehensive scheduler service. The scheduler can be configured to check for and download wanted videos at regular intervals, including hourly downloads.

## Scheduler Configuration

### Default Settings (Optimized for Hourly Downloads)
- **Enabled**: `true` (automatic downloads enabled by default)
- **Frequency**: `hourly` (checks every hour)  
- **Max Videos per Run**: `10` (optimized for frequent checks)
- **Schedule Time**: `02:00` (ignored for hourly downloads)

### Available Frequencies

#### Hourly Downloads (Recommended)
```
Schedule Frequency: hourly
- Checks for wanted videos every hour
- Downloads up to 10 videos per check (configurable)
- Provides consistent, timely downloads
- Optimized logging (debug level when no videos found)
```

#### Daily Downloads
```
Schedule Frequency: daily
Schedule Time: 02:00 (or custom time)
- Checks once per day at specified time
- Downloads up to 50 videos per check (configurable)
- Good for less frequent, bulk processing
```

#### Weekly Downloads
```
Schedule Frequency: weekly
Schedule Time: 02:00 (or custom time)
- Checks once per week on Sunday at specified time
- Downloads up to 50 videos per check (configurable)
- Suitable for minimal maintenance setups
```

#### Custom Day Downloads
```
Schedule Frequency: monday,wednesday,friday
Schedule Time: 02:00 (or custom time)
- Checks on specified days at specified time
- Supports comma-separated day names
- Downloads up to 50 videos per check (configurable)
```

## Configuration Settings

### Database Settings
All scheduler settings are stored in the database and can be modified through the Settings API:

| Setting Key | Default Value | Description |
|-------------|---------------|-------------|
| `auto_download_schedule_enabled` | `true` | Enable/disable automatic downloads |
| `auto_download_schedule_days` | `hourly` | Schedule frequency |
| `auto_download_schedule_time` | `02:00` | Time for daily/weekly/custom schedules |
| `auto_download_max_videos` | `10` | Max videos per scheduled run |

### Settings API Endpoints
- **GET** `/api/settings/scheduler/status` - Get scheduler status and configuration
- **POST** `/api/settings/scheduler/start` - Start the scheduler service
- **POST** `/api/settings/scheduler/stop` - Stop the scheduler service
- **POST** `/api/settings/scheduler/reload` - Reload scheduler configuration

### Environment Variables
Settings can also be configured via environment variables:
```bash
AUTO_DOWNLOAD_SCHEDULE_ENABLED=true
AUTO_DOWNLOAD_SCHEDULE_DAYS=hourly
AUTO_DOWNLOAD_SCHEDULE_TIME=02:00
AUTO_DOWNLOAD_MAX_VIDEOS=10
```

## How It Works

### Automatic Startup
1. **Application Start**: Scheduler automatically starts if `auto_download_schedule_enabled` is `true`
2. **Service Initialization**: Background thread starts and configures scheduled jobs
3. **Job Scheduling**: Jobs are scheduled based on the configured frequency
4. **Continuous Operation**: Scheduler runs continuously, checking for scheduled jobs

### Download Process
1. **Scheduled Check**: At the configured interval, scheduler triggers download check
2. **Wanted Video Query**: System queries database for videos with `WANTED` status
3. **Batch Processing**: Downloads up to the configured maximum number of videos
4. **Queue Management**: Videos are queued for download via the existing download system
5. **Status Tracking**: Download results are logged with success/failure counts

### Hourly Download Optimization
For hourly downloads, the system includes several optimizations:

#### Smart Logging
- **Debug Level**: When no wanted videos are found (reduces log noise)
- **Info Level**: When wanted videos are found and downloads are queued
- **Status Updates**: Periodic logging of wanted video count

#### Resource Management
- **Reduced Batch Size**: Default 10 videos per hour vs 50 for daily
- **Pre-check Optimization**: Counts wanted videos before attempting downloads
- **Early Exit**: Skips download process if no wanted videos exist

#### Error Handling
- **Graceful Failures**: Individual download failures don't stop the scheduler
- **Continuous Operation**: Scheduler continues running even if download attempts fail
- **Automatic Retry**: Next scheduled run will retry failed downloads

## Monitoring and Troubleshooting

### Scheduler Status
Check scheduler status via API or application logs:
```bash
# Get scheduler status
curl http://localhost:5000/api/settings/scheduler/status

# Check application logs
docker logs mvidarr | grep scheduler
```

### Log Messages
```bash
# Scheduler startup
[INFO] Starting scheduler service...
[INFO] Scheduled hourly downloads (every hour)

# Hourly operations
[INFO] Hourly check: Found 5 wanted videos, attempting to download up to 10
[INFO] Hourly download completed: 5 queued, 0 failed, 5 total wanted videos

# Status monitoring (every 5 minutes)
[INFO] Hourly scheduler: 3 videos currently marked as WANTED
```

### Common Issues

#### Scheduler Not Starting
- **Check Settings**: Verify `auto_download_schedule_enabled` is `true`
- **Database Connection**: Ensure database is accessible
- **Settings Service**: Confirm SettingsService is properly initialized

#### Downloads Not Processing
- **Wanted Videos**: Verify videos are marked with `WANTED` status
- **Download Service**: Check that the underlying download service is working
- **API Keys**: Ensure required API keys (YouTube, etc.) are configured

#### Too Many/Few Downloads
- **Adjust Max Videos**: Modify `auto_download_max_videos` setting
- **Change Frequency**: Consider switching between hourly/daily scheduling
- **Monitor Queue**: Check download queue status to avoid overwhelming the system

## Integration with Existing Features

### Download Queue
- Automatic downloads use the same queue system as manual downloads
- Downloads appear in the Downloads page with standard progress tracking
- Queue management and prioritization work normally

### Video Status Management
- Only videos with `WANTED` status are considered for automatic downloads
- Status changes to `DOWNLOADING` when queued, then `DOWNLOADED` when complete
- Failed downloads maintain `WANTED` status for retry on next schedule

### Settings Integration
- All scheduler settings integrate with the existing Settings system
- Changes via Settings API immediately reload the scheduler configuration
- Frontend settings interface includes scheduler status and controls

## Benefits of Hourly Downloads

### User Experience
- **Timely Downloads**: Videos are downloaded shortly after being marked as wanted
- **Consistent Processing**: Regular, predictable download intervals
- **Reduced Wait Times**: No need to manually trigger downloads or wait for daily runs

### System Performance
- **Load Distribution**: Smaller, frequent batches vs large bulk operations
- **Resource Management**: Controlled resource usage with optimized batch sizes
- **Responsive System**: System remains responsive during download processing

### Operational Efficiency
- **Automated Workflow**: Complete automation of wanted video processing
- **Reduced Manual Intervention**: Minimal user interaction required
- **Scalable Architecture**: Handles varying loads efficiently

## Migration from Manual Downloads

### Existing Users
- **Automatic Upgrade**: Hourly downloads enabled by default for new installations
- **Backward Compatibility**: Manual "Download Wanted" button continues to work
- **Gradual Transition**: Users can disable automatic downloads if preferred

### Configuration Migration
- **Settings Preservation**: Existing daily/weekly schedules are maintained
- **Easy Switching**: Change `auto_download_schedule_days` to `hourly` to enable
- **No Data Loss**: All existing wanted videos continue to be processed

This automatic download system transforms MVidarr from a manual download management tool into a fully automated video acquisition system, significantly improving the user experience while maintaining system stability and performance.