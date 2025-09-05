"""
MVidarr AI Content Analyzer - Phase 3 Week 25
AI-powered content analysis and recognition for intelligent media processing
"""

import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import base64

# AI/ML Libraries
try:
    import torch
    import torchvision.transforms as transforms
    from torchvision import models
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    np = None

try:
    from PIL import Image, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from src.services.media_cache_manager import get_media_cache_manager, CacheType
from src.services.performance_monitor import track_media_processing_time
from src.utils.logger import get_logger

logger = get_logger("mvidarr.ai_content_analyzer")


class ContentType(Enum):
    """Types of content that can be analyzed"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"


class AnalysisType(Enum):
    """Types of AI analysis available"""
    OBJECT_DETECTION = "object_detection"
    SCENE_RECOGNITION = "scene_recognition"
    TEXT_EXTRACTION = "text_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    QUALITY_ASSESSMENT = "quality_assessment"
    CONTENT_MODERATION = "content_moderation"
    FACIAL_DETECTION = "facial_detection"
    COLOR_ANALYSIS = "color_analysis"


@dataclass
class AIAnalysisResult:
    """Result of AI content analysis"""
    content_path: str
    content_type: ContentType
    analysis_type: AnalysisType
    confidence: float
    results: Dict[str, Any]
    processing_time: float
    model_version: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_path": self.content_path,
            "content_type": self.content_type.value,
            "analysis_type": self.analysis_type.value,
            "confidence": self.confidence,
            "results": self.results,
            "processing_time": self.processing_time,
            "model_version": self.model_version,
            "timestamp": self.timestamp
        }


@dataclass
class ContentAnalysisConfig:
    """Configuration for AI content analysis"""
    enable_object_detection: bool = True
    enable_scene_recognition: bool = True
    enable_text_extraction: bool = True
    enable_quality_assessment: bool = True
    confidence_threshold: float = 0.7
    max_processing_time: int = 30  # seconds
    cache_results: bool = True
    cache_ttl: int = 7200  # 2 hours
    batch_size: int = 8
    enable_gpu: bool = True


class AIContentAnalyzer:
    """Advanced AI-powered content analysis system"""
    
    def __init__(self, config: Optional[ContentAnalysisConfig] = None):
        """Initialize AI content analyzer"""
        self.config = config or ContentAnalysisConfig()
        
        # Model storage
        self.models = {}
        self.model_info = {}
        self.device = "cuda" if torch.cuda.is_available() and self.config.enable_gpu else "cpu"
        
        # Analysis pipelines
        self.pipelines = {}
        
        # Performance tracking
        self.analysis_stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_processing_time": 0.0,
            "cache_hits": 0
        }
        
        logger.info(f"🧠 AI Content Analyzer initialized with device: {self.device}")
        
    async def initialize_models(self):
        """Initialize AI models for content analysis"""
        try:
            await self._load_object_detection_model()
            await self._load_scene_recognition_model()
            await self._load_text_analysis_models()
            await self._load_quality_assessment_model()
            
            logger.info(f"✅ AI models initialized: {len(self.models)} models loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI models: {e}")
            raise
    
    async def _load_object_detection_model(self):
        """Load object detection model"""
        if not TORCH_AVAILABLE:
            logger.warning("⚠️ PyTorch not available - object detection disabled")
            return
            
        try:
            # Load pre-trained YOLO or similar model
            model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
            model.eval()
            model.to(self.device)
            
            self.models["object_detection"] = model
            self.model_info["object_detection"] = {
                "version": "1.0.0",
                "type": "FasterRCNN-ResNet50",
                "classes": 80,  # COCO classes
                "input_size": (224, 224)
            }
            
            logger.info("🔍 Object detection model loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load object detection model: {e}")
    
    async def _load_scene_recognition_model(self):
        """Load scene recognition model"""
        if not TORCH_AVAILABLE:
            logger.warning("⚠️ PyTorch not available - scene recognition disabled")
            return
            
        try:
            # Load pre-trained ResNet model for scene classification
            model = models.resnet50(pretrained=True)
            model.eval()
            model.to(self.device)
            
            # Transform for image preprocessing
            self.scene_transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                   std=[0.229, 0.224, 0.225])
            ])
            
            self.models["scene_recognition"] = model
            self.model_info["scene_recognition"] = {
                "version": "1.0.0",
                "type": "ResNet50-ImageNet",
                "classes": 1000,
                "input_size": (224, 224)
            }
            
            logger.info("🏞️ Scene recognition model loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load scene recognition model: {e}")
    
    async def _load_text_analysis_models(self):
        """Load text analysis models"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("⚠️ Transformers not available - text analysis disabled")
            return
            
        try:
            # Load sentiment analysis pipeline
            self.pipelines["sentiment"] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1
            )
            
            # Load text classification pipeline
            self.pipelines["text_classification"] = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli",
                device=0 if self.device == "cuda" else -1
            )
            
            self.model_info["text_analysis"] = {
                "version": "1.0.0",
                "sentiment_model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
                "classification_model": "facebook/bart-large-mnli"
            }
            
            logger.info("📝 Text analysis models loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load text analysis models: {e}")
    
    async def _load_quality_assessment_model(self):
        """Load image quality assessment model"""
        if not TORCH_AVAILABLE:
            logger.warning("⚠️ PyTorch not available - quality assessment disabled")
            return
            
        try:
            # Simple quality assessment based on image statistics
            # In production, this would use a specialized quality assessment model
            self.model_info["quality_assessment"] = {
                "version": "1.0.0",
                "type": "Statistical-Analysis",
                "metrics": ["sharpness", "contrast", "brightness", "noise"]
            }
            
            logger.info("⭐ Quality assessment model loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load quality assessment model: {e}")
    
    async def analyze_content(
        self,
        content_path: str,
        content_type: ContentType,
        analysis_types: List[AnalysisType] = None
    ) -> List[AIAnalysisResult]:
        """Perform comprehensive AI analysis on content"""
        start_time = time.time()
        
        # Default to all analysis types if none specified
        if analysis_types is None:
            analysis_types = [
                AnalysisType.OBJECT_DETECTION,
                AnalysisType.SCENE_RECOGNITION,
                AnalysisType.QUALITY_ASSESSMENT
            ]
        
        results = []
        path_obj = Path(content_path)
        
        try:
            # Check cache first
            cache_manager = await get_media_cache_manager()
            cache_key = f"ai_analysis_{hashlib.md5(content_path.encode()).hexdigest()}"
            
            if self.config.cache_results:
                cached_results = await cache_manager.get(CacheType.IMAGE_ANALYSIS, cache_key)
                if cached_results:
                    self.analysis_stats["cache_hits"] += 1
                    logger.debug(f"📊 Cache hit for AI analysis: {content_path}")
                    return [AIAnalysisResult(**result) for result in cached_results]
            
            # Perform analysis based on content type
            if content_type == ContentType.IMAGE and path_obj.exists():
                for analysis_type in analysis_types:
                    if analysis_type == AnalysisType.OBJECT_DETECTION:
                        result = await self._analyze_objects(content_path)
                        if result:
                            results.append(result)
                    
                    elif analysis_type == AnalysisType.SCENE_RECOGNITION:
                        result = await self._analyze_scene(content_path)
                        if result:
                            results.append(result)
                    
                    elif analysis_type == AnalysisType.QUALITY_ASSESSMENT:
                        result = await self._assess_quality(content_path)
                        if result:
                            results.append(result)
                    
                    elif analysis_type == AnalysisType.COLOR_ANALYSIS:
                        result = await self._analyze_colors(content_path)
                        if result:
                            results.append(result)
            
            # Cache results
            if self.config.cache_results and results:
                await cache_manager.set(
                    CacheType.IMAGE_ANALYSIS,
                    cache_key,
                    [result.to_dict() for result in results],
                    ttl=self.config.cache_ttl
                )
            
            # Update statistics
            processing_time = time.time() - start_time
            self.analysis_stats["total_analyses"] += 1
            self.analysis_stats["successful_analyses"] += len(results)
            self._update_average_processing_time(processing_time)
            
            # Track performance
            await track_media_processing_time("ai_content_analysis", processing_time, content_path)
            
            logger.info(f"🧠 AI analysis completed: {len(results)} results for {path_obj.name}")
            return results
            
        except Exception as e:
            self.analysis_stats["failed_analyses"] += 1
            logger.error(f"❌ AI content analysis failed for {content_path}: {e}")
            return []
    
    async def _analyze_objects(self, content_path: str) -> Optional[AIAnalysisResult]:
        """Perform object detection analysis"""
        if "object_detection" not in self.models:
            return None
            
        start_time = time.time()
        
        try:
            if not PIL_AVAILABLE:
                return None
                
            # Load and preprocess image
            image = Image.open(content_path).convert("RGB")
            image_tensor = transforms.ToTensor()(image).unsqueeze(0).to(self.device)
            
            # Run object detection
            with torch.no_grad():
                predictions = self.models["object_detection"](image_tensor)
            
            # Process results
            detected_objects = []
            if predictions and len(predictions) > 0:
                pred = predictions[0]
                boxes = pred["boxes"].cpu().numpy()
                labels = pred["labels"].cpu().numpy()
                scores = pred["scores"].cpu().numpy()
                
                for i, score in enumerate(scores):
                    if score > self.config.confidence_threshold:
                        detected_objects.append({
                            "label": int(labels[i]),
                            "confidence": float(score),
                            "bbox": boxes[i].tolist()
                        })
            
            processing_time = time.time() - start_time
            
            return AIAnalysisResult(
                content_path=content_path,
                content_type=ContentType.IMAGE,
                analysis_type=AnalysisType.OBJECT_DETECTION,
                confidence=max([obj["confidence"] for obj in detected_objects], default=0.0),
                results={
                    "objects_detected": len(detected_objects),
                    "objects": detected_objects
                },
                processing_time=processing_time,
                model_version=self.model_info["object_detection"]["version"]
            )
            
        except Exception as e:
            logger.error(f"❌ Object detection failed for {content_path}: {e}")
            return None
    
    async def _analyze_scene(self, content_path: str) -> Optional[AIAnalysisResult]:
        """Perform scene recognition analysis"""
        if "scene_recognition" not in self.models:
            return None
            
        start_time = time.time()
        
        try:
            if not PIL_AVAILABLE:
                return None
                
            # Load and preprocess image
            image = Image.open(content_path).convert("RGB")
            image_tensor = self.scene_transform(image).unsqueeze(0).to(self.device)
            
            # Run scene recognition
            with torch.no_grad():
                outputs = self.models["scene_recognition"](image_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            
            # Get top predictions
            top5_prob, top5_idx = torch.topk(probabilities, 5)
            
            scene_predictions = []
            for i in range(5):
                scene_predictions.append({
                    "class_idx": int(top5_idx[i]),
                    "confidence": float(top5_prob[i])
                })
            
            processing_time = time.time() - start_time
            
            return AIAnalysisResult(
                content_path=content_path,
                content_type=ContentType.IMAGE,
                analysis_type=AnalysisType.SCENE_RECOGNITION,
                confidence=float(top5_prob[0]),
                results={
                    "top_predictions": scene_predictions,
                    "predicted_scene": int(top5_idx[0])
                },
                processing_time=processing_time,
                model_version=self.model_info["scene_recognition"]["version"]
            )
            
        except Exception as e:
            logger.error(f"❌ Scene recognition failed for {content_path}: {e}")
            return None
    
    async def _assess_quality(self, content_path: str) -> Optional[AIAnalysisResult]:
        """Perform image quality assessment"""
        start_time = time.time()
        
        try:
            if not OPENCV_AVAILABLE or not PIL_AVAILABLE:
                return None
                
            # Load image
            image_pil = Image.open(content_path)
            image_cv = cv2.imread(content_path)
            
            if image_cv is None:
                return None
            
            # Calculate quality metrics
            quality_metrics = {}
            
            # Sharpness (Laplacian variance)
            gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            quality_metrics["sharpness"] = float(sharpness)
            
            # Contrast (standard deviation)
            contrast = np.std(gray)
            quality_metrics["contrast"] = float(contrast)
            
            # Brightness (mean pixel value)
            brightness = np.mean(gray)
            quality_metrics["brightness"] = float(brightness)
            
            # Noise estimation (using median blur difference)
            blur = cv2.medianBlur(gray, 5)
            noise = np.sum(np.abs(gray.astype(np.float32) - blur.astype(np.float32)))
            quality_metrics["noise"] = float(noise)
            
            # Overall quality score (normalized)
            quality_score = min(1.0, (sharpness / 1000 + contrast / 100) / 2)
            quality_metrics["overall_score"] = quality_score
            
            processing_time = time.time() - start_time
            
            return AIAnalysisResult(
                content_path=content_path,
                content_type=ContentType.IMAGE,
                analysis_type=AnalysisType.QUALITY_ASSESSMENT,
                confidence=quality_score,
                results=quality_metrics,
                processing_time=processing_time,
                model_version=self.model_info.get("quality_assessment", {}).get("version", "1.0.0")
            )
            
        except Exception as e:
            logger.error(f"❌ Quality assessment failed for {content_path}: {e}")
            return None
    
    async def _analyze_colors(self, content_path: str) -> Optional[AIAnalysisResult]:
        """Perform color analysis"""
        start_time = time.time()
        
        try:
            if not PIL_AVAILABLE or not np:
                return None
                
            # Load image
            image = Image.open(content_path).convert("RGB")
            image_array = np.array(image)
            
            # Calculate color statistics
            color_stats = {}
            
            # Mean colors
            mean_colors = np.mean(image_array, axis=(0, 1))
            color_stats["mean_rgb"] = mean_colors.tolist()
            
            # Dominant colors (simplified - top 5 most frequent colors)
            pixels = image_array.reshape(-1, 3)
            unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
            
            # Sort by frequency
            sorted_indices = np.argsort(counts)[::-1]
            top_colors = unique_colors[sorted_indices[:5]]
            top_counts = counts[sorted_indices[:5]]
            
            dominant_colors = []
            total_pixels = len(pixels)
            for i in range(len(top_colors)):
                dominant_colors.append({
                    "rgb": top_colors[i].tolist(),
                    "frequency": float(top_counts[i] / total_pixels)
                })
            
            color_stats["dominant_colors"] = dominant_colors
            
            # Color distribution
            color_stats["color_variance"] = np.var(pixels, axis=0).tolist()
            
            processing_time = time.time() - start_time
            
            return AIAnalysisResult(
                content_path=content_path,
                content_type=ContentType.IMAGE,
                analysis_type=AnalysisType.COLOR_ANALYSIS,
                confidence=1.0,  # Color analysis is deterministic
                results=color_stats,
                processing_time=processing_time,
                model_version="1.0.0"
            )
            
        except Exception as e:
            logger.error(f"❌ Color analysis failed for {content_path}: {e}")
            return None
    
    def _update_average_processing_time(self, new_time: float):
        """Update running average processing time"""
        if self.analysis_stats["average_processing_time"] == 0:
            self.analysis_stats["average_processing_time"] = new_time
        else:
            # Weighted average
            weight = 0.1
            self.analysis_stats["average_processing_time"] = (
                (1 - weight) * self.analysis_stats["average_processing_time"] +
                weight * new_time
            )
    
    async def batch_analyze(
        self,
        content_paths: List[str],
        content_type: ContentType,
        analysis_types: List[AnalysisType] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, List[AIAnalysisResult]]:
        """Perform batch AI analysis on multiple content items"""
        logger.info(f"🧠 Starting batch AI analysis: {len(content_paths)} items")
        
        results = {}
        processed = 0
        
        # Process in batches to manage memory
        for i in range(0, len(content_paths), self.config.batch_size):
            batch = content_paths[i:i + self.config.batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.analyze_content(path, content_type, analysis_types)
                for path in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Collect results
            for j, path in enumerate(batch):
                if isinstance(batch_results[j], list):
                    results[path] = batch_results[j]
                else:
                    results[path] = []
                    logger.error(f"❌ Batch analysis failed for {path}: {batch_results[j]}")
                
                processed += 1
                
                if progress_callback:
                    progress_callback(processed, len(content_paths), Path(path).name)
        
        logger.info(f"✅ Batch AI analysis completed: {processed} items processed")
        return results
    
    async def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get AI analysis performance statistics"""
        return {
            "analysis_stats": self.analysis_stats.copy(),
            "models_loaded": list(self.models.keys()),
            "device": self.device,
            "config": {
                "confidence_threshold": self.config.confidence_threshold,
                "cache_enabled": self.config.cache_results,
                "batch_size": self.config.batch_size
            },
            "model_info": self.model_info.copy()
        }


# Global AI analyzer instance
_ai_analyzer: Optional[AIContentAnalyzer] = None

async def get_ai_content_analyzer(config: Optional[ContentAnalysisConfig] = None) -> AIContentAnalyzer:
    """Get or create global AI content analyzer instance"""
    global _ai_analyzer
    
    if _ai_analyzer is None:
        _ai_analyzer = AIContentAnalyzer(config)
        await _ai_analyzer.initialize_models()
    
    return _ai_analyzer


# Convenience functions for AI analysis
async def analyze_image_content(image_path: str, analysis_types: List[AnalysisType] = None) -> List[AIAnalysisResult]:
    """Quick image content analysis"""
    analyzer = await get_ai_content_analyzer()
    return await analyzer.analyze_content(image_path, ContentType.IMAGE, analysis_types)


async def batch_analyze_images(image_paths: List[str], progress_callback: Optional[callable] = None) -> Dict[str, List[AIAnalysisResult]]:
    """Quick batch image analysis"""
    analyzer = await get_ai_content_analyzer()
    return await analyzer.batch_analyze(image_paths, ContentType.IMAGE, progress_callback=progress_callback)