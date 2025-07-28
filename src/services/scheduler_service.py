"""
Background Scheduler Service for MVidarr
Handles scheduled tasks like automated video downloads
"""

import threading
import time
from datetime import datetime
from datetime import time as dt_time
from typing import Any, Dict, Optional

import schedule

from src.database.connection import get_db
from src.database.models import Setting
from src.services.settings_service import SettingsService
from src.utils.logger import get_logger

logger = get_logger("mvidarr.scheduler")


class SchedulerService:
    """Service for managing scheduled tasks"""

    def __init__(self):
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False
        self._last_check_time = None

    def start(self):
        """Start the scheduler service"""
        if self.running:
            logger.warning("Scheduler service is already running")
            return

        logger.info("Starting scheduler service...")
        self.running = True

        # Clear any existing jobs
        schedule.clear()

        # Set up scheduled jobs based on current settings
        self._setup_scheduled_jobs()

        # Start the scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler, daemon=True
        )
        self.scheduler_thread.start()

        logger.info("Scheduler service started successfully")

    def stop(self):
        """Stop the scheduler service"""
        if not self.running:
            logger.warning("Scheduler service is not running")
            return

        logger.info("Stopping scheduler service...")
        self.running = False

        # Clear scheduled jobs
        schedule.clear()

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        logger.info("Scheduler service stopped")

    def reload_schedule(self):
        """Reload the schedule from current settings"""
        logger.info("Reloading scheduled jobs from settings...")

        # Clear existing jobs
        schedule.clear()

        # Set up jobs again
        self._setup_scheduled_jobs()

        logger.info("Scheduled jobs reloaded")

    def _setup_scheduled_jobs(self):
        """Set up scheduled jobs based on current settings"""
        try:
            # Check if scheduled downloads are enabled
            if not SettingsService.get_bool("auto_download_schedule_enabled", False):
                logger.info("Scheduled downloads are disabled")
                return

            # Get schedule settings
            schedule_time = SettingsService.get("auto_download_schedule_time", "02:00")
            schedule_days = SettingsService.get("auto_download_schedule_days", "daily")

            logger.info(
                f"Setting up scheduled downloads for {schedule_days} at {schedule_time}"
            )

            # Parse time
            try:
                hour, minute = map(int, schedule_time.split(":"))
                schedule_time_obj = dt_time(hour, minute)
            except (ValueError, IndexError):
                logger.error(
                    f"Invalid schedule time format: {schedule_time}. Using default 02:00"
                )
                schedule_time_obj = dt_time(2, 0)
                hour, minute = 2, 0

            # Schedule based on frequency
            if schedule_days == "daily":
                schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
                    self._run_scheduled_download
                )
                logger.info(f"Scheduled daily downloads at {hour:02d}:{minute:02d}")

            elif schedule_days == "weekly":
                # Default to Sunday for weekly
                schedule.every().sunday.at(f"{hour:02d}:{minute:02d}").do(
                    self._run_scheduled_download
                )
                logger.info(
                    f"Scheduled weekly downloads on Sunday at {hour:02d}:{minute:02d}"
                )

            else:
                # Handle specific days (comma-separated: monday,wednesday,friday)
                days_map = {
                    "monday": schedule.every().monday,
                    "tuesday": schedule.every().tuesday,
                    "wednesday": schedule.every().wednesday,
                    "thursday": schedule.every().thursday,
                    "friday": schedule.every().friday,
                    "saturday": schedule.every().saturday,
                    "sunday": schedule.every().sunday,
                }

                if "," in schedule_days:
                    selected_days = [
                        day.strip().lower() for day in schedule_days.split(",")
                    ]
                    for day in selected_days:
                        if day in days_map:
                            days_map[day].at(f"{hour:02d}:{minute:02d}").do(
                                self._run_scheduled_download
                            )
                            logger.info(
                                f"Scheduled downloads on {day.capitalize()} at {hour:02d}:{minute:02d}"
                            )
                        else:
                            logger.warning(f"Invalid day name: {day}")
                else:
                    # Single day
                    day = schedule_days.strip().lower()
                    if day in days_map:
                        days_map[day].at(f"{hour:02d}:{minute:02d}").do(
                            self._run_scheduled_download
                        )
                        logger.info(
                            f"Scheduled downloads on {day.capitalize()} at {hour:02d}:{minute:02d}"
                        )
                    else:
                        logger.error(
                            f"Invalid schedule days: {schedule_days}. Defaulting to daily"
                        )
                        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
                            self._run_scheduled_download
                        )

        except Exception as e:
            logger.error(f"Failed to set up scheduled jobs: {e}")

    def _run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Scheduler thread started")

        while self.running:
            try:
                # Run pending scheduled jobs
                schedule.run_pending()

                # Check for settings changes every 5 minutes
                current_time = datetime.now()
                if (
                    self._last_check_time is None
                    or (current_time - self._last_check_time).total_seconds() > 300
                ):
                    self._check_settings_changes()
                    self._last_check_time = current_time

                # Sleep for 1 minute before checking again
                time.sleep(60)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)

        logger.info("Scheduler thread stopped")

    def _check_settings_changes(self):
        """Check if schedule settings have changed and reload if necessary"""
        try:
            # This is a simple check - in a more complex system you might track
            # setting modification timestamps
            if SettingsService.get_bool("auto_download_schedule_enabled", False):
                # Settings might have changed, reload the schedule
                self.reload_schedule()
        except Exception as e:
            logger.error(f"Error checking settings changes: {e}")

    def _run_scheduled_download(self):
        """Execute the scheduled download of wanted videos"""
        try:
            logger.info("Starting scheduled download of wanted videos...")

            # Get maximum videos setting
            max_videos = SettingsService.get_int("auto_download_max_videos", 50)

            # Import here to avoid circular imports
            from src.api.videos import download_all_wanted_videos_internal

            # Run the download function
            result = download_all_wanted_videos_internal(limit=max_videos)

            if result.get("success"):
                success_count = result.get("success_count", 0)
                failed_count = result.get("failed_count", 0)
                total_wanted = result.get("total_wanted", 0)

                logger.info(
                    f"Scheduled download completed: {success_count} queued, {failed_count} failed, {total_wanted} total wanted videos"
                )

                # Log summary
                if success_count > 0:
                    logger.info(
                        f"Successfully queued {success_count} videos for download"
                    )
                if failed_count > 0:
                    logger.warning(f"{failed_count} videos failed to queue")
                if total_wanted == 0:
                    logger.info("No wanted videos found to download")

            else:
                error = result.get("error", "Unknown error")
                logger.error(f"Scheduled download failed: {error}")

        except Exception as e:
            logger.error(f"Error running scheduled download: {e}")

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time"""
        try:
            if not schedule.jobs:
                return None

            # Get the next run time from all jobs
            next_times = [job.next_run for job in schedule.jobs if job.next_run]
            if next_times:
                return min(next_times)
            return None

        except Exception as e:
            logger.error(f"Error getting next run time: {e}")
            return None

    def get_schedule_info(self) -> Dict[str, Any]:
        """Get information about current schedule"""
        try:
            enabled = SettingsService.get_bool("auto_download_schedule_enabled", False)

            if not enabled:
                return {"enabled": False, "next_run": None, "schedule": "Disabled"}

            schedule_time = SettingsService.get("auto_download_schedule_time", "02:00")
            schedule_days = SettingsService.get("auto_download_schedule_days", "daily")
            max_videos = SettingsService.get_int("auto_download_max_videos", 50)
            next_run = self.get_next_run_time()

            return {
                "enabled": True,
                "schedule_time": schedule_time,
                "schedule_days": schedule_days,
                "max_videos": max_videos,
                "next_run": next_run.isoformat() if next_run else None,
                "next_run_human": (
                    next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else None
                ),
                "job_count": len(schedule.jobs),
            }

        except Exception as e:
            logger.error(f"Error getting schedule info: {e}")
            return {"enabled": False, "error": str(e)}


# Global scheduler instance
scheduler_service = SchedulerService()
