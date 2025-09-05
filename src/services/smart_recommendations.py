"""
MVidarr Smart Recommendations Engine - Phase 3 Week 25
AI-powered content recommendations using collaborative filtering, content analysis, and user behavior
"""

import asyncio
import logging
import time
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import heapq

# ML Libraries
try:
    import numpy as np
    from scipy.spatial.distance import cosine
    from scipy.sparse import csr_matrix
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    np = None
    cosine = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.decomposition import TruncatedSVD
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    cosine_similarity = None

from src.services.ai_content_analyzer import get_ai_content_analyzer, AIAnalysisResult
from src.services.auto_tagging_service import get_auto_tagging_service, Tag
from src.services.media_cache_manager import get_media_cache_manager, CacheType
from src.services.performance_monitor import track_media_processing_time
from src.utils.logger import get_logger

logger = get_logger("mvidarr.smart_recommendations")


class RecommendationType(Enum):
    """Types of recommendations available"""
    SIMILAR_CONTENT = "similar_content"
    USER_BASED = "user_based"
    CONTENT_BASED = "content_based"
    COLLABORATIVE = "collaborative"
    TRENDING = "trending"
    PERSONALIZED = "personalized"
    SEASONAL = "seasonal"
    CONTEXTUAL = "contextual"


class RecommendationSource(Enum):
    """Sources for recommendation generation"""
    CONTENT_ANALYSIS = "content_analysis"
    USER_BEHAVIOR = "user_behavior"
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    TAG_SIMILARITY = "tag_similarity"
    VISUAL_SIMILARITY = "visual_similarity"
    TEMPORAL_PATTERNS = "temporal_patterns"
    SOCIAL_SIGNALS = "social_signals"


@dataclass
class RecommendationItem:
    """Individual recommendation item"""
    content_path: str
    content_id: str
    title: str
    confidence: float
    relevance_score: float
    recommendation_type: RecommendationType
    source: RecommendationSource
    reasons: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_path": self.content_path,
            "content_id": self.content_id,
            "title": self.title,
            "confidence": self.confidence,
            "relevance_score": self.relevance_score,
            "recommendation_type": self.recommendation_type.value,
            "source": self.source.value,
            "reasons": self.reasons,
            "tags": self.tags,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class RecommendationRequest:
    """Request for recommendations"""
    user_id: str
    content_id: Optional[str] = None
    recommendation_types: List[RecommendationType] = field(default_factory=list)
    max_recommendations: int = 10
    include_reasons: bool = True
    filter_viewed: bool = True
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.recommendation_types:
            self.recommendation_types = [
                RecommendationType.SIMILAR_CONTENT,
                RecommendationType.PERSONALIZED,
                RecommendationType.TRENDING
            ]


@dataclass
class RecommendationResult:
    """Result of recommendation generation"""
    user_id: str
    recommendations: List[RecommendationItem]
    processing_time: float
    model_version: str
    algorithms_used: List[str]
    cache_hit: bool = False
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "recommendations": [item.to_dict() for item in self.recommendations],
            "processing_time": self.processing_time,
            "model_version": self.model_version,
            "algorithms_used": self.algorithms_used,
            "cache_hit": self.cache_hit,
            "timestamp": self.timestamp
        }


@dataclass
class UserProfile:
    """User profile for personalized recommendations"""
    user_id: str
    preferences: Dict[str, float] = field(default_factory=dict)
    viewing_history: List[str] = field(default_factory=list)
    liked_content: List[str] = field(default_factory=list)
    disliked_content: List[str] = field(default_factory=list)
    favorite_tags: List[str] = field(default_factory=list)
    interaction_patterns: Dict[str, Any] = field(default_factory=dict)
    demographic_info: Dict[str, Any] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)


@dataclass
class ContentFeatures:
    """Feature representation of content for similarity calculations"""
    content_id: str
    visual_features: List[float] = field(default_factory=list)
    tag_features: List[float] = field(default_factory=list)
    content_features: List[float] = field(default_factory=list)
    metadata_features: Dict[str, Any] = field(default_factory=dict)
    popularity_score: float = 0.0
    quality_score: float = 0.0
    freshness_score: float = 0.0


class SmartRecommendationEngine:
    """Advanced AI-powered recommendation system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize smart recommendation engine"""
        self.config = config or {
            "max_recommendations": 20,
            "similarity_threshold": 0.3,
            "popularity_weight": 0.2,
            "freshness_weight": 0.1,
            "quality_weight": 0.3,
            "personalization_weight": 0.4,
            "cache_ttl": 1800,  # 30 minutes
            "enable_collaborative_filtering": True,
            "enable_content_based": True,
            "enable_hybrid": True
        }
        
        # Data storage
        self.user_profiles: Dict[str, UserProfile] = {}
        self.content_features: Dict[str, ContentFeatures] = {}
        self.interaction_matrix = defaultdict(lambda: defaultdict(float))
        self.content_similarity_matrix = defaultdict(dict)
        
        # ML models
        self.tfidf_vectorizer = None
        self.svd_model = None
        
        # Performance tracking
        self.recommendation_stats = {
            "total_requests": 0,
            "successful_recommendations": 0,
            "failed_recommendations": 0,
            "average_processing_time": 0.0,
            "cache_hits": 0,
            "algorithm_usage": defaultdict(int)
        }
        
        logger.info("🎯 Smart recommendation engine initialized")
    
    async def initialize_models(self):
        """Initialize ML models for recommendations"""
        try:
            if SKLEARN_AVAILABLE:
                # Initialize TF-IDF vectorizer for content-based recommendations
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words='english',
                    ngram_range=(1, 2),
                    max_df=0.8,
                    min_df=2
                )
                
                # Initialize SVD for dimensionality reduction
                self.svd_model = TruncatedSVD(n_components=100, random_state=42)
            
            logger.info("✅ Recommendation models initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize recommendation models: {e}")
            raise
    
    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResult:
        """Generate personalized recommendations for a user"""
        start_time = time.time()
        algorithms_used = []
        
        try:
            # Check cache first
            cache_manager = await get_media_cache_manager()
            cache_key = f"recommendations_{request.user_id}_{hash(str(request.__dict__))}"
            
            cached_result = await cache_manager.get(CacheType.BULK_OPERATION_RESULT, cache_key)
            if cached_result:
                self.recommendation_stats["cache_hits"] += 1
                cached_result["cache_hit"] = True
                return RecommendationResult(**cached_result)
            
            # Get or create user profile
            user_profile = await self._get_user_profile(request.user_id)
            
            # Generate recommendations using different algorithms
            all_recommendations = []
            
            for rec_type in request.recommendation_types:
                if rec_type == RecommendationType.SIMILAR_CONTENT and request.content_id:
                    recs = await self._get_similar_content_recommendations(
                        request.content_id, request.max_recommendations // len(request.recommendation_types)
                    )
                    all_recommendations.extend(recs)
                    algorithms_used.append("similar_content")
                
                elif rec_type == RecommendationType.PERSONALIZED:
                    recs = await self._get_personalized_recommendations(
                        user_profile, request.max_recommendations // len(request.recommendation_types)
                    )
                    all_recommendations.extend(recs)
                    algorithms_used.append("personalized")
                
                elif rec_type == RecommendationType.COLLABORATIVE:
                    recs = await self._get_collaborative_recommendations(
                        user_profile, request.max_recommendations // len(request.recommendation_types)
                    )
                    all_recommendations.extend(recs)
                    algorithms_used.append("collaborative_filtering")
                
                elif rec_type == RecommendationType.TRENDING:
                    recs = await self._get_trending_recommendations(
                        request.max_recommendations // len(request.recommendation_types)
                    )
                    all_recommendations.extend(recs)
                    algorithms_used.append("trending")
                
                elif rec_type == RecommendationType.CONTEXTUAL:
                    recs = await self._get_contextual_recommendations(
                        user_profile, request.context, request.max_recommendations // len(request.recommendation_types)
                    )
                    all_recommendations.extend(recs)
                    algorithms_used.append("contextual")
            
            # Merge and rank recommendations
            final_recommendations = await self._merge_and_rank_recommendations(
                all_recommendations, user_profile, request.max_recommendations
            )
            
            # Filter out viewed content if requested
            if request.filter_viewed:
                final_recommendations = [
                    rec for rec in final_recommendations
                    if rec.content_id not in user_profile.viewing_history
                ]
            
            # Limit to max recommendations
            final_recommendations = final_recommendations[:request.max_recommendations]
            
            processing_time = time.time() - start_time
            
            result = RecommendationResult(
                user_id=request.user_id,
                recommendations=final_recommendations,
                processing_time=processing_time,
                model_version="1.0.0",
                algorithms_used=algorithms_used
            )
            
            # Cache result
            await cache_manager.set(
                CacheType.BULK_OPERATION_RESULT,
                cache_key,
                result.to_dict(),
                ttl=self.config["cache_ttl"]
            )
            
            # Update statistics
            self._update_recommendation_stats(result, algorithms_used)
            
            # Track performance
            await track_media_processing_time("smart_recommendations", processing_time)
            
            logger.info(f"🎯 Generated {len(final_recommendations)} recommendations for user {request.user_id}")
            return result
            
        except Exception as e:
            self.recommendation_stats["failed_recommendations"] += 1
            logger.error(f"❌ Recommendation generation failed: {e}")
            
            return RecommendationResult(
                user_id=request.user_id,
                recommendations=[],
                processing_time=time.time() - start_time,
                model_version="1.0.0",
                algorithms_used=algorithms_used
            )
    
    async def _get_similar_content_recommendations(self, content_id: str, max_count: int) -> List[RecommendationItem]:
        """Get recommendations based on content similarity"""
        recommendations = []
        
        try:
            # Get content features
            if content_id not in self.content_features:
                await self._extract_content_features(content_id)
            
            source_features = self.content_features.get(content_id)
            if not source_features:
                return recommendations
            
            # Calculate similarity with other content
            similarities = []
            
            for other_id, other_features in self.content_features.items():
                if other_id == content_id:
                    continue
                
                # Calculate feature similarity
                similarity = await self._calculate_content_similarity(source_features, other_features)
                
                if similarity > self.config["similarity_threshold"]:
                    similarities.append((other_id, similarity))
            
            # Sort by similarity and create recommendations
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            for other_id, similarity in similarities[:max_count]:
                recommendations.append(RecommendationItem(
                    content_path=f"/path/to/{other_id}",  # Would be resolved from content database
                    content_id=other_id,
                    title=f"Content {other_id}",
                    confidence=similarity,
                    relevance_score=similarity,
                    recommendation_type=RecommendationType.SIMILAR_CONTENT,
                    source=RecommendationSource.CONTENT_ANALYSIS,
                    reasons=[f"Similar to content you viewed ({similarity:.1%} match)"]
                ))
        
        except Exception as e:
            logger.error(f"❌ Similar content recommendations failed: {e}")
        
        return recommendations
    
    async def _get_personalized_recommendations(self, user_profile: UserProfile, max_count: int) -> List[RecommendationItem]:
        """Get personalized recommendations based on user profile"""
        recommendations = []
        
        try:
            # Score content based on user preferences
            content_scores = {}
            
            for content_id, features in self.content_features.items():
                if content_id in user_profile.viewing_history:
                    continue
                
                score = 0.0
                
                # Tag preference matching
                for tag in features.metadata_features.get("tags", []):
                    if tag in user_profile.favorite_tags:
                        score += 0.3
                
                # Quality preference
                score += features.quality_score * self.config["quality_weight"]
                
                # Freshness preference
                score += features.freshness_score * self.config["freshness_weight"]
                
                # Popularity adjustment
                score += features.popularity_score * self.config["popularity_weight"]
                
                content_scores[content_id] = score
            
            # Sort by score and create recommendations
            sorted_content = sorted(content_scores.items(), key=lambda x: x[1], reverse=True)
            
            for content_id, score in sorted_content[:max_count]:
                recommendations.append(RecommendationItem(
                    content_path=f"/path/to/{content_id}",
                    content_id=content_id,
                    title=f"Content {content_id}",
                    confidence=min(1.0, score),
                    relevance_score=score,
                    recommendation_type=RecommendationType.PERSONALIZED,
                    source=RecommendationSource.USER_BEHAVIOR,
                    reasons=["Based on your viewing preferences"]
                ))
        
        except Exception as e:
            logger.error(f"❌ Personalized recommendations failed: {e}")
        
        return recommendations
    
    async def _get_collaborative_recommendations(self, user_profile: UserProfile, max_count: int) -> List[RecommendationItem]:
        """Get recommendations using collaborative filtering"""
        recommendations = []
        
        try:
            if not SCIPY_AVAILABLE or not self.config["enable_collaborative_filtering"]:
                return recommendations
            
            # Find similar users
            similar_users = await self._find_similar_users(user_profile.user_id)
            
            # Get content liked by similar users
            recommended_content = defaultdict(float)
            
            for similar_user_id, similarity in similar_users[:10]:  # Top 10 similar users
                similar_profile = self.user_profiles.get(similar_user_id)
                if similar_profile:
                    for content_id in similar_profile.liked_content:
                        if content_id not in user_profile.viewing_history:
                            recommended_content[content_id] += similarity
            
            # Sort by collaborative score
            sorted_content = sorted(recommended_content.items(), key=lambda x: x[1], reverse=True)
            
            for content_id, score in sorted_content[:max_count]:
                recommendations.append(RecommendationItem(
                    content_path=f"/path/to/{content_id}",
                    content_id=content_id,
                    title=f"Content {content_id}",
                    confidence=min(1.0, score),
                    relevance_score=score,
                    recommendation_type=RecommendationType.COLLABORATIVE,
                    source=RecommendationSource.COLLABORATIVE_FILTERING,
                    reasons=["Users with similar taste also liked this"]
                ))
        
        except Exception as e:
            logger.error(f"❌ Collaborative filtering recommendations failed: {e}")
        
        return recommendations
    
    async def _get_trending_recommendations(self, max_count: int) -> List[RecommendationItem]:
        """Get trending content recommendations"""
        recommendations = []
        
        try:
            # Calculate trending scores (simplified - would use more sophisticated algorithms)
            trending_scores = {}
            current_time = time.time()
            
            for content_id, features in self.content_features.items():
                # Simple trending calculation based on popularity and recency
                age_hours = (current_time - features.metadata_features.get("created_time", current_time)) / 3600
                
                if age_hours <= 24:  # Recent content only
                    trending_score = features.popularity_score / (1 + age_hours * 0.1)
                    trending_scores[content_id] = trending_score
            
            # Sort by trending score
            sorted_content = sorted(trending_scores.items(), key=lambda x: x[1], reverse=True)
            
            for content_id, score in sorted_content[:max_count]:
                recommendations.append(RecommendationItem(
                    content_path=f"/path/to/{content_id}",
                    content_id=content_id,
                    title=f"Content {content_id}",
                    confidence=min(1.0, score),
                    relevance_score=score,
                    recommendation_type=RecommendationType.TRENDING,
                    source=RecommendationSource.TEMPORAL_PATTERNS,
                    reasons=["Trending now"]
                ))
        
        except Exception as e:
            logger.error(f"❌ Trending recommendations failed: {e}")
        
        return recommendations
    
    async def _get_contextual_recommendations(self, user_profile: UserProfile, context: Dict[str, Any], max_count: int) -> List[RecommendationItem]:
        """Get contextual recommendations based on current context"""
        recommendations = []
        
        try:
            context_scores = {}
            
            for content_id, features in self.content_features.items():
                if content_id in user_profile.viewing_history:
                    continue
                
                score = 0.0
                
                # Time-based context
                if "time_of_day" in context:
                    time_pref = user_profile.interaction_patterns.get("time_preferences", {})
                    if context["time_of_day"] in time_pref:
                        score += 0.2
                
                # Location-based context
                if "location" in context:
                    location_tags = features.metadata_features.get("location_tags", [])
                    if context["location"] in location_tags:
                        score += 0.3
                
                # Device context
                if "device_type" in context:
                    device_pref = user_profile.interaction_patterns.get("device_preferences", {})
                    if context["device_type"] in device_pref:
                        score += 0.1
                
                # Mood context
                if "mood" in context:
                    mood_tags = features.metadata_features.get("mood_tags", [])
                    if context["mood"] in mood_tags:
                        score += 0.4
                
                context_scores[content_id] = score
            
            # Sort by contextual relevance
            sorted_content = sorted(context_scores.items(), key=lambda x: x[1], reverse=True)
            
            for content_id, score in sorted_content[:max_count]:
                if score > 0.1:  # Minimum contextual relevance
                    recommendations.append(RecommendationItem(
                        content_path=f"/path/to/{content_id}",
                        content_id=content_id,
                        title=f"Content {content_id}",
                        confidence=min(1.0, score),
                        relevance_score=score,
                        recommendation_type=RecommendationType.CONTEXTUAL,
                        source=RecommendationSource.TEMPORAL_PATTERNS,
                        reasons=[f"Perfect for your current context"]
                    ))
        
        except Exception as e:
            logger.error(f"❌ Contextual recommendations failed: {e}")
        
        return recommendations
    
    async def _merge_and_rank_recommendations(self, recommendations: List[RecommendationItem], user_profile: UserProfile, max_count: int) -> List[RecommendationItem]:
        """Merge recommendations from different sources and rank them"""
        # Remove duplicates
        unique_recs = {}
        for rec in recommendations:
            if rec.content_id not in unique_recs:
                unique_recs[rec.content_id] = rec
            else:
                # Combine confidence scores
                existing = unique_recs[rec.content_id]
                combined_confidence = (existing.confidence + rec.confidence) / 2
                existing.confidence = combined_confidence
                existing.reasons.extend(rec.reasons)
        
        # Calculate final ranking score
        for rec in unique_recs.values():
            final_score = (
                rec.relevance_score * 0.6 +
                rec.confidence * 0.3 +
                self._get_personalization_boost(rec, user_profile) * 0.1
            )
            rec.relevance_score = final_score
        
        # Sort by final score
        ranked_recs = sorted(unique_recs.values(), key=lambda x: x.relevance_score, reverse=True)
        
        return ranked_recs[:max_count]
    
    def _get_personalization_boost(self, recommendation: RecommendationItem, user_profile: UserProfile) -> float:
        """Calculate personalization boost for a recommendation"""
        boost = 0.0
        
        # Tag preference boost
        for tag in recommendation.tags:
            if tag in user_profile.favorite_tags:
                boost += 0.1
        
        # Source preference boost (if user historically prefers certain sources)
        source_prefs = user_profile.interaction_patterns.get("source_preferences", {})
        if recommendation.source.value in source_prefs:
            boost += source_prefs[recommendation.source.value] * 0.2
        
        return min(1.0, boost)
    
    async def _get_user_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(user_id=user_id)
        
        return self.user_profiles[user_id]
    
    async def _extract_content_features(self, content_id: str):
        """Extract features for content"""
        try:
            # Get AI analysis results
            ai_analyzer = await get_ai_content_analyzer()
            analysis_results = await ai_analyzer.analyze_content(
                content_path=f"/path/to/{content_id}",  # Would be resolved from database
                content_type=ai_analyzer.ContentType.IMAGE
            )
            
            # Get tags
            tagging_service = await get_auto_tagging_service()
            tagging_result = await tagging_service.generate_tags(f"/path/to/{content_id}")
            
            # Create content features
            features = ContentFeatures(content_id=content_id)
            
            # Extract visual features from AI analysis
            for result in analysis_results:
                if result.analysis_type.value == "quality_assessment":
                    features.quality_score = result.confidence
                # Add more feature extraction logic
            
            # Extract tag features
            features.metadata_features["tags"] = [tag.name for tag in tagging_result.tags]
            
            # Calculate popularity and freshness (mock values)
            features.popularity_score = 0.5  # Would be calculated from actual usage data
            features.freshness_score = 0.8   # Would be based on content age
            
            self.content_features[content_id] = features
            
        except Exception as e:
            logger.error(f"❌ Feature extraction failed for {content_id}: {e}")
    
    async def _calculate_content_similarity(self, features1: ContentFeatures, features2: ContentFeatures) -> float:
        """Calculate similarity between two content items"""
        similarity = 0.0
        
        try:
            # Tag similarity (Jaccard coefficient)
            tags1 = set(features1.metadata_features.get("tags", []))
            tags2 = set(features2.metadata_features.get("tags", []))
            
            if tags1 or tags2:
                intersection = len(tags1.intersection(tags2))
                union = len(tags1.union(tags2))
                tag_similarity = intersection / union if union > 0 else 0
                similarity += tag_similarity * 0.4
            
            # Quality similarity
            quality_diff = abs(features1.quality_score - features2.quality_score)
            quality_similarity = 1.0 - quality_diff
            similarity += quality_similarity * 0.2
            
            # Visual similarity (if available)
            if features1.visual_features and features2.visual_features and SCIPY_AVAILABLE:
                try:
                    visual_sim = 1.0 - cosine(features1.visual_features, features2.visual_features)
                    similarity += visual_sim * 0.4
                except:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Similarity calculation failed: {e}")
        
        return similarity
    
    async def _find_similar_users(self, user_id: str) -> List[Tuple[str, float]]:
        """Find users similar to the given user"""
        similar_users = []
        
        try:
            user_profile = self.user_profiles.get(user_id)
            if not user_profile:
                return similar_users
            
            user_liked = set(user_profile.liked_content)
            
            for other_user_id, other_profile in self.user_profiles.items():
                if other_user_id == user_id:
                    continue
                
                other_liked = set(other_profile.liked_content)
                
                # Calculate Jaccard similarity
                if user_liked or other_liked:
                    intersection = len(user_liked.intersection(other_liked))
                    union = len(user_liked.union(other_liked))
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity > 0.1:  # Minimum similarity threshold
                        similar_users.append((other_user_id, similarity))
            
            # Sort by similarity
            similar_users.sort(key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Similar user finding failed: {e}")
        
        return similar_users
    
    def _update_recommendation_stats(self, result: RecommendationResult, algorithms_used: List[str]):
        """Update recommendation statistics"""
        self.recommendation_stats["total_requests"] += 1
        self.recommendation_stats["successful_recommendations"] += 1
        
        # Update average processing time
        current_avg = self.recommendation_stats["average_processing_time"]
        total = self.recommendation_stats["total_requests"]
        new_avg = ((current_avg * (total - 1)) + result.processing_time) / total
        self.recommendation_stats["average_processing_time"] = new_avg
        
        # Update algorithm usage stats
        for algorithm in algorithms_used:
            self.recommendation_stats["algorithm_usage"][algorithm] += 1
    
    async def update_user_interaction(self, user_id: str, content_id: str, interaction_type: str, context: Dict[str, Any] = None):
        """Update user profile based on interaction"""
        try:
            user_profile = await self._get_user_profile(user_id)
            
            if interaction_type == "view":
                if content_id not in user_profile.viewing_history:
                    user_profile.viewing_history.append(content_id)
                    # Keep only recent history
                    if len(user_profile.viewing_history) > 1000:
                        user_profile.viewing_history = user_profile.viewing_history[-1000:]
            
            elif interaction_type == "like":
                if content_id not in user_profile.liked_content:
                    user_profile.liked_content.append(content_id)
                
                # Update tag preferences
                if content_id in self.content_features:
                    content_tags = self.content_features[content_id].metadata_features.get("tags", [])
                    for tag in content_tags:
                        user_profile.preferences[tag] = user_profile.preferences.get(tag, 0) + 0.1
            
            elif interaction_type == "dislike":
                if content_id not in user_profile.disliked_content:
                    user_profile.disliked_content.append(content_id)
                
                # Decrease tag preferences
                if content_id in self.content_features:
                    content_tags = self.content_features[content_id].metadata_features.get("tags", [])
                    for tag in content_tags:
                        user_profile.preferences[tag] = user_profile.preferences.get(tag, 0) - 0.1
            
            # Update interaction matrix for collaborative filtering
            self.interaction_matrix[user_id][content_id] = 1.0 if interaction_type in ["like", "view"] else -1.0
            
            user_profile.last_updated = time.time()
            
        except Exception as e:
            logger.error(f"❌ User interaction update failed: {e}")
    
    async def get_recommendation_statistics(self) -> Dict[str, Any]:
        """Get recommendation engine performance statistics"""
        return {
            "recommendation_stats": self.recommendation_stats.copy(),
            "user_profiles": len(self.user_profiles),
            "content_features": len(self.content_features),
            "config": self.config.copy(),
            "model_info": {
                "tfidf_enabled": self.tfidf_vectorizer is not None,
                "svd_enabled": self.svd_model is not None,
                "collaborative_filtering_enabled": self.config["enable_collaborative_filtering"],
                "content_based_enabled": self.config["enable_content_based"]
            }
        }


# Global recommendation engine instance
_recommendation_engine: Optional[SmartRecommendationEngine] = None

async def get_smart_recommendation_engine(config: Optional[Dict[str, Any]] = None) -> SmartRecommendationEngine:
    """Get or create global recommendation engine instance"""
    global _recommendation_engine
    
    if _recommendation_engine is None:
        _recommendation_engine = SmartRecommendationEngine(config)
        await _recommendation_engine.initialize_models()
    
    return _recommendation_engine


# Convenience functions
async def get_user_recommendations(user_id: str, max_count: int = 10, content_id: str = None) -> RecommendationResult:
    """Get recommendations for a user"""
    engine = await get_smart_recommendation_engine()
    request = RecommendationRequest(
        user_id=user_id,
        content_id=content_id,
        max_recommendations=max_count
    )
    return await engine.get_recommendations(request)


async def update_user_feedback(user_id: str, content_id: str, interaction_type: str):
    """Update user feedback for recommendations"""
    engine = await get_smart_recommendation_engine()
    await engine.update_user_interaction(user_id, content_id, interaction_type)