"""
Optimization API endpoints for MVidarr
"""

from flask import Blueprint, jsonify, request

from src.services.search_optimization_service import search_optimization_service
from src.services.thumbnail_optimization_service import thumbnail_optimization_service
from src.utils.logger import get_logger

optimization_bp = Blueprint("optimization", __name__, url_prefix="/optimization")
logger = get_logger("mvidarr.api.optimization")


@optimization_bp.route("/search/performance", methods=["GET"])
def get_search_performance():
    """Get search performance statistics"""
    try:
        stats = search_optimization_service.get_performance_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Failed to get search performance stats: {e}")
        return jsonify({"error": str(e)}), 500


@optimization_bp.route("/search/cache/clear", methods=["POST"])
def clear_search_cache():
    """Clear search cache"""
    try:
        search_optimization_service.cache.clear()
        return jsonify({"message": "Search cache cleared successfully"}), 200
    except Exception as e:
        logger.error(f"Failed to clear search cache: {e}")
        return jsonify({"error": str(e)}), 500


@optimization_bp.route("/search/cache/cleanup", methods=["POST"])
def cleanup_search_cache():
    """Clean up expired cache entries"""
    try:
        search_optimization_service.cleanup_cache()
        return jsonify({"message": "Cache cleanup completed"}), 200
    except Exception as e:
        logger.error(f"Failed to cleanup cache: {e}")
        return jsonify({"error": str(e)}), 500


@optimization_bp.route("/thumbnails/analyze", methods=["GET"])
def analyze_thumbnail_storage():
    """Analyze thumbnail storage usage"""
    try:
        analysis = thumbnail_optimization_service.analyze_storage_usage()
        return jsonify(analysis), 200
    except Exception as e:
        logger.error(f"Failed to analyze thumbnail storage: {e}")
        return jsonify({"error": str(e)}), 500


@optimization_bp.route("/thumbnails/recommendations", methods=["GET"])
def get_optimization_recommendations():
    """Get optimization recommendations"""
    try:
        recommendations = (
            thumbnail_optimization_service.get_optimization_recommendations()
        )
        return jsonify({"recommendations": recommendations}), 200
    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {e}")
        return jsonify({"error": str(e)}), 500


@optimization_bp.route("/thumbnails/optimize", methods=["POST"])
def optimize_thumbnails():
    """Optimize existing thumbnails by converting to WebP"""
    try:
        data = request.get_json() or {}
        dry_run = data.get("dry_run", False)

        results = thumbnail_optimization_service.optimize_existing_thumbnails(
            dry_run=dry_run
        )

        message = (
            f"Thumbnail optimization {'analysis' if dry_run else 'completed'}: "
            f"{results['analyzed']} analyzed, {results['converted']} converted, "
            f"{results['space_saved']} bytes saved"
        )

        return jsonify({"message": message, "results": results}), 200
    except Exception as e:
        logger.error(f"Failed to optimize thumbnails: {e}")
        return jsonify({"error": str(e)}), 500


@optimization_bp.route("/thumbnails/cleanup-duplicates", methods=["POST"])
def cleanup_duplicate_thumbnails():
    """Find and remove duplicate thumbnails"""
    try:
        results = thumbnail_optimization_service.cleanup_duplicate_thumbnails()

        message = (
            f"Duplicate cleanup completed: {results['duplicates_found']} duplicates removed, "
            f"{results['space_saved']} bytes saved"
        )

        return jsonify({"message": message, "results": results}), 200
    except Exception as e:
        logger.error(f"Failed to cleanup duplicate thumbnails: {e}")
        return jsonify({"error": str(e)}), 500


@optimization_bp.route("/database/indexes", methods=["POST"])
def optimize_database_indexes():
    """Optimize database indexes for better performance"""
    try:
        result = search_optimization_service.optimize_database_indexes()

        if result:
            return jsonify({"message": "Database indexes optimized successfully"}), 200
        else:
            return jsonify({"error": "Failed to optimize database indexes"}), 500
    except Exception as e:
        logger.error(f"Failed to optimize database indexes: {e}")
        return jsonify({"error": str(e)}), 500


@optimization_bp.route("/status", methods=["GET"])
def get_optimization_status():
    """Get overall optimization status"""
    try:
        # Get search performance stats
        search_stats = search_optimization_service.get_performance_stats()

        # Get thumbnail analysis
        thumbnail_analysis = thumbnail_optimization_service.analyze_storage_usage()

        # Get recommendations
        recommendations = (
            thumbnail_optimization_service.get_optimization_recommendations()
        )

        status = {
            "search_optimization": {
                "enabled": True,
                "cache_hit_rate": search_stats.get("hit_rate", 0),
                "total_requests": search_stats.get("total_requests", 0),
                "cache_entries": search_stats.get("cache_stats", {}).get(
                    "active_entries", 0
                ),
            },
            "thumbnail_optimization": {
                "total_files": thumbnail_analysis.get("total_files", 0),
                "total_size": thumbnail_analysis.get("total_size", 0),
                "webp_percentage": (
                    thumbnail_analysis.get("by_format", {})
                    .get(".webp", {})
                    .get("files", 0)
                    / max(thumbnail_analysis.get("total_files", 1), 1)
                    * 100
                ),
                "optimization_potential": thumbnail_analysis.get(
                    "optimization_potential", 0
                ),
            },
            "recommendations": recommendations,
            "system_health": (
                "optimal" if len(recommendations) == 0 else "needs_attention"
            ),
        }

        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Failed to get optimization status: {e}")
        return jsonify({"error": str(e)}), 500
