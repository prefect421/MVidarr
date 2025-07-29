"""
IMVDb API endpoints
"""

from flask import Blueprint, jsonify, request

from src.services.imvdb_service import imvdb_service
from src.utils.logger import get_logger

imvdb_bp = Blueprint("imvdb", __name__, url_prefix="/imvdb")
logger = get_logger("mvidarr.api.imvdb")


@imvdb_bp.route("/search-artist", methods=["GET"])
def search_artist():
    """Search for artists in IMVDb"""
    try:
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400

        # Search for multiple artists
        artists = imvdb_service.search_artists(query, limit=10)

        return jsonify({"success": True, "results": artists, "count": len(artists)})

    except Exception as e:
        logger.error(f"Error searching IMVDb artists: {e}")
        return jsonify({"error": str(e)}), 500


@imvdb_bp.route("/search-videos", methods=["GET"])
def search_videos():
    """Search for videos in IMVDb"""
    try:
        query = request.args.get("q", "").strip()
        artist_id = request.args.get("artist_id")

        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400

        if artist_id:
            # Get videos for specific artist
            result = imvdb_service.search_artist_videos(query, limit=25)
            videos = result.get("videos", []) if result else []
        else:
            # General video search
            videos = imvdb_service.search_videos(query)

        return jsonify({"success": True, "results": videos, "count": len(videos)})

    except Exception as e:
        logger.error(f"Error searching IMVDb videos: {e}")
        return jsonify({"error": str(e)}), 500


@imvdb_bp.route("/artist/<int:artist_id>", methods=["GET"])
def get_artist_details(artist_id):
    """Get detailed artist information from IMVDb"""
    try:
        artist = imvdb_service.get_artist_by_id(artist_id)

        if not artist:
            return jsonify({"error": "Artist not found"}), 404

        return jsonify({"success": True, "artist": artist})

    except Exception as e:
        logger.error(f"Error getting IMVDb artist details: {e}")
        return jsonify({"error": str(e)}), 500


@imvdb_bp.route("/video/<int:video_id>", methods=["GET"])
def get_video_details(video_id):
    """Get detailed video information from IMVDb"""
    try:
        video = imvdb_service.get_video_by_id(video_id)

        if not video:
            return jsonify({"error": "Video not found"}), 404

        return jsonify({"success": True, "video": video})

    except Exception as e:
        logger.error(f"Error getting IMVDb video details: {e}")
        return jsonify({"error": str(e)}), 500
