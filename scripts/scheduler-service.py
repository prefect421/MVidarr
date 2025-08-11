#!/usr/bin/env python3
"""
MVidarr Standalone Scheduler Service
Independent scheduler service that can run alongside or instead of the web app scheduler
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for standalone service
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/mike/mvidarr/data/logs/scheduler-service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('mvidarr.scheduler-service')

class SchedulerService:
    def __init__(self):
        self.running = True
        self.last_check = None
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def check_and_run_downloads(self):
        """Check if it's time to run downloads and execute them"""
        try:
            from src.services.settings_service import SettingsService
            from src.database.connection import init_db_standalone
            
            # Initialize database connection
            init_db_standalone()
            
            # Load settings
            SettingsService.load_cache()
            
            # Check if auto-download is enabled
            if not SettingsService.get_bool("auto_download_schedule_enabled", False):
                logger.info("Auto-download scheduling is disabled")
                return False
                
            # Get schedule configuration
            schedule_frequency = SettingsService.get("auto_download_schedule_frequency", "daily")
            schedule_time = SettingsService.get("auto_download_schedule_time", "03:30")
            
            # Parse schedule time
            try:
                hour, minute = map(int, schedule_time.split(':'))
            except:
                logger.error(f"Invalid schedule time format: {schedule_time}")
                return False
            
            now = datetime.now()
            
            # Check if it's time to run based on frequency
            should_run = False
            
            if schedule_frequency == "hourly":
                if now.minute == minute and (not self.last_check or 
                    (now - self.last_check).total_seconds() >= 3600):
                    should_run = True
            elif schedule_frequency == "daily":
                if now.hour == hour and now.minute == minute and (not self.last_check or 
                    self.last_check.date() != now.date()):
                    should_run = True
            
            if should_run:
                logger.info(f"Running scheduled downloads at {now}")
                self.run_downloads()
                self.last_check = now
                return True
                
        except Exception as e:
            logger.error(f"Error checking downloads: {e}")
            
        return False
    
    def run_downloads(self):
        """Execute the download process"""
        try:
            import requests
            import subprocess
            
            # Option 1: Call the API endpoint (if web app is running)
            try:
                response = requests.post('http://localhost:5000/api/scheduler/trigger', 
                                       timeout=30,
                                       auth=self.get_auth_credentials())
                if response.status_code == 200:
                    logger.info("Successfully triggered downloads via API")
                    return
            except requests.exceptions.RequestException:
                logger.info("Web app not available, running downloads directly")
            
            # Option 2: Run downloads directly
            self.run_downloads_directly()
            
        except Exception as e:
            logger.error(f"Error running downloads: {e}")
    
    def get_auth_credentials(self):
        """Get authentication credentials for API calls"""
        try:
            from src.services.simple_auth_service import SimpleAuthService
            username, _ = SimpleAuthService.get_credentials()
            return (username, username)  # Simple auth uses username as password by default
        except:
            return None
    
    def run_downloads_directly(self):
        """Run downloads directly without API"""
        try:
            from src.services.settings_service import SettingsService
            from src.api.videos import get_wanted_videos_for_download
            
            # Get wanted videos
            max_downloads = SettingsService.get_int("scheduler_max_downloads_per_run", 10)
            logger.info(f"Looking for up to {max_downloads} videos to download")
            
            # This would need to be implemented to work standalone
            # For now, log that we would run downloads
            logger.info("Direct downloads would run here (implementation needed)")
            
        except Exception as e:
            logger.error(f"Error in direct downloads: {e}")
    
    def run(self):
        """Main service loop"""
        logger.info("MVidarr Scheduler Service starting...")
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        while self.running:
            try:
                self.check_and_run_downloads()
                # Check every minute
                time.sleep(60)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                logger.error(f"Unexpected error in scheduler loop: {e}")
                time.sleep(60)  # Wait before retrying
                
        logger.info("MVidarr Scheduler Service stopped")

if __name__ == "__main__":
    service = SchedulerService()
    service.run()