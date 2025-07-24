# Music Video Organization System

## Overview

MVidarr Enhanced now includes an automatic video organization system that cleans up downloaded video filenames and organizes them into artist-specific folders.

## Features

### Filename Cleanup
- Removes quality indicators (4K, 1080p, 720p, etc.)
- Strips platform-specific tags ([YouTube], [Official Video], etc.)
- Eliminates download metadata and timestamps
- Normalizes special characters and Unicode
- Extracts artist and song title from various filename patterns

### Automatic Organization
- Creates artist folders in the music videos directory
- Moves and renames videos to clean format: "Artist - Title.ext"
- Handles filename conflicts by adding numbers
- Updates database records when matching artists/videos exist
- Preserves original file extensions

### Directory Structure
```
data/music_videos/
├── Taylor Swift/
│   ├── Taylor Swift - Anti-Hero.mp4
│   └── Taylor Swift - Shake It Off.mp4
├── The Weeknd/
│   └── The Weeknd - Blinding Lights.mkv
└── Ed Sheeran/
    └── Ed Sheeran - Shape of You.avi
```

## Usage

### API Endpoints

#### Get Organization Status
```
GET /api/video-organization/status
```
Returns current status including paths, file counts, and directory info.

#### Scan Downloads Directory
```
GET /api/video-organization/downloads/scan
```
Returns list of video files awaiting organization.

#### Organize All Videos
```
POST /api/video-organization/organize-all
```
Processes all videos in downloads directory.

#### Organize Single Video
```
POST /api/video-organization/organize/{filename}
```
Organizes a specific video file.

#### Get Artist Directories
```
GET /api/video-organization/artists
```
Returns list of artist directories with video counts.

#### Preview Organization
```
GET /api/video-organization/preview/{filename}
```
Shows how a file would be organized without moving it.

#### Cleanup Empty Directories
```
POST /api/video-organization/cleanup
```
Removes empty artist directories.

### Command Line Scripts

#### Interactive Organization
```bash
# Organize all videos
python3 scripts/organize_videos.py --organize-all

# Organize specific video
python3 scripts/organize_videos.py --organize "video.mp4"

# Show artist directories
python3 scripts/organize_videos.py --show-artists

# Clean up empty directories
python3 scripts/organize_videos.py --cleanup

# Test filename cleanup
python3 scripts/organize_videos.py --test
```

#### Automated Organization
```bash
# Run automated organization script
./scripts/auto_organize.sh

# Add to crontab for automatic processing
# Run every 30 minutes:
*/30 * * * * /home/mike/mvidarr/scripts/auto_organize.sh
```

## Settings

### Music Videos Path
Configure the organized videos directory in Settings:
- **Setting**: `music_videos_path`
- **Default**: `data/music_videos`
- **Description**: Directory where organized videos are stored by artist

### Downloads Path
The source directory for videos to organize:
- **Setting**: `downloads_path` 
- **Default**: `data/downloads`
- **Description**: Directory where downloads are placed before organization

## Supported Filename Patterns

The system can extract artist and title from various filename formats:

### Delimiter-Based
- `Artist - Song Title.mp4`
- `Artist | Song Title.mkv`
- `Artist : Song Title.avi`
- `Artist – Song Title.webm` (em dash)

### With Metadata
- `Taylor Swift - Anti-Hero [Official Music Video] [4K] (2022).mp4`
- `[Downloaded 2023-12-01] Ed Sheeran - Shape of You (Official).avi`
- `The Weeknd | Blinding Lights (Official Video) [1080p].mkv`

### Cleaned Output
All organized videos follow the format: `Artist - Title.ext`

## File Extension Support

Supported video formats:
- `.mp4`, `.mkv`, `.avi`, `.mov`
- `.wmv`, `.flv`, `.webm`, `.m4v`

## Error Handling

### Common Issues
1. **Cannot extract artist/title**: Files with unrecognizable patterns are skipped
2. **Filename conflicts**: Automatic numbering (e.g., "Song (2).mp4")
3. **Permission errors**: Ensure proper directory permissions
4. **Database errors**: Organization continues even if database updates fail

### Logging
- Application logs: `data/logs/mvidarr.log`
- Auto-organization logs: `data/logs/auto_organize.log`

## Database Integration

When artist and video records exist in the database:
- Updates video record with local file path
- Sets download status to 'completed'
- Updates timestamp for last modification

## Best Practices

1. **Regular Organization**: Set up automated processing to keep downloads organized
2. **Monitor Logs**: Check logs for files that couldn't be processed
3. **Backup Important Files**: Ensure important videos are backed up before organization
4. **Test Patterns**: Use preview functionality to verify organization before processing
5. **Clean Downloads**: Regularly clean the downloads directory after organization

## Troubleshooting

### Videos Not Being Organized
1. Check file extensions are supported
2. Verify filename contains recognizable artist/title pattern
3. Ensure proper permissions on directories
4. Check logs for specific error messages

### Database Connection Issues
1. Organization continues without database updates
2. Check database connectivity in main application
3. Files are still moved and organized properly

### Path Configuration
1. Verify `music_videos_path` setting is correct
2. Ensure directories exist and are writable
3. Check absolute vs relative path configuration