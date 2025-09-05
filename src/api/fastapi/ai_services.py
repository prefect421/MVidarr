"""
MVidarr AI Services API - Phase 3 Week 25
FastAPI endpoints for AI/ML services integration with media processing pipeline
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path as FastAPIPath
from pydantic import BaseModel, Field

from src.services.ai_content_analyzer import (
    get_ai_content_analyzer,
    AIAnalysisResult,
    ContentType,
    AnalysisType,
    analyze_image_content,
    batch_analyze_images
)
from src.services.auto_tagging_service import (
    get_auto_tagging_service,
    TaggingResult,
    Tag,
    TagCategory,
    generate_content_tags,
    batch_tag_content
)
from src.services.smart_recommendations import (
    get_smart_recommendation_engine,
    RecommendationRequest,
    RecommendationResult,
    RecommendationType,
    get_user_recommendations,
    update_user_feedback
)
from src.services.media_cache_manager import get_media_cache_manager, CacheType
from src.services.performance_monitor import track_media_processing_time
from src.utils.logger import get_logger

logger = get_logger("mvidarr.api.ai_services")

# Create AI services router
ai_router = APIRouter(prefix="/api/ai", tags=["AI Services"])


# Pydantic models for request/response schemas
class ContentAnalysisRequest(BaseModel):
    content_path: str = Field(..., description="Path to the content file")
    content_type: str = Field(default="image", description="Type of content (image, video, audio)")
    analysis_types: Optional[List[str]] = Field(
        default=None,
        description="Types of analysis to perform (object_detection, scene_recognition, quality_assessment, color_analysis)"
    )

class ContentAnalysisResponse(BaseModel):
    content_path: str
    results: List[Dict[str, Any]]
    processing_time: float
    success: bool
    message: str

class BatchAnalysisRequest(BaseModel):
    content_paths: List[str] = Field(..., description="List of content file paths")
    content_type: str = Field(default="image", description="Type of content")
    analysis_types: Optional[List[str]] = Field(default=None)

class BatchAnalysisResponse(BaseModel):
    total_processed: int
    successful_analyses: int
    failed_analyses: int
    processing_time: float
    results: Dict[str, List[Dict[str, Any]]]
    errors: Dict[str, str]

class TaggingRequest(BaseModel):
    content_path: str = Field(..., description="Path to the content file")
    existing_tags: Optional[List[str]] = Field(default=None, description="Existing tags to consider")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional user context")

class TaggingResponse(BaseModel):
    content_path: str
    tags: List[Dict[str, Any]]
    confidence_score: float
    processing_time: float
    success: bool
    message: str

class BatchTaggingRequest(BaseModel):
    content_paths: List[str] = Field(..., description="List of content file paths")

class BatchTaggingResponse(BaseModel):
    total_processed: int
    successful_tagging: int
    failed_tagging: int
    processing_time: float
    results: Dict[str, Dict[str, Any]]
    errors: Dict[str, str]

class RecommendationsRequest(BaseModel):
    user_id: str = Field(..., description="User ID for personalized recommendations")
    content_id: Optional[str] = Field(default=None, description="Content ID for similar content recommendations")
    recommendation_types: Optional[List[str]] = Field(
        default=None,
        description="Types of recommendations (similar_content, personalized, collaborative, trending)"
    )
    max_recommendations: int = Field(default=10, description="Maximum number of recommendations")
    include_reasons: bool = Field(default=True, description="Include recommendation reasons")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for recommendations")

class RecommendationsResponse(BaseModel):
    user_id: str
    recommendations: List[Dict[str, Any]]
    processing_time: float
    algorithms_used: List[str]
    cache_hit: bool
    success: bool
    message: str

class UserFeedbackRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    content_id: str = Field(..., description="Content ID")
    interaction_type: str = Field(..., description="Type of interaction (view, like, dislike)")
    context: Optional[Dict[str, Any]] = Field(default=None)


# AI Content Analysis Endpoints
@ai_router.post("/analyze", response_model=ContentAnalysisResponse)
async def analyze_content(request: ContentAnalysisRequest):
    """
    Perform AI content analysis on a single media file
    """
    start_time = time.time()
    
    try:
        logger.info(f"🧠 AI analysis request for: {request.content_path}")
        
        # Validate content path
        content_path = Path(request.content_path)
        if not content_path.exists():
            raise HTTPException(status_code=404, detail=f"Content file not found: {request.content_path}")
        
        # Map string types to enums
        content_type_mapping = {
            "image": ContentType.IMAGE,
            "video": ContentType.VIDEO,
            "audio": ContentType.AUDIO,
            "text": ContentType.TEXT
        }
        
        analysis_type_mapping = {
            "object_detection": AnalysisType.OBJECT_DETECTION,
            "scene_recognition": AnalysisType.SCENE_RECOGNITION,
            "quality_assessment": AnalysisType.QUALITY_ASSESSMENT,
            "color_analysis": AnalysisType.COLOR_ANALYSIS,
            "text_extraction": AnalysisType.TEXT_EXTRACTION,
            "sentiment_analysis": AnalysisType.SENTIMENT_ANALYSIS,
            "content_moderation": AnalysisType.CONTENT_MODERATION,
            "facial_detection": AnalysisType.FACIAL_DETECTION
        }
        
        content_type = content_type_mapping.get(request.content_type, ContentType.IMAGE)
        
        analysis_types = None
        if request.analysis_types:
            analysis_types = [
                analysis_type_mapping.get(analysis_type)
                for analysis_type in request.analysis_types
                if analysis_type in analysis_type_mapping
            ]
        
        # Perform AI analysis
        analyzer = await get_ai_content_analyzer()
        results = await analyzer.analyze_content(
            content_path=str(content_path),
            content_type=content_type,
            analysis_types=analysis_types
        )
        
        # Convert results to dict format
        results_dict = [result.to_dict() for result in results]
        
        processing_time = time.time() - start_time
        
        # Track performance
        await track_media_processing_time("ai_content_analysis_api", processing_time, str(content_path))
        
        return ContentAnalysisResponse(
            content_path=request.content_path,
            results=results_dict,
            processing_time=processing_time,
            success=True,
            message=f"Successfully analyzed content with {len(results)} analysis results"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ AI content analysis failed for {request.content_path}: {e}")
        
        return ContentAnalysisResponse(
            content_path=request.content_path,
            results=[],
            processing_time=processing_time,
            success=False,
            message=f"Analysis failed: {str(e)}"
        )


@ai_router.post("/batch-analyze", response_model=BatchAnalysisResponse)
async def batch_analyze_content(request: BatchAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Perform AI content analysis on multiple media files
    """
    start_time = time.time()
    
    try:
        logger.info(f"🧠 Batch AI analysis request for {len(request.content_paths)} files")
        
        # Validate content paths
        valid_paths = []
        for path in request.content_paths:
            if Path(path).exists():
                valid_paths.append(path)
        
        if not valid_paths:
            raise HTTPException(status_code=404, detail="No valid content files found")
        
        # Map content type
        content_type_mapping = {
            "image": ContentType.IMAGE,
            "video": ContentType.VIDEO,
            "audio": ContentType.AUDIO,
            "text": ContentType.TEXT
        }
        
        analysis_type_mapping = {
            "object_detection": AnalysisType.OBJECT_DETECTION,
            "scene_recognition": AnalysisType.SCENE_RECOGNITION,
            "quality_assessment": AnalysisType.QUALITY_ASSESSMENT,
            "color_analysis": AnalysisType.COLOR_ANALYSIS,
            "text_extraction": AnalysisType.TEXT_EXTRACTION,
            "sentiment_analysis": AnalysisType.SENTIMENT_ANALYSIS,
            "content_moderation": AnalysisType.CONTENT_MODERATION,
            "facial_detection": AnalysisType.FACIAL_DETECTION
        }
        
        content_type = content_type_mapping.get(request.content_type, ContentType.IMAGE)
        
        analysis_types = None
        if request.analysis_types:
            analysis_types = [
                analysis_type_mapping.get(analysis_type)
                for analysis_type in request.analysis_types
                if analysis_type in analysis_type_mapping
            ]
        
        # Perform batch analysis
        analyzer = await get_ai_content_analyzer()
        results = await analyzer.batch_analyze(
            content_paths=valid_paths,
            content_type=content_type,
            analysis_types=analysis_types
        )
        
        # Process results
        results_dict = {}
        errors = {}
        successful_analyses = 0
        
        for path, analysis_results in results.items():
            if analysis_results:
                results_dict[path] = [result.to_dict() for result in analysis_results]
                successful_analyses += 1
            else:
                errors[path] = "Analysis failed or returned empty results"
        
        processing_time = time.time() - start_time
        
        # Track performance
        await track_media_processing_time("batch_ai_analysis_api", processing_time)
        
        return BatchAnalysisResponse(
            total_processed=len(valid_paths),
            successful_analyses=successful_analyses,
            failed_analyses=len(valid_paths) - successful_analyses,
            processing_time=processing_time,
            results=results_dict,
            errors=errors
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Batch AI analysis failed: {e}")
        
        return BatchAnalysisResponse(
            total_processed=0,
            successful_analyses=0,
            failed_analyses=len(request.content_paths),
            processing_time=processing_time,
            results={},
            errors={"batch_error": str(e)}
        )


# Auto-Tagging Endpoints
@ai_router.post("/tag", response_model=TaggingResponse)
async def tag_content(request: TaggingRequest):
    """
    Generate automatic tags for media content
    """
    start_time = time.time()
    
    try:
        logger.info(f"🏷️ Auto-tagging request for: {request.content_path}")
        
        # Validate content path
        content_path = Path(request.content_path)
        if not content_path.exists():
            raise HTTPException(status_code=404, detail=f"Content file not found: {request.content_path}")
        
        # Perform auto-tagging
        service = await get_auto_tagging_service()
        result = await service.generate_tags(
            content_path=str(content_path),
            existing_tags=request.existing_tags,
            user_context=request.user_context
        )
        
        # Convert tags to dict format
        tags_dict = [tag.to_dict() for tag in result.tags]
        
        processing_time = time.time() - start_time
        
        # Track performance
        await track_media_processing_time("auto_tagging_api", processing_time, str(content_path))
        
        return TaggingResponse(
            content_path=request.content_path,
            tags=tags_dict,
            confidence_score=result.confidence_score,
            processing_time=processing_time,
            success=True,
            message=f"Successfully generated {len(result.tags)} tags"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Auto-tagging failed for {request.content_path}: {e}")
        
        return TaggingResponse(
            content_path=request.content_path,
            tags=[],
            confidence_score=0.0,
            processing_time=processing_time,
            success=False,
            message=f"Tagging failed: {str(e)}"
        )


@ai_router.post("/batch-tag", response_model=BatchTaggingResponse)
async def batch_tag_content(request: BatchTaggingRequest, background_tasks: BackgroundTasks):
    """
    Generate automatic tags for multiple media files
    """
    start_time = time.time()
    
    try:
        logger.info(f"🏷️ Batch auto-tagging request for {len(request.content_paths)} files")
        
        # Validate content paths
        valid_paths = []
        for path in request.content_paths:
            if Path(path).exists():
                valid_paths.append(path)
        
        if not valid_paths:
            raise HTTPException(status_code=404, detail="No valid content files found")
        
        # Perform batch tagging
        service = await get_auto_tagging_service()
        results = await service.batch_generate_tags(valid_paths)
        
        # Process results
        results_dict = {}
        errors = {}
        successful_tagging = 0
        
        for path, tagging_result in results.items():
            if tagging_result.tags:
                results_dict[path] = tagging_result.to_dict()
                successful_tagging += 1
            else:
                errors[path] = "Tagging failed or returned empty results"
        
        processing_time = time.time() - start_time
        
        # Track performance
        await track_media_processing_time("batch_auto_tagging_api", processing_time)
        
        return BatchTaggingResponse(
            total_processed=len(valid_paths),
            successful_tagging=successful_tagging,
            failed_tagging=len(valid_paths) - successful_tagging,
            processing_time=processing_time,
            results=results_dict,
            errors=errors
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Batch auto-tagging failed: {e}")
        
        return BatchTaggingResponse(
            total_processed=0,
            successful_tagging=0,
            failed_tagging=len(request.content_paths),
            processing_time=processing_time,
            results={},
            errors={"batch_error": str(e)}
        )


# Smart Recommendations Endpoints
@ai_router.post("/recommend", response_model=RecommendationsResponse)
async def get_recommendations(request: RecommendationsRequest):
    """
    Get personalized content recommendations for a user
    """
    start_time = time.time()
    
    try:
        logger.info(f"🎯 Recommendations request for user: {request.user_id}")
        
        # Map recommendation types
        rec_type_mapping = {
            "similar_content": RecommendationType.SIMILAR_CONTENT,
            "user_based": RecommendationType.USER_BASED,
            "content_based": RecommendationType.CONTENT_BASED,
            "collaborative": RecommendationType.COLLABORATIVE,
            "trending": RecommendationType.TRENDING,
            "personalized": RecommendationType.PERSONALIZED,
            "seasonal": RecommendationType.SEASONAL,
            "contextual": RecommendationType.CONTEXTUAL
        }
        
        recommendation_types = []
        if request.recommendation_types:
            recommendation_types = [
                rec_type_mapping.get(rec_type)
                for rec_type in request.recommendation_types
                if rec_type in rec_type_mapping
            ]
        
        # Create recommendation request
        rec_request = RecommendationRequest(
            user_id=request.user_id,
            content_id=request.content_id,
            recommendation_types=recommendation_types,
            max_recommendations=request.max_recommendations,
            include_reasons=request.include_reasons,
            context=request.context or {}
        )
        
        # Get recommendations
        engine = await get_smart_recommendation_engine()
        result = await engine.get_recommendations(rec_request)
        
        # Convert recommendations to dict format
        recommendations_dict = [rec.to_dict() for rec in result.recommendations]
        
        processing_time = time.time() - start_time
        
        # Track performance
        await track_media_processing_time("smart_recommendations_api", processing_time)
        
        return RecommendationsResponse(
            user_id=request.user_id,
            recommendations=recommendations_dict,
            processing_time=processing_time,
            algorithms_used=result.algorithms_used,
            cache_hit=result.cache_hit,
            success=True,
            message=f"Successfully generated {len(result.recommendations)} recommendations"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Recommendations failed for user {request.user_id}: {e}")
        
        return RecommendationsResponse(
            user_id=request.user_id,
            recommendations=[],
            processing_time=processing_time,
            algorithms_used=[],
            cache_hit=False,
            success=False,
            message=f"Recommendations failed: {str(e)}"
        )


@ai_router.post("/feedback")
async def submit_user_feedback(request: UserFeedbackRequest):
    """
    Submit user feedback for improving recommendations
    """
    try:
        logger.info(f"📊 User feedback: {request.user_id} -> {request.content_id} ({request.interaction_type})")
        
        # Update user interaction data
        engine = await get_smart_recommendation_engine()
        await engine.update_user_interaction(
            user_id=request.user_id,
            content_id=request.content_id,
            interaction_type=request.interaction_type,
            context=request.context
        )
        
        return {
            "success": True,
            "message": "User feedback submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ User feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


# Statistics and Health Endpoints
@ai_router.get("/statistics")
async def get_ai_statistics():
    """
    Get AI services performance statistics
    """
    try:
        # Get statistics from all AI services
        analyzer = await get_ai_content_analyzer()
        tagging_service = await get_auto_tagging_service()
        recommendation_engine = await get_smart_recommendation_engine()
        
        analyzer_stats = await analyzer.get_analysis_statistics()
        tagging_stats = await tagging_service.get_tagging_statistics()
        recommendation_stats = await recommendation_engine.get_recommendation_statistics()
        
        return {
            "ai_content_analyzer": analyzer_stats,
            "auto_tagging_service": tagging_stats,
            "smart_recommendations": recommendation_stats,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get AI statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@ai_router.get("/health")
async def ai_health_check():
    """
    AI services health check endpoint
    """
    try:
        health_status = {
            "status": "healthy",
            "services": {},
            "timestamp": time.time()
        }
        
        # Check AI content analyzer
        try:
            analyzer = await get_ai_content_analyzer()
            health_status["services"]["ai_content_analyzer"] = {
                "status": "healthy",
                "models_loaded": len(analyzer.models),
                "device": analyzer.device
            }
        except Exception as e:
            health_status["services"]["ai_content_analyzer"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check auto-tagging service
        try:
            tagging_service = await get_auto_tagging_service()
            health_status["services"]["auto_tagging_service"] = {
                "status": "healthy",
                "pipelines_loaded": len(tagging_service.pipelines)
            }
        except Exception as e:
            health_status["services"]["auto_tagging_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check smart recommendations
        try:
            recommendation_engine = await get_smart_recommendation_engine()
            health_status["services"]["smart_recommendations"] = {
                "status": "healthy",
                "user_profiles": len(recommendation_engine.user_profiles),
                "content_features": len(recommendation_engine.content_features)
            }
        except Exception as e:
            health_status["services"]["smart_recommendations"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Determine overall health
        unhealthy_services = [
            service for service, status in health_status["services"].items()
            if status.get("status") == "unhealthy"
        ]
        
        if unhealthy_services:
            health_status["status"] = "degraded"
            health_status["unhealthy_services"] = unhealthy_services
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ AI health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


# Export the router
__all__ = ["ai_router"]