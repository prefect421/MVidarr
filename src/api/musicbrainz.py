"""
MusicBrainz API endpoints for frontend integration
"""

from flask import Blueprint, jsonify, request

from src.middleware.simple_auth_middleware import auth_required
from src.services.musicbrainz_service import musicbrainz_service
from src.utils.logger import get_logger

musicbrainz_bp = Blueprint("musicbrainz", __name__, url_prefix="/musicbrainz")
logger = get_logger("mvidarr.api.musicbrainz")


@musicbrainz_bp.route("/search-artist", methods=["POST"])
@auth_required
def search_artist():
    """Search for artists in MusicBrainz database"""
    try:
        if not request.is_json:
            return jsonify({"error": "JSON payload required"}), 400

        data = request.get_json()
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        # Search MusicBrainz for artists
        results = musicbrainz_service.search_artist(query)

        return (
            jsonify(
                {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to search MusicBrainz artists: {e}")
        return jsonify({"error": str(e)}), 500


@musicbrainz_bp.route("/artist/<mbid>", methods=["GET"])
@auth_required
def get_artist_details(mbid: str):
    """Get detailed artist information by MusicBrainz ID"""
    try:
        if not mbid:
            return jsonify({"error": "MusicBrainz ID is required"}), 400

        # Get artist details from MusicBrainz
        artist_data = musicbrainz_service.get_artist_by_mbid(mbid)

        if not artist_data:
            return jsonify({"error": "Artist not found in MusicBrainz"}), 404

        return jsonify({"success": True, "mbid": mbid, "artist": artist_data}), 200

    except Exception as e:
        logger.error(f"Failed to get MusicBrainz artist details for {mbid}: {e}")
        return jsonify({"error": str(e)}), 500


@musicbrainz_bp.route("/test", methods=["GET"])
@auth_required
def test_connection():
    """Test MusicBrainz API connectivity"""
    try:
        is_connected = musicbrainz_service.test_connection()

        return jsonify(
            {
                "success": is_connected,
                "service": "MusicBrainz",
                "status": "connected" if is_connected else "disconnected",
                "enabled": musicbrainz_service.enabled,
            }
        ), (200 if is_connected else 503)

    except Exception as e:
        logger.error(f"MusicBrainz connection test failed: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "service": "MusicBrainz",
                    "status": "error",
                    "error": str(e),
                }
            ),
            500,
        )
