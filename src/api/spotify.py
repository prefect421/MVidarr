"""
Spotify API endpoints for playlist import and artist synchronization
"""

import os

from flask import Blueprint, jsonify, redirect, request, session

from src.services.spotify_service import spotify_service
from src.utils.logger import get_logger

spotify_bp = Blueprint("spotify", __name__, url_prefix="/spotify")
logger = get_logger("mvidarr.api.spotify")


@spotify_bp.route("/auth/url", methods=["GET"])
def get_auth_url():
    """Get Spotify authorization URL"""
    try:
        if not spotify_service.client_id:
            return (
                jsonify(
                    {
                        "error": "Spotify integration not configured. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET"
                    }
                ),
                400,
            )

        auth_url = spotify_service.get_auth_url()
        return jsonify({"auth_url": auth_url, "configured": True}), 200

    except Exception as e:
        logger.error(f"Failed to generate Spotify auth URL: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/callback", methods=["GET"])
def callback():
    """Handle Spotify OAuth callback"""
    try:
        code = request.args.get("code")
        error = request.args.get("error")

        if error:
            logger.error(f"Spotify OAuth error: {error}")
            return redirect(f"/settings?spotify_error={error}")

        if not code:
            return jsonify({"error": "No authorization code received"}), 400

        # Exchange code for access token
        token_data = spotify_service.get_access_token(code)

        # Store tokens in session (in production, use database)
        session["spotify_access_token"] = token_data.get("access_token")
        session["spotify_refresh_token"] = token_data.get("refresh_token")
        session["spotify_token_expires"] = token_data.get("expires_in")

        logger.info("Spotify authentication successful")
        return redirect("/settings?spotify_success=true")

    except Exception as e:
        logger.error(f"Spotify callback error: {e}")
        return redirect(f"/settings?spotify_error={str(e)}")


@spotify_bp.route("/profile", methods=["GET"])
def get_profile():
    """Get current user's Spotify profile"""
    try:
        # Load tokens from session
        if "spotify_access_token" in session:
            spotify_service.access_token = session["spotify_access_token"]
            spotify_service.refresh_token = session.get("spotify_refresh_token")

        if not spotify_service.access_token:
            return jsonify({"error": "Not authenticated with Spotify"}), 401

        profile = spotify_service.get_user_profile()
        return jsonify({"profile": profile, "authenticated": True}), 200

    except Exception as e:
        logger.error(f"Failed to get Spotify profile: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/playlists", methods=["GET"])
def get_playlists():
    """Get user's Spotify playlists"""
    try:
        # Load tokens from session
        if "spotify_access_token" in session:
            spotify_service.access_token = session["spotify_access_token"]
            spotify_service.refresh_token = session.get("spotify_refresh_token")

        if not spotify_service.access_token:
            return jsonify({"error": "Not authenticated with Spotify"}), 401

        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        playlists = spotify_service.get_user_playlists(limit, offset)

        # Format playlist data
        formatted_playlists = []
        for playlist in playlists.get("items", []):
            formatted_playlists.append(
                {
                    "id": playlist.get("id"),
                    "name": playlist.get("name"),
                    "description": playlist.get("description"),
                    "tracks_total": playlist.get("tracks", {}).get("total", 0),
                    "images": playlist.get("images", []),
                    "owner": playlist.get("owner", {}).get("display_name"),
                    "public": playlist.get("public", False),
                    "collaborative": playlist.get("collaborative", False),
                    "external_urls": playlist.get("external_urls", {}),
                }
            )

        return (
            jsonify(
                {
                    "playlists": formatted_playlists,
                    "total": playlists.get("total", 0),
                    "limit": limit,
                    "offset": offset,
                    "next": playlists.get("next") is not None,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get Spotify playlists: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/playlists/<playlist_id>/tracks", methods=["GET"])
def get_playlist_tracks(playlist_id):
    """Get tracks from a specific playlist"""
    try:
        # Load tokens from session
        if "spotify_access_token" in session:
            spotify_service.access_token = session["spotify_access_token"]
            spotify_service.refresh_token = session.get("spotify_refresh_token")

        if not spotify_service.access_token:
            return jsonify({"error": "Not authenticated with Spotify"}), 401

        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        tracks_data = spotify_service.get_playlist_tracks(playlist_id, limit, offset)

        # Format track data
        formatted_tracks = []
        for track_item in tracks_data.get("items", []):
            track = track_item.get("track")
            if not track:
                continue

            formatted_tracks.append(
                {
                    "id": track.get("id"),
                    "name": track.get("name"),
                    "artists": [
                        {"name": a.get("name"), "id": a.get("id")}
                        for a in track.get("artists", [])
                    ],
                    "album": {
                        "name": track.get("album", {}).get("name"),
                        "images": track.get("album", {}).get("images", []),
                    },
                    "duration_ms": track.get("duration_ms"),
                    "popularity": track.get("popularity"),
                    "external_urls": track.get("external_urls", {}),
                }
            )

        return (
            jsonify(
                {
                    "tracks": formatted_tracks,
                    "total": tracks_data.get("total", 0),
                    "limit": limit,
                    "offset": offset,
                    "next": tracks_data.get("next") is not None,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get playlist tracks: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/playlists/<playlist_id>/import", methods=["POST"])
def import_playlist(playlist_id):
    """Import artists from a Spotify playlist"""
    try:
        # Load tokens from session
        if "spotify_access_token" in session:
            spotify_service.access_token = session["spotify_access_token"]
            spotify_service.refresh_token = session.get("spotify_refresh_token")

        if not spotify_service.access_token:
            return jsonify({"error": "Not authenticated with Spotify"}), 401

        logger.info(f"Starting import of Spotify playlist: {playlist_id}")

        # Import playlist artists
        results = spotify_service.import_playlist_artists(playlist_id)

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Successfully imported {results['imported_artists']} artists from playlist '{results['playlist_name']}'",
                    "results": results,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to import playlist: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/followed/artists", methods=["GET"])
def get_followed_artists():
    """Get user's followed artists"""
    try:
        # Load tokens from session
        if "spotify_access_token" in session:
            spotify_service.access_token = session["spotify_access_token"]
            spotify_service.refresh_token = session.get("spotify_refresh_token")

        if not spotify_service.access_token:
            return jsonify({"error": "Not authenticated with Spotify"}), 401

        limit = int(request.args.get("limit", 50))

        followed_data = spotify_service.get_followed_artists(limit)
        artists = followed_data.get("artists", {}).get("items", [])

        # Format artist data
        formatted_artists = []
        for artist in artists:
            formatted_artists.append(
                {
                    "id": artist.get("id"),
                    "name": artist.get("name"),
                    "genres": artist.get("genres", []),
                    "popularity": artist.get("popularity"),
                    "followers": artist.get("followers", {}).get("total", 0),
                    "images": artist.get("images", []),
                    "external_urls": artist.get("external_urls", {}),
                }
            )

        return (
            jsonify(
                {
                    "artists": formatted_artists,
                    "total": followed_data.get("artists", {}).get("total", 0),
                    "limit": limit,
                    "next": followed_data.get("artists", {}).get("next") is not None,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get followed artists: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/followed/sync", methods=["POST"])
def sync_followed_artists():
    """Sync user's followed artists from Spotify"""
    try:
        # Load tokens from session
        if "spotify_access_token" in session:
            spotify_service.access_token = session["spotify_access_token"]
            spotify_service.refresh_token = session.get("spotify_refresh_token")

        if not spotify_service.access_token:
            return jsonify({"error": "Not authenticated with Spotify"}), 401

        logger.info("Starting sync of followed artists from Spotify")

        # Sync followed artists
        results = spotify_service.sync_followed_artists()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Successfully synced {results['imported_artists']} followed artists",
                    "results": results,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to sync followed artists: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/top/artists", methods=["GET"])
def get_top_artists():
    """Get user's top artists"""
    try:
        # Load tokens from session
        if "spotify_access_token" in session:
            spotify_service.access_token = session["spotify_access_token"]
            spotify_service.refresh_token = session.get("spotify_refresh_token")

        if not spotify_service.access_token:
            return jsonify({"error": "Not authenticated with Spotify"}), 401

        time_range = request.args.get("time_range", "medium_term")
        limit = int(request.args.get("limit", 50))

        top_artists = spotify_service.get_user_top_artists(time_range, limit)

        # Format artist data
        formatted_artists = []
        for artist in top_artists.get("items", []):
            formatted_artists.append(
                {
                    "id": artist.get("id"),
                    "name": artist.get("name"),
                    "genres": artist.get("genres", []),
                    "popularity": artist.get("popularity"),
                    "followers": artist.get("followers", {}).get("total", 0),
                    "images": artist.get("images", []),
                    "external_urls": artist.get("external_urls", {}),
                }
            )

        return (
            jsonify(
                {
                    "artists": formatted_artists,
                    "total": top_artists.get("total", 0),
                    "time_range": time_range,
                    "limit": limit,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get top artists: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/top/tracks", methods=["GET"])
def get_top_tracks():
    """Get user's top tracks"""
    try:
        # Load tokens from session
        if "spotify_access_token" in session:
            spotify_service.access_token = session["spotify_access_token"]
            spotify_service.refresh_token = session.get("spotify_refresh_token")

        if not spotify_service.access_token:
            return jsonify({"error": "Not authenticated with Spotify"}), 401

        time_range = request.args.get("time_range", "medium_term")
        limit = int(request.args.get("limit", 50))

        top_tracks = spotify_service.get_user_top_tracks(time_range, limit)

        # Format track data
        formatted_tracks = []
        for track in top_tracks.get("items", []):
            formatted_tracks.append(
                {
                    "id": track.get("id"),
                    "name": track.get("name"),
                    "artists": [
                        {"name": a.get("name"), "id": a.get("id")}
                        for a in track.get("artists", [])
                    ],
                    "album": {
                        "name": track.get("album", {}).get("name"),
                        "images": track.get("album", {}).get("images", []),
                    },
                    "duration_ms": track.get("duration_ms"),
                    "popularity": track.get("popularity"),
                    "external_urls": track.get("external_urls", {}),
                }
            )

        return (
            jsonify(
                {
                    "tracks": formatted_tracks,
                    "total": top_tracks.get("total", 0),
                    "time_range": time_range,
                    "limit": limit,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get top tracks: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/disconnect", methods=["POST"])
def disconnect():
    """Disconnect from Spotify"""
    try:
        # Clear session tokens
        session.pop("spotify_access_token", None)
        session.pop("spotify_refresh_token", None)
        session.pop("spotify_token_expires", None)

        # Clear service tokens
        spotify_service.access_token = None
        spotify_service.refresh_token = None
        spotify_service.token_expires = None

        logger.info("Spotify disconnected successfully")
        return (
            jsonify(
                {"success": True, "message": "Successfully disconnected from Spotify"}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to disconnect from Spotify: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/status", methods=["GET"])
def get_status():
    """Get Spotify integration status"""
    try:
        # Check if tokens are available
        has_access_token = (
            "spotify_access_token" in session
            or spotify_service.access_token is not None
        )

        # Check if client credentials are configured
        configured = (
            spotify_service.client_id is not None
            and spotify_service.client_secret is not None
        )

        profile = None
        if has_access_token:
            try:
                # Load tokens from session
                if "spotify_access_token" in session:
                    spotify_service.access_token = session["spotify_access_token"]
                    spotify_service.refresh_token = session.get("spotify_refresh_token")

                profile = spotify_service.get_user_profile()
            except Exception as e:
                logger.warning(f"Failed to get profile for status check: {e}")

        return (
            jsonify(
                {
                    "configured": configured,
                    "authenticated": has_access_token,
                    "profile": profile,
                    "client_id": (
                        spotify_service.client_id[:8] + "..."
                        if spotify_service.client_id
                        else None
                    ),
                    "redirect_uri": spotify_service.redirect_uri,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get Spotify status: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/reload", methods=["POST"])
def reload_settings():
    """Force reload Spotify settings from database"""
    try:
        logger.info("Manual Spotify settings reload requested")
        spotify_service.reload_settings()
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Spotify settings reloaded successfully",
                    "redirect_uri": spotify_service.redirect_uri,
                    "client_id": (
                        spotify_service.client_id[:8] + "..."
                        if spotify_service.client_id
                        else None
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to reload Spotify settings: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/test", methods=["POST"])
def test_spotify_integration():
    """Test Spotify API connection"""
    try:
        # Check if client credentials are configured
        if not spotify_service.client_id or not spotify_service.client_secret:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Spotify client credentials not configured. Please set spotify_client_id and spotify_client_secret in settings.",
                    }
                ),
                400,
            )

        # Test client credentials flow
        try:
            token_data = spotify_service.get_client_credentials_token()
            if token_data and token_data.get("access_token"):
                return (
                    jsonify(
                        {
                            "status": "success",
                            "message": "Spotify API connection successful",
                            "token_type": token_data.get("token_type"),
                            "expires_in": token_data.get("expires_in"),
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Failed to get access token from Spotify",
                        }
                    ),
                    500,
                )
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Spotify API connection failed: {str(e)}",
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Spotify integration test failed: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Spotify integration test failed: {str(e)}",
                }
            ),
            500,
        )


@spotify_bp.route("/authorize", methods=["POST"])
def authorize_spotify():
    """Get Spotify authorization URL for user authentication"""
    try:
        # Force reload settings to ensure we have the latest configuration
        spotify_service.reload_settings()

        if not spotify_service.client_id or not spotify_service.client_secret:
            return jsonify({"error": "Spotify client credentials not configured"}), 400

        auth_url = spotify_service.get_auth_url()
        logger.info(
            f"Generated Spotify authorization URL with redirect URI: {spotify_service.redirect_uri}"
        )

        return (
            jsonify(
                {
                    "authorization_url": auth_url,
                    "redirect_uri": spotify_service.redirect_uri,
                    "message": "Please visit the authorization URL to connect your Spotify account",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get Spotify authorization URL: {e}")
        return jsonify({"error": str(e)}), 500


@spotify_bp.route("/import-playlists", methods=["POST"])
def import_playlists():
    """Import all user playlists from Spotify"""
    try:
        # Load tokens from session
        if "spotify_access_token" in session:
            spotify_service.access_token = session["spotify_access_token"]
            spotify_service.refresh_token = session.get("spotify_refresh_token")

        if not spotify_service.access_token:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Not authenticated with Spotify. Please authorize first.",
                    }
                ),
                401,
            )

        # Get all playlists
        playlists = spotify_service.get_user_playlists(limit=50)

        imported_count = 0
        total_artists = 0

        # Import artists from each playlist
        for playlist in playlists.get("items", []):
            try:
                results = spotify_service.import_playlist_artists(playlist["id"])
                imported_count += results.get("imported_artists", 0)
                total_artists += results.get("total_artists", 0)
            except Exception as e:
                logger.warning(f"Failed to import playlist {playlist['name']}: {e}")
                continue

        return (
            jsonify(
                {
                    "success": True,
                    "imported_count": imported_count,
                    "total_artists": total_artists,
                    "playlists_processed": len(playlists.get("items", [])),
                    "message": f'Successfully imported {imported_count} unique artists from {len(playlists.get("items", []))} playlists',
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to import playlists: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
