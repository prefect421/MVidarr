"""
Lidarr API integration for MVidarr
"""

import json

import requests
from flask import Blueprint, jsonify, request

from src.database.connection import get_db
from src.database.models import Artist
from src.services.settings_service import SettingsService
from src.utils.logger import get_logger

lidarr_bp = Blueprint("lidarr", __name__)
logger = get_logger("mvidarr.api.lidarr")


@lidarr_bp.route("/test", methods=["POST"])
def test_lidarr_connection():
    """Test Lidarr server connection and API key"""
    try:
        # Get settings from database
        server_url = SettingsService.get("lidarr_server_url")
        api_key = SettingsService.get("lidarr_api_key")

        if not server_url or not api_key:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Lidarr server URL or API key not configured",
                    }
                ),
                400,
            )

        server_url = server_url.rstrip("/")

        # Test system status endpoint
        headers = {"X-Api-Key": api_key}
        response = requests.get(
            f"{server_url}/api/v1/system/status", headers=headers, timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return jsonify(
                {
                    "status": "success",
                    "message": f'Connected to Lidarr {data.get("version", "unknown")}',
                    "server_info": {
                        "version": data.get("version"),
                        "build_time": data.get("buildTime"),
                        "is_production": data.get("isProduction"),
                        "branch": data.get("branch"),
                    },
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to connect to Lidarr: HTTP {response.status_code}",
                    }
                ),
                400,
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"Lidarr connection test failed: {e}")
        return (
            jsonify({"status": "error", "message": f"Connection failed: {str(e)}"}),
            500,
        )
    except Exception as e:
        logger.error(f"Lidarr test error: {e}")
        return jsonify({"status": "error", "message": f"Test failed: {str(e)}"}), 500


@lidarr_bp.route("/sync-library", methods=["POST"])
def sync_lidarr_library():
    """Sync artist library from Lidarr to MVidarr"""
    try:
        # Get settings from database using SettingsService
        server_url = SettingsService.get("lidarr_server_url")
        api_key = SettingsService.get("lidarr_api_key")

        if not server_url or not api_key:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Lidarr server URL or API key not configured",
                    }
                ),
                400,
            )

        server_url = server_url.rstrip("/")

        # Get all artists from Lidarr
        headers = {"X-Api-Key": api_key}
        response = requests.get(
            f"{server_url}/api/v1/artist", headers=headers, timeout=30
        )

        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Failed to fetch artists from Lidarr: HTTP {response.status_code}",
                    }
                ),
                400,
            )

        artists = response.json()
        synced_count = 0

        # Process each artist
        with get_db() as session:
            for artist in artists:
                try:
                    # Check if artist already exists in MVidarr
                    existing_artist = (
                        session.query(Artist)
                        .filter_by(name=artist["artistName"])
                        .first()
                    )

                    if not existing_artist:
                        # Add new artist to MVidarr
                        from src.utils.filename_cleanup import FilenameCleanup

                        folder_path = FilenameCleanup.sanitize_folder_name(
                            artist["artistName"]
                        )

                        new_artist = Artist(
                            name=artist["artistName"],
                            imvdb_id=artist.get("foreignArtistId"),
                            monitored=artist.get("monitored", False),
                            source="lidarr",
                            folder_path=folder_path,
                        )
                        session.add(new_artist)
                        synced_count += 1
                        logger.info(f"Added artist from Lidarr: {artist['artistName']}")
                    else:
                        # Update existing artist monitoring status
                        existing_artist.monitored = artist.get("monitored", False)
                        existing_artist.source = "lidarr"

                except Exception as e:
                    logger.error(
                        f"Error processing artist {artist.get('artistName', 'unknown')}: {e}"
                    )
                    continue

            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully synced {synced_count} artists from Lidarr",
                    "processed_count": len(artists),
                    "synced_count": synced_count,
                }
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"Lidarr library sync failed: {e}")
        return jsonify({"success": False, "error": f"Connection failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Lidarr sync error: {e}")
        return jsonify({"success": False, "error": f"Sync failed: {str(e)}"}), 500


@lidarr_bp.route("/import-artists", methods=["POST"])
def import_lidarr_artists():
    """Import monitored artists from Lidarr and search for their music videos"""
    try:
        # Get settings from database using SettingsService
        server_url = SettingsService.get("lidarr_server_url")
        api_key = SettingsService.get("lidarr_api_key")

        if not server_url or not api_key:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Lidarr server URL or API key not configured",
                    }
                ),
                400,
            )

        server_url = server_url.rstrip("/")

        # Get monitored artists from Lidarr
        headers = {"X-Api-Key": api_key}
        response = requests.get(
            f"{server_url}/api/v1/artist", headers=headers, timeout=30
        )

        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Failed to fetch artists from Lidarr: HTTP {response.status_code}",
                    }
                ),
                400,
            )

        artists = response.json()
        monitored_artists = [a for a in artists if a.get("monitored", False)]
        imported_count = 0

        # Process each monitored artist
        with get_db() as session:
            for artist in monitored_artists:
                try:
                    # Check if artist already exists in MVidarr
                    existing_artist = (
                        session.query(Artist)
                        .filter_by(name=artist["artistName"])
                        .first()
                    )

                    if not existing_artist:
                        # Add new artist to MVidarr
                        from src.utils.filename_cleanup import FilenameCleanup

                        folder_path = FilenameCleanup.sanitize_folder_name(
                            artist["artistName"]
                        )

                        new_artist = Artist(
                            name=artist["artistName"],
                            imvdb_id=artist.get("foreignArtistId"),
                            monitored=True,  # Set to monitored since they're monitored in Lidarr
                            source="lidarr",
                            folder_path=folder_path,
                        )
                        session.add(new_artist)
                        imported_count += 1
                        logger.info(
                            f"Imported monitored artist from Lidarr: {artist['artistName']}"
                        )
                    else:
                        # Update existing artist to monitored
                        existing_artist.monitored = True
                        existing_artist.source = "lidarr"

                except Exception as e:
                    logger.error(
                        f"Error importing artist {artist.get('artistName', 'unknown')}: {e}"
                    )
                    continue

        return jsonify(
            {
                "success": True,
                "message": f"Successfully imported {imported_count} monitored artists from Lidarr",
                "total_artists": len(artists),
                "monitored_artists": len(monitored_artists),
                "imported_count": imported_count,
            }
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Lidarr artist import failed: {e}")
        return jsonify({"success": False, "error": f"Connection failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Lidarr import error: {e}")
        return jsonify({"success": False, "error": f"Import failed: {str(e)}"}), 500


@lidarr_bp.route("/sync-albums", methods=["POST"])
def sync_lidarr_albums():
    """Sync album information from Lidarr to help identify wanted music videos"""
    try:
        # Get settings from database using SettingsService
        server_url = SettingsService.get("lidarr_server_url")
        api_key = SettingsService.get("lidarr_api_key")

        if not server_url or not api_key:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Lidarr server URL or API key not configured",
                    }
                ),
                400,
            )

        server_url = server_url.rstrip("/")

        # Get all albums from Lidarr
        headers = {"X-Api-Key": api_key}
        response = requests.get(
            f"{server_url}/api/v1/album", headers=headers, timeout=30
        )

        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Failed to fetch albums from Lidarr: HTTP {response.status_code}",
                    }
                ),
                400,
            )

        albums = response.json()
        processed_count = 0

        # Process each album
        for album in albums:
            try:
                # Get artist name from artist ID
                artist_response = requests.get(
                    f'{server_url}/api/v1/artist/{album["artistId"]}',
                    headers=headers,
                    timeout=10,
                )
                if artist_response.status_code == 200:
                    artist_data = artist_response.json()
                    artist_name = artist_data["artistName"]

                    # Check if artist exists in MVidarr
                    with get_db() as session:
                        existing_artist = (
                            session.query(Artist).filter_by(name=artist_name).first()
                        )

                        if existing_artist:
                            # Log album information for potential video discovery
                            logger.info(
                                f"Lidarr album sync: {artist_name} - {album['title']} ({album.get('releaseDate', 'unknown date')})"
                            )

                            # Store album information in a custom table if needed
                            # For now, we'll just log it for video discovery purposes
                            processed_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing album {album.get('title', 'unknown')}: {e}"
                )
                continue

        return jsonify(
            {
                "success": True,
                "message": f"Successfully processed {processed_count} albums from Lidarr",
                "total_albums": len(albums),
                "processed_count": processed_count,
            }
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Lidarr album sync failed: {e}")
        return jsonify({"success": False, "error": f"Connection failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Lidarr album sync error: {e}")
        return jsonify({"success": False, "error": f"Sync failed: {str(e)}"}), 500


@lidarr_bp.route("/wanted-albums", methods=["GET"])
def get_wanted_albums():
    """Get list of wanted/missing albums from Lidarr for video discovery"""
    try:
        # Get settings from database using SettingsService
        server_url = SettingsService.get("lidarr_server_url")
        api_key = SettingsService.get("lidarr_api_key")

        if not server_url or not api_key:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Lidarr server URL or API key not configured",
                    }
                ),
                400,
            )

        server_url = server_url.rstrip("/")

        # Get wanted albums from Lidarr
        headers = {"X-Api-Key": api_key}
        response = requests.get(
            f"{server_url}/api/v1/wanted/missing", headers=headers, timeout=30
        )

        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Failed to fetch wanted albums from Lidarr: HTTP {response.status_code}",
                    }
                ),
                400,
            )

        data = response.json()
        wanted_albums = []

        for album in data.get("records", []):
            try:
                # Get artist name from artist ID
                artist_response = requests.get(
                    f'{server_url}/api/v1/artist/{album["artistId"]}',
                    headers=headers,
                    timeout=10,
                )
                if artist_response.status_code == 200:
                    artist_data = artist_response.json()
                    wanted_albums.append(
                        {
                            "artist": artist_data["artistName"],
                            "album": album["title"],
                            "releaseDate": album.get("releaseDate"),
                            "monitored": album.get("monitored", False),
                        }
                    )

            except Exception as e:
                logger.error(
                    f"Error processing wanted album {album.get('title', 'unknown')}: {e}"
                )
                continue

        return jsonify(
            {
                "success": True,
                "wanted_albums": wanted_albums,
                "total_wanted": len(wanted_albums),
            }
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Lidarr wanted albums request failed: {e}")
        return jsonify({"success": False, "error": f"Connection failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Lidarr wanted albums error: {e}")
        return jsonify({"success": False, "error": f"Request failed: {str(e)}"}), 500
