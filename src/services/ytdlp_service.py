"""
yt-dlp CLI service for downloading videos directly
"""

import json
import os
import shutil
import subprocess
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.database.connection import get_db
from src.database.models import Video
from src.services.settings_service import settings
from src.utils.filename_cleanup import FilenameCleanup
from src.utils.logger import get_logger

logger = get_logger("mvidarr.ytdlp_service")


class YtDlpService:
    """Service for downloading videos using yt-dlp CLI directly"""

    def __init__(self):
        # Find yt-dlp executable dynamically
        self.yt_dlp_path = (
            shutil.which("yt-dlp")
            or shutil.which("yt-dlp.exe")
            or "/usr/local/bin/yt-dlp"
        )
        self.active_downloads = {}
        self.download_queue = []
        self.download_history = []
        self._next_id = 1
        self.custom_cookie_file = None

    def _get_next_id(self) -> int:
        """Get next unique download ID"""
        download_id = self._next_id
        self._next_id += 1
        return download_id

    def add_music_video_download(
        self,
        artist: str,
        title: str,
        url: str,
        quality: str = "best",
        video_id: int = None,
        download_subtitles: bool = False,
        artist_folder_path: str = None,
    ) -> Dict:
        """
        Add a music video download using yt-dlp CLI directly

        Args:
            artist: Artist name
            title: Video title
            url: Video URL
            quality: Video quality preference
            video_id: Optional video ID for database tracking
            download_subtitles: Whether to download closed captions/subtitles
            artist_folder_path: Optional custom folder path for the artist (overrides artist name)

        Returns:
            Dictionary with download submission result
        """
        try:
            # Get music videos path from settings
            music_videos_path = settings.get("music_videos_path", "data/musicvideos")

            # If setting exists but is empty, use default
            if not music_videos_path or music_videos_path.strip() == "":
                music_videos_path = "data/musicvideos"

            # Ensure base music videos directory exists first
            try:
                os.makedirs(music_videos_path, exist_ok=True, mode=0o755)
                logger.info(f"Ensured base directory exists: {music_videos_path}")
            except Exception as base_e:
                logger.error(
                    f"Failed to create base directory {music_videos_path}: {base_e}"
                )
                return {
                    "success": False,
                    "error": f"Cannot create base directory: {str(base_e)}",
                }

            # Determine folder name: use artist_folder_path if provided, otherwise sanitized artist name
            if artist_folder_path and artist_folder_path.strip():
                folder_name = FilenameCleanup.sanitize_folder_name(
                    artist_folder_path.strip()
                )
                logger.info(f"Using custom folder path: {folder_name}")
            else:
                folder_name = FilenameCleanup.sanitize_folder_name(artist)
                logger.info(f"Using auto-generated folder name: {folder_name}")

            clean_title = FilenameCleanup.sanitize_folder_name(title)

            # Create output path: music_videos_path/folder_name/
            output_dir = os.path.join(music_videos_path, folder_name)

            # Debug logging for permission issues
            logger.info(f"Attempting to create directory: {output_dir}")
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(
                f"Music videos path exists: {os.path.exists(music_videos_path)}"
            )
            logger.info(
                f"Music videos path writable: {os.access(music_videos_path, os.W_OK)}"
            )

            try:
                os.makedirs(output_dir, exist_ok=True, mode=0o755)
                logger.info(f"Successfully created directory: {output_dir}")
            except PermissionError as e:
                logger.error(f"Permission denied creating {output_dir}: {e}")
                if os.path.exists(music_videos_path):
                    logger.error(
                        f"Parent directory permissions: {oct(os.stat(music_videos_path).st_mode)}"
                    )
                    logger.error(
                        f"Parent directory owner: {os.stat(music_videos_path).st_uid}:{os.stat(music_videos_path).st_gid}"
                    )

                # Try alternative approach: create without specifying mode
                try:
                    logger.info(
                        "Attempting fallback directory creation without mode specification"
                    )
                    os.makedirs(output_dir, exist_ok=True)
                    logger.info(f"Fallback successful for directory: {output_dir}")
                except Exception as fallback_e:
                    logger.error(f"Fallback also failed: {fallback_e}")
                    return {
                        "success": False,
                        "error": f"Cannot create artist directory: {str(e)}",
                    }
            except Exception as e:
                logger.error(f"Unexpected error creating {output_dir}: {e}")
                return {
                    "success": False,
                    "error": f"Directory creation failed: {str(e)}",
                }

            # Create download entry
            download_id = self._get_next_id()
            download_entry = {
                "id": download_id,
                "artist": artist,
                "artist_folder_path": artist_folder_path,
                "title": title,
                "url": url,
                "quality": quality,
                "video_id": video_id,
                "download_subtitles": download_subtitles,
                "status": "pending",
                "progress": 0,
                "output_dir": output_dir,
                "created_at": datetime.utcnow().isoformat(),
                "started_at": None,
                "completed_at": None,
                "error_message": None,
                "file_path": None,
                "file_size": None,
                "db_download_id": None,  # Track corresponding database ID
            }

            # Create database record for persistent history
            try:
                from src.database.models import Artist as ArtistModel
                from src.database.models import Download

                with get_db() as session:
                    # Find or create artist
                    artist_obj = (
                        session.query(ArtistModel).filter_by(name=artist).first()
                    )
                    if not artist_obj:
                        artist_obj = ArtistModel(name=artist)
                        session.add(artist_obj)
                        session.flush()  # Get the ID

                    # Create database download record
                    db_download = Download(
                        artist_id=artist_obj.id,
                        video_id=video_id,
                        title=title,
                        original_url=url,
                        quality=quality,
                        status="pending",
                        progress=0,
                    )
                    session.add(db_download)
                    session.commit()

                    # Store the database ID in the download entry
                    download_entry["db_download_id"] = db_download.id
                    logger.info(
                        f"Created database download record with ID {db_download.id}"
                    )

            except Exception as db_error:
                logger.warning(f"Failed to create database download record: {db_error}")
                # Continue with in-memory tracking even if database fails

            # Add to queue
            self.download_queue.append(download_entry)
            self.active_downloads[download_id] = download_entry

            # Start download in background thread
            thread = threading.Thread(
                target=self._download_video, args=(download_entry,)
            )
            thread.daemon = True
            thread.start()

            logger.info(f"Queued download: {artist} - {title}")

            return {
                "success": True,
                "id": download_id,
                "message": f"Download queued: {artist} - {title}",
            }

        except Exception as e:
            logger.error(f"Failed to queue download: {e}")
            return {"success": False, "error": str(e)}

    def _download_video(self, download_entry: Dict):
        """Download video using yt-dlp CLI with fallback cookie sources"""
        download_id = download_entry["id"]
        video_id = download_entry.get("video_id")

        try:
            download_entry["status"] = "downloading"
            download_entry["started_at"] = datetime.utcnow().isoformat()

            # Update database status to downloading
            self._update_database_download_status(download_entry, "downloading")

            # Build yt-dlp command - use just the song name as requested
            output_template = os.path.join(
                download_entry["output_dir"],
                f"{FilenameCleanup.sanitize_folder_name(download_entry['title'])}.%(ext)s",
            )

            # Try different cookie sources for age-restricted videos
            cookie_sources = []

            # First, try uploaded cookie file if available
            if self.custom_cookie_file and os.path.exists(self.custom_cookie_file):
                cookie_sources.append(("file", self.custom_cookie_file))

            # Then try browser cookies
            cookie_sources.extend(
                [
                    ("browser", "firefox"),
                    ("browser", "chrome"),
                    ("browser", "chromium"),
                    ("browser", "edge"),
                    (None, None),  # Fallback with no cookies
                ]
            )

            success = False
            last_error = None

            for cookie_type, cookie_source in cookie_sources:
                if cookie_type == "file":
                    logger.info(
                        f"Attempting download {download_id} with uploaded cookie file: {cookie_source}"
                    )
                elif cookie_type == "browser":
                    logger.info(
                        f"Attempting download {download_id} with cookies from browser: {cookie_source}"
                    )
                else:
                    logger.info(f"Attempting download {download_id} with no cookies")

                cmd = [
                    self.yt_dlp_path,
                    "--format",
                    "best[height<=1080]",  # Limit to 1080p max
                    "--output",
                    output_template,
                    "--no-playlist",
                    "--write-info-json",
                    "--embed-metadata",
                    "--add-metadata",
                    "--ignore-errors",  # Continue on errors
                    "--no-check-certificate",  # Skip SSL certificate verification if needed
                ]

                # Add cookie source if available
                if cookie_type == "file":
                    cmd.extend(["--cookies", cookie_source])
                elif cookie_type == "browser":
                    cmd.extend(["--cookies-from-browser", cookie_source])

                # Add subtitle options if requested
                if download_entry.get("download_subtitles", False):
                    cmd.extend(
                        [
                            "--write-subs",  # Download subtitle files
                            "--write-auto-subs",  # Download auto-generated subtitles
                            "--sub-langs",
                            "en,en-US",  # Prefer English subtitles
                            "--embed-subs",  # Embed subtitles in video file
                        ]
                    )

                cmd.append(download_entry["url"])

                try:
                    # Execute yt-dlp
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        universal_newlines=True,
                    )

                    # Monitor progress
                    output_lines = []
                    for line in iter(process.stdout.readline, ""):
                        output_lines.append(line.strip())

                        # Parse progress if available
                        if "[download]" in line and "%" in line:
                            try:
                                # Extract percentage
                                parts = line.split()
                                for part in parts:
                                    if "%" in part:
                                        progress_str = part.replace("%", "")
                                        download_entry["progress"] = float(progress_str)
                                        break
                            except:
                                pass

                    process.wait()

                    if process.returncode == 0:
                        # Download successful
                        download_entry["status"] = "completed"
                        download_entry["completed_at"] = datetime.utcnow().isoformat()
                        download_entry["progress"] = 100

                        # Find downloaded file
                        for ext in ["mp4", "mkv", "webm", "avi"]:
                            potential_file = output_template.replace("%(ext)s", ext)
                            if os.path.exists(potential_file):
                                download_entry["file_path"] = potential_file
                                download_entry["file_size"] = os.path.getsize(
                                    potential_file
                                )
                                break

                        if cookie_type == "file":
                            logger.info(
                                f"Download {download_id} completed successfully using uploaded cookie file"
                            )
                        elif cookie_type == "browser":
                            logger.info(
                                f"Download {download_id} completed successfully using cookies from: {cookie_source}"
                            )
                        else:
                            logger.info(
                                f"Download {download_id} completed successfully with no cookies"
                            )

                        # Sync to database (both Video and Download models)
                        self._update_video_status_in_database(
                            video_id,
                            "DOWNLOADED",
                            download_entry.get("file_path"),
                            download_entry.get("file_size"),
                        )
                        self._update_database_download_status(
                            download_entry,
                            "completed",
                            download_entry.get("file_path"),
                            download_entry.get("file_size"),
                        )
                        success = True
                        break
                    else:
                        # This attempt failed, try next cookie source
                        error_output = "\n".join(output_lines[-5:])  # Last 5 lines
                        last_error = error_output

                        if cookie_type == "file":
                            logger.warning(
                                f"Download {download_id} failed with uploaded cookie file: {error_output}"
                            )
                        elif cookie_type == "browser":
                            logger.warning(
                                f"Download {download_id} failed with {cookie_source} cookies: {error_output}"
                            )
                        else:
                            logger.warning(
                                f"Download {download_id} failed with no cookies: {error_output}"
                            )

                except Exception as attempt_error:
                    # This attempt failed, try next cookie source
                    last_error = str(attempt_error)

                    if cookie_type == "file":
                        logger.warning(
                            f"Download {download_id} attempt with uploaded cookie file failed: {attempt_error}"
                        )
                    elif cookie_type == "browser":
                        logger.warning(
                            f"Download {download_id} attempt with {cookie_source} cookies failed: {attempt_error}"
                        )
                    else:
                        logger.warning(
                            f"Download {download_id} attempt with no cookies failed: {attempt_error}"
                        )

            if not success:
                # All attempts failed
                download_entry["status"] = "failed"
                download_entry["completed_at"] = datetime.utcnow().isoformat()
                download_entry["error_message"] = (
                    f"All download attempts failed. Last error: {last_error}"
                )
                self._update_video_status_in_database(video_id, "FAILED")
                self._update_database_download_status(
                    download_entry,
                    "failed",
                    None,
                    None,
                    download_entry["error_message"],
                )
                logger.error(
                    f"Download {download_id} failed after all attempts: {last_error}"
                )

        except Exception as e:
            download_entry["status"] = "failed"
            download_entry["completed_at"] = datetime.utcnow().isoformat()
            download_entry["error_message"] = str(e)
            self._update_video_status_in_database(video_id, "FAILED")
            self._update_database_download_status(
                download_entry, "failed", None, None, str(e)
            )
            logger.error(f"Download {download_id} exception: {e}")

        finally:
            # Move from active to history
            if download_id in self.active_downloads:
                self.download_history.append(self.active_downloads[download_id])
                del self.active_downloads[download_id]

            # Remove from queue
            self.download_queue = [
                d for d in self.download_queue if d["id"] != download_id
            ]

    def _update_video_status_in_database(
        self, video_id: int, status: str, file_path: str = None, file_size: int = None
    ):
        """Update video status in database"""
        if not video_id:
            return

        try:
            with get_db() as session:
                video = session.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = status
                    if file_path:
                        video.local_path = file_path
                    if status == "DOWNLOADED":
                        # Ensure we have the file info
                        if file_path and os.path.exists(file_path):
                            video.local_path = file_path
                            if not file_size:
                                file_size = os.path.getsize(file_path)
                    session.commit()
                    logger.info(
                        f"Updated video {video_id} status to {status} in database"
                    )
                else:
                    logger.warning(f"Video {video_id} not found in database")
        except Exception as e:
            logger.error(f"Failed to update video {video_id} status in database: {e}")

    def _update_database_download_status(
        self,
        download_entry: dict,
        status: str,
        file_path: str = None,
        file_size: int = None,
        error_message: str = None,
    ):
        """Update download status in database"""
        db_download_id = download_entry.get("db_download_id")
        if not db_download_id:
            return

        try:
            from src.database.models import Download

            with get_db() as session:
                db_download = (
                    session.query(Download)
                    .filter(Download.id == db_download_id)
                    .first()
                )
                if db_download:
                    db_download.status = status
                    db_download.progress = download_entry.get("progress", 0)
                    db_download.updated_at = datetime.utcnow()

                    if file_path:
                        db_download.file_path = file_path
                    if file_size:
                        db_download.file_size = file_size
                    if error_message:
                        db_download.error_message = error_message

                    session.commit()
                    logger.info(
                        f"Updated database download {db_download_id} status to {status}"
                    )
                else:
                    logger.warning(f"Database download {db_download_id} not found")
        except Exception as e:
            logger.error(f"Failed to update database download {db_download_id}: {e}")

    def get_queue(self) -> Dict:
        """Get current download queue status"""
        queue_items = list(self.active_downloads.values())
        return {"queue": queue_items, "count": len(queue_items)}

    def get_history(self, limit: int = 50) -> Dict:
        """Get download history from both in-memory and database sources"""
        try:
            # Get in-memory history
            memory_history = list(self.download_history)

            # Get database history
            database_history = []
            try:
                from src.database.models import Artist, Download, Video

                with get_db() as session:
                    # Query database downloads with artist and video info
                    db_downloads = (
                        session.query(Download, Artist.name, Video.title)
                        .join(Artist, Download.artist_id == Artist.id)
                        .outerjoin(Video, Download.video_id == Video.id)
                        .order_by(Download.created_at.desc())
                        .limit(limit * 2)  # Get more to account for merging
                        .all()
                    )

                    for download, artist_name, video_title in db_downloads:
                        # Convert database download to ytdlp_service format
                        db_entry = {
                            "id": f"db_{download.id}",  # Prefix to avoid ID conflicts
                            "artist": artist_name,
                            "title": video_title or download.title,
                            "url": download.original_url,
                            "quality": download.quality or "best",
                            "video_id": download.video_id,
                            "download_subtitles": False,
                            "status": download.status,
                            "progress": download.progress,
                            "output_dir": (
                                os.path.dirname(download.file_path)
                                if download.file_path
                                else None
                            ),
                            "created_at": download.created_at.isoformat(),
                            "started_at": download.created_at.isoformat(),
                            "completed_at": (
                                download.updated_at.isoformat()
                                if download.status in ["completed", "failed"]
                                else None
                            ),
                            "error_message": download.error_message,
                            "file_path": download.file_path,
                            "file_size": download.file_size,
                        }
                        database_history.append(db_entry)

            except Exception as db_error:
                logger.warning(f"Failed to get database download history: {db_error}")
                # Continue with just in-memory history if database fails

            # Combine and deduplicate histories
            all_history = memory_history + database_history

            # Deduplicate based on URL and creation time (keep most recent)
            seen_downloads = {}
            deduplicated_history = []

            for entry in all_history:
                # Create a unique key based on URL and title
                key = f"{entry.get('url', '')}_{entry.get('title', '')}"
                created_at = entry.get("created_at", "")

                # Keep the entry with the latest created_at for each unique download
                if (
                    key not in seen_downloads
                    or created_at > seen_downloads[key]["created_at"]
                ):
                    seen_downloads[key] = entry

            # Convert back to list and sort by creation time (most recent first)
            deduplicated_history = list(seen_downloads.values())
            deduplicated_history.sort(
                key=lambda x: x.get("created_at", ""), reverse=True
            )

            # Apply limit
            recent_history = (
                deduplicated_history[:limit] if limit > 0 else deduplicated_history
            )

            return {
                "history": recent_history,
                "count": len(recent_history),
                "memory_count": len(memory_history),
                "database_count": len(database_history),
            }

        except Exception as e:
            logger.error(f"Error getting download history: {e}")
            # Fallback to original in-memory only behavior
            recent_history = (
                self.download_history[-limit:] if limit > 0 else self.download_history
            )
            return {
                "history": list(reversed(recent_history)),
                "count": len(recent_history),
            }

    def stop_download(self, download_id: int) -> Dict:
        """Stop a download (not easily implemented with subprocess, return success for UI)"""
        if download_id in self.active_downloads:
            download_entry = self.active_downloads[download_id]
            download_entry["status"] = "stopped"
            download_entry["completed_at"] = datetime.utcnow().isoformat()
            download_entry["error_message"] = "Download stopped by user"

            # Move to history
            self.download_history.append(download_entry)
            del self.active_downloads[download_id]

            return {"success": True, "message": f"Download {download_id} stopped"}

        return {"success": False, "error": "Download not found"}

    def retry_download(self, download_id: int) -> Dict:
        """Retry a failed download"""
        # Find in history
        for entry in self.download_history:
            if entry["id"] == download_id and entry["status"] in ["failed", "stopped"]:
                # Create new download with same parameters
                return self.add_music_video_download(
                    artist=entry["artist"],
                    title=entry["title"],
                    url=entry["url"],
                    quality=entry["quality"],
                    video_id=entry.get("video_id"),
                    download_subtitles=entry.get("download_subtitles", False),
                    artist_folder_path=entry.get("artist_folder_path"),
                )

        return {"success": False, "error": "Download not found or not retryable"}

    def clear_history(self) -> Dict:
        """Clear download history from both memory and database"""
        memory_count = len(self.download_history)
        self.download_history.clear()

        # Also clear database records
        db_count = 0
        try:
            from src.database.models import Download

            with get_db() as session:
                db_count = session.query(Download).count()
                session.query(Download).delete()
                session.commit()
                logger.info(f"Cleared {db_count} download records from database")
        except Exception as e:
            logger.error(f"Failed to clear download history from database: {e}")
            # Still return success for memory clearing even if DB fails

        # Also clear download queue to prevent re-adding completed downloads
        cleared_queue_count = len(self.download_queue)
        self.download_queue.clear()

        total_count = memory_count + db_count
        logger.info(
            f"Clear history summary - Memory: {memory_count}, Database: {db_count}, Queue: {cleared_queue_count}"
        )

        return {
            "success": True,
            "deleted_count": total_count,
            "details": {
                "memory": memory_count,
                "database": db_count,
                "queue_cleared": cleared_queue_count,
            },
        }

    def clear_stuck_downloads(self, minutes: int = 10) -> Dict:
        """Clear downloads stuck at 0% for more than specified minutes"""
        current_time = datetime.utcnow()
        cleared_count = 0

        stuck_ids = []
        for download_id, entry in self.active_downloads.items():
            if entry["status"] == "downloading" and entry["progress"] == 0:
                started_at = (
                    datetime.fromisoformat(entry["started_at"])
                    if entry["started_at"]
                    else current_time
                )
                if (current_time - started_at).total_seconds() > (minutes * 60):
                    stuck_ids.append(download_id)

        for download_id in stuck_ids:
            self.stop_download(download_id)
            cleared_count += 1

        return {"success": True, "cleared_count": cleared_count}

    def set_cookie_file(self, cookie_file_path: str):
        """Set custom cookie file for age-restricted videos"""
        self.custom_cookie_file = cookie_file_path
        logger.info(f"Custom cookie file set: {cookie_file_path}")

    def clear_cookie_file(self):
        """Clear custom cookie file"""
        self.custom_cookie_file = None
        logger.info("Custom cookie file cleared")

    def get_cookie_status(self) -> Dict:
        """Get status of custom cookie file"""
        if self.custom_cookie_file and os.path.exists(self.custom_cookie_file):
            try:
                stat = os.stat(self.custom_cookie_file)
                return {
                    "cookies_available": True,
                    "file_path": self.custom_cookie_file,
                    "file_size": stat.st_size,
                    "modified_time": stat.st_mtime,
                }
            except Exception as e:
                return {"cookies_available": False, "error": str(e)}
        else:
            return {"cookies_available": False}

    def health_check(self) -> Dict:
        """Check if yt-dlp is available and working"""
        try:
            result = subprocess.run(
                [self.yt_dlp_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                cookie_status = self.get_cookie_status()
                return {
                    "status": "healthy",
                    "version": result.stdout.strip(),
                    "active_downloads": len(self.active_downloads),
                    "queued_downloads": len(self.download_queue),
                    "cookie_status": cookie_status,
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "yt-dlp command failed",
                    "stderr": result.stderr,
                }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global instance
ytdlp_service = YtDlpService()
