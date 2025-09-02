"""
Video Download Background Worker
Handles video download jobs with progress tracking and error recovery.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from sqlalchemy.exc import SQLAlchemyError

from ..background_worker_base import BaseWorker
from ...database.connection import get_db
from ...database.models import Video, VideoDownload
from ...services.ytdlp_service import ytdlp_service
from ...utils.logger import get_logger

logger = get_logger(__name__)


class VideoDownloadWorker(BaseWorker):
    """
    Background worker for video download operations
    """
    
    async def process(self):
        """Process video download job"""
        try:
            # Extract job payload
            video_id = self.job.payload.get('video_id')
            quality = self.job.payload.get('quality', 'best')
            force_redownload = self.job.payload.get('force_redownload', False)
            
            if not video_id:
                raise ValueError("Missing video_id in job payload")
            
            logger.info(f"Starting video download job for video {video_id}")
            await self.update_progress(5, f"Initializing download for video {video_id}")
            
            # Get video from database
            with get_db() as session:
                video = session.query(Video).filter(Video.id == video_id).first()
                if not video:
                    raise ValueError(f"Video {video_id} not found")
                
                video_title = video.title or f"Video {video_id}"
                video_url = video.url
                artist_name = video.artist.name if video.artist else "Unknown Artist"
            
            await self.update_progress(10, f"Starting download: {video_title}")
            
            # Check if video is already downloaded and not forcing redownload
            if not force_redownload:
                with get_db() as session:
                    video = session.query(Video).filter(Video.id == video_id).first()
                    if video and video.file_path and hasattr(video, 'downloaded') and video.downloaded:
                        # Check if file actually exists
                        import os
                        if os.path.exists(video.file_path):
                            await self.complete({
                                'video_id': video_id,
                                'message': f"Video already downloaded: {video_title}",
                                'file_path': video.file_path,
                                'skipped': True
                            })
                            return
            
            await self.update_progress(15, f"Preparing download for: {video_title}")
            
            # Create or update download record
            with get_db() as session:
                download = session.query(VideoDownload).filter(
                    VideoDownload.video_id == video_id
                ).first()
                
                if not download:
                    download = VideoDownload(
                        video_id=video_id,
                        status='downloading',
                        progress=0
                    )
                    session.add(download)
                else:
                    download.status = 'downloading'
                    download.progress = 0
                    download.error_message = None
                
                session.commit()
                download_id = download.id
            
            await self.update_progress(20, f"Download record created for: {video_title}")
            
            # Set up progress callback
            async def progress_callback(progress_data: Dict[str, Any]):
                """Handle download progress updates"""
                try:
                    if 'percent' in progress_data:
                        # Map download progress to job progress (20-95%)
                        download_progress = float(progress_data['percent'].rstrip('%'))
                        job_progress = int(20 + (download_progress * 0.75))  # 20% to 95%
                        
                        status_msg = f"Downloading {video_title}: {download_progress:.1f}%"
                        if 'speed' in progress_data:
                            status_msg += f" at {progress_data['speed']}"
                        
                        await self.update_progress(job_progress, status_msg)
                        
                        # Update download record
                        with get_db() as session:
                            download = session.query(VideoDownload).filter(
                                VideoDownload.id == download_id
                            ).first()
                            if download:
                                download.progress = download_progress
                                session.commit()
                
                except Exception as e:
                    logger.warning(f"Error updating download progress: {e}")
            
            # Perform the actual download using ytdlp service
            try:
                logger.info(f"Starting ytdlp download for video {video_id}: {video_url}")
                
                # Use the existing ytdlp service but run in async context
                loop = asyncio.get_event_loop()
                download_result = await loop.run_in_executor(
                    None,
                    self._sync_download_video,
                    video_id, video_url, quality, progress_callback
                )
                
                if not download_result or not download_result.get('success'):
                    raise Exception(download_result.get('error', 'Download failed'))
                
                file_path = download_result.get('file_path')
                if not file_path:
                    raise Exception("No file path returned from download")
                
                await self.update_progress(95, f"Download completed: {video_title}")
                
                # Update video record with download info
                with get_db() as session:
                    video = session.query(Video).filter(Video.id == video_id).first()
                    if video:
                        video.file_path = file_path
                        video.downloaded = True
                        video.file_size = download_result.get('file_size')
                        video.duration = download_result.get('duration')
                        
                        # Update technical metadata if available
                        if 'technical_metadata' in download_result:
                            video.technical_metadata = download_result['technical_metadata']
                        
                        session.commit()
                        logger.info(f"Updated video {video_id} with download info")
                
                # Update download record as completed
                with get_db() as session:
                    download = session.query(VideoDownload).filter(
                        VideoDownload.id == download_id
                    ).first()
                    if download:
                        download.status = 'completed'
                        download.progress = 100.0
                        download.completed_at = asyncio.get_event_loop().time()
                        session.commit()
                
                await self.complete({
                    'video_id': video_id,
                    'file_path': file_path,
                    'message': f"Successfully downloaded: {video_title}",
                    'artist': artist_name,
                    'file_size': download_result.get('file_size'),
                    'duration': download_result.get('duration')
                })
                
            except Exception as download_error:
                logger.error(f"Download failed for video {video_id}: {download_error}")
                
                # Update download record as failed
                with get_db() as session:
                    download = session.query(VideoDownload).filter(
                        VideoDownload.id == download_id
                    ).first()
                    if download:
                        download.status = 'failed'
                        download.error_message = str(download_error)
                        session.commit()
                
                raise download_error
                
        except Exception as e:
            logger.error(f"Video download job {self.job.id} failed: {e}")
            await self.fail(f"Video download failed: {str(e)}")
    
    def _sync_download_video(self, video_id: int, video_url: str, quality: str, progress_callback) -> Dict[str, Any]:
        """
        Synchronous video download using ytdlp service
        This runs in a thread pool to avoid blocking the async event loop
        """
        try:
            # Use the existing ytdlp_service
            result = ytdlp_service.download_video(
                url=video_url,
                video_id=video_id,
                quality=quality,
                progress_callback=progress_callback
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Sync download failed for video {video_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }