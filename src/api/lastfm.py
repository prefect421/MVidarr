"""
Last.fm API endpoints for listening history and artist discovery
"""

from flask import Blueprint, jsonify, request, session

from src.services.lastfm_service import lastfm_service
from src.utils.logger import get_logger

lastfm_bp = Blueprint("lastfm", __name__, url_prefix="/lastfm")
logger = get_logger("mvidarr.api.lastfm")


@lastfm_bp.route("/auth/url", methods=["GET"])
def get_auth_url():
    """Get Last.fm authentication URL"""
    try:
        if not lastfm_service.api_key:
            return (
                jsonify(
                    {
                        "error": "Last.fm integration not configured. Please set LASTFM_API_KEY and LASTFM_API_SECRET"
                    }
                ),
                400,
            )

        auth_url = lastfm_service.get_auth_url()
        return jsonify({"auth_url": auth_url, "configured": True}), 200

    except Exception as e:
        logger.error(f"Failed to generate Last.fm auth URL: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/callback", methods=["GET"])
def callback():
    """Handle Last.fm authentication callback"""
    try:
        token = request.args.get("token")

        if not token:
            return jsonify({"error": "No authentication token received"}), 400

        # Get session key
        session_data = lastfm_service.get_session_key(token)

        # Store session data
        session["lastfm_session_key"] = session_data.get("session_key")
        session["lastfm_username"] = session_data.get("username")
        session["lastfm_subscriber"] = session_data.get("subscriber")

        logger.info(
            f"Last.fm authentication successful for user: {session_data.get('username')}"
        )
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Successfully authenticated with Last.fm",
                    "username": session_data.get("username"),
                    "subscriber": session_data.get("subscriber"),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Last.fm callback error: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/profile", methods=["GET"])
def get_profile():
    """Get Last.fm user profile"""
    try:
        username = request.args.get("username") or session.get("lastfm_username")

        if not username:
            return jsonify({"error": "No username provided or not authenticated"}), 400

        profile = lastfm_service.get_user_info(username)

        return (
            jsonify(
                {
                    "profile": profile,
                    "authenticated": session.get("lastfm_session_key") is not None,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get Last.fm profile: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/top/artists", methods=["GET"])
def get_top_artists():
    """Get user's top artists from Last.fm"""
    try:
        username = request.args.get("username") or session.get("lastfm_username")
        period = request.args.get("period", "overall")
        limit = min(int(request.args.get("limit", 50)), 200)
        page = int(request.args.get("page", 1))

        if not username:
            return jsonify({"error": "No username provided or not authenticated"}), 400

        # Validate period
        valid_periods = ["overall", "7day", "1month", "3month", "6month", "12month"]
        if period not in valid_periods:
            period = "overall"

        top_artists = lastfm_service.get_user_top_artists(username, period, limit, page)

        return (
            jsonify(
                {
                    "artists": top_artists["artists"],
                    "total": top_artists["total"],
                    "page": top_artists["page"],
                    "per_page": top_artists["per_page"],
                    "total_pages": top_artists["total_pages"],
                    "period": top_artists["period"],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get top artists: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/top/tracks", methods=["GET"])
def get_top_tracks():
    """Get user's top tracks from Last.fm"""
    try:
        username = request.args.get("username") or session.get("lastfm_username")
        period = request.args.get("period", "overall")
        limit = min(int(request.args.get("limit", 50)), 200)
        page = int(request.args.get("page", 1))

        if not username:
            return jsonify({"error": "No username provided or not authenticated"}), 400

        # Validate period
        valid_periods = ["overall", "7day", "1month", "3month", "6month", "12month"]
        if period not in valid_periods:
            period = "overall"

        top_tracks = lastfm_service.get_user_top_tracks(username, period, limit, page)

        return (
            jsonify(
                {
                    "tracks": top_tracks["tracks"],
                    "total": top_tracks["total"],
                    "page": top_tracks["page"],
                    "per_page": top_tracks["per_page"],
                    "total_pages": top_tracks["total_pages"],
                    "period": top_tracks["period"],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get top tracks: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/recent", methods=["GET"])
def get_recent_tracks():
    """Get user's recent tracks from Last.fm"""
    try:
        username = request.args.get("username") or session.get("lastfm_username")
        limit = min(int(request.args.get("limit", 50)), 200)
        page = int(request.args.get("page", 1))
        from_timestamp = request.args.get("from")
        to_timestamp = request.args.get("to")

        if not username:
            return jsonify({"error": "No username provided or not authenticated"}), 400

        # Convert timestamps if provided
        from_ts = int(from_timestamp) if from_timestamp else None
        to_ts = int(to_timestamp) if to_timestamp else None

        recent_tracks = lastfm_service.get_recent_tracks(
            username, limit, page, from_ts, to_ts
        )

        return (
            jsonify(
                {
                    "tracks": recent_tracks["tracks"],
                    "total": recent_tracks["total"],
                    "page": recent_tracks["page"],
                    "per_page": recent_tracks["per_page"],
                    "total_pages": recent_tracks["total_pages"],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get recent tracks: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/loved", methods=["GET"])
def get_loved_tracks():
    """Get user's loved tracks from Last.fm"""
    try:
        username = request.args.get("username") or session.get("lastfm_username")
        limit = min(int(request.args.get("limit", 50)), 200)
        page = int(request.args.get("page", 1))

        if not username:
            return jsonify({"error": "No username provided or not authenticated"}), 400

        loved_tracks = lastfm_service.get_loved_tracks(username, limit, page)

        return (
            jsonify(
                {
                    "tracks": loved_tracks["tracks"],
                    "total": loved_tracks["total"],
                    "page": loved_tracks["page"],
                    "per_page": loved_tracks["per_page"],
                    "total_pages": loved_tracks["total_pages"],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get loved tracks: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/artist/<artist_name>", methods=["GET"])
def get_artist_info(artist_name):
    """Get artist information from Last.fm"""
    try:
        username = request.args.get("username") or session.get("lastfm_username")

        artist_info = lastfm_service.get_artist_info(artist_name, username)

        return jsonify({"artist": artist_info}), 200

    except Exception as e:
        logger.error(f"Failed to get artist info: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/import/top-artists", methods=["POST"])
def import_top_artists():
    """Import user's top artists to MVidarr"""
    try:
        data = request.get_json() or {}

        username = data.get("username") or session.get("lastfm_username")
        if not username:
            return jsonify({"error": "No username provided or not authenticated"}), 400

        period = data.get("period", "overall")
        limit = min(int(data.get("limit", 50)), 200)
        min_playcount = int(data.get("min_playcount", 1))

        # Validate period
        valid_periods = ["overall", "7day", "1month", "3month", "6month", "12month"]
        if period not in valid_periods:
            period = "overall"

        logger.info(
            f"Starting import of top artists for user: {username}, period: {period}"
        )

        results = lastfm_service.import_top_artists(
            username, period, limit, min_playcount
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Successfully imported {results['imported_artists']} artists from Last.fm",
                    "results": results,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to import top artists: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/import/loved-tracks", methods=["POST"])
def import_loved_tracks():
    """Import user's loved tracks and find music videos"""
    try:
        data = request.get_json() or {}

        username = data.get("username") or session.get("lastfm_username")
        if not username:
            return jsonify({"error": "No username provided or not authenticated"}), 400

        limit = min(int(data.get("limit", 200)), 1000)

        logger.info(f"Starting import of loved tracks for user: {username}")

        results = lastfm_service.sync_loved_tracks(username, limit)

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Successfully processed {results['artists_processed']} artists from {results['total_tracks']} loved tracks",
                    "results": results,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to import loved tracks: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/stats", methods=["GET"])
def get_listening_stats():
    """Get detailed listening statistics"""
    try:
        username = request.args.get("username") or session.get("lastfm_username")
        days = min(int(request.args.get("days", 30)), 365)

        if not username:
            return jsonify({"error": "No username provided or not authenticated"}), 400

        stats = lastfm_service.get_listening_stats(username, days)

        return jsonify({"stats": stats, "username": username}), 200

    except Exception as e:
        logger.error(f"Failed to get listening stats: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/disconnect", methods=["POST"])
def disconnect():
    """Disconnect from Last.fm"""
    try:
        # Clear session data
        session.pop("lastfm_session_key", None)
        session.pop("lastfm_username", None)
        session.pop("lastfm_subscriber", None)

        # Clear service data
        lastfm_service.session_key = None
        lastfm_service.username = None

        logger.info("Last.fm disconnected successfully")
        return (
            jsonify(
                {"success": True, "message": "Successfully disconnected from Last.fm"}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to disconnect from Last.fm: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/status", methods=["GET"])
def get_status():
    """Get Last.fm integration status"""
    try:
        # Check if session key is available
        has_session = (
            session.get("lastfm_session_key") is not None
            or lastfm_service.session_key is not None
        )

        # Check if API credentials are configured
        configured = (
            lastfm_service.api_key is not None and lastfm_service.api_secret is not None
        )

        username = session.get("lastfm_username") or lastfm_service.username

        # Get user profile if authenticated
        profile = None
        if has_session and username:
            try:
                profile = lastfm_service.get_user_info(username)
            except Exception as e:
                logger.warning(f"Failed to get profile for status check: {e}")

        return (
            jsonify(
                {
                    "configured": configured,
                    "authenticated": has_session,
                    "username": username,
                    "subscriber": session.get("lastfm_subscriber", False),
                    "profile": profile,
                    "api_key": lastfm_service.api_key[:8] + "..."
                    if lastfm_service.api_key
                    else None,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get Last.fm status: {e}")
        return jsonify({"error": str(e)}), 500


@lastfm_bp.route("/test", methods=["POST"])
def test_lastfm_integration():
    """Test Last.fm API connection"""
    try:
        # Check if API credentials are configured
        if not lastfm_service.api_key or not lastfm_service.api_secret:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Last.fm API credentials not configured. Please set lastfm_api_key and lastfm_api_secret in settings.",
                    }
                ),
                400,
            )

        # Test API connection by searching for a test artist
        try:
            result = lastfm_service.call_api(
                "artist.search", {"artist": "test", "limit": 1}
            )

            if result and "results" in result:
                return (
                    jsonify(
                        {
                            "status": "success",
                            "message": "Last.fm API connection successful",
                            "test_results": len(
                                result["results"]
                                .get("artistmatches", {})
                                .get("artist", [])
                            ),
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Last.fm API returned unexpected response",
                        }
                    ),
                    500,
                )

        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Last.fm API connection failed: {str(e)}",
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Last.fm integration test failed: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Last.fm integration test failed: {str(e)}",
                }
            ),
            500,
        )


@lastfm_bp.route("/import-artists", methods=["POST"])
def import_artists():
    """Import top artists from Last.fm"""
    try:
        data = request.get_json() or {}

        # Get username from settings or session
        from src.services.settings_service import SettingsService

        username = SettingsService.get("lastfm_username", "")

        if not username:
            username = session.get("lastfm_username")

        if not username:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Last.fm username not configured. Please set lastfm_username in settings.",
                    }
                ),
                400,
            )

        # Import top artists
        period = data.get("period", "overall")
        limit = min(int(data.get("limit", 50)), 200)
        min_playcount = int(data.get("min_playcount", 1))

        results = lastfm_service.import_top_artists(
            username, period, limit, min_playcount
        )

        return (
            jsonify(
                {
                    "success": True,
                    "imported_count": results.get("imported_artists", 0),
                    "total_artists": results.get("total_artists", 0),
                    "message": f'Successfully imported {results.get("imported_artists", 0)} artists from Last.fm',
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to import artists: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@lastfm_bp.route("/sync-history", methods=["POST"])
def sync_history():
    """Sync listening history from Last.fm"""
    try:
        data = request.get_json() or {}

        # Get username from settings or session
        from src.services.settings_service import SettingsService

        username = SettingsService.get("lastfm_username", "")

        if not username:
            username = session.get("lastfm_username")

        if not username:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Last.fm username not configured. Please set lastfm_username in settings.",
                    }
                ),
                400,
            )

        # Sync listening history
        limit = min(int(data.get("limit", 200)), 1000)

        results = lastfm_service.sync_loved_tracks(username, limit)

        return (
            jsonify(
                {
                    "success": True,
                    "processed_count": results.get("total_tracks", 0),
                    "artists_processed": results.get("artists_processed", 0),
                    "message": f'Successfully processed {results.get("total_tracks", 0)} tracks from Last.fm history',
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to sync history: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
