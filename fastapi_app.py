"""
FastAPI Application for MVidarr
Modern async web framework with native background job support
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Database and services
from src.database.connection import get_db
from src.services.settings_service import SettingsService
from src.utils.logger import get_logger

# Background job system
from src.services.job_queue import get_job_queue, cleanup_job_queue
from src.services.background_workers import start_background_workers, stop_background_workers

logger = get_logger("mvidarr.fastapi")

# Global references for cleanup
job_queue = None
worker_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - starts/stops background services"""
    global job_queue, worker_tasks
    
    logger.info("FastAPI MVidarr application starting up...")
    
    try:
        # Initialize job system
        logger.info("Initializing job queue...")
        job_queue = await get_job_queue()
        
        # Start background workers
        worker_count = 3  # TODO: make configurable
        logger.info(f"Starting {worker_count} background workers...")
        await start_background_workers(worker_count)
        
        logger.info("✅ Background job system started successfully")
        
        yield  # Application is running
        
    except Exception as e:
        logger.error(f"Failed to start background services: {e}")
        raise
    
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down background services...")
        
        try:
            await stop_background_workers()
            await cleanup_job_queue()
            logger.info("✅ Background services stopped cleanly")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="MVidarr",
    description="Music Video Management and Automation System",
    version="0.9.8",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add performance monitoring middleware
from src.middleware.performance_middleware import (
    PerformanceTrackingMiddleware,
    CacheHeadersMiddleware, 
    ResourceMonitoringMiddleware
)

app.add_middleware(ResourceMonitoringMiddleware, track_memory=True)
app.add_middleware(CacheHeadersMiddleware, default_cache_ttl=300)
app.add_middleware(PerformanceTrackingMiddleware)

# Static files and templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/css", StaticFiles(directory="frontend/CSS"), name="css")
templates = Jinja2Templates(directory="frontend/templates")

# Include API routers
from src.api.fastapi.jobs import router as jobs_router
from src.api.fastapi.video_quality import router as video_quality_router
from src.api.fastapi.media_processing import router as media_processing_router
from src.api.fastapi.image_processing import router as image_processing_router
from src.api.fastapi.advanced_image_processing import router as advanced_image_router
from src.api.fastapi.bulk_operations import router as bulk_operations_router
from src.api.fastapi.videos import router as fastapi_videos_router
from src.api.fastapi.artists import router as fastapi_artists_router
from src.api.fastapi.playlists import router as fastapi_playlists_router
from src.api.fastapi.admin import router as fastapi_admin_router
from src.api.fastapi.settings import router as fastapi_settings_router
from src.api.fastapi.auth import router as fastapi_auth_router
from src.api.system_health import router as system_health_router

app.include_router(jobs_router)
app.include_router(video_quality_router)
app.include_router(media_processing_router)
app.include_router(image_processing_router)
app.include_router(advanced_image_router)
app.include_router(bulk_operations_router)
app.include_router(fastapi_videos_router)
app.include_router(fastapi_artists_router)
app.include_router(fastapi_playlists_router)
app.include_router(fastapi_admin_router)
app.include_router(fastapi_settings_router)
app.include_router(fastapi_auth_router)
app.include_router(system_health_router)


# Basic health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "version": "0.9.8",
        "framework": "FastAPI",
        "job_system": "native_asyncio"
    }


# Root redirect for now
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - FastAPI with Phase 2 advanced processing"""
    return """
    <html>
        <head><title>MVidarr - FastAPI with Advanced Processing</title></head>
        <body>
            <h1>MVidarr FastAPI</h1>
            <p>Phase 3 Week 30 Admin API Migration Complete!</p>
            <p><strong>Advanced FFmpeg Operations Available</strong></p>
            <ul>
                <li>Advanced Video Format Conversion</li>
                <li>Concurrent Video Quality Analysis</li>
                <li>Bulk Thumbnail Creation</li>
                <li>Enhanced Video Validation</li>
            </ul>
            <p><strong>Image Processing Thread Pools Available</strong></p>
            <ul>
                <li>Concurrent Thumbnail Generation</li>
                <li>Bulk Image Optimization</li>
                <li>Parallel Image Analysis</li>
                <li>Memory-Efficient Processing</li>
            </ul>
            <p><strong>Advanced Image Operations Available</strong></p>
            <ul>
                <li>Bulk Image Collection Analysis (5000+ images)</li>
                <li>Concurrent Format Conversion (JPEG/PNG/WEBP/TIFF)</li>
                <li>Automated Quality Enhancement</li>
                <li>Parallel Metadata Extraction</li>
                <li>AI-Driven Quality Issue Detection</li>
            </ul>
            <p><strong>Bulk Media Operations Available</strong></p>
            <ul>
                <li>Large-Scale Metadata Enrichment (10,000+ files)</li>
                <li>Collection Import from Directories</li>
                <li>Automated Cleanup Operations</li>
                <li>Real-Time Progress Tracking</li>
                <li>WebSocket Progress Updates</li>
            </ul>
            <p><strong>FastAPI Core & Admin APIs Available</strong></p>
            <ul>
                <li>Complete Video, Artist & Playlist CRUD Operations (async)</li>
                <li>System Administration & User Management</li>
                <li>Settings Management & Application Control</li>
                <li>Authentication & OAuth Management</li>
                <li>Advanced Search & Filtering with Authentication</li>
                <li>HTTP Range-based Video Streaming</li>
                <li>Thumbnail Management System</li>
                <li>Download Queue & Priority Management</li>
                <li>Bulk Operations (delete, download, status updates)</li>
                <li>Dynamic Playlists with Auto-Update</li>
                <li>Playlist File Upload & Management</li>
                <li>Advanced Access Control & Permissions</li>
                <li>System Health & Performance Monitoring</li>
                <li>Application Restart & Service Control</li>
                <li>IMVDb Integration & Auto-Discovery</li>
                <li>Security-Enhanced with Authentication</li>
                <li>Pydantic Validation & Type Safety</li>
            </ul>
            <p><strong>Advanced Caching & Performance Available</strong></p>
            <ul>
                <li>Redis-based Media Metadata Caching</li>
                <li>Real-Time System Performance Monitoring</li>
                <li>Intelligent Cache Invalidation & Optimization</li>
                <li>System Health Monitoring & Alerting</li>
                <li>Performance Metrics & Reporting</li>
            </ul>
            <p><a href="/docs">FastAPI API Documentation</a></p>
            <p><a href="/health">Health Check</a></p>
            <p><a href="http://192.168.1.145:5010">Flask Frontend</a></p>
        </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the application
    uvicorn.run(
        "fastapi_app:app", 
        host="0.0.0.0", 
        port=5000,  # Standard MVidarr port
        reload=True,
        log_level="info"
    )