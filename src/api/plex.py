"""
Plex API endpoints for library synchronization and metadata exchange
"""

from flask import Blueprint, jsonify, request

from src.services.plex_service import plex_service
from src.utils.logger import get_logger

plex_bp = Blueprint("plex", __name__, url_prefix="/plex")
logger = get_logger("mvidarr.api.plex")


@plex_bp.route("/status", methods=["GET"])
def get_status():
    """Get Plex integration status"""
    try:
        # Check if Plex is configured
        configured = plex_service.server_url and plex_service.server_token is not None

        status = {
            "configured": configured,
            "server_url": plex_service.server_url,
            "token": plex_service.server_token[:8] + "..."
            if plex_service.server_token
            else None,
            "connected": False,
            "server_info": None,
        }

        if configured:
            # Test connection
            connection_test = plex_service.test_connection()
            status["connected"] = connection_test["connected"]

            if connection_test["connected"]:
                status["server_info"] = {
                    "name": connection_test["server_name"],
                    "version": connection_test["version"],
                    "platform": connection_test["platform"],
                    "platform_version": connection_test["platform_version"],
                }
            else:
                status["error"] = connection_test.get("error")

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Failed to get Plex status: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/libraries", methods=["GET"])
def get_libraries():
    """Get all Plex libraries"""
    try:
        libraries = plex_service.get_libraries()

        return jsonify({"libraries": libraries, "count": len(libraries)}), 200

    except Exception as e:
        logger.error(f"Failed to get Plex libraries: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/music-library", methods=["GET"])
def get_music_library():
    """Get the music library from Plex"""
    try:
        music_library = plex_service.get_music_library()

        if music_library:
            return jsonify({"library": music_library, "found": True}), 200
        else:
            return (
                jsonify({"found": False, "message": "No music library found in Plex"}),
                404,
            )

    except Exception as e:
        logger.error(f"Failed to get music library: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/artists", methods=["GET"])
def get_artists():
    """Get artists from Plex music library"""
    try:
        library_key = request.args.get("library_key")
        limit = int(request.args.get("limit", 100))

        artists = plex_service.get_library_artists(library_key)

        # Apply limit
        if limit > 0:
            artists = artists[:limit]

        return jsonify({"artists": artists, "count": len(artists)}), 200

    except Exception as e:
        logger.error(f"Failed to get Plex artists: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/artists/<artist_key>/albums", methods=["GET"])
def get_artist_albums(artist_key):
    """Get albums for a specific artist"""
    try:
        albums = plex_service.get_artist_albums(artist_key)

        return jsonify({"albums": albums, "count": len(albums)}), 200

    except Exception as e:
        logger.error(f"Failed to get artist albums: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/albums/<album_key>/tracks", methods=["GET"])
def get_album_tracks(album_key):
    """Get tracks for a specific album"""
    try:
        tracks = plex_service.get_album_tracks(album_key)

        return jsonify({"tracks": tracks, "count": len(tracks)}), 200

    except Exception as e:
        logger.error(f"Failed to get album tracks: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/search", methods=["GET"])
def search_library():
    """Search Plex library"""
    try:
        query = request.args.get("query")
        library_key = request.args.get("library_key")

        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        results = plex_service.search_library(query, library_key)

        return jsonify({"results": results, "count": len(results), "query": query}), 200

    except Exception as e:
        logger.error(f"Failed to search Plex library: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/sync/from-plex", methods=["POST"])
def sync_from_plex():
    """Sync artists from Plex to MVidarr"""
    try:
        data = request.get_json() or {}
        limit = int(data.get("limit", 100))

        logger.info(f"Starting sync from Plex with limit: {limit}")

        results = plex_service.sync_artists_to_mvidarr(limit)

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Successfully synced {results['imported_artists']} artists from Plex",
                    "results": results,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to sync from Plex: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/sync/to-plex", methods=["POST"])
def sync_to_plex():
    """Sync MVidarr artists to Plex for matching"""
    try:
        logger.info("Starting sync to Plex for artist matching")

        results = plex_service.sync_mvidarr_to_plex()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Successfully matched {results['matched_artists']} artists with Plex",
                    "results": results,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to sync to Plex: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/artist/<artist_name>/stats", methods=["GET"])
def get_artist_stats(artist_name):
    """Get listening statistics for an artist"""
    try:
        stats = plex_service.get_artist_listening_stats(artist_name)

        return jsonify({"artist_name": artist_name, "stats": stats}), 200

    except Exception as e:
        logger.error(f"Failed to get artist stats: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/recently-played", methods=["GET"])
def get_recently_played():
    """Get recently played tracks from Plex"""
    try:
        limit = int(request.args.get("limit", 50))

        recently_played = plex_service.get_recently_played(limit)

        return jsonify({"tracks": recently_played, "count": len(recently_played)}), 200

    except Exception as e:
        logger.error(f"Failed to get recently played: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/library/stats", methods=["GET"])
def get_library_stats():
    """Get overall library statistics"""
    try:
        stats = plex_service.get_library_stats()

        return jsonify({"stats": stats}), 200

    except Exception as e:
        logger.error(f"Failed to get library stats: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/playlists", methods=["POST"])
def create_playlist():
    """Create a playlist in Plex"""
    try:
        data = request.get_json()

        if not data or "name" not in data or "track_keys" not in data:
            return jsonify({"error": "Name and track_keys are required"}), 400

        name = data["name"]
        track_keys = data["track_keys"]

        result = plex_service.create_playlist(name, track_keys)

        return jsonify(result), 200 if result["success"] else 400

    except Exception as e:
        logger.error(f"Failed to create playlist: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/test-connection", methods=["GET"])
def test_connection():
    """Test connection to Plex server"""
    try:
        result = plex_service.test_connection()

        return jsonify(result), 200 if result["connected"] else 400

    except Exception as e:
        logger.error(f"Failed to test Plex connection: {e}")
        return jsonify({"error": str(e)}), 500


@plex_bp.route("/test", methods=["POST"])
def test_plex_integration():
    """Test Plex integration for settings page"""
    try:
        # Check if Plex is configured
        if not plex_service.server_url or not plex_service.server_token:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Plex server not configured. Please set plex_server_url and plex_token in settings.",
                    }
                ),
                400,
            )

        # Test connection
        result = plex_service.test_connection()

        if result["connected"]:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Plex server connection successful",
                        "server_name": result.get("server_name"),
                        "version": result.get("version"),
                        "platform": result.get("platform"),
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f'Plex server connection failed: {result.get("error", "Unknown error")}',
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Plex integration test failed: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Plex integration test failed: {str(e)}",
                }
            ),
            500,
        )


@plex_bp.route("/sync-library", methods=["POST"])
def sync_library():
    """Sync Plex library for settings page"""
    try:
        data = request.get_json() or {}
        limit = int(data.get("limit", 100))

        # Sync artists from Plex
        results = plex_service.sync_artists_to_mvidarr(limit)

        return (
            jsonify(
                {
                    "success": True,
                    "processed_count": results.get("total_artists", 0),
                    "imported_count": results.get("imported_artists", 0),
                    "message": f'Successfully processed {results.get("total_artists", 0)} artists from Plex library',
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to sync library: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@plex_bp.route("/import-artists", methods=["POST"])
def import_artists():
    """Import artists from Plex for settings page"""
    try:
        data = request.get_json() or {}
        limit = int(data.get("limit", 100))

        # Import artists from Plex
        results = plex_service.sync_artists_to_mvidarr(limit)

        return (
            jsonify(
                {
                    "success": True,
                    "imported_count": results.get("imported_artists", 0),
                    "total_artists": results.get("total_artists", 0),
                    "message": f'Successfully imported {results.get("imported_artists", 0)} artists from Plex',
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to import artists: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
