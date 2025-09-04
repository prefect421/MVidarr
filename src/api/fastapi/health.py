"""
FastAPI Health Check API Endpoints
Async version of health checks using non-blocking subprocess operations
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.database.async_connection import async_db_manager
from src.utils.async_subprocess import get_git_version, get_git_branch
from src.utils.logger import get_logger

logger = get_logger("mvidarr.api.fastapi.health")

# Pydantic response models
class HealthResponse(BaseModel):
    status: str
    service: str = "mvidarr"

class DetailedHealthResponse(BaseModel):
    status: str
    components: Dict[str, str]
    timestamp: str

class DatabaseHealthResponse(BaseModel):
    status: str
    message: str

class VersionInfoResponse(BaseModel):
    version: str
    git_commit: str
    git_branch: str

class ServiceHealthResponse(BaseModel):
    status: str
    service: str
    message: Optional[str] = None
    error: Optional[str] = None

# Create router
health_router = APIRouter(prefix="/health", tags=["health"])

@health_router.get("/", response_model=HealthResponse)
async def health_check():
    """Simple async health check endpoint for Docker health checks"""
    try:
        # Quick async database connectivity check
        from sqlalchemy import text
        
        async with async_db_manager.session_scope() as session:
            await session.execute(text("SELECT 1"))
        
        return HealthResponse(status="healthy")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy", 
            "error": str(e)
        })

@health_router.get("/status", response_model=DetailedHealthResponse)
async def get_health_status():
    """Get overall system health status with async checks"""
    try:
        status = {
            "status": "healthy",
            "components": {
                "database": "healthy", 
                "api": "healthy"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check async database health
        try:
            async with async_db_manager.session_scope() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
                logger.debug("Database health check passed")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            status["components"]["database"] = "unhealthy"
            status["status"] = "unhealthy"
        
        return DetailedHealthResponse(**status)
        
    except Exception as e:
        logger.error(f"Health status check failed: {e}")
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

@health_router.get("/database", response_model=DatabaseHealthResponse)
async def check_database():
    """Check async database connectivity and health"""
    try:
        async with async_db_manager.session_scope() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
            if row and row.test == 1:
                return DatabaseHealthResponse(
                    status="healthy",
                    message="Database is accessible and healthy"
                )
            else:
                raise HTTPException(status_code=503, detail={
                    "status": "unhealthy", 
                    "message": "Database query failed"
                })
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy", 
            "error": str(e)
        })

@health_router.get("/imvdb", response_model=ServiceHealthResponse)
async def check_imvdb():
    """Check IMVDB API connectivity with async HTTP client"""
    try:
        from src.services.imvdb_service import imvdb_service
        
        # If the service has async methods, use them; otherwise wrap in async
        result = await asyncio.create_task(
            asyncio.to_thread(imvdb_service.test_connection)
        )
        
        if result["status"] == "success":
            return ServiceHealthResponse(
                status="healthy",
                service="imvdb",
                message=result.get("message")
            )
        else:
            raise HTTPException(status_code=503, detail=result)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IMVDB health check failed: {e}")
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy", 
            "service": "imvdb",
            "error": str(e)
        })

@health_router.get("/metube", response_model=ServiceHealthResponse)
async def check_metube():
    """Check yt-dlp Web UI connectivity with async HTTP client"""
    try:
        from src.services.ytdlp_service import ytdlp_service
        
        # If the service has async methods, use them; otherwise wrap in async
        result = await asyncio.create_task(
            asyncio.to_thread(ytdlp_service.test_connection)
        )
        
        if result["status"] == "success":
            return ServiceHealthResponse(
                status="healthy",
                service="metube",
                message=result.get("message")
            )
        else:
            raise HTTPException(status_code=503, detail=result)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"yt-dlp Web UI health check failed: {e}")
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy",
            "service": "metube", 
            "error": str(e)
        })

@health_router.get("/version", response_model=VersionInfoResponse)
async def get_version_info():
    """Get version information with async git commands (non-blocking)"""
    try:
        # Get version from src/__init__.py
        from src import __version__
        
        version_info = {
            "version": __version__,
            "git_commit": "unknown",
            "git_branch": "unknown"
        }
        
        # Use async subprocess utilities for git commands (non-blocking)
        try:
            git_commit = await get_git_version()
            if git_commit:
                version_info["git_commit"] = git_commit
        except Exception as e:
            logger.debug(f"Could not get git commit: {e}")
        
        try:
            git_branch = await get_git_branch()
            if git_branch:
                version_info["git_branch"] = git_branch
        except Exception as e:
            logger.debug(f"Could not get git branch: {e}")
        
        # Try to read version.json as fallback
        try:
            version_json_path = Path(__file__).parent.parent.parent.parent / "version.json"
            if version_json_path.exists():
                with open(version_json_path) as f:
                    version_data = json.load(f)
                    if version_info["git_commit"] == "unknown":
                        version_info["git_commit"] = version_data.get("git_commit", "unknown")
        except Exception as e:
            logger.debug(f"Could not read version.json: {e}")
        
        return VersionInfoResponse(**version_info)
        
    except Exception as e:
        logger.error(f"Version info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

@health_router.get("/performance", response_model=Dict[str, Any])
async def get_performance_stats():
    """Get subprocess performance statistics for monitoring"""
    try:
        from src.utils.async_subprocess import async_subprocess_manager
        
        stats = async_subprocess_manager.get_performance_stats()
        
        return {
            "subprocess_performance": stats,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Performance stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

# Add missing import
import asyncio