"""
MVidarr Auto-Tagging Service - Phase 3 Week 25
ML-powered automatic content tagging with confidence scoring and validation
"""

import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from collections import defaultdict

# AI/ML Libraries
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    import nltk
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    cosine_similarity = None

from src.services.ai_content_analyzer import get_ai_content_analyzer, AIAnalysisResult, AnalysisType
from src.services.media_cache_manager import get_media_cache_manager, CacheType
from src.services.performance_monitor import track_media_processing_time
from src.utils.logger import get_logger

logger = get_logger("mvidarr.auto_tagging")


class TagCategory(Enum):
    """Categories of tags that can be generated"""
    OBJECT = "object"
    SCENE = "scene"
    EMOTION = "emotion"
    COLOR = "color"
    STYLE = "style"
    QUALITY = "quality"
    CONTENT = "content"
    TECHNICAL = "technical"


class TagSource(Enum):
    """Sources of tag generation"""
    AI_VISION = "ai_vision"
    ML_CLASSIFICATION = "ml_classification"
    METADATA_EXTRACTION = "metadata_extraction"
    USER_INPUT = "user_input"
    COLLABORATIVE = "collaborative"
    RULE_BASED = "rule_based"


@dataclass
class Tag:
    """Individual tag with metadata"""
    name: str
    category: TagCategory
    confidence: float
    source: TagSource
    synonyms: List[str] = field(default_factory=list)
    parent_tags: List[str] = field(default_factory=list)
    child_tags: List[str] = field(default_factory=list)
    frequency: int = 1
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "confidence": self.confidence,
            "source": self.source.value,
            "synonyms": self.synonyms,
            "parent_tags": self.parent_tags,
            "child_tags": self.child_tags,
            "frequency": self.frequency,
            "timestamp": self.timestamp
        }


@dataclass
class TaggingResult:
    """Result of auto-tagging process"""
    content_path: str
    tags: List[Tag]
    processing_time: float
    model_version: str
    confidence_score: float
    validation_status: str = "pending"
    human_reviewed: bool = False
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_path": self.content_path,
            "tags": [tag.to_dict() for tag in self.tags],
            "processing_time": self.processing_time,
            "model_version": self.model_version,
            "confidence_score": self.confidence_score,
            "validation_status": self.validation_status,
            "human_reviewed": self.human_reviewed,
            "timestamp": self.timestamp
        }


@dataclass
class AutoTaggingConfig:
    """Configuration for auto-tagging service"""
    min_confidence_threshold: float = 0.6
    max_tags_per_content: int = 20
    enable_hierarchical_tags: bool = True
    enable_synonym_expansion: bool = True
    cache_results: bool = True
    cache_ttl: int = 3600  # 1 hour
    batch_size: int = 16
    enable_collaborative_filtering: bool = True
    tag_validation_threshold: float = 0.8
    enable_custom_models: bool = False


class TagHierarchy:
    """Hierarchical tag management system"""
    
    def __init__(self):
        """Initialize tag hierarchy"""
        self.hierarchy = self._build_default_hierarchy()
        self.synonyms = self._build_synonym_map()
        
    def _build_default_hierarchy(self) -> Dict[str, Dict[str, List[str]]]:
        """Build default tag hierarchy"""
        return {
            "objects": {
                "animals": ["dog", "cat", "bird", "horse", "cow", "sheep"],
                "vehicles": ["car", "truck", "motorcycle", "bicycle", "train", "plane"],
                "furniture": ["chair", "table", "bed", "sofa", "desk", "cabinet"],
                "electronics": ["phone", "computer", "tv", "camera", "headphones"]
            },
            "scenes": {
                "indoor": ["kitchen", "bedroom", "living room", "office", "bathroom"],
                "outdoor": ["park", "beach", "mountain", "forest", "city", "street"],
                "nature": ["landscape", "sunset", "ocean", "trees", "flowers", "sky"]
            },
            "styles": {
                "photography": ["portrait", "landscape", "macro", "street", "abstract"],
                "artistic": ["painting", "drawing", "sketch", "digital art", "illustration"],
                "technical": ["black and white", "color", "high contrast", "soft focus"]
            },
            "emotions": {
                "positive": ["happy", "joyful", "peaceful", "exciting", "beautiful"],
                "negative": ["sad", "angry", "dark", "scary", "dramatic"],
                "neutral": ["calm", "neutral", "documentary", "informational"]
            }
        }
    
    def _build_synonym_map(self) -> Dict[str, List[str]]:
        """Build synonym mapping for tags"""
        return {
            "dog": ["puppy", "canine", "pet"],
            "cat": ["kitten", "feline", "pet"],
            "car": ["automobile", "vehicle", "auto"],
            "house": ["home", "building", "residence"],
            "person": ["human", "people", "individual"],
            "water": ["ocean", "sea", "lake", "river"],
            "tree": ["trees", "forest", "woods"],
            "food": ["meal", "cuisine", "dish", "cooking"]
        }
    
    def get_parent_tags(self, tag: str) -> List[str]:
        """Get parent tags for a given tag"""
        parents = []
        for category, subcategories in self.hierarchy.items():
            for subcategory, tags in subcategories.items():
                if tag.lower() in [t.lower() for t in tags]:
                    parents.append(subcategory)
                    parents.append(category)
        return parents
    
    def get_child_tags(self, tag: str) -> List[str]:
        """Get child tags for a given tag"""
        tag_lower = tag.lower()
        for category, subcategories in self.hierarchy.items():
            if tag_lower == category.lower():
                return list(subcategories.keys())
            for subcategory, tags in subcategories.items():
                if tag_lower == subcategory.lower():
                    return tags
        return []
    
    def get_synonyms(self, tag: str) -> List[str]:
        """Get synonyms for a tag"""
        return self.synonyms.get(tag.lower(), [])


class AutoTaggingService:
    """Advanced ML-powered automatic tagging service"""
    
    # Pre-defined object class mappings (COCO classes)
    COCO_CLASSES = [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
        "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
        "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
        "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
        "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
        "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
        "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
        "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
        "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
        "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
        "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
        "toothbrush"
    ]
    
    def __init__(self, config: Optional[AutoTaggingConfig] = None):
        """Initialize auto-tagging service"""
        self.config = config or AutoTaggingConfig()
        self.tag_hierarchy = TagHierarchy()
        
        # ML models and pipelines
        self.pipelines = {}
        self.custom_models = {}
        
        # Tag statistics and learning
        self.tag_stats = defaultdict(int)
        self.co_occurrence_matrix = defaultdict(lambda: defaultdict(int))
        self.user_feedback = defaultdict(list)
        
        # Performance tracking
        self.tagging_stats = {
            "total_tagged": 0,
            "successful_tagging": 0,
            "failed_tagging": 0,
            "average_tags_per_content": 0.0,
            "average_confidence": 0.0,
            "cache_hits": 0
        }
        
        logger.info("🏷️ Auto-tagging service initialized")
    
    async def initialize_models(self):
        """Initialize ML models for tagging"""
        try:
            if TRANSFORMERS_AVAILABLE:
                await self._load_text_classification_models()
            
            if SKLEARN_AVAILABLE:
                await self._load_similarity_models()
            
            logger.info(f"✅ Auto-tagging models initialized: {len(self.pipelines)} pipelines loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize auto-tagging models: {e}")
            raise
    
    async def _load_text_classification_models(self):
        """Load text classification models"""
        try:
            # Load zero-shot classification pipeline
            self.pipelines["zero_shot"] = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            
            # Load feature extraction pipeline
            self.pipelines["feature_extraction"] = pipeline(
                "feature-extraction",
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            logger.info("📝 Text classification models loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load text classification models: {e}")
    
    async def _load_similarity_models(self):
        """Load similarity computation models"""
        try:
            # Initialize TF-IDF vectorizer for text similarity
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            logger.info("🔍 Similarity models loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load similarity models: {e}")
    
    async def generate_tags(
        self,
        content_path: str,
        ai_analysis_results: List[AIAnalysisResult] = None,
        existing_tags: List[str] = None,
        user_context: Dict[str, Any] = None
    ) -> TaggingResult:
        """Generate tags for content using multiple ML approaches"""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_manager = await get_media_cache_manager()
            cache_key = f"auto_tags_{hashlib.md5(content_path.encode()).hexdigest()}"
            
            if self.config.cache_results:
                cached_result = await cache_manager.get(CacheType.IMAGE_ANALYSIS, cache_key)
                if cached_result:
                    self.tagging_stats["cache_hits"] += 1
                    logger.debug(f"🏷️ Cache hit for auto-tagging: {content_path}")
                    return TaggingResult(**cached_result)
            
            # Get AI analysis results if not provided
            if ai_analysis_results is None:
                ai_analyzer = await get_ai_content_analyzer()
                ai_analysis_results = await ai_analyzer.analyze_content(
                    content_path, 
                    content_type=ai_analyzer.ContentType.IMAGE
                )
            
            # Generate tags from different sources
            all_tags = []
            
            # Tags from AI vision analysis
            vision_tags = await self._generate_vision_tags(ai_analysis_results)
            all_tags.extend(vision_tags)
            
            # Tags from metadata
            metadata_tags = await self._generate_metadata_tags(content_path)
            all_tags.extend(metadata_tags)
            
            # Tags from filename and context
            context_tags = await self._generate_context_tags(content_path, user_context)
            all_tags.extend(context_tags)
            
            # Tags from collaborative filtering (if existing tags provided)
            if existing_tags and self.config.enable_collaborative_filtering:
                collab_tags = await self._generate_collaborative_tags(existing_tags)
                all_tags.extend(collab_tags)
            
            # Merge and rank tags
            final_tags = await self._merge_and_rank_tags(all_tags)
            
            # Apply hierarchical expansion if enabled
            if self.config.enable_hierarchical_tags:
                final_tags = await self._expand_hierarchical_tags(final_tags)
            
            # Limit to max tags
            final_tags = final_tags[:self.config.max_tags_per_content]
            
            # Calculate overall confidence
            overall_confidence = sum(tag.confidence for tag in final_tags) / len(final_tags) if final_tags else 0.0
            
            processing_time = time.time() - start_time
            
            result = TaggingResult(
                content_path=content_path,
                tags=final_tags,
                processing_time=processing_time,
                model_version="1.0.0",
                confidence_score=overall_confidence
            )
            
            # Cache result
            if self.config.cache_results:
                await cache_manager.set(
                    CacheType.IMAGE_ANALYSIS,
                    cache_key,
                    result.to_dict(),
                    ttl=self.config.cache_ttl
                )
            
            # Update statistics
            self._update_tagging_stats(result)
            
            # Track performance
            await track_media_processing_time("auto_tagging", processing_time, content_path)
            
            logger.info(f"🏷️ Generated {len(final_tags)} tags for {Path(content_path).name}")
            return result
            
        except Exception as e:
            self.tagging_stats["failed_tagging"] += 1
            logger.error(f"❌ Auto-tagging failed for {content_path}: {e}")
            
            # Return empty result
            return TaggingResult(
                content_path=content_path,
                tags=[],
                processing_time=time.time() - start_time,
                model_version="1.0.0",
                confidence_score=0.0
            )
    
    async def _generate_vision_tags(self, ai_results: List[AIAnalysisResult]) -> List[Tag]:
        """Generate tags from AI vision analysis results"""
        tags = []
        
        for result in ai_results:
            if result.analysis_type == AnalysisType.OBJECT_DETECTION:
                # Tags from detected objects
                for obj in result.results.get("objects", []):
                    if obj["confidence"] >= self.config.min_confidence_threshold:
                        class_idx = obj.get("label", 0)
                        if 0 <= class_idx < len(self.COCO_CLASSES):
                            object_name = self.COCO_CLASSES[class_idx]
                            tags.append(Tag(
                                name=object_name,
                                category=TagCategory.OBJECT,
                                confidence=obj["confidence"],
                                source=TagSource.AI_VISION
                            ))
            
            elif result.analysis_type == AnalysisType.SCENE_RECOGNITION:
                # Tags from scene recognition
                if result.confidence >= self.config.min_confidence_threshold:
                    # Map scene class to tag (simplified)
                    scene_tag = f"scene_{result.results.get('predicted_scene', 'unknown')}"
                    tags.append(Tag(
                        name=scene_tag,
                        category=TagCategory.SCENE,
                        confidence=result.confidence,
                        source=TagSource.AI_VISION
                    ))
            
            elif result.analysis_type == AnalysisType.QUALITY_ASSESSMENT:
                # Tags from quality assessment
                quality_results = result.results
                if quality_results.get("overall_score", 0) > 0.8:
                    tags.append(Tag(
                        name="high_quality",
                        category=TagCategory.QUALITY,
                        confidence=quality_results["overall_score"],
                        source=TagSource.AI_VISION
                    ))
                
                # Sharpness tags
                if quality_results.get("sharpness", 0) > 500:
                    tags.append(Tag(
                        name="sharp",
                        category=TagCategory.TECHNICAL,
                        confidence=min(1.0, quality_results["sharpness"] / 1000),
                        source=TagSource.AI_VISION
                    ))
            
            elif result.analysis_type == AnalysisType.COLOR_ANALYSIS:
                # Tags from color analysis
                color_results = result.results
                dominant_colors = color_results.get("dominant_colors", [])
                
                for color_info in dominant_colors[:3]:  # Top 3 colors
                    if color_info["frequency"] > 0.1:  # At least 10% of image
                        rgb = color_info["rgb"]
                        color_name = self._rgb_to_color_name(rgb)
                        tags.append(Tag(
                            name=color_name,
                            category=TagCategory.COLOR,
                            confidence=color_info["frequency"],
                            source=TagSource.AI_VISION
                        ))
        
        return tags
    
    async def _generate_metadata_tags(self, content_path: str) -> List[Tag]:
        """Generate tags from file metadata"""
        tags = []
        
        try:
            path = Path(content_path)
            
            # File extension tag
            if path.suffix:
                format_tag = path.suffix[1:].lower()  # Remove dot
                tags.append(Tag(
                    name=format_tag,
                    category=TagCategory.TECHNICAL,
                    confidence=1.0,
                    source=TagSource.METADATA_EXTRACTION
                ))
            
            # File size tags
            if path.exists():
                file_size = path.stat().st_size
                if file_size > 10 * 1024 * 1024:  # > 10MB
                    tags.append(Tag(
                        name="large_file",
                        category=TagCategory.TECHNICAL,
                        confidence=0.9,
                        source=TagSource.METADATA_EXTRACTION
                    ))
                elif file_size < 100 * 1024:  # < 100KB
                    tags.append(Tag(
                        name="small_file",
                        category=TagCategory.TECHNICAL,
                        confidence=0.9,
                        source=TagSource.METADATA_EXTRACTION
                    ))
        
        except Exception as e:
            logger.error(f"❌ Failed to extract metadata tags: {e}")
        
        return tags
    
    async def _generate_context_tags(self, content_path: str, user_context: Dict[str, Any] = None) -> List[Tag]:
        """Generate tags from filename and user context"""
        tags = []
        
        try:
            path = Path(content_path)
            
            # Extract meaningful words from filename
            filename_words = self._extract_filename_words(path.stem)
            for word in filename_words:
                if len(word) > 2 and word.lower() not in ['img', 'image', 'pic', 'photo']:
                    tags.append(Tag(
                        name=word.lower(),
                        category=TagCategory.CONTENT,
                        confidence=0.7,
                        source=TagSource.METADATA_EXTRACTION
                    ))
            
            # Tags from user context
            if user_context:
                if "album" in user_context:
                    album_name = user_context["album"]
                    tags.append(Tag(
                        name=f"album_{album_name}",
                        category=TagCategory.CONTENT,
                        confidence=0.8,
                        source=TagSource.USER_INPUT
                    ))
                
                if "event" in user_context:
                    event_name = user_context["event"]
                    tags.append(Tag(
                        name=f"event_{event_name}",
                        category=TagCategory.CONTENT,
                        confidence=0.8,
                        source=TagSource.USER_INPUT
                    ))
        
        except Exception as e:
            logger.error(f"❌ Failed to generate context tags: {e}")
        
        return tags
    
    async def _generate_collaborative_tags(self, existing_tags: List[str]) -> List[Tag]:
        """Generate tags based on collaborative filtering"""
        tags = []
        
        try:
            # Find tags that frequently co-occur with existing tags
            for existing_tag in existing_tags:
                co_occurring_tags = self.co_occurrence_matrix.get(existing_tag, {})
                
                # Sort by co-occurrence frequency
                sorted_tags = sorted(co_occurring_tags.items(), key=lambda x: x[1], reverse=True)
                
                # Add top co-occurring tags
                for tag_name, frequency in sorted_tags[:5]:
                    if frequency > 2:  # Minimum co-occurrence threshold
                        confidence = min(0.8, frequency / 10)  # Scale confidence
                        tags.append(Tag(
                            name=tag_name,
                            category=TagCategory.CONTENT,
                            confidence=confidence,
                            source=TagSource.COLLABORATIVE
                        ))
        
        except Exception as e:
            logger.error(f"❌ Failed to generate collaborative tags: {e}")
        
        return tags
    
    async def _merge_and_rank_tags(self, tags: List[Tag]) -> List[Tag]:
        """Merge duplicate tags and rank by confidence"""
        tag_dict = {}
        
        # Merge tags with same name
        for tag in tags:
            if tag.name in tag_dict:
                # Combine confidence scores (weighted average)
                existing_tag = tag_dict[tag.name]
                combined_confidence = (existing_tag.confidence + tag.confidence) / 2
                existing_tag.confidence = min(1.0, combined_confidence)
                existing_tag.frequency += 1
                
                # Merge synonyms
                existing_tag.synonyms.extend(tag.synonyms)
                existing_tag.synonyms = list(set(existing_tag.synonyms))
            else:
                tag_dict[tag.name] = tag
        
        # Filter by confidence threshold and rank
        filtered_tags = [
            tag for tag in tag_dict.values() 
            if tag.confidence >= self.config.min_confidence_threshold
        ]
        
        # Sort by confidence
        return sorted(filtered_tags, key=lambda x: x.confidence, reverse=True)
    
    async def _expand_hierarchical_tags(self, tags: List[Tag]) -> List[Tag]:
        """Expand tags with hierarchical relationships"""
        expanded_tags = tags.copy()
        
        for tag in tags:
            # Add parent tags
            parent_tags = self.tag_hierarchy.get_parent_tags(tag.name)
            for parent in parent_tags:
                # Check if parent tag already exists
                if not any(t.name == parent for t in expanded_tags):
                    expanded_tags.append(Tag(
                        name=parent,
                        category=tag.category,
                        confidence=tag.confidence * 0.8,  # Reduce confidence for parent
                        source=tag.source,
                        child_tags=[tag.name]
                    ))
            
            # Add child tags (less common, only for high-confidence tags)
            if tag.confidence > 0.9:
                child_tags = self.tag_hierarchy.get_child_tags(tag.name)
                for child in child_tags[:2]:  # Limit child tags
                    if not any(t.name == child for t in expanded_tags):
                        expanded_tags.append(Tag(
                            name=child,
                            category=tag.category,
                            confidence=tag.confidence * 0.6,  # Reduce confidence for child
                            source=tag.source,
                            parent_tags=[tag.name]
                        ))
            
            # Add synonyms if enabled
            if self.config.enable_synonym_expansion:
                synonyms = self.tag_hierarchy.get_synonyms(tag.name)
                tag.synonyms.extend(synonyms)
                tag.synonyms = list(set(tag.synonyms))
        
        return expanded_tags
    
    def _extract_filename_words(self, filename: str) -> List[str]:
        """Extract meaningful words from filename"""
        # Remove common separators and split
        import re
        words = re.split(r'[_\-\s\d]+', filename)
        
        # Filter out short words and numbers
        meaningful_words = [
            word for word in words 
            if len(word) > 2 and not word.isdigit()
        ]
        
        return meaningful_words
    
    def _rgb_to_color_name(self, rgb: List[int]) -> str:
        """Convert RGB values to color name"""
        r, g, b = rgb
        
        # Simple color name mapping (can be expanded with more sophisticated color analysis)
        if r > 200 and g < 100 and b < 100:
            return "red"
        elif r < 100 and g > 200 and b < 100:
            return "green"
        elif r < 100 and g < 100 and b > 200:
            return "blue"
        elif r > 200 and g > 200 and b < 100:
            return "yellow"
        elif r > 200 and g < 100 and b > 200:
            return "magenta"
        elif r < 100 and g > 200 and b > 200:
            return "cyan"
        elif r > 200 and g > 200 and b > 200:
            return "white"
        elif r < 50 and g < 50 and b < 50:
            return "black"
        elif r > 100 and r < 200 and g > 100 and g < 200 and b > 100 and b < 200:
            return "gray"
        else:
            return "mixed_color"
    
    def _update_tagging_stats(self, result: TaggingResult):
        """Update tagging statistics"""
        self.tagging_stats["total_tagged"] += 1
        self.tagging_stats["successful_tagging"] += 1
        
        # Update average tags per content
        current_avg = self.tagging_stats["average_tags_per_content"]
        total = self.tagging_stats["total_tagged"]
        new_avg = ((current_avg * (total - 1)) + len(result.tags)) / total
        self.tagging_stats["average_tags_per_content"] = new_avg
        
        # Update average confidence
        if result.tags:
            current_conf_avg = self.tagging_stats["average_confidence"]
            new_conf_avg = ((current_conf_avg * (total - 1)) + result.confidence_score) / total
            self.tagging_stats["average_confidence"] = new_conf_avg
        
        # Update co-occurrence matrix
        tag_names = [tag.name for tag in result.tags]
        for i, tag1 in enumerate(tag_names):
            for j, tag2 in enumerate(tag_names):
                if i != j:
                    self.co_occurrence_matrix[tag1][tag2] += 1
    
    async def batch_generate_tags(
        self,
        content_paths: List[str],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, TaggingResult]:
        """Generate tags for multiple content items in batch"""
        logger.info(f"🏷️ Starting batch auto-tagging: {len(content_paths)} items")
        
        results = {}
        processed = 0
        
        # Process in batches
        for i in range(0, len(content_paths), self.config.batch_size):
            batch = content_paths[i:i + self.config.batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.generate_tags(path)
                for path in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Collect results
            for j, path in enumerate(batch):
                if isinstance(batch_results[j], TaggingResult):
                    results[path] = batch_results[j]
                else:
                    logger.error(f"❌ Batch tagging failed for {path}: {batch_results[j]}")
                    results[path] = TaggingResult(
                        content_path=path,
                        tags=[],
                        processing_time=0.0,
                        model_version="1.0.0",
                        confidence_score=0.0
                    )
                
                processed += 1
                
                if progress_callback:
                    progress_callback(processed, len(content_paths), Path(path).name)
        
        logger.info(f"✅ Batch auto-tagging completed: {processed} items processed")
        return results
    
    async def validate_tags(self, tags: List[Tag], validation_context: Dict[str, Any] = None) -> List[Tag]:
        """Validate and improve tag quality"""
        validated_tags = []
        
        for tag in tags:
            # Basic validation rules
            if len(tag.name) < 2 or len(tag.name) > 50:
                continue
            
            # Confidence threshold validation
            if tag.confidence < self.config.min_confidence_threshold:
                continue
            
            # Context-based validation
            if validation_context:
                # Add context-specific validation rules here
                pass
            
            # Mark as validated if above threshold
            if tag.confidence >= self.config.tag_validation_threshold:
                tag.name = "validated_" + tag.name if not tag.name.startswith("validated_") else tag.name
            
            validated_tags.append(tag)
        
        return validated_tags
    
    async def get_tagging_statistics(self) -> Dict[str, Any]:
        """Get auto-tagging performance statistics"""
        return {
            "tagging_stats": self.tagging_stats.copy(),
            "tag_statistics": dict(self.tag_stats),
            "config": {
                "min_confidence_threshold": self.config.min_confidence_threshold,
                "max_tags_per_content": self.config.max_tags_per_content,
                "cache_enabled": self.config.cache_results,
                "batch_size": self.config.batch_size
            },
            "model_info": {
                "pipelines_loaded": list(self.pipelines.keys()),
                "hierarchy_categories": len(self.tag_hierarchy.hierarchy),
                "synonym_mappings": len(self.tag_hierarchy.synonyms)
            }
        }


# Global auto-tagging service instance
_auto_tagging_service: Optional[AutoTaggingService] = None

async def get_auto_tagging_service(config: Optional[AutoTaggingConfig] = None) -> AutoTaggingService:
    """Get or create global auto-tagging service instance"""
    global _auto_tagging_service
    
    if _auto_tagging_service is None:
        _auto_tagging_service = AutoTaggingService(config)
        await _auto_tagging_service.initialize_models()
    
    return _auto_tagging_service


# Convenience functions
async def generate_content_tags(content_path: str, user_context: Dict[str, Any] = None) -> TaggingResult:
    """Quick content tagging"""
    service = await get_auto_tagging_service()
    return await service.generate_tags(content_path, user_context=user_context)


async def batch_tag_content(content_paths: List[str], progress_callback: Optional[callable] = None) -> Dict[str, TaggingResult]:
    """Quick batch content tagging"""
    service = await get_auto_tagging_service()
    return await service.batch_generate_tags(content_paths, progress_callback)