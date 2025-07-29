"""
YouTube API endpoints
"""

from flask import Blueprint, jsonify, request

from src.services.youtube_service import youtube_service
from src.utils.logger import get_logger

youtube_bp = Blueprint("youtube", __name__, url_prefix="/youtube")
logger = get_logger("mvidarr.api.youtube")


@youtube_bp.route("/search", methods=["POST"])
def search_videos():
    """Search for videos on YouTube"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        query = data.get("q", "").strip()
        max_results = data.get("maxResults", 25)
        video_category_id = data.get("videoCategoryId")

        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400

        # Search YouTube
        result = youtube_service.search_videos(query, max_results)

        if not result.get("success", True):
            return jsonify({"error": result.get("error", "Search failed")}), 500

        return jsonify(
            {
                "success": True,
                "items": result.get("items", []),
                "totalResults": result.get("pageInfo", {}).get("totalResults", 0),
            }
        )

    except Exception as e:
        logger.error(f"Error searching YouTube: {e}")
        return jsonify({"error": str(e)}), 500


@youtube_bp.route("/search-artist", methods=["POST"])
def search_artist_videos():
    """Search for videos by a specific artist on YouTube"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        artist_name = data.get("artist", "").strip()
        max_results = data.get("maxResults", 25)

        if not artist_name:
            return jsonify({"error": "Artist name is required"}), 400

        # Search for artist videos
        result = youtube_service.search_artist_videos(artist_name, max_results)

        if not result.get("success", True):
            return jsonify({"error": result.get("error", "Search failed")}), 500

        return jsonify(
            {
                "success": True,
                "items": result.get("items", []),
                "totalResults": result.get("pageInfo", {}).get("totalResults", 0),
            }
        )

    except Exception as e:
        logger.error(f"Error searching YouTube artist videos: {e}")
        return jsonify({"error": str(e)}), 500


@youtube_bp.route("/video/<video_id>", methods=["GET"])
def get_video_details(video_id):
    """Get detailed video information from YouTube"""
    try:
        result = youtube_service.get_video_details(video_id)

        if not result.get("success", True):
            return jsonify({"error": result.get("error", "Video not found")}), 404

        return jsonify({"success": True, "video": result.get("video")})

    except Exception as e:
        logger.error(f"Error getting YouTube video details: {e}")
        return jsonify({"error": str(e)}), 500


@youtube_bp.route("/test-connection", methods=["GET"])
def test_connection():
    """Test YouTube API connection"""
    try:
        result = youtube_service.test_connection()

        return jsonify(
            {
                "success": result.get("success", False),
                "message": result.get("message", "Connection test failed"),
                "quota_exceeded": result.get("quota_exceeded", False),
            }
        )

    except Exception as e:
        logger.error(f"Error testing YouTube connection: {e}")
        return jsonify({"error": str(e)}), 500
