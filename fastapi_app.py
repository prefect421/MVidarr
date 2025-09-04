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

# Static files and templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/css", StaticFiles(directory="frontend/CSS"), name="css")
templates = Jinja2Templates(directory="frontend/templates")

# Include API routers
from src.api.fastapi.jobs import router as jobs_router
from src.api.fastapi.video_quality import router as video_quality_router

app.include_router(jobs_router)
app.include_router(video_quality_router)


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
    """Root endpoint - temporary redirect to Flask during migration"""
    return """
    <html>
        <head><title>MVidarr - FastAPI Migration</title></head>
        <body>
            <h1>MVidarr FastAPI</h1>
            <p>FastAPI migration in progress...</p>
            <p><a href="http://localhost:5000">Continue to Flask app</a></p>
            <p><a href="/docs">FastAPI API Documentation</a></p>
            <p><a href="/health">Health Check</a></p>
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
        port=8000,  # Different port from Flask during migration
        reload=True,
        log_level="info"
    )