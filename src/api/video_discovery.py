"""
Video discovery API endpoints
"""

from flask import Blueprint, jsonify, request

from src.services.video_discovery_service import video_discovery_service
from src.utils.logger import get_logger

video_discovery_bp = Blueprint("video_discovery", __name__, url_prefix="/discovery")
logger = get_logger("mvidarr.api.video_discovery")


@video_discovery_bp.route("/artist/<int:artist_id>", methods=["POST"])
def discover_for_artist(artist_id):
    """Discover new videos for a specific artist"""
    try:
        data = request.get_json() or {}
        limit = data.get("limit", 10)

        result = video_discovery_service.discover_videos_for_artist(artist_id, limit)

        status_code = 200 if result["success"] else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Artist discovery failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_discovery_bp.route("/all", methods=["POST"])
def discover_for_all_artists():
    """Discover new videos for all monitored artists"""
    try:
        data = request.get_json() or {}
        limit_per_artist = data.get("limit_per_artist", 5)

        result = video_discovery_service.discover_videos_for_all_artists(
            limit_per_artist
        )

        status_code = 200 if result["success"] else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Bulk discovery failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_discovery_bp.route("/stats", methods=["GET"])
def get_discovery_stats():
    """Get video discovery statistics"""
    try:
        stats = video_discovery_service.get_discovery_stats()

        return jsonify({"success": True, "stats": stats}), 200

    except Exception as e:
        logger.error(f"Failed to get discovery stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_discovery_bp.route("/test/<int:artist_id>", methods=["GET"])
def test_discovery_for_artist(artist_id):
    """Test video discovery for an artist (returns preview without storing)"""
    try:
        # This would be a dry-run version that doesn't store results
        result = video_discovery_service.discover_videos_for_artist(artist_id, limit=3)

        # Remove stored videos from response for preview
        if result.get("success"):
            result["preview"] = True
            result["note"] = "This is a preview - videos were not stored"

        status_code = 200 if result["success"] else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Discovery test failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
