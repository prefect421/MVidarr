"""
YouTube Quality Check Service

Checks YouTube for available video qualities and stores results in the database.
This helps determine which videos are truly upgradeable.
"""

import re
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_

from src.database.connection import get_db
from src.database.models import Video, VideoStatus
from src.utils.logger import get_logger

logger = get_logger("mvidarr.youtube_quality_check")


class YouTubeQualityCheckService:
    """Service for checking available YouTube video qualities"""

    def __init__(self):
        self.rate_limit_delay = 2.0  # Seconds between requests to avoid throttling
        self.last_request_time = 0

    def _rate_limit(self):
        """Implement rate limiting for YouTube requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def check_video_quality(self, video: Video) -> Dict:
        """
        Check available qualities for a single video
        
        Args:
            video: Video database object
            
        Returns:
            Dictionary with quality check results
        """
        result = {
            "success": False,
            "available_qualities": [],
            "max_available_quality": None,
            "error": None,
            "check_date": datetime.utcnow()
        }

        try:
            # Get video URL
            video_url = video.youtube_url or video.url
            if not video_url:
                result["error"] = "No video URL available"
                return result

            # Rate limit requests
            self._rate_limit()

            # Run yt-dlp to get available formats
            logger.info(f"Checking available qualities for video {video.id}: {video.title}")
            
            cmd = [
                "yt-dlp",
                "--list-formats",
                "--no-warnings",
                video_url
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if process.returncode != 0:
                result["error"] = f"yt-dlp failed: {process.stderr.strip()}"
                return result

            # Parse the output to extract available qualities
            qualities = self._parse_formats_output(process.stdout)
            
            result["available_qualities"] = qualities
            result["max_available_quality"] = self._get_max_quality(qualities)
            result["success"] = True

            logger.info(f"Video {video.id} qualities: {qualities}, max: {result['max_available_quality']}")

        except subprocess.TimeoutExpired:
            result["error"] = "yt-dlp request timed out"
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error checking quality for video {video.id}: {e}")

        return result

    def _parse_formats_output(self, output: str) -> List[Dict]:
        """
        Parse yt-dlp format list output to extract quality information
        
        Args:
            output: Raw yt-dlp output
            
        Returns:
            List of quality dictionaries
        """
        qualities = []
        
        # Look for format lines (skip headers and storyboards)
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Skip headers, empty lines, and storyboard formats
            if not line or line.startswith('ID') or line.startswith('-') or 'storyboard' in line:
                continue
                
            # Parse format line: ID EXT RESOLUTION FPS CH | FILESIZE TBR PROTO | VCODEC VBR ACODEC ASR MORE
            parts = line.split()
            if len(parts) < 3:
                continue
                
            try:
                format_id = parts[0]
                extension = parts[1]
                resolution = parts[2] if parts[2] != 'audio' else None
                
                # Skip audio-only formats
                if resolution is None or resolution == 'only':
                    continue
                
                # Extract height from resolution (e.g., "1920x1080" -> 1080)
                height = None
                if 'x' in resolution:
                    try:
                        height = int(resolution.split('x')[1])
                    except (ValueError, IndexError):
                        pass
                
                if height:
                    quality_dict = {
                        "format_id": format_id,
                        "extension": extension,
                        "resolution": resolution,
                        "height": height,
                        "quality_label": f"{height}p"
                    }
                    qualities.append(quality_dict)
                    
            except (IndexError, ValueError) as e:
                # Skip malformed lines
                continue
                
        # Sort by height (highest first)
        qualities.sort(key=lambda x: x["height"], reverse=True)
        return qualities

    def _get_max_quality(self, qualities: List[Dict]) -> Optional[str]:
        """
        Get the maximum available quality from the qualities list
        
        Args:
            qualities: List of quality dictionaries
            
        Returns:
            String representation of max quality (e.g., "1080p") or None
        """
        if not qualities:
            return None
            
        # Already sorted by height (highest first)
        return qualities[0]["quality_label"]

    def update_video_quality_info(self, video: Video, check_result: Dict):
        """
        Update video record with quality check results
        
        Args:
            video: Video database object
            check_result: Result from check_video_quality
        """
        try:
            video.available_qualities = check_result["available_qualities"]
            video.quality_check_date = check_result["check_date"]
            video.max_available_quality = check_result["max_available_quality"]
            
            if check_result["success"]:
                video.quality_check_status = "success"
            else:
                video.quality_check_status = "failed"
                logger.warning(f"Quality check failed for video {video.id}: {check_result['error']}")

        except Exception as e:
            logger.error(f"Error updating video {video.id} quality info: {e}")
            video.quality_check_status = "failed"

    def check_all_videos(self, limit: Optional[int] = None, only_unchecked: bool = True) -> Dict:
        """
        Check qualities for multiple videos
        
        Args:
            limit: Maximum number of videos to check
            only_unchecked: Only check videos not checked recently
            
        Returns:
            Summary of check results
        """
        summary = {
            "total_checked": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "skipped": 0,
            "errors": []
        }

        try:
            with get_db() as session:
                # Build query for videos to check
                query = session.query(Video).filter(
                    Video.status == VideoStatus.DOWNLOADED,
                    Video.youtube_url.isnot(None)
                )

                # Only check videos not checked in the last 7 days
                if only_unchecked:
                    week_ago = datetime.utcnow() - timedelta(days=7)
                    query = query.filter(
                        and_(
                            Video.quality_check_date.is_(None),
                            Video.quality_check_date < week_ago
                        )
                    )

                if limit:
                    query = query.limit(limit)

                videos = query.all()
                
                logger.info(f"Starting quality check for {len(videos)} videos")

                for video in videos:
                    try:
                        # Check this video's quality
                        check_result = self.check_video_quality(video)
                        
                        # Update the database
                        self.update_video_quality_info(video, check_result)
                        session.commit()
                        
                        summary["total_checked"] += 1
                        if check_result["success"]:
                            summary["successful_checks"] += 1
                        else:
                            summary["failed_checks"] += 1
                            summary["errors"].append(f"Video {video.id}: {check_result['error']}")

                    except Exception as e:
                        summary["failed_checks"] += 1
                        summary["errors"].append(f"Video {video.id}: {str(e)}")
                        logger.error(f"Error processing video {video.id}: {e}")

                logger.info(f"Quality check complete: {summary}")

        except Exception as e:
            logger.error(f"Error in check_all_videos: {e}")
            summary["errors"].append(str(e))

        return summary

    def is_video_upgradeable(self, video: Video) -> bool:
        """
        Check if a video is truly upgradeable based on quality check data
        
        Args:
            video: Video database object
            
        Returns:
            True if video can be upgraded to better quality
        """
        # Must have quality check data
        if not video.quality_check_date or video.quality_check_status != "success":
            return False
            
        # Must have current quality
        current_quality = video.quality
        if not current_quality:
            return False
            
        # Must have max available quality
        max_available = video.max_available_quality
        if not max_available:
            return False
            
        # Compare qualities (extract numeric height)
        try:
            current_height = int(re.sub(r'[^\d]', '', current_quality))
            max_height = int(re.sub(r'[^\d]', '', max_available))
            
            return max_height > current_height
            
        except (ValueError, TypeError):
            return False


# Global service instance
youtube_quality_check_service = YouTubeQualityCheckService()