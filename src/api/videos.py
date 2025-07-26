"""
Videos API endpoints
"""

import mimetypes
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from flask import Blueprint, Response, jsonify, request, send_file
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from src.database.connection import get_db
from src.database.models import Artist, Download, Video, VideoStatus
from src.services.imvdb_service import imvdb_service
from src.utils.logger import get_logger

videos_bp = Blueprint("videos", __name__, url_prefix="/videos")
logger = get_logger("mvidarr.api.videos")


def resolve_video_url(video, session):
    """
    Helper function to resolve video URL using yt-dlp search

    Args:
        video: Video object
        session: Database session

    Returns:
        str: Resolved URL or None
    """
    if video.url:
        return video.url

    try:
        import json
        import subprocess

        artist_name = video.artist.name if video.artist else "Unknown Artist"
        # Ensure title is a string (fix for integer title issue)
        video_title = str(video.title) if video.title is not None else "Unknown"
        search_query = f"{artist_name} {video_title}"
        logger.info(f"Searching for video URL: {search_query}")

        # Use yt-dlp to search YouTube
        cmd = [
            "/usr/local/bin/yt-dlp",  # Use the system-installed version
            "--dump-json",
            "--no-download",
            "--playlist-items",
            "1",
            f"ytsearch1:{search_query}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0 and result.stdout:
            video_info = json.loads(result.stdout.strip())
            resolved_url = video_info.get("webpage_url") or video_info.get("url")

            if resolved_url:
                # Update video with resolved URL
                video.url = resolved_url
                if "id" in video_info:
                    video.youtube_id = video_info["id"]
                session.commit()
                logger.info(f"Resolved video URL for '{video.title}': {resolved_url}")
                return resolved_url
            else:
                logger.warning(f"No URL found in video info for '{video.title}'")
        else:
            logger.error(f"yt-dlp search failed for '{search_query}': {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error(f"yt-dlp search timed out for '{search_query}'")
    except Exception as e:
        logger.error(f"Error resolving video URL for '{video.title}': {e}")

    return None


def find_relocated_video(video, session):
    """
    Try to find a relocated video file in expected artist folders

    Args:
        video: Video object with artist relationship
        session: Database session

    Returns:
        str: Path to relocated file or None if not found
    """
    if not video.artist:
        return None

    from src.services.settings_service import settings

    try:
        # Get the downloads directory from settings
        downloads_dir = settings.get("downloads_directory", "data/downloads")
        if not os.path.isabs(downloads_dir):
            downloads_dir = os.path.join(os.getcwd(), downloads_dir)

        # Expected artist folder path
        artist_folder = os.path.join(downloads_dir, video.artist.name)

        if not os.path.exists(artist_folder):
            # Try with sanitized artist name
            import re

            sanitized_name = re.sub(r'[<>:"/\\|?*]', "_", video.artist.name)
            artist_folder = os.path.join(downloads_dir, sanitized_name)

        if os.path.exists(artist_folder):
            # Search for video files with similar names
            # Ensure title is a string (fix for integer title issue)
            video_title = str(video.title) if video.title is not None else ""
            video_title_clean = (
                video_title.lower().replace(" ", "").replace("_", "").replace("-", "")
            )

            for filename in os.listdir(artist_folder):
                if filename.lower().endswith((".mp4", ".mkv", ".avi", ".webm", ".mov")):
                    # Check if filename contains the video title (fuzzy match)
                    filename_clean = (
                        filename.lower()
                        .replace(" ", "")
                        .replace("_", "")
                        .replace("-", "")
                    )

                    # Try different matching strategies
                    if (
                        video_title_clean in filename_clean
                        or filename_clean.startswith(video_title_clean[:10])
                        or any(
                            word in filename_clean
                            for word in video_title_clean.split()
                            if len(word) > 3
                        )
                    ):
                        full_path = os.path.join(artist_folder, filename)
                        logger.info(f"Found potential relocated video: {full_path}")
                        return full_path

            # If no fuzzy match, try exact YouTube ID match if available
            if video.youtube_id:
                for filename in os.listdir(artist_folder):
                    if video.youtube_id in filename:
                        full_path = os.path.join(artist_folder, filename)
                        logger.info(f"Found relocated video by YouTube ID: {full_path}")
                        return full_path

    except Exception as e:
        logger.error(f"Error searching for relocated video: {e}")

    return None


def _trigger_video_download(video_id):
    """
    Helper function to trigger video download

    Args:
        video_id: Video ID to download

    Returns:
        dict: Download result with success/error information
    """
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return {"success": False, "error": "Video not found"}

            # Store video data for URL resolution
            artist_name = video.artist.name if video.artist else "Unknown Artist"

            # Resolve video URL using helper function
            video_url = resolve_video_url(video, session)

            if not video_url:
                return {
                    "success": False,
                    "error": "Video has no URL to download and could not resolve one",
                }

            # Import ytdlp service
            from src.services.ytdlp_service import ytdlp_service

            # Check if video is already downloaded
            status_value = (
                video.status.value if hasattr(video.status, "value") else video.status
            )
            if (
                status_value == "DOWNLOADED"
                and video.local_path
                and os.path.exists(video.local_path)
            ):
                return {"success": False, "error": "Video is already downloaded"}

            # Add download to yt-dlp queue
            result = ytdlp_service.add_music_video_download(
                artist=artist_name,
                title=video.title,
                url=video_url,
                quality="best",
                video_id=video_id,
            )

            if result and result.get("success"):
                # Update video status to indicate download started
                # Re-query the video object to ensure it's bound to the current session
                video = session.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = VideoStatus.DOWNLOADING
                    session.commit()

                return {
                    "success": True,
                    "message": f'Download queued for "{video.title}"',
                    "download_id": result.get("id"),
                    "video_id": video_id,
                }
            else:
                error_msg = (
                    result.get("error", "Failed to queue download")
                    if result
                    else "yt-dlp service unavailable"
                )
                return {"success": False, "error": error_msg}

    except Exception as e:
        logger.error(f"Failed to trigger download for video {video_id}: {e}")
        return {"success": False, "error": str(e)}


@videos_bp.route("/", methods=["GET"])
def get_videos():
    """Get all videos with optional sorting and pagination"""
    try:
        # Get sorting and pagination parameters
        sort_by = request.args.get("sort", "title")
        sort_order = request.args.get("order", "asc")
        limit = request.args.get("limit", type=int)
        offset = request.args.get("offset", 0, type=int)

        with get_db() as session:
            query = session.query(Video).join(
                Artist, Video.artist_id == Artist.id, isouter=True
            )

            # Get total count before applying limit/offset
            total_count = query.count()

            # Apply sorting
            if sort_by == "title":
                sort_column = Video.title
            elif sort_by == "artist_name":
                sort_column = Artist.name
            elif sort_by == "year":
                sort_column = Video.year
            elif sort_by == "created_at":
                sort_column = Video.created_at
            elif sort_by == "status":
                sort_column = Video.status
            else:
                sort_column = Video.title

            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

            # Apply pagination if limit is specified
            if limit is not None:
                query = query.offset(offset).limit(limit)

            videos = query.all()

            videos_list = []
            for video in videos:
                videos_list.append(
                    {
                        "id": video.id,
                        "title": video.title,
                        "artist_id": video.artist_id,
                        "artist_name": video.artist.name if video.artist else None,
                        "status": video.status.value
                        if hasattr(video.status, "value")
                        else video.status,
                        "imvdb_id": video.imvdb_id,
                        "video_url": video.url,
                        "local_path": video.local_path,
                        "thumbnail_url": video.thumbnail_url,
                        "duration": video.duration,
                        "year": video.year,
                        "created_at": video.created_at.isoformat(),
                    }
                )

            return (
                jsonify(
                    {
                        "videos": videos_list,
                        "count": len(videos_list),
                        "total": total_count,
                        "offset": offset,
                        "limit": limit,
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to get videos: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/search", methods=["GET"])
def search_videos():
    """Search videos with multiple filters"""
    try:
        # Get search parameters
        query = request.args.get("q", "").strip()
        artist_name = request.args.get("artist", "").strip()
        status = request.args.get("status", "").strip()
        year = request.args.get("year", "").strip()
        genre = request.args.get("genre", "").strip()
        quality = request.args.get("quality", "").strip()
        has_thumbnail = request.args.get("has_thumbnail", "").strip()
        source = request.args.get("source", "").strip()
        duration_min = request.args.get("duration_min", type=int)
        duration_max = request.args.get("duration_max", type=int)
        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()
        keywords = request.args.get("keywords", "").strip()
        sort_by = request.args.get("sort_by", request.args.get("sort", "title"))
        sort_order = request.args.get("sort_order", request.args.get("order", "asc"))
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        with get_db() as session:
            # Start with base query
            videos_query = session.query(Video).join(Artist)

            # Apply filters
            if query:
                # Search in video title or artist name
                videos_query = videos_query.filter(
                    Video.title.contains(query) | Artist.name.contains(query)
                )

            if artist_name:
                videos_query = videos_query.filter(Artist.name.contains(artist_name))

            if status:
                videos_query = videos_query.filter(Video.status == status)

            if year:
                try:
                    year_int = int(year)
                    videos_query = videos_query.filter(Video.year == year_int)
                except ValueError:
                    pass

            # Filter by genre
            if genre:
                videos_query = videos_query.filter(Video.genres.contains(f'"{genre}"'))

            # Filter by quality
            if quality:
                videos_query = videos_query.filter(Video.quality == quality)

            # Filter by thumbnail presence
            if has_thumbnail:
                has_thumbnail_bool = has_thumbnail.lower() in ["true", "1", "yes"]
                if has_thumbnail_bool:
                    videos_query = videos_query.filter(Video.thumbnail_path.isnot(None))
                else:
                    videos_query = videos_query.filter(Video.thumbnail_path.is_(None))

            # Filter by source
            if source:
                if source == "youtube":
                    videos_query = videos_query.filter(Video.youtube_id.isnot(None))
                elif source == "imvdb":
                    videos_query = videos_query.filter(Video.imvdb_id.isnot(None))
                elif source == "manual":
                    videos_query = videos_query.filter(
                        Video.youtube_id.is_(None) & Video.imvdb_id.is_(None)
                    )

            # Filter by duration range
            if duration_min is not None:
                videos_query = videos_query.filter(Video.duration >= duration_min)
            if duration_max is not None:
                videos_query = videos_query.filter(Video.duration <= duration_max)

            # Filter by date range
            if date_from:
                try:
                    from datetime import datetime

                    date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
                    videos_query = videos_query.filter(Video.created_at >= date_from_dt)
                except ValueError:
                    pass

            if date_to:
                try:
                    from datetime import datetime

                    date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
                    videos_query = videos_query.filter(Video.created_at <= date_to_dt)
                except ValueError:
                    pass

            # Filter by keywords (search in title)
            if keywords:
                keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
                for keyword in keyword_list:
                    videos_query = videos_query.filter(Video.title.contains(keyword))

            # Apply sorting
            if sort_by == "title":
                sort_column = Video.title
            elif sort_by in ["artist_name", "artist"]:
                sort_column = Artist.name
            elif sort_by == "year":
                sort_column = Video.year
            elif sort_by in ["created_at", "date_added"]:
                sort_column = Video.created_at
            elif sort_by == "status":
                sort_column = Video.status
            elif sort_by == "quality":
                sort_column = Video.quality
            elif sort_by == "duration":
                sort_column = Video.duration
            else:
                sort_column = Video.title

            if sort_order.lower() == "desc":
                videos_query = videos_query.order_by(sort_column.desc())
            else:
                videos_query = videos_query.order_by(sort_column.asc())

            # Get total count for pagination
            total_count = videos_query.count()

            # Apply pagination
            videos = videos_query.offset(offset).limit(limit).all()

            # Format results
            videos_list = []
            for video in videos:
                videos_list.append(
                    {
                        "id": video.id,
                        "title": video.title,
                        "artist_id": video.artist_id,
                        "artist_name": video.artist.name if video.artist else None,
                        "status": video.status.value
                        if hasattr(video.status, "value")
                        else video.status,
                        "imvdb_id": video.imvdb_id,
                        "video_url": video.url,
                        "local_path": video.local_path,
                        "thumbnail_url": video.thumbnail_url,
                        "duration": video.duration,
                        "year": video.year,
                        "genres": video.genres if video.genres else [],
                        "quality": video.quality,
                        "created_at": video.created_at.isoformat(),
                    }
                )

            return (
                jsonify(
                    {
                        "videos": videos_list,
                        "count": len(videos_list),
                        "total": total_count,
                        "offset": offset,
                        "limit": limit,
                        "filters": {
                            "query": query,
                            "artist": artist_name,
                            "status": status,
                            "year": year,
                            "genre": genre,
                            "quality": quality,
                            "has_thumbnail": has_thumbnail,
                            "source": source,
                            "duration_min": duration_min,
                            "duration_max": duration_max,
                            "date_from": date_from,
                            "date_to": date_to,
                            "keywords": keywords,
                        },
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to search videos: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>", methods=["GET"])
def get_video(video_id):
    """Get specific video by ID"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            video_data = {
                "id": video.id,
                "title": video.title,
                "artist_id": video.artist_id,
                "artist_name": video.artist.name if video.artist else None,
                "status": video.status.value
                if hasattr(video.status, "value")
                else video.status,
                "imvdb_id": video.imvdb_id,
                "video_url": video.url,
                "local_path": video.local_path,
                "thumbnail_url": video.thumbnail_url,
                "duration": video.duration,
                "year": video.year,
                "genres": video.genres,
                "created_at": video.created_at.isoformat(),
            }

            return jsonify(video_data), 200

    except Exception as e:
        logger.error(f"Failed to get video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/download", methods=["POST"])
def download_video(video_id):
    """Queue video for download"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Store video data for URL resolution
            artist_name = video.artist.name if video.artist else "Unknown Artist"

            # Resolve video URL using helper function
            video_url = resolve_video_url(video, session)

            if not video_url:
                return (
                    jsonify(
                        {
                            "error": "Video has no URL to download and could not resolve one"
                        }
                    ),
                    400,
                )

            # Import ytdlp service
            from src.services.ytdlp_service import ytdlp_service

            # Check if video is already downloaded
            status_value = (
                video.status.value if hasattr(video.status, "value") else video.status
            )
            if (
                status_value == "DOWNLOADED"
                and video.local_path
                and os.path.exists(video.local_path)
            ):
                return (
                    jsonify({"success": False, "error": "Video is already downloaded"}),
                    400,
                )

            # Add download to yt-dlp queue
            result = ytdlp_service.add_music_video_download(
                artist=artist_name,
                title=video.title,
                url=video_url,
                quality="best",
                video_id=video_id,
            )

            if result and result.get("success"):
                # Update video status to indicate download started
                # Re-query the video object to ensure it's bound to the current session
                video = session.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = VideoStatus.DOWNLOADING
                    session.commit()

                logger.info(f"Queued download for video {video_id}: {video.title}")

                return (
                    jsonify(
                        {
                            "success": True,
                            "message": f'Download queued for "{video.title}"',
                            "download_id": result.get("id"),
                            "video_id": video_id,
                        }
                    ),
                    200,
                )
            else:
                error_msg = (
                    result.get("error", "Failed to queue download")
                    if result
                    else "MeTube service unavailable"
                )
                return jsonify({"success": False, "error": error_msg}), 500

    except Exception as e:
        logger.error(f"Failed to download video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/identify-artist", methods=["POST"])
def identify_artist(video_id):
    """Get artist identification suggestions for a video"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Extract video data within the session
            video_title = video.title
            current_artist = video.artist.name if video.artist else None

        # Import the identification service
        from src.services.artist_identification_service import (
            artist_identification_service,
        )

        # Get identification candidates
        candidates = artist_identification_service.identify_artist_from_title(
            video_title
        )

        # Filter to top 3 candidates with confidence > 0.6
        top_candidates = [c for c in candidates if c["confidence"] > 0.6][:3]

        # Format response
        result = {
            "video_id": video_id,
            "title": video_title,
            "current_artist": current_artist,
            "suggestions": [],
        }

        for candidate in top_candidates:
            result["suggestions"].append(
                {
                    "artist_name": candidate["artist_name"],
                    "confidence": candidate["confidence"],
                    "source": candidate["source"],
                    "reason": candidate.get("match_reason", "No additional info"),
                }
            )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Failed to identify artist for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/search-artists", methods=["GET"])
def search_artists():
    """Search for existing artists by name"""
    try:
        query = request.args.get("q", "").strip()

        if not query:
            return jsonify({"artists": []}), 200

        # Minimum query length to avoid too many results
        if len(query) < 2:
            return jsonify({"artists": []}), 200

        with get_db() as session:
            # Search for artists whose names contain the query (case-insensitive)
            artists = (
                session.query(Artist)
                .filter(Artist.name.ilike(f"%{query}%"))
                .filter(Artist.name != "Unknown Artist")
                .order_by(Artist.name)
                .limit(10)
                .all()
            )

            # Format results
            results = []
            for artist in artists:
                results.append(
                    {
                        "id": artist.id,
                        "name": artist.name,
                        "video_count": len(artist.videos),
                    }
                )

            return jsonify({"artists": results}), 200

    except Exception as e:
        logger.error(f"Failed to search artists: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>", methods=["DELETE"])
def delete_video(video_id):
    """Delete a specific video"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Store video info for response
            video_info = {
                "id": video.id,
                "title": video.title,
                "artist_name": video.artist.name if video.artist else None,
            }

            # Delete the video record
            session.delete(video)
            session.commit()

            logger.info(
                f"Deleted video: {video_info['title']} by {video_info['artist_name']}"
            )

            return (
                jsonify({"message": "Video deleted successfully", "video": video_info}),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to delete video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/bulk/delete", methods=["POST"])
def bulk_delete_videos():
    """Delete multiple videos"""
    try:
        data = request.get_json()
        video_ids = data.get("video_ids", [])

        if not video_ids:
            return jsonify({"error": "No video IDs provided"}), 400

        if not isinstance(video_ids, list):
            return jsonify({"error": "video_ids must be a list"}), 400

        deleted_videos = []
        failed_videos = []

        with get_db() as session:
            for video_id in video_ids:
                try:
                    video = session.query(Video).filter(Video.id == video_id).first()

                    if not video:
                        failed_videos.append(
                            {"id": video_id, "error": "Video not found"}
                        )
                        continue

                    # Store video info for response
                    video_info = {
                        "id": video.id,
                        "title": video.title,
                        "artist_name": video.artist.name if video.artist else None,
                    }

                    # Delete the video record
                    session.delete(video)
                    deleted_videos.append(video_info)

                    logger.info(
                        f"Bulk deleted video: {video_info['title']} by {video_info['artist_name']}"
                    )

                except Exception as e:
                    failed_videos.append({"id": video_id, "error": str(e)})
                    logger.error(
                        f"Failed to delete video {video_id} in bulk operation: {e}"
                    )

            # Commit all successful deletes
            session.commit()

        response = {
            "message": f"Bulk delete completed: {len(deleted_videos)} deleted, {len(failed_videos)} failed",
            "deleted_count": len(deleted_videos),
            "failed_count": len(failed_videos),
            "deleted_videos": deleted_videos,
            "failed_videos": failed_videos,
        }

        if failed_videos:
            return jsonify(response), 207  # Multi-status
        else:
            return jsonify(response), 200

    except Exception as e:
        logger.error(f"Failed to bulk delete videos: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/thumbnail", methods=["GET"])
def get_video_thumbnail(video_id):
    """Get thumbnail for a specific video"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Check if we have a local thumbnail file
            if video.thumbnail_path and os.path.exists(video.thumbnail_path):
                return send_file(video.thumbnail_path, as_attachment=False)

            # If we have a thumbnail URL but no local file, download and cache it
            if video.thumbnail_url and not video.thumbnail_path:
                try:
                    from src.services.thumbnail_service import thumbnail_service

                    artist_name = video.artist.name if video.artist else "Unknown"
                    thumbnail_path = thumbnail_service.download_video_thumbnail(
                        artist_name, video.title, video.thumbnail_url
                    )

                    if thumbnail_path and os.path.exists(thumbnail_path):
                        # Update the database with the new thumbnail path
                        video.thumbnail_path = thumbnail_path
                        session.commit()
                        logger.info(
                            f"Downloaded and cached thumbnail for video {video_id}"
                        )
                        return send_file(thumbnail_path, as_attachment=False)

                except Exception as e:
                    logger.error(
                        f"Failed to download thumbnail for video {video_id}: {e}"
                    )

            # If we have a thumbnail URL but couldn't download, proxy it
            if video.thumbnail_url:
                try:
                    import requests

                    response = requests.get(
                        video.thumbnail_url, timeout=10, stream=True
                    )
                    if response.status_code == 200:
                        # Get content type from response
                        content_type = response.headers.get(
                            "Content-Type", "image/jpeg"
                        )

                        def generate():
                            for chunk in response.iter_content(chunk_size=8192):
                                yield chunk

                        return Response(generate(), content_type=content_type)

                except Exception as e:
                    logger.error(f"Failed to proxy thumbnail for video {video_id}: {e}")

            # Return placeholder if no thumbnail available
            placeholder_path = "frontend/static/placeholder-video.png"
            if os.path.exists(placeholder_path):
                return send_file(placeholder_path, as_attachment=False)

            return jsonify({"error": "Thumbnail not available"}), 404

    except Exception as e:
        logger.error(f"Failed to get thumbnail for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/refresh-thumbnails", methods=["POST"])
def refresh_thumbnails():
    """Download thumbnails for videos that have thumbnail_url but no thumbnail_path"""
    try:
        from src.services.thumbnail_service import thumbnail_service

        with get_db() as session:
            # Find videos with thumbnail_url but no thumbnail_path (include artist relationship)
            # Process YouTube and Google Images URLs, exclude IMVDb URLs that likely expire
            videos = (
                session.query(Video)
                .join(Artist)
                .filter(
                    Video.thumbnail_url.isnot(None),
                    Video.thumbnail_path.is_(None),
                    or_(
                        Video.thumbnail_url.like("%youtube%"),
                        Video.thumbnail_url.like("%googleusercontent%"),
                        Video.thumbnail_url.like("%google.com%"),
                    ),
                )
                .all()
            )

            downloaded_count = 0
            skipped_count = 0
            failed_count = 0

            for video in videos:
                try:
                    # Get the artist name for proper thumbnail naming
                    artist_name = video.artist.name if video.artist else "Unknown"

                    # Check if thumbnail file already exists before trying to download
                    from pathlib import Path

                    from src.services.settings_service import SettingsService

                    thumbnails_dir = SettingsService.get(
                        "thumbnails_path", "data/thumbnails"
                    )
                    expected_filename = thumbnail_service.generate_filename(
                        video.thumbnail_url
                    )
                    expected_path = (
                        Path(thumbnails_dir) / artist_name / expected_filename
                    )

                    file_already_exists = expected_path.exists()

                    thumbnail_path = thumbnail_service.download_video_thumbnail(
                        artist_name, video.title, video.thumbnail_url
                    )
                    if thumbnail_path:
                        video.thumbnail_path = thumbnail_path
                        if file_already_exists:
                            skipped_count += 1
                            logger.debug(
                                f"Skipped existing thumbnail for video: {video.title} by {artist_name}"
                            )
                        else:
                            downloaded_count += 1
                            logger.info(
                                f"Downloaded thumbnail for video: {video.title} by {artist_name}"
                            )
                    else:
                        failed_count += 1
                        logger.warning(
                            f"Failed to download thumbnail for video: {video.title}"
                        )

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to download thumbnail for video {video.title}: {e}"
                    )

            # Also count IMVDb URLs that we're intentionally not processing
            imvdb_videos = (
                session.query(Video)
                .filter(
                    Video.thumbnail_url.isnot(None),
                    Video.thumbnail_path.is_(None),
                    Video.thumbnail_url.like("%imvdb%"),
                )
                .count()
            )

            # Add IMVDb URLs to skipped count (separate from file-already-exists skips)
            imvdb_skipped_count = imvdb_videos

            session.commit()

            total_skipped = skipped_count + imvdb_skipped_count

            # Create detailed message
            message_parts = []
            if downloaded_count > 0:
                message_parts.append(f"Downloaded {downloaded_count} thumbnails")
            if skipped_count > 0:
                message_parts.append(f"skipped {skipped_count} existing files")
            if imvdb_skipped_count > 0:
                message_parts.append(
                    f"skipped {imvdb_skipped_count} IMVDb URLs (likely expired)"
                )
            if failed_count > 0:
                message_parts.append(f"failed {failed_count}")

            if not message_parts:
                message = "No thumbnails needed processing"
            else:
                message = ", ".join(message_parts).capitalize()

            return (
                jsonify(
                    {
                        "message": message,
                        "processed": len(videos) + imvdb_skipped_count,
                        "downloaded": downloaded_count,
                        "skipped": total_skipped,
                        "skipped_existing": skipped_count,
                        "skipped_imvdb": imvdb_skipped_count,
                        "failed": failed_count,
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to refresh thumbnails: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/thumbnail", methods=["PUT"])
def update_video_thumbnail(video_id):
    """Update video thumbnail URL or remove thumbnail"""
    try:
        data = request.get_json()
        thumbnail_url = data.get("thumbnail_url")
        action = data.get("action", "update")

        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            if action == "remove":
                # Remove thumbnail files and clear database fields
                from src.services.thumbnail_service import thumbnail_service

                if video.thumbnail_path:
                    thumbnail_service.delete_thumbnail_files(video.thumbnail_path)

                video.thumbnail_url = None
                video.thumbnail_path = None
                video.thumbnail_source = None
                video.thumbnail_metadata = None
                video.thumbnail_uploaded_at = None
                session.commit()

                logger.info(f"Removed thumbnail for video {video_id}")
                return jsonify({"message": "Thumbnail removed successfully"}), 200

            elif action == "update" and thumbnail_url:
                # Update thumbnail URL and clear cached path to force new download
                video.thumbnail_url = thumbnail_url
                video.thumbnail_source = "manual"
                # Clear cached thumbnail path so new URL will be used
                if video.thumbnail_path:
                    from src.services.thumbnail_service import thumbnail_service

                    thumbnail_service.delete_thumbnail_files(video.thumbnail_path)
                    video.thumbnail_path = None
                session.commit()

                logger.info(f"Updated thumbnail URL for video {video_id}")
                return jsonify({"message": "Thumbnail URL updated successfully"}), 200

            else:
                return (
                    jsonify({"error": "Invalid action or missing thumbnail_url"}),
                    400,
                )

    except Exception as e:
        logger.error(f"Failed to update thumbnail for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/thumbnail/upload", methods=["POST"])
def upload_video_thumbnail(video_id):
    """Upload a manual thumbnail file for a video"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            from src.services.thumbnail_service import thumbnail_service

            # Generate filename based on video info
            artist_name = video.artist.name if video.artist else "Unknown"
            # Ensure title is a string (fix for integer title issue)
            video_title = str(video.title) if video.title is not None else "Unknown"
            filename = f"{artist_name} - {video_title}".replace("/", "_")

            result = thumbnail_service.upload_manual_thumbnail(
                file, filename, entity_type="video"
            )

            if result["success"]:
                # Update video thumbnail information
                video.thumbnail_path = result["thumbnail_path"]
                video.thumbnail_url = (
                    None  # Clear external URL since we have local file
                )
                video.thumbnail_source = "manual"
                video.thumbnail_metadata = result["metadata"]
                video.thumbnail_uploaded_at = datetime.now()
                session.commit()

                logger.info(f"Uploaded manual thumbnail for video {video_id}")
                return (
                    jsonify(
                        {
                            "message": "Thumbnail uploaded successfully",
                            "thumbnail_path": result["thumbnail_path"],
                            "metadata": result["metadata"],
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"error": result["error"]}), 400

    except Exception as e:
        logger.error(f"Failed to upload thumbnail for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/thumbnail/crop", methods=["POST"])
def crop_video_thumbnail(video_id):
    """Crop existing video thumbnail"""
    try:
        data = request.get_json()
        crop_data = data.get("crop_data")

        if not crop_data:
            return jsonify({"error": "No crop data provided"}), 400

        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            if not video.thumbnail_path or not os.path.exists(video.thumbnail_path):
                return (
                    jsonify(
                        {"error": "No local thumbnail file available for cropping"}
                    ),
                    400,
                )

            from src.services.thumbnail_service import thumbnail_service

            result = thumbnail_service.crop_thumbnail(video.thumbnail_path, crop_data)

            if result["success"]:
                # Update video thumbnail metadata
                video.thumbnail_source = "manual_crop"
                video.thumbnail_metadata = result["metadata"]
                video.thumbnail_uploaded_at = datetime.now()
                session.commit()

                logger.info(f"Cropped thumbnail for video {video_id}")
                return (
                    jsonify(
                        {
                            "message": "Thumbnail cropped successfully",
                            "metadata": result["metadata"],
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"error": result["error"]}), 400

    except Exception as e:
        logger.error(f"Failed to crop thumbnail for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/thumbnail/search", methods=["POST"])
def search_video_thumbnails(video_id):
    """Search for video thumbnails using various sources"""
    try:
        data = request.get_json()
        search_query = data.get("search_query", "")
        sources = data.get("sources", ["youtube", "imvdb", "google"])

        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Capture video attributes while session is active
            artist_name = video.artist.name if video.artist else "Unknown"
            video_title = video.title
            video_url = video.url
            video_imvdb_id = video.imvdb_id

            # Use video info for search if no custom query provided
            if not search_query:
                search_query = f"{artist_name} {video_title}"

            results = []

            # 1. First check video URL for thumbnails (highest priority)
            youtube_id = None

            # Try to extract YouTube ID from existing URL if available
            if video_url:
                import re

                patterns = [
                    r"(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)",
                    r"youtube\.com/embed/([^&\n?#]+)",
                    r"(?:youtube\.com/v/|youtube\.com/watch\?.*&v=)([^&\n?#]+)",
                ]

                logger.debug(f"Checking video URL for YouTube ID: {video_url}")
                for pattern in patterns:
                    match = re.search(pattern, video_url)
                    if match:
                        youtube_id = match.group(1)
                        logger.info(
                            f"Extracted YouTube ID from video URL: {youtube_id}"
                        )
                        break

            # 2. Search YouTube by artist - song title if no URL or ID found
            if not youtube_id and "youtube" in sources:
                try:
                    logger.info(f"Searching YouTube for: {search_query}")
                    from src.services.youtube_service import youtube_service

                    search_results = youtube_service.search_videos(
                        search_query, max_results=1
                    )
                    if search_results["success"] and search_results["results"]:
                        # Get video ID from YouTube API response format
                        first_result = search_results["results"][0]
                        youtube_id = first_result["id"]["videoId"]
                        logger.info(f"Found YouTube video via search: {youtube_id}")
                except Exception as e:
                    logger.warning(f"YouTube search failed for '{search_query}': {e}")

            # Add YouTube thumbnails if we have an ID (from URL or search)
            if youtube_id and "youtube" in sources:
                try:
                    yt_thumbnails = [
                        {
                            "url": f"https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg",
                            "source": "youtube",
                            "quality": "maxres",
                            "title": f"{video_title} - Max Resolution",
                        },
                        {
                            "url": f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg",
                            "source": "youtube",
                            "quality": "hq",
                            "title": f"{video_title} - High Quality",
                        },
                        {
                            "url": f"https://img.youtube.com/vi/{youtube_id}/mqdefault.jpg",
                            "source": "youtube",
                            "quality": "mq",
                            "title": f"{video_title} - Medium Quality",
                        },
                    ]
                    results.extend(yt_thumbnails)
                    logger.info(
                        f"Added {len(yt_thumbnails)} YouTube thumbnail options for video {video_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to create YouTube thumbnails for video {video_id}: {e}"
                    )

            # Search IMVDb
            if "imvdb" in sources:
                try:
                    from src.services.imvdb_service import imvdb_service

                    video_details = None

                    # First try to get by existing IMVDb ID
                    if video_imvdb_id:
                        video_details = imvdb_service.get_video_by_id(video_imvdb_id)
                        logger.debug(f"Retrieved IMVDb data using ID: {video_imvdb_id}")

                    # If no ID or no details found, try searching
                    if not video_details:
                        logger.info(f"No IMVDb ID found, searching for: {search_query}")
                        try:
                            search_result = imvdb_service.find_best_video_match(
                                artist_name, video_title
                            )
                            if search_result:
                                video_details = search_result
                                logger.info(f"Found IMVDb video via search")
                        except Exception as search_e:
                            logger.debug(f"IMVDb search failed: {search_e}")

                    if video_details:
                        # Extract thumbnail metadata using existing extract_metadata method
                        metadata = imvdb_service.extract_metadata(video_details)
                        thumbnail_url = metadata.get("thumbnail_url")

                        if thumbnail_url:
                            imvdb_thumbnails = [
                                {
                                    "url": thumbnail_url,
                                    "source": "imvdb",
                                    "quality": "original",
                                    "title": f"{video_title} - IMVDb Original",
                                }
                            ]
                            results.extend(imvdb_thumbnails)
                            logger.info(
                                f"Found IMVDb thumbnail for video {video_id}: {thumbnail_url}"
                            )
                        else:
                            logger.debug(
                                f"No thumbnail URL found in IMVDb data for video {video_id}"
                            )
                    else:
                        logger.info(f"No IMVDb thumbnails found for: {search_query}")
                except Exception as e:
                    logger.warning(
                        f"Failed to get IMVDb thumbnails for video {video_id}: {e}"
                    )

            # Search Google Images
            if "google" in sources:
                try:
                    logger.info(f"Searching Google Images for: {search_query}")

                    # Use requests to search Google Images
                    from urllib.parse import quote

                    import requests

                    # Format query for image search
                    image_query = f"{search_query} music video thumbnail"
                    encoded_query = quote(image_query)

                    # Google Images search URL
                    search_url = f"https://www.google.com/search?q={encoded_query}&tbm=isch&safe=off"

                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }

                    response = requests.get(search_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        # Simple regex to extract image URLs from the page
                        import re

                        # Look for image URLs in the page content
                        image_pattern = r'"(https?://[^"]*\.(?:jpg|jpeg|png|webp))"'
                        matches = re.findall(image_pattern, response.text)

                        # Filter and clean up the results
                        google_thumbnails = []
                        seen_urls = set()

                        for match in matches[:6]:  # Limit to first 6 results
                            if match not in seen_urls and "encrypted" not in match:
                                seen_urls.add(match)
                                google_thumbnails.append(
                                    {
                                        "url": match,
                                        "source": "google",
                                        "quality": "varies",
                                        "title": f"{video_title} - Google Images",
                                    }
                                )

                        if google_thumbnails:
                            results.extend(google_thumbnails)
                            logger.info(
                                f"Added {len(google_thumbnails)} Google Images results for video {video_id}"
                            )
                        else:
                            logger.info(
                                f"No Google Images results found for: {search_query}"
                            )
                    else:
                        logger.warning(
                            f"Google Images search failed with status: {response.status_code}"
                        )

                except Exception as e:
                    logger.warning(
                        f"Failed to search Google Images for video {video_id}: {e}"
                    )

            logger.info(
                f"Found {len(results)} thumbnail options for video {video_id} (query: '{search_query}', sources: {sources})"
            )

        # Add debugging info for empty results
        if not results:
            debug_info = {
                "video_url": video_url,
                "imvdb_id": video_imvdb_id,
                "sources_requested": sources,
                "has_youtube_url": bool(
                    video_url
                    and ("youtube.com" in video_url or "youtu.be" in video_url)
                ),
                "has_imvdb_id": bool(video_imvdb_id),
            }
            logger.warning(
                f"No thumbnail results found for video {video_id}. Debug info: {debug_info}"
            )

        return (
            jsonify(
                {
                    "results": results,
                    "query": search_query,
                    "sources_searched": sources,
                    "total_results": len(results),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to search thumbnails for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/thumbnail/info", methods=["GET"])
def get_video_thumbnail_info(video_id):
    """Get detailed thumbnail information for a video"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            from src.services.thumbnail_service import thumbnail_service

            info = {
                "has_thumbnail": bool(video.thumbnail_url or video.thumbnail_path),
                "thumbnail_url": video.thumbnail_url,
                "thumbnail_path": video.thumbnail_path,
                "thumbnail_source": video.thumbnail_source,
                "thumbnail_uploaded_at": video.thumbnail_uploaded_at.isoformat()
                if video.thumbnail_uploaded_at
                else None,
                "thumbnail_metadata": video.thumbnail_metadata,
            }

            # Get file information if local thumbnail exists
            if video.thumbnail_path and os.path.exists(video.thumbnail_path):
                file_info = thumbnail_service.get_thumbnail_info(video.thumbnail_path)
                info.update(file_info)

            return jsonify(info), 200

    except Exception as e:
        logger.error(f"Failed to get thumbnail info for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/thumbnail/<size>", methods=["GET"])
def get_video_thumbnail_size(video_id, size):
    """Get specific size of video thumbnail (small/medium/large/original)"""
    try:
        if size not in ["small", "medium", "large", "original"]:
            return (
                jsonify(
                    {"error": "Invalid size. Use: small, medium, large, or original"}
                ),
                400,
            )

        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            if not video.thumbnail_path:
                return jsonify({"error": "No local thumbnail available"}), 404

            from src.services.thumbnail_service import thumbnail_service

            # Get the specific size path
            size_path = thumbnail_service.get_thumbnail_size_path(
                video.thumbnail_path, size
            )

            if size_path and os.path.exists(size_path):
                return send_file(size_path, as_attachment=False)
            else:
                # Fallback to original if specific size doesn't exist
                if os.path.exists(video.thumbnail_path):
                    return send_file(video.thumbnail_path, as_attachment=False)
                else:
                    return jsonify({"error": "Thumbnail file not found"}), 404

    except Exception as e:
        logger.error(f"Failed to get thumbnail size {size} for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/stream", methods=["GET"])
def stream_video(video_id):
    """Stream local video file with HTTP range support for better video playback"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Check if we have a local file
            if video.local_path:
                # Construct absolute path
                if os.path.isabs(video.local_path):
                    full_path = video.local_path
                else:
                    # Relative path - construct from app root
                    full_path = os.path.join(os.getcwd(), video.local_path)

                if os.path.exists(full_path):
                    # Check if this is an MKV file that needs transcoding
                    if full_path.lower().endswith(".mkv") or full_path.lower().endswith(
                        ".avi"
                    ):
                        # Use FFmpeg streaming for MKV/AVI files
                        from src.services.ffmpeg_streaming_service import (
                            ffmpeg_streaming_service,
                        )

                        return ffmpeg_streaming_service.stream_video(full_path)

                    # Get MIME type based on file extension
                    mime_type, _ = mimetypes.guess_type(full_path)

                    # Set default MIME type if not detected
                    if not mime_type:
                        # Common video formats
                        if full_path.lower().endswith(".mp4"):
                            mime_type = "video/mp4"
                        elif full_path.lower().endswith(".webm"):
                            mime_type = "video/webm"
                        elif full_path.lower().endswith(".mkv"):
                            mime_type = "video/x-matroska"
                        elif full_path.lower().endswith(".avi"):
                            mime_type = "video/x-msvideo"
                        elif full_path.lower().endswith(".mov"):
                            mime_type = "video/quicktime"
                        else:
                            mime_type = "video/mp4"  # Default fallback

                    logger.info(
                        f"Serving video {video.title} from {full_path} with MIME type: {mime_type}"
                    )

                    # Always use send_file for simplicity - let Flask handle the range requests
                    return send_file(
                        full_path,
                        as_attachment=False,
                        mimetype=mime_type,
                        conditional=True,  # This enables range request support in Flask
                    )

                else:
                    # File not found at stored path - try to locate it in artist folders
                    logger.warning(f"Video file not found at stored path: {full_path}")

                    # Try to find the file in the expected artist folder
                    relocated_path = find_relocated_video(video, session)
                    if relocated_path:
                        logger.info(f"Found relocated video at: {relocated_path}")
                        # Update the database with the correct path
                        video.local_path = relocated_path
                        session.commit()

                        # Serve the relocated file
                        mime_type, _ = mimetypes.guess_type(relocated_path)
                        if not mime_type:
                            if relocated_path.lower().endswith(".mp4"):
                                mime_type = "video/mp4"
                            elif relocated_path.lower().endswith(".mkv"):
                                mime_type = "video/x-matroska"
                            else:
                                mime_type = "video/mp4"

                        return send_file(
                            relocated_path,
                            as_attachment=False,
                            mimetype=mime_type,
                            conditional=True,
                        )
                    else:
                        # File truly missing - mark as wanted and track artist
                        logger.error(
                            f"Video file not found and could not be relocated: {full_path}"
                        )

                        # Mark video as wanted if it was previously downloaded
                        if video.status == VideoStatus.DOWNLOADED:
                            video.status = VideoStatus.WANTED
                            video.local_path = None
                            session.commit()
                            logger.info(
                                f"Marked missing video as wanted: {video.title}"
                            )

                            # Ensure artist is being tracked
                            if video.artist:
                                video.artist.monitored = True
                                session.commit()
                                logger.info(
                                    f"Enabled monitoring for artist: {video.artist.name}"
                                )

                        return (
                            jsonify(
                                {
                                    "error": "Video file not found",
                                    "message": "File has been marked as wanted and will be re-downloaded",
                                    "status": "wanted",
                                }
                            ),
                            404,
                        )

            return jsonify({"error": "Local video file not found"}), 404

    except Exception as e:
        logger.error(f"Failed to stream video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/recovery/fix-missing", methods=["POST"])
def fix_missing_downloaded_videos():
    """Fix all videos marked as downloaded but with missing files"""
    try:
        from src.services.video_recovery_service import video_recovery_service

        # Run the fix operation
        stats = video_recovery_service.fix_missing_downloaded_videos()

        logger.info(f"Missing downloaded videos fix completed: {stats}")

        message = f"Fixed {stats['missing_files']} missing videos: "
        message += f"{stats['recovered_videos']} recovered, {stats['marked_wanted']} marked as wanted"

        return jsonify({"success": True, "message": message, "statistics": stats})

    except Exception as e:
        logger.error(f"Error fixing missing downloaded videos: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/recovery/scan", methods=["POST"])
def scan_missing_videos():
    """Scan for missing videos and attempt recovery"""
    try:
        from src.services.video_recovery_service import video_recovery_service

        # Run the recovery scan
        stats = video_recovery_service.scan_missing_videos()

        logger.info(f"Video recovery scan completed: {stats}")

        return jsonify(
            {
                "success": True,
                "message": "Video recovery scan completed",
                "statistics": stats,
            }
        )

    except Exception as e:
        logger.error(f"Error during video recovery scan: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/recovery/orphans", methods=["POST"])
def scan_orphaned_files():
    """Scan for orphaned video files without database records"""
    try:
        from src.services.video_recovery_service import video_recovery_service

        # Run the orphaned files scan
        stats = video_recovery_service.scan_orphaned_files()

        logger.info(f"Orphaned files scan completed: {stats}")

        return jsonify(
            {
                "success": True,
                "message": "Orphaned files scan completed",
                "statistics": stats,
            }
        )

    except Exception as e:
        logger.error(f"Error during orphaned files scan: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/transcode", methods=["POST"])
def transcode_video(video_id):
    """Transcode video to MP4 format for better browser compatibility"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            if not video.local_path:
                return (
                    jsonify({"error": "No local file available for transcoding"}),
                    400,
                )

            # Construct absolute path
            if os.path.isabs(video.local_path):
                source_path = video.local_path
            else:
                source_path = os.path.join(os.getcwd(), video.local_path)

            if not os.path.exists(source_path):
                return jsonify({"error": "Source video file not found"}), 404

            # Check if already an MP4
            if source_path.lower().endswith(".mp4"):
                return jsonify({"error": "Video is already in MP4 format"}), 400

            # Generate output path
            source_dir = os.path.dirname(source_path)
            source_name = Path(source_path).stem
            output_path = os.path.join(source_dir, f"{source_name}_transcoded.mp4")

            # Check if transcoded version already exists
            if os.path.exists(output_path):
                return jsonify({"error": "Transcoded version already exists"}), 400

            # Start transcoding in background thread
            def transcode_worker():
                try:
                    logger.info(f"Starting transcoding: {source_path} -> {output_path}")

                    # FFmpeg command for transcoding
                    cmd = [
                        "ffmpeg",
                        "-i",
                        source_path,  # Input file
                        "-c:v",
                        "libx264",  # Video codec
                        "-crf",
                        "23",  # Quality (18-28, 23 is good balance)
                        "-preset",
                        "medium",  # Encoding speed vs compression
                        "-c:a",
                        "aac",  # Audio codec
                        "-b:a",
                        "128k",  # Audio bitrate
                        "-movflags",
                        "+faststart",  # Web optimization
                        "-y",  # Overwrite output file
                        output_path,
                    ]

                    # Run ffmpeg
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=3600,  # 1 hour timeout
                    )

                    if result.returncode == 0:
                        logger.info(
                            f"Transcoding completed successfully: {output_path}"
                        )

                        # Update database with transcoded path
                        with get_db() as update_session:
                            update_video = (
                                update_session.query(Video)
                                .filter(Video.id == video_id)
                                .first()
                            )
                            if update_video:
                                # Store relative path for transcoded file
                                relative_output = os.path.relpath(
                                    output_path, os.getcwd()
                                )
                                update_video.local_path = relative_output
                                update_session.commit()
                                logger.info(
                                    f"Updated video {video_id} with transcoded path: {relative_output}"
                                )
                    else:
                        logger.error(
                            f"Transcoding failed for video {video_id}: {result.stderr}"
                        )

                        # Clean up failed output file
                        if os.path.exists(output_path):
                            os.remove(output_path)

                except subprocess.TimeoutExpired:
                    logger.error(f"Transcoding timeout for video {video_id}")
                except Exception as e:
                    logger.error(f"Transcoding error for video {video_id}: {e}")
                    if os.path.exists(output_path):
                        os.remove(output_path)

            # Start transcoding in background
            thread = threading.Thread(target=transcode_worker)
            thread.daemon = True
            thread.start()

            return (
                jsonify(
                    {
                        "message": "Transcoding started",
                        "video_id": video_id,
                        "source_file": source_path,
                        "output_file": output_path,
                        "status": "processing",
                    }
                ),
                202,
            )

    except Exception as e:
        logger.error(f"Failed to start transcoding for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/transcode/status", methods=["GET"])
def transcode_status(video_id):
    """Check transcoding status for a video"""
    try:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            if not video.local_path:
                return jsonify({"status": "no_file"}), 200

            # Check if current file is MP4
            if video.local_path.lower().endswith(".mp4"):
                return jsonify({"status": "completed", "format": "mp4"}), 200

            # Check for transcoded version
            if os.path.isabs(video.local_path):
                source_path = video.local_path
            else:
                source_path = os.path.join(os.getcwd(), video.local_path)

            source_dir = os.path.dirname(source_path)
            source_name = Path(source_path).stem
            transcoded_path = os.path.join(source_dir, f"{source_name}_transcoded.mp4")

            if os.path.exists(transcoded_path):
                return (
                    jsonify(
                        {"status": "completed", "transcoded_file": transcoded_path}
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "not_started",
                            "format": Path(video.local_path).suffix,
                        }
                    ),
                    200,
                )

    except Exception as e:
        logger.error(f"Failed to check transcoding status for video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/refresh-metadata", methods=["POST"])
def refresh_video_metadata(video_id):
    """Refresh metadata from IMVDb for a specific video"""
    try:
        from src.services.imvdb_service import imvdb_service
        from src.services.settings_service import settings

        # Force reload settings cache to ensure we have the latest API key
        settings.reload_cache()
        # IMVDb service will get the API key from settings automatically

        # First, get video data and close session to avoid binding issues
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Extract data we need before closing session
            artist_name = video.artist.name if video.artist else None
            video_title = video.title
            current_imvdb_id = video.imvdb_id

            if not artist_name:
                return jsonify({"error": "No artist associated with video"}), 400

        # Now perform external API calls without holding the session
        logger.info(f"Refreshing metadata for video: {video_title} by {artist_name}")

        # Try to find best match on IMVDb
        imvdb_data = None

        # If we have an existing IMVDb ID, try to get detailed info
        if current_imvdb_id:
            logger.info(
                f"Attempting to refresh using existing IMVDb ID: {current_imvdb_id}"
            )
            imvdb_data = imvdb_service.get_video_by_id(current_imvdb_id)

        # If no IMVDb ID or the lookup failed, try searching
        if not imvdb_data:
            logger.info(f"Searching for new match: {artist_name} - {video_title}")
            imvdb_data = imvdb_service.find_best_video_match(artist_name, video_title)

        # If IMVDb search failed, try YouTube as fallback
        youtube_metadata = None
        if not imvdb_data:
            try:
                logger.info(
                    f"IMVDb search failed, trying YouTube: {artist_name} - {video_title}"
                )
                from src.services.youtube_service import youtube_service

                search_query = f"{artist_name} {video_title}"
                youtube_results = youtube_service.search_videos(
                    search_query, max_results=1
                )

                if youtube_results["success"] and youtube_results["results"]:
                    video_item = youtube_results["results"][0]
                    video_id_yt = video_item["id"]["videoId"]

                    # Get detailed video information
                    video_details = youtube_service.get_video_details(video_id_yt)
                    if video_details["success"] and video_details.get("video"):
                        yt_video = video_details["video"]

                        # Extract metadata from YouTube
                        snippet = yt_video.get("snippet", {})
                        youtube_metadata = {
                            "source": "youtube",
                            "youtube_id": video_id_yt,
                            "title": snippet.get("title", video_title),
                            "description": snippet.get("description", ""),
                            "published_at": snippet.get("publishedAt"),
                            "thumbnail_url": snippet.get("thumbnails", {})
                            .get("high", {})
                            .get("url"),
                            "channel_title": snippet.get("channelTitle"),
                            "tags": snippet.get("tags", []),
                        }
                        logger.info(f"Found YouTube metadata for: {video_title}")

            except Exception as e:
                logger.warning(f"YouTube metadata search failed: {e}")

        if not imvdb_data and not youtube_metadata:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "No matching video found on IMVDb or YouTube",
                        "searched_for": f"{artist_name} - {video_title}",
                    }
                ),
                404,
            )

        # Extract and update metadata
        if imvdb_data:
            metadata = imvdb_service.extract_metadata(imvdb_data)
            metadata_source = "IMVDb"
        else:
            # Use YouTube metadata
            metadata = youtube_metadata
            metadata_source = "YouTube"

        # Now update the video in a fresh session
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return (
                    jsonify({"error": "Video was deleted during metadata refresh"}),
                    404,
                )

            # Update video with new metadata based on source
            if metadata_source == "IMVDb":
                video.imvdb_id = metadata.get("imvdb_id")
                if metadata.get("year"):
                    video.year = metadata["year"]
                if metadata.get("thumbnail_url"):
                    video.thumbnail_url = metadata["thumbnail_url"]
                if metadata.get("directors"):
                    video.directors = metadata["directors"]
                if metadata.get("producers"):
                    video.producers = metadata["producers"]

                # Store full IMVDb metadata
                video.imvdb_metadata = metadata.get("raw_metadata", {})
            else:
                # YouTube metadata
                if metadata.get("youtube_id"):
                    video.youtube_id = metadata["youtube_id"]
                    # Update URL if we don't have one
                    if not video.url:
                        video.url = (
                            f"https://www.youtube.com/watch?v={metadata['youtube_id']}"
                        )
                if metadata.get("thumbnail_url"):
                    video.thumbnail_url = metadata["thumbnail_url"]
                if metadata.get("published_at"):
                    # Extract year from published date
                    try:
                        from datetime import datetime

                        published_date = datetime.fromisoformat(
                            metadata["published_at"].replace("Z", "+00:00")
                        )
                        video.year = published_date.year
                    except:
                        pass

                # Store YouTube metadata in custom field or use existing metadata field
                video.youtube_metadata = metadata

            session.commit()

            logger.info(f"Successfully updated metadata for video {video_id}")

            # Return updated video data
            updated_video = {
                "id": video.id,
                "title": video.title,
                "artist_id": video.artist_id,
                "artist_name": video.artist.name if video.artist else None,
                "status": video.status.value
                if hasattr(video.status, "value")
                else video.status,
                "imvdb_id": video.imvdb_id,
                "video_url": video.url,
                "local_path": video.local_path,
                "thumbnail_url": video.thumbnail_url,
                "duration": video.duration,
                "year": video.year,
                "directors": video.directors,
                "producers": video.producers,
                "created_at": video.created_at.isoformat(),
                "metadata_refreshed": True,
                "metadata_source": metadata_source,
                "youtube_id": video.youtube_id
                if hasattr(video, "youtube_id")
                else None,
            }

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Metadata refreshed successfully from {metadata_source}",
                        "video": updated_video,
                        "metadata_match": metadata,
                        "source": metadata_source,
                    }
                ),
                200,
            )

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logger.error(f"Failed to refresh metadata for video {video_id}: {e}")
        logger.error(f"Full traceback: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500


@videos_bp.route("/fix-title-artist-swap", methods=["POST"])
def fix_title_artist_swap():
    """Fix videos where song title is in artist field and title is 'video'"""
    try:
        from src.database.models import Artist

        # Get request parameters
        data = request.get_json() or {}
        dry_run = data.get("dry_run", True)  # Default to dry run for safety
        limit = data.get("limit", None)  # Optional limit for testing

        with get_db() as session:
            # Find videos with title 'video' (case insensitive)
            query = session.query(Video).filter(Video.title.ilike("video"))

            if limit:
                query = query.limit(limit)

            problematic_videos = query.all()

            if not problematic_videos:
                return (
                    jsonify(
                        {
                            "success": True,
                            "message": 'No videos found with title "video"',
                            "processed": 0,
                            "fixed": 0,
                            "errors": 0,
                        }
                    ),
                    200,
                )

            logger.info(f"Found {len(problematic_videos)} videos with title 'video'")

            processed = 0
            fixed = 0
            errors = 0
            changes = []
            error_details = []

            for video in problematic_videos:
                # Capture video data while session is active
                video_id = video.id
                current_artist_name = video.artist.name if video.artist else None
                current_title = video.title

                try:
                    processed += 1

                    # Skip if we don't have an artist name to swap
                    if not current_artist_name:
                        logger.warning(f"Video {video_id} has no artist name to swap")
                        continue

                    # Skip if the artist name looks like an actual artist (common artists)
                    common_artists = [
                        "Unknown",
                        "Various Artists",
                        "Compilation",
                        "Soundtrack",
                    ]
                    if current_artist_name in common_artists:
                        logger.debug(
                            f"Skipping video {video_id} - artist name '{current_artist_name}' looks like actual artist"
                        )
                        continue

                    # The fix: swap artist name and title
                    new_title = current_artist_name  # Move artist name to title
                    new_artist_name = (
                        "Unknown"  # Reset artist to Unknown (will be fixed later)
                    )

                    # Try to extract actual artist from the current artist name if it contains " - "
                    if " - " in current_artist_name:
                        parts = current_artist_name.split(" - ", 1)
                        if len(parts) == 2:
                            new_artist_name = parts[0].strip()
                            new_title = parts[1].strip()

                    change_record = {
                        "video_id": video_id,
                        "old_artist": current_artist_name,
                        "old_title": current_title,
                        "new_artist": new_artist_name,
                        "new_title": new_title,
                    }

                    if not dry_run:
                        # Find or create the new artist
                        if new_artist_name != "Unknown":
                            artist = (
                                session.query(Artist)
                                .filter(Artist.name == new_artist_name)
                                .first()
                            )
                            if not artist:
                                artist = Artist(name=new_artist_name)
                                session.add(artist)
                                session.flush()  # Get the artist ID
                            video.artist_id = artist.id

                        # Update the title
                        video.title = new_title

                        # Log the change
                        logger.info(
                            f"Fixed video {video_id}: '{current_artist_name}' -> '{new_artist_name}' | '{current_title}' -> '{new_title}'"
                        )

                        # Commit periodically to avoid long transactions
                        if processed % 50 == 0:
                            session.commit()

                    changes.append(change_record)
                    fixed += 1

                except Exception as e:
                    errors += 1
                    error_msg = str(e)
                    logger.error(f"Error processing video {video_id}: {error_msg}")
                    error_details.append({"video_id": video_id, "error": error_msg})

            # Final commit if not dry run
            if not dry_run:
                session.commit()

            logger.info(
                f"Title/Artist swap {'dry run' if dry_run else 'fix'} completed: {processed} processed, {fixed} fixed, {errors} errors"
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f'Title/Artist swap {"dry run" if dry_run else "fix"} completed',
                        "dry_run": dry_run,
                        "processed": processed,
                        "fixed": fixed,
                        "errors": errors,
                        "changes": changes[:20]
                        if dry_run
                        else [],  # Show first 20 changes for dry run
                        "error_details": error_details[:10] if error_details else [],
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to fix title/artist swap: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/refresh-all-metadata", methods=["POST"])
def refresh_all_metadata():
    """Refresh metadata from IMVDb for all videos"""
    try:
        from src.services.imvdb_service import imvdb_service
        from src.services.settings_service import settings

        # Force reload settings cache to ensure we have the latest API key
        settings.reload_cache()
        # IMVDb service will get the API key from settings automatically

        # Get request parameters
        data = request.get_json() or {}
        force_refresh = data.get(
            "force_refresh", False
        )  # Refresh even if IMVDb ID exists
        limit = data.get("limit", None)  # Limit number of videos to process

        processed = 0
        updated = 0
        errors = 0
        error_details = []

        with get_db() as session:
            query = session.query(Video).join(Video.artist)

            # If not forcing refresh, only process videos without IMVDb metadata
            if not force_refresh:
                query = query.filter(Video.imvdb_id.is_(None))

            if limit:
                query = query.limit(limit)

            videos = query.all()

            if not videos:
                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "No videos found to refresh",
                            "processed": 0,
                            "updated": 0,
                            "errors": 0,
                        }
                    ),
                    200,
                )

            logger.info(f"Starting metadata refresh for {len(videos)} videos")

            for video in videos:
                # Capture video data while session is active
                video_id = video.id
                video_title = video.title
                artist_name = video.artist.name if video.artist else None
                imvdb_id = video.imvdb_id

                try:
                    processed += 1

                    if not artist_name:
                        logger.warning(
                            f"Skipping video {video_id}: No artist associated"
                        )
                        errors += 1
                        error_details.append(
                            {
                                "video_id": video_id,
                                "title": video_title,
                                "error": "No artist associated",
                            }
                        )
                        continue

                    logger.info(
                        f"Processing {processed}/{len(videos)}: {video_title} by {artist_name}"
                    )

                    # Try to find match on IMVDb
                    imvdb_data = None

                    # If forcing refresh and we have an IMVDb ID, try to get detailed info
                    if force_refresh and imvdb_id:
                        imvdb_data = imvdb_service.get_video_by_id(imvdb_id)

                    # If no IMVDb data yet, try searching
                    if not imvdb_data:
                        imvdb_data = imvdb_service.find_best_video_match(
                            artist_name, video_title
                        )

                    # Try YouTube as fallback if IMVDb failed
                    youtube_metadata = None
                    if not imvdb_data:
                        try:
                            logger.debug(
                                f"Trying YouTube fallback for: {video_title} by {artist_name}"
                            )
                            from src.services.youtube_service import youtube_service

                            search_query = f"{artist_name} {video_title}"
                            youtube_results = youtube_service.search_videos(
                                search_query, max_results=1
                            )

                            if (
                                youtube_results["success"]
                                and youtube_results["results"]
                            ):
                                video_item = youtube_results["results"][0]
                                video_id_yt = video_item["id"]["videoId"]

                                # Get detailed video information
                                video_details = youtube_service.get_video_details(
                                    video_id_yt
                                )
                                if video_details["success"] and video_details.get(
                                    "video"
                                ):
                                    yt_video = video_details["video"]

                                    # Extract metadata from YouTube
                                    snippet = yt_video.get("snippet", {})
                                    youtube_metadata = {
                                        "source": "youtube",
                                        "youtube_id": video_id_yt,
                                        "title": snippet.get("title", video_title),
                                        "description": snippet.get("description", ""),
                                        "published_at": snippet.get("publishedAt"),
                                        "thumbnail_url": snippet.get("thumbnails", {})
                                        .get("high", {})
                                        .get("url"),
                                        "channel_title": snippet.get("channelTitle"),
                                        "tags": snippet.get("tags", []),
                                    }

                        except Exception as yt_e:
                            logger.debug(
                                f"YouTube search failed for {video_title}: {yt_e}"
                            )

                    if imvdb_data:
                        # Extract and update metadata from IMVDb
                        metadata = imvdb_service.extract_metadata(imvdb_data)

                        # Update video with new metadata
                        video.imvdb_id = metadata.get("imvdb_id")
                        if metadata.get("year"):
                            video.year = metadata["year"]
                        if metadata.get("thumbnail_url"):
                            video.thumbnail_url = metadata["thumbnail_url"]
                        if metadata.get("directors"):
                            video.directors = metadata["directors"]
                        if metadata.get("producers"):
                            video.producers = metadata["producers"]

                        # Store full IMVDb metadata
                        video.imvdb_metadata = metadata.get("raw_metadata", {})

                        updated += 1
                        logger.info(f"Updated metadata for: {video_title} (IMVDb)")

                    elif youtube_metadata:
                        # Update with YouTube metadata
                        if youtube_metadata.get("youtube_id"):
                            video.youtube_id = youtube_metadata["youtube_id"]
                            # Update URL if we don't have one
                            if not video.url:
                                video.url = f"https://www.youtube.com/watch?v={youtube_metadata['youtube_id']}"
                        if youtube_metadata.get("thumbnail_url"):
                            video.thumbnail_url = youtube_metadata["thumbnail_url"]
                        if youtube_metadata.get("published_at"):
                            # Extract year from published date
                            try:
                                from datetime import datetime

                                published_date = datetime.fromisoformat(
                                    youtube_metadata["published_at"].replace(
                                        "Z", "+00:00"
                                    )
                                )
                                video.year = published_date.year
                            except:
                                pass

                        # Store YouTube metadata
                        video.youtube_metadata = youtube_metadata

                        updated += 1
                        logger.info(f"Updated metadata for: {video_title} (YouTube)")

                    else:
                        logger.debug(
                            f"No metadata found for: {video_title} by {artist_name}"
                        )

                    # Commit changes periodically to avoid long transactions
                    if processed % 10 == 0:
                        session.commit()

                except Exception as e:
                    errors += 1
                    error_msg = str(e)
                    logger.error(f"Error processing video {video_id}: {error_msg}")
                    error_details.append(
                        {"video_id": video_id, "title": video_title, "error": error_msg}
                    )

            # Final commit
            session.commit()

            logger.info(
                f"Metadata refresh completed: {processed} processed, {updated} updated, {errors} errors"
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Metadata refresh completed",
                        "processed": processed,
                        "updated": updated,
                        "errors": errors,
                        "error_details": error_details[:10]
                        if error_details
                        else [],  # Limit error details
                    }
                ),
                200,
            )

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logger.error(f"Failed to refresh all metadata: {e}")
        logger.error(f"Full traceback: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500


@videos_bp.route("/<int:video_id>", methods=["PUT"])
def update_video(video_id):
    """Update video metadata and optionally move/rename file"""
    try:
        data = request.get_json()

        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Store original values for file operations
            original_title = video.title
            original_artist_name = video.artist.name if video.artist else None
            original_local_path = video.local_path
            move_file = data.get("move_file", False)

            # Update video metadata
            if "title" in data and data["title"]:
                video.title = data["title"]
            if "year" in data:
                video.year = data["year"]
            if "status" in data and data["status"]:
                video.status = data["status"]
            if "video_url" in data:
                video.url = data["video_url"]
            if "thumbnail_url" in data:
                video.thumbnail_url = data["thumbnail_url"]
            if "duration" in data:
                video.duration = data["duration"]
            if "imvdb_id" in data:
                video.imvdb_id = data["imvdb_id"]
            if "genres" in data:
                video.genres = data["genres"]

            # Handle artist name change
            new_artist_name = data.get("artist_name")
            if new_artist_name and new_artist_name != original_artist_name:
                # Find or create artist
                from src.database.models import Artist

                artist = (
                    session.query(Artist).filter(Artist.name == new_artist_name).first()
                )
                if not artist:
                    artist = Artist(name=new_artist_name)
                    session.add(artist)
                    session.flush()  # Get the artist ID
                video.artist_id = artist.id

            # Handle file moving/renaming if requested
            new_local_path = original_local_path
            if move_file and original_local_path:
                new_local_path = _move_and_rename_video_file(
                    original_local_path,
                    new_artist_name or original_artist_name,
                    video.title,
                    original_title,
                    original_artist_name,
                )
                if new_local_path != original_local_path:
                    video.local_path = new_local_path

            session.commit()

            # Update artist genres if video genres were changed
            if "genres" in data and video.artist_id:
                try:
                    from src.services.genre_service import genre_service

                    # Use the same session for genre operations
                    genre_service._update_artist_genres_with_session(
                        video.artist_id, session
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to update artist genres for video {video_id}: {e}"
                    )

            # Return updated video data
            updated_video = {
                "id": video.id,
                "title": video.title,
                "artist_id": video.artist_id,
                "artist_name": video.artist.name if video.artist else None,
                "status": video.status.value
                if hasattr(video.status, "value")
                else video.status,
                "imvdb_id": video.imvdb_id,
                "video_url": video.url,
                "local_path": video.local_path,
                "thumbnail_url": video.thumbnail_url,
                "duration": video.duration,
                "year": video.year,
                "genres": video.genres,
                "created_at": video.created_at.isoformat(),
                "file_moved": new_local_path != original_local_path,
            }

            logger.info(
                f"Updated video {video_id}: {video.title} by {video.artist.name if video.artist else 'Unknown'}"
            )

            return jsonify(updated_video), 200

    except Exception as e:
        logger.error(f"Failed to update video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500


def _move_and_rename_video_file(
    original_path, new_artist_name, new_title, original_title, original_artist_name
):
    """
    Move and rename video file based on new metadata
    Returns the new file path
    """
    try:
        # Skip if no actual changes
        if new_artist_name == original_artist_name and new_title == original_title:
            return original_path

        # Construct absolute path
        if os.path.isabs(original_path):
            current_file_path = original_path
        else:
            current_file_path = os.path.join(os.getcwd(), original_path)

        if not os.path.exists(current_file_path):
            logger.warning(f"Original file not found: {current_file_path}")
            return original_path

        # Get file extension
        file_extension = os.path.splitext(current_file_path)[1]

        # Clean names for filename
        clean_artist = _clean_filename(new_artist_name)
        clean_title = _clean_filename(new_title)

        # Create new directory structure
        base_dir = os.path.dirname(
            os.path.dirname(current_file_path)
        )  # Go up from artist folder
        new_artist_dir = os.path.join(base_dir, clean_artist)

        # Create artist directory if it doesn't exist
        os.makedirs(new_artist_dir, exist_ok=True)

        # Create new filename
        new_filename = f"{clean_artist} - {clean_title}{file_extension}"
        new_file_path = os.path.join(new_artist_dir, new_filename)

        # Move and rename the file
        if current_file_path != new_file_path:
            os.rename(current_file_path, new_file_path)
            logger.info(f"Moved file from {current_file_path} to {new_file_path}")

            # Try to remove old artist directory if it's empty
            old_artist_dir = os.path.dirname(current_file_path)
            try:
                if os.path.exists(old_artist_dir) and not os.listdir(old_artist_dir):
                    os.rmdir(old_artist_dir)
                    logger.info(f"Removed empty directory: {old_artist_dir}")
            except OSError:
                pass  # Directory not empty or other error

        # Return relative path
        return os.path.relpath(new_file_path, os.getcwd())

    except Exception as e:
        logger.error(f"Failed to move/rename file {original_path}: {e}")
        return original_path  # Return original path if move fails


def _clean_filename(name):
    """Clean filename by removing invalid characters"""
    if not name:
        return "Unknown"

    # Replace invalid characters with underscores
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")

    # Remove extra whitespace and limit length
    name = " ".join(name.split())[:100]

    return name or "Unknown"


@videos_bp.route("/<int:video_id>/status", methods=["PUT"])
def update_video_status(video_id):
    """Update video status"""
    try:
        data = request.get_json()
        if not data or "status" not in data:
            return jsonify({"error": "Status is required"}), 400

        new_status = data["status"]

        # Validate status
        valid_statuses = ["WANTED", "DOWNLOADING", "DOWNLOADED", "FAILED", "IGNORED"]
        if new_status not in valid_statuses:
            return (
                jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}),
                400,
            )

        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()

            if not video:
                return jsonify({"error": "Video not found"}), 404

            old_status = (
                video.status.value if hasattr(video.status, "value") else video.status
            )
            video.status = VideoStatus[new_status]
            session.commit()

            logger.info(
                f"Updated video {video_id} status from {old_status} to {new_status}"
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Video status updated to {new_status}",
                        "video_id": video_id,
                        "old_status": old_status,
                        "new_status": new_status,
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to update video status: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/bulk/download", methods=["POST"])
def bulk_download_videos():
    """Download multiple videos"""
    try:
        data = request.get_json()
        if not data or "video_ids" not in data:
            return jsonify({"error": "video_ids array is required"}), 400

        video_ids = data["video_ids"]
        if not isinstance(video_ids, list):
            return jsonify({"error": "video_ids must be an array"}), 400

        results = []
        success_count = 0
        failed_count = 0

        with get_db() as session:
            for video_id in video_ids:
                try:
                    video = session.query(Video).filter(Video.id == video_id).first()

                    if not video:
                        results.append(
                            {
                                "video_id": video_id,
                                "success": False,
                                "error": "Video not found",
                            }
                        )
                        failed_count += 1
                        continue

                    # Resolve video URL using helper function
                    video_url = resolve_video_url(video, session)

                    if not video_url:
                        results.append(
                            {
                                "video_id": video_id,
                                "success": False,
                                "error": "No URL available for download",
                            }
                        )
                        failed_count += 1
                        continue

                    # Import yt-dlp service
                    from src.services.ytdlp_service import ytdlp_service

                    # Queue download
                    artist_name = video.artist.name if video.artist else "Unknown"
                    result = ytdlp_service.add_music_video_download(
                        artist=artist_name,
                        title=video.title,
                        url=video_url,
                        quality="best",
                        video_id=video_id,
                    )

                    if result and result.get("success"):
                        # Re-query the video object to ensure it's bound to the current session
                        video = (
                            session.query(Video).filter(Video.id == video_id).first()
                        )
                        if video:
                            video.status = VideoStatus.DOWNLOADING
                            session.commit()

                        results.append(
                            {
                                "video_id": video_id,
                                "success": True,
                                "title": video.title,
                                "download_id": result.get("id"),
                            }
                        )
                        success_count += 1
                    else:
                        error_msg = (
                            result.get("error", "Failed to queue download")
                            if result
                            else "MeTube service unavailable"
                        )
                        results.append(
                            {"video_id": video_id, "success": False, "error": error_msg}
                        )
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Failed to download video {video_id}: {e}")
                    results.append(
                        {"video_id": video_id, "success": False, "error": str(e)}
                    )
                    failed_count += 1

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Bulk download completed: {success_count} success, {failed_count} failed",
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "results": results,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to bulk download videos: {e}")
        return jsonify({"error": str(e)}), 500


def download_all_wanted_videos_internal(limit=50):
    """Internal function to download all videos with WANTED status"""
    try:
        results = []
        success_count = 0
        failed_count = 0
        wanted_video_ids = []

        # First, get all wanted video IDs
        with get_db() as session:
            wanted_videos = (
                session.query(Video.id, Video.title, Artist.name)
                .join(Artist)
                .filter(Video.status == VideoStatus.WANTED)
                .limit(limit)
                .all()
            )

            if not wanted_videos:
                return {
                    "success": True,
                    "message": "No wanted videos found",
                    "success_count": 0,
                    "failed_count": 0,
                    "results": [],
                }

            wanted_video_ids = [(v.id, v.title, v.name) for v in wanted_videos]

        logger.info(f"Found {len(wanted_video_ids)} wanted videos to download")

        # Process each video individually to avoid session issues
        for video_id, video_title, artist_name in wanted_video_ids:
            try:
                with get_db() as session:
                    # Get fresh video object for each download
                    video = session.query(Video).filter(Video.id == video_id).first()

                    if not video:
                        results.append(
                            {
                                "video_id": video_id,
                                "title": video_title,
                                "artist": artist_name,
                                "success": False,
                                "error": "Video not found",
                            }
                        )
                        failed_count += 1
                        continue

                    # Resolve video URL using helper function
                    video_url = resolve_video_url(video, session)

                    if not video_url:
                        results.append(
                            {
                                "video_id": video_id,
                                "title": video_title,
                                "artist": artist_name,
                                "success": False,
                                "error": "No URL available for download",
                            }
                        )
                        failed_count += 1
                        continue

                    # Import yt-dlp service
                    from src.services.ytdlp_service import ytdlp_service

                    # Queue download
                    result = ytdlp_service.add_music_video_download(
                        artist=artist_name,
                        title=video_title,
                        url=video_url,
                        quality="best",
                        video_id=video_id,
                    )

                    if result and result.get("success"):
                        # Update the video status in a separate transaction
                        video.status = VideoStatus.DOWNLOADING
                        session.commit()

                        results.append(
                            {
                                "video_id": video_id,
                                "title": video_title,
                                "artist": artist_name,
                                "success": True,
                                "download_id": result.get("id"),
                            }
                        )
                        success_count += 1
                    else:
                        error_msg = (
                            result.get("error", "Failed to queue download")
                            if result
                            else "MeTube service unavailable"
                        )
                        results.append(
                            {
                                "video_id": video_id,
                                "title": video_title,
                                "artist": artist_name,
                                "success": False,
                                "error": error_msg,
                            }
                        )
                        failed_count += 1

            except Exception as e:
                logger.error(f"Failed to download wanted video {video_id}: {e}")
                results.append(
                    {
                        "video_id": video_id,
                        "title": video_title,
                        "artist": artist_name,
                        "success": False,
                        "error": str(e),
                    }
                )
                failed_count += 1

        message = f"Downloaded all wanted videos: {success_count} queued successfully"
        if failed_count > 0:
            message += f", {failed_count} failed"

        return {
            "success": True,
            "message": message,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_wanted": len(wanted_video_ids),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Failed to download wanted videos: {e}")
        return {"success": False, "error": str(e)}


@videos_bp.route("/bulk/download-wanted", methods=["POST"])
def download_all_wanted_videos():
    """Download all videos with WANTED status"""
    try:
        data = request.get_json() or {}
        limit = data.get(
            "limit", 50
        )  # Default limit to prevent overwhelming the system

        # Call the internal function
        result = download_all_wanted_videos_internal(limit=limit)

        # Return JSON response
        if result.get("success"):
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        logger.error(f"Failed to download wanted videos: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/bulk/status", methods=["PUT"])
def bulk_update_video_status():
    """Update status for multiple videos"""
    try:
        data = request.get_json()
        if not data or "video_ids" not in data or "status" not in data:
            return jsonify({"error": "video_ids array and status are required"}), 400

        video_ids = data["video_ids"]
        new_status = data["status"]

        if not isinstance(video_ids, list):
            return jsonify({"error": "video_ids must be an array"}), 400

        # Validate status
        valid_statuses = ["WANTED", "DOWNLOADING", "DOWNLOADED", "FAILED", "IGNORED"]
        if new_status not in valid_statuses:
            return (
                jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}),
                400,
            )

        results = []
        success_count = 0
        failed_count = 0

        with get_db() as session:
            for video_id in video_ids:
                try:
                    video = session.query(Video).filter(Video.id == video_id).first()

                    if not video:
                        results.append(
                            {
                                "video_id": video_id,
                                "success": False,
                                "error": "Video not found",
                            }
                        )
                        failed_count += 1
                        continue

                    old_status = (
                        video.status.value
                        if hasattr(video.status, "value")
                        else video.status
                    )
                    video.status = VideoStatus[new_status]
                    session.commit()

                    results.append(
                        {
                            "video_id": video_id,
                            "success": True,
                            "title": video.title,
                            "old_status": old_status,
                            "new_status": new_status,
                        }
                    )
                    success_count += 1

                except Exception as e:
                    logger.error(f"Failed to update video {video_id} status: {e}")
                    results.append(
                        {"video_id": video_id, "success": False, "error": str(e)}
                    )
                    failed_count += 1

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Bulk status update completed: {success_count} success, {failed_count} failed",
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "results": results,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to bulk update video status: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/scan-directories", methods=["POST"])
def scan_artist_directories():
    """Scan artist directories to find downloaded videos not tracked in database"""
    try:
        logger.info("Starting directory scan request")
        import re
        from pathlib import Path

        from src.database.models import Artist

        # Get request parameters
        data = request.get_json() or {}
        artist_id = data.get("artist_id")  # Optional: scan specific artist
        dry_run = data.get("dry_run", True)  # Default to dry run
        video_extensions = [".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm", ".m4v"]

        base_video_dir = Path("data/musicvideos")
        if not base_video_dir.exists():
            return jsonify({"error": "Video directory not found"}), 404

        found_videos = []
        updated_videos = []
        errors = []

        with get_db() as session:
            # Get artists to scan
            if artist_id:
                artists = session.query(Artist).filter(Artist.id == artist_id).all()
                if not artists:
                    return jsonify({"error": "Artist not found"}), 404
            else:
                # Scan all artists with video directories
                artists = session.query(Artist).all()

            for artist in artists:
                try:
                    artist_name = artist.name

                    # Try multiple variations of the artist name for directory matching
                    artist_name_variations = [
                        artist_name,
                        artist_name.replace(
                            '"', "'"
                        ),  # Replace double quotes with single quotes
                        artist_name.replace('"', ""),  # Remove quotes entirely
                        artist_name.replace(
                            "'", '"'
                        ),  # Replace single quotes with double quotes
                        artist_name.replace("'", ""),  # Remove single quotes entirely
                    ]

                    artist_dir = None
                    for name_variant in artist_name_variations:
                        potential_dir = base_video_dir / name_variant
                        if potential_dir.exists():
                            artist_dir = potential_dir
                            logger.info(
                                f"Found directory for artist '{artist_name}' using variant: '{name_variant}'"
                            )
                            break

                    # Check if artist directory exists
                    if not artist_dir:
                        logger.debug(
                            f"No directory found for artist: {artist_name} (tried {len(artist_name_variations)} variations)"
                        )
                        continue

                    # Find video files in directory
                    video_files = []
                    for ext in video_extensions:
                        video_files.extend(artist_dir.glob(f"*{ext}"))

                    if not video_files:
                        continue

                    logger.info(
                        f"Scanning {len(video_files)} video files for artist: {artist_name}"
                    )

                    # Get existing videos for this artist
                    existing_videos = (
                        session.query(Video).filter(Video.artist_id == artist.id).all()
                    )
                    existing_paths = {
                        v.local_path for v in existing_videos if v.local_path
                    }
                    existing_titles = {v.title.lower() for v in existing_videos}

                    for video_file in video_files:
                        try:
                            # Get relative path from the app root
                            try:
                                relative_path = str(video_file.relative_to(Path.cwd()))
                            except ValueError:
                                # If relative_to fails, construct the path manually
                                relative_path = str(video_file)
                                if relative_path.startswith("/"):
                                    # Try to make it relative to current working directory
                                    cwd = str(Path.cwd())
                                    if relative_path.startswith(cwd):
                                        relative_path = relative_path[
                                            len(cwd) :
                                        ].lstrip("/")

                            # Skip if already tracked with correct path
                            if relative_path in existing_paths:
                                continue

                            # Extract title from filename
                            filename = video_file.stem

                            # Try different patterns to extract title
                            title_patterns = [
                                rf"^{re.escape(artist_name)}\s*-\s*(.+)$",  # "Artist - Title"
                                rf"^(.+?)\s*-\s*{re.escape(artist_name)}$",  # "Title - Artist"
                                rf"^(.+)$",  # Just the filename
                            ]

                            extracted_title = None
                            for pattern in title_patterns:
                                match = re.match(pattern, filename, re.IGNORECASE)
                                if match:
                                    extracted_title = match.group(1).strip()
                                    break

                            if not extracted_title:
                                extracted_title = filename

                            # Check if we have an existing video with similar title
                            matching_video = None
                            for video in existing_videos:
                                if (
                                    video.title.lower() == extracted_title.lower()
                                    or video.title.lower() in extracted_title.lower()
                                    or extracted_title.lower() in video.title.lower()
                                ):
                                    matching_video = video
                                    break

                            video_info = {
                                "artist_id": artist.id,
                                "artist_name": artist_name,
                                "file_path": relative_path,
                                "filename": video_file.name,
                                "extracted_title": extracted_title,
                                "file_size": video_file.stat().st_size,
                                "existing_video_id": matching_video.id
                                if matching_video
                                else None,
                                "existing_video_title": matching_video.title
                                if matching_video
                                else None,
                                "existing_status": matching_video.status.value
                                if matching_video
                                and hasattr(matching_video.status, "value")
                                else (
                                    matching_video.status if matching_video else None
                                ),
                                "existing_local_path": matching_video.local_path
                                if matching_video
                                else None,
                            }

                            found_videos.append(video_info)

                            # If we found a matching video, update it (unless dry run)
                            if matching_video and not dry_run:
                                old_status = (
                                    matching_video.status.value
                                    if hasattr(matching_video.status, "value")
                                    else matching_video.status
                                )
                                old_path = matching_video.local_path

                                matching_video.local_path = relative_path
                                matching_video.status = VideoStatus.DOWNLOADED

                                updated_videos.append(
                                    {
                                        "video_id": matching_video.id,
                                        "title": matching_video.title,
                                        "artist_name": artist_name,
                                        "old_status": old_status,
                                        "new_status": "DOWNLOADED",
                                        "old_path": old_path,
                                        "new_path": relative_path,
                                    }
                                )

                                logger.info(
                                    f"Updated video {matching_video.id}: {matching_video.title}"
                                )

                        except Exception as e:
                            logger.error(f"Error processing file {video_file}: {e}")
                            errors.append(
                                {
                                    "file": str(video_file),
                                    "artist": artist_name,
                                    "error": str(e),
                                }
                            )

                except Exception as e:
                    logger.error(f"Error processing artist {artist.name}: {e}")
                    errors.append({"artist": artist.name, "error": str(e)})

            # Commit changes if not dry run
            if not dry_run:
                session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "dry_run": dry_run,
                    "summary": {
                        "artists_scanned": len(artists),
                        "video_files_found": len(found_videos),
                        "videos_updated": len(updated_videos),
                        "errors": len(errors),
                    },
                    "found_videos": found_videos[:50],  # Limit for response size
                    "updated_videos": updated_videos,
                    "errors": errors[:10] if errors else [],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to scan directories: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/import-from-imvdb", methods=["POST"])
def import_video_from_imvdb():
    """Import a single video from IMVDb by ID"""
    try:
        data = request.get_json()
        if not data or "imvdb_id" not in data or "artist_id" not in data:
            return jsonify({"error": "imvdb_id and artist_id are required"}), 400

        imvdb_id = data["imvdb_id"]
        artist_id = data["artist_id"]
        auto_download = data.get("auto_download", False)
        skip_existing = data.get("skip_existing", True)
        priority = data.get("priority", 5)  # Default to normal priority

        with get_db() as session:
            # Check if artist exists
            artist = session.query(Artist).filter_by(id=artist_id).first()
            if not artist:
                return jsonify({"error": "Artist not found"}), 404

            # Store artist name for later use (avoid session binding issues)
            artist_name = artist.name

            # Check if video already exists
            existing_video = session.query(Video).filter_by(imvdb_id=imvdb_id).first()
            if existing_video:
                if skip_existing:
                    # Get existing video artist name safely
                    existing_artist_name = None
                    if existing_video.artist_id:
                        existing_artist = (
                            session.query(Artist)
                            .filter_by(id=existing_video.artist_id)
                            .first()
                        )
                        existing_artist_name = (
                            existing_artist.name if existing_artist else None
                        )

                    return (
                        jsonify(
                            {
                                "success": True,
                                "skipped": True,
                                "message": f'Video "{existing_video.title}" already exists',
                                "video_id": existing_video.id,
                                "title": existing_video.title,
                                "artist_name": existing_artist_name,
                            }
                        ),
                        200,
                    )
                else:
                    # Get existing video artist name safely
                    existing_artist_name = None
                    if existing_video.artist_id:
                        existing_artist = (
                            session.query(Artist)
                            .filter_by(id=existing_video.artist_id)
                            .first()
                        )
                        existing_artist_name = (
                            existing_artist.name if existing_artist else None
                        )

                    return (
                        jsonify(
                            {
                                "error": "Video already exists",
                                "video_id": existing_video.id,
                                "title": existing_video.title,
                                "artist_name": existing_artist_name,
                            }
                        ),
                        409,
                    )

            # Fetch video data from IMVDb (outside session to avoid blocking)
            video_data = imvdb_service.get_video_by_id(imvdb_id)
            if not video_data:
                return jsonify({"error": "Video not found on IMVDb"}), 404

            # Extract metadata using IMVDb service
            video_metadata = imvdb_service.extract_metadata(video_data)
            if not video_metadata:
                return (
                    jsonify({"error": "Failed to extract video metadata from IMVDb"}),
                    500,
                )

            # Create new video
            new_video = Video(
                artist_id=artist_id,
                title=video_metadata["title"],
                imvdb_id=imvdb_id,
                thumbnail_url=video_metadata.get("thumbnail_url"),
                year=video_metadata.get("year"),
                directors=video_metadata.get("directors", []),
                producers=video_metadata.get("producers", []),
                duration=video_metadata.get("duration"),
                description=video_metadata.get("description"),
                imvdb_metadata=video_metadata.get("raw_metadata"),
                video_metadata=video_metadata.get("raw_metadata"),
                status=VideoStatus.WANTED,
                discovered_date=datetime.utcnow(),
            )

            session.add(new_video)
            session.commit()

            # Refresh the new_video object to get the generated ID and ensure it's bound to session
            session.refresh(new_video)

            logger.info(
                f"Successfully imported video '{video_metadata['title']}' for artist '{artist_name}'"
            )

            # Store video ID for automatic download
            video_id = new_video.id

        # Conditionally trigger download after import (outside session to avoid blocking)
        download_result = None
        download_error = None

        if auto_download:
            try:
                # Trigger automatic download with priority
                download_result = _trigger_video_download(video_id)

                if download_result and download_result.get("success"):
                    # Update download priority if specified
                    if priority != 5:  # Only update if not default priority
                        try:
                            from src.database.models import Download

                            with get_db() as session:
                                download = (
                                    session.query(Download)
                                    .filter(Download.video_id == video_id)
                                    .first()
                                )
                                if download:
                                    download.priority = priority
                                    session.commit()
                        except Exception as priority_error:
                            logger.warning(
                                f"Could not set priority for download: {priority_error}"
                            )

                    logger.info(
                        f"Automatically started download for imported video: {video_metadata['title']} (Priority: {priority})"
                    )
                else:
                    download_error = (
                        download_result.get("error", "Unknown download error")
                        if download_result
                        else "Failed to start download"
                    )
                    logger.warning(
                        f"Could not automatically start download for imported video {video_metadata['title']}: {download_error}"
                    )
            except Exception as e:
                download_error = str(e)
                logger.error(
                    f"Error during automatic download for imported video {video_metadata['title']}: {e}"
                )

        return (
            jsonify(
                {
                    "success": True,
                    "message": f'Video "{video_metadata["title"]}" imported successfully',
                    "auto_download": {
                        "attempted": auto_download,
                        "success": download_result.get("success", False)
                        if download_result and auto_download
                        else False,
                        "error": download_error,
                        "priority": priority if auto_download else None,
                    },
                    "video": {
                        "id": video_id,
                        "title": video_metadata["title"],
                        "imvdb_id": imvdb_id,
                        "artist_id": artist_id,
                        "artist_name": artist_name,
                        "status": "DOWNLOADING"
                        if download_result and download_result.get("success")
                        else "WANTED",
                        "year": video_metadata.get("year"),
                        "directors": video_metadata.get("directors", []),
                        "producers": video_metadata.get("producers", []),
                        "thumbnail_url": video_metadata.get("thumbnail_url"),
                        "duration": video_metadata.get("duration"),
                        "created_at": datetime.utcnow().isoformat(),
                    },
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Failed to import video from IMVDb: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/import-from-youtube", methods=["POST"])
def import_video_from_youtube():
    """Import a single video from YouTube by ID"""
    try:
        data = request.get_json()
        if not data or "youtube_id" not in data or "artist_id" not in data:
            return jsonify({"error": "youtube_id and artist_id are required"}), 400

        youtube_id = data["youtube_id"]
        artist_id = data["artist_id"]
        auto_download = data.get("auto_download", False)
        skip_existing = data.get("skip_existing", True)
        priority = data.get("priority", 5)  # Default to normal priority

        with get_db() as session:
            # Check if artist exists
            artist = session.query(Artist).filter_by(id=artist_id).first()
            if not artist:
                return jsonify({"error": "Artist not found"}), 404

            # Store artist name for later use (avoid session binding issues)
            artist_name = artist.name

            # Check if video already exists
            existing_video = (
                session.query(Video).filter_by(youtube_id=youtube_id).first()
            )
            if existing_video:
                if skip_existing:
                    # Get existing video artist name safely
                    existing_artist_name = None
                    if existing_video.artist_id:
                        existing_artist = (
                            session.query(Artist)
                            .filter_by(id=existing_video.artist_id)
                            .first()
                        )
                        existing_artist_name = (
                            existing_artist.name if existing_artist else None
                        )

                    return (
                        jsonify(
                            {
                                "success": True,
                                "skipped": True,
                                "message": f'Video "{existing_video.title}" already exists',
                                "video_id": existing_video.id,
                                "title": existing_video.title,
                                "artist_name": existing_artist_name,
                            }
                        ),
                        200,
                    )
                else:
                    # Get existing video artist name safely
                    existing_artist_name = None
                    if existing_video.artist_id:
                        existing_artist = (
                            session.query(Artist)
                            .filter_by(id=existing_video.artist_id)
                            .first()
                        )
                        existing_artist_name = (
                            existing_artist.name if existing_artist else None
                        )

                    return (
                        jsonify(
                            {
                                "error": "Video already exists",
                                "video_id": existing_video.id,
                                "title": existing_video.title,
                                "artist_name": existing_artist_name,
                            }
                        ),
                        409,
                    )

            # For YouTube videos, we need to get the video data from the discovery results
            # If title is not provided, fetch it from YouTube API
            title = data.get("title")
            if not title:
                # Try to fetch title from YouTube API
                from src.services.youtube_search_service import youtube_search_service

                try:
                    # Get video details from YouTube
                    youtube_details = youtube_search_service._get_video_details(
                        [youtube_id]
                    )
                    if youtube_details and youtube_id in youtube_details:
                        video_data = youtube_details[youtube_id]
                        # Try to get title from video details
                        if "title" in video_data:
                            title = video_data["title"]
                        else:
                            # Make a direct API call to get snippet data
                            import requests

                            api_key = youtube_search_service.api_key
                            if api_key:
                                try:
                                    url = f"{youtube_search_service.base_url}/videos"
                                    params = {
                                        "part": "snippet",
                                        "id": youtube_id,
                                        "key": api_key,
                                    }
                                    response = requests.get(
                                        url, params=params, timeout=10
                                    )
                                    if response.status_code == 200:
                                        video_info = response.json()
                                        items = video_info.get("items", [])
                                        if items:
                                            title = (
                                                items[0].get("snippet", {}).get("title")
                                            )
                                except:
                                    pass
                except Exception as e:
                    logger.warning(
                        f"Could not fetch YouTube title for video {youtube_id}: {e}"
                    )

                # Final fallback
                if not title:
                    title = f"YouTube Video {youtube_id}"
            description = data.get("description", "")
            thumbnail_url = data.get("thumbnail_url", "")
            duration = data.get("duration")
            view_count = data.get("view_count")
            like_count = data.get("like_count")
            published_at = data.get("published_at")
            channel_title = data.get("channel_title", "")

            # Parse year from published_at if available
            year = None
            if published_at:
                try:
                    year = int(published_at[:4])
                except:
                    pass

            # Prepare video metadata
            video_metadata = {
                "youtube_data": {
                    "published_at": published_at,
                    "channel_title": channel_title,
                    "like_count": like_count,
                    "imported_at": datetime.utcnow().isoformat(),
                }
            }

            # Create new video
            new_video = Video(
                artist_id=artist_id,
                title=title,
                youtube_id=youtube_id,
                youtube_url=f"https://www.youtube.com/watch?v={youtube_id}",
                thumbnail_url=thumbnail_url,
                year=year,
                duration=duration,
                description=description,
                view_count=view_count,
                like_count=like_count,
                video_metadata=video_metadata,
                source="youtube_discovery",
                status=VideoStatus.WANTED,
                discovered_date=datetime.utcnow(),
            )

            session.add(new_video)
            session.commit()

            # Refresh the new_video object to get the generated ID and ensure it's bound to session
            session.refresh(new_video)

            logger.info(
                f"Successfully imported YouTube video '{title}' for artist '{artist_name}'"
            )

            # Store video ID for automatic download
            video_id = new_video.id

        # Conditionally trigger download after import (outside session to avoid blocking)
        download_result = None
        download_error = None

        if auto_download:
            try:
                # Trigger automatic download with priority
                download_result = _trigger_video_download(video_id)

                if download_result and download_result.get("success"):
                    # Update download priority if specified
                    if priority != 5:  # Only update if not default priority
                        try:
                            from src.database.models import Download

                            with get_db() as session:
                                download = (
                                    session.query(Download)
                                    .filter(Download.video_id == video_id)
                                    .first()
                                )
                                if download:
                                    download.priority = priority
                                    session.commit()
                        except Exception as priority_error:
                            logger.warning(
                                f"Could not set priority for download: {priority_error}"
                            )

                    logger.info(
                        f"Automatically started download for imported YouTube video: {title} (Priority: {priority})"
                    )
                else:
                    download_error = (
                        download_result.get("error", "Unknown download error")
                        if download_result
                        else "Failed to start download"
                    )
                    logger.warning(
                        f"Could not automatically start download for imported YouTube video {title}: {download_error}"
                    )
            except Exception as e:
                download_error = str(e)
                logger.error(
                    f"Error during automatic download for imported YouTube video {title}: {e}"
                )

        return (
            jsonify(
                {
                    "success": True,
                    "message": f'Video "{title}" imported successfully',
                    "auto_download": {
                        "attempted": auto_download,
                        "success": download_result.get("success", False)
                        if download_result and auto_download
                        else False,
                        "error": download_error,
                        "priority": priority if auto_download else None,
                    },
                    "video": {
                        "id": video_id,
                        "title": title,
                        "youtube_id": youtube_id,
                        "youtube_url": f"https://www.youtube.com/watch?v={youtube_id}",
                        "artist_id": artist_id,
                        "artist_name": artist_name,
                        "status": "DOWNLOADING"
                        if download_result and download_result.get("success")
                        else "WANTED",
                        "year": year,
                        "channel_title": channel_title,
                        "thumbnail_url": thumbnail_url,
                        "duration": duration,
                        "view_count": view_count,
                        "like_count": like_count,
                        "created_at": datetime.utcnow().isoformat(),
                    },
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Failed to import video from YouTube: {e}")
        return jsonify({"error": str(e)}), 500


# Download Queue Priority Management Endpoints


@videos_bp.route("/downloads/queue", methods=["GET"])
def get_download_queue():
    """Get prioritized download queue with detailed status"""
    try:
        with get_db() as session:
            from src.database.models import Download

            # Get filter parameters
            status_filter = request.args.get("status")
            priority_filter = request.args.get("priority")
            artist_id_filter = request.args.get("artist_id")
            limit = min(int(request.args.get("limit", 100)), 500)

            # Build query with priority ordering
            query = session.query(Download).join(Download.artist)

            # Apply filters
            if status_filter:
                query = query.filter(Download.status == status_filter)
            if priority_filter:
                query = query.filter(Download.priority == int(priority_filter))
            if artist_id_filter:
                query = query.filter(Download.artist_id == int(artist_id_filter))

            # Order by priority (ascending = higher priority first), then by created_at
            downloads = (
                query.order_by(Download.priority.asc(), Download.created_at.asc())
                .limit(limit)
                .all()
            )

            # Format response with enhanced data
            queue_data = []
            for download in downloads:
                queue_data.append(
                    {
                        "id": download.id,
                        "title": download.title,
                        "artist_name": download.artist.name
                        if download.artist
                        else "Unknown",
                        "artist_id": download.artist_id,
                        "video_id": download.video_id,
                        "status": download.status,
                        "priority": download.priority,
                        "priority_label": get_priority_label(download.priority),
                        "progress": download.progress,
                        "file_size": download.file_size,
                        "quality": download.quality,
                        "format": download.format,
                        "download_date": download.download_date.isoformat()
                        if download.download_date
                        else None,
                        "created_at": download.created_at.isoformat(),
                        "updated_at": download.updated_at.isoformat(),
                        "error_message": download.error_message,
                        "metube_id": download.metube_id,
                        "estimated_time_remaining": calculate_eta(download),
                        "can_modify_priority": download.status in ["pending", "failed"],
                    }
                )

            # Calculate queue statistics
            stats = calculate_queue_statistics(session)

            return (
                jsonify(
                    {
                        "queue": queue_data,
                        "count": len(queue_data),
                        "statistics": stats,
                        "priority_levels": get_priority_levels(),
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to get download queue: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/downloads/<int:download_id>/priority", methods=["PUT"])
def update_download_priority(download_id):
    """Update download priority"""
    try:
        data = request.get_json()
        new_priority = data.get("priority")

        if (
            not new_priority
            or not isinstance(new_priority, int)
            or new_priority < 1
            or new_priority > 10
        ):
            return (
                jsonify(
                    {
                        "error": "Priority must be an integer between 1 (highest) and 10 (lowest)"
                    }
                ),
                400,
            )

        with get_db() as session:
            from src.database.models import Download

            download = (
                session.query(Download).filter(Download.id == download_id).first()
            )
            if not download:
                return jsonify({"error": "Download not found"}), 404

            # Check if priority can be modified
            if download.status not in ["pending", "failed"]:
                return (
                    jsonify(
                        {
                            "error": f"Cannot modify priority for {download.status} downloads"
                        }
                    ),
                    400,
                )

            old_priority = download.priority
            download.priority = new_priority
            session.commit()

            logger.info(
                f"Updated download {download_id} priority from {old_priority} to {new_priority}"
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Priority updated from {get_priority_label(old_priority)} to {get_priority_label(new_priority)}",
                        "download": {
                            "id": download.id,
                            "title": download.title,
                            "old_priority": old_priority,
                            "new_priority": new_priority,
                            "priority_label": get_priority_label(new_priority),
                        },
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to update download priority: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/downloads/bulk/priority", methods=["PUT"])
def bulk_update_priority():
    """Bulk update download priorities"""
    try:
        data = request.get_json()
        download_ids = data.get("download_ids", [])
        new_priority = data.get("priority")

        if not download_ids:
            return jsonify({"error": "No download IDs provided"}), 400

        if (
            not new_priority
            or not isinstance(new_priority, int)
            or new_priority < 1
            or new_priority > 10
        ):
            return (
                jsonify(
                    {
                        "error": "Priority must be an integer between 1 (highest) and 10 (lowest)"
                    }
                ),
                400,
            )

        with get_db() as session:
            from src.database.models import Download

            downloads = (
                session.query(Download).filter(Download.id.in_(download_ids)).all()
            )

            if not downloads:
                return jsonify({"error": "No downloads found with provided IDs"}), 404

            updated_count = 0
            skipped_count = 0
            results = []

            for download in downloads:
                if download.status in ["pending", "failed"]:
                    old_priority = download.priority
                    download.priority = new_priority
                    updated_count += 1
                    results.append(
                        {
                            "id": download.id,
                            "title": download.title,
                            "updated": True,
                            "old_priority": old_priority,
                            "new_priority": new_priority,
                        }
                    )
                else:
                    skipped_count += 1
                    results.append(
                        {
                            "id": download.id,
                            "title": download.title,
                            "updated": False,
                            "reason": f"Cannot modify priority for {download.status} downloads",
                        }
                    )

            session.commit()

            logger.info(
                f"Bulk priority update: {updated_count} updated, {skipped_count} skipped"
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Updated priority for {updated_count} downloads (skipped {skipped_count})",
                        "updated_count": updated_count,
                        "skipped_count": skipped_count,
                        "new_priority": new_priority,
                        "priority_label": get_priority_label(new_priority),
                        "results": results,
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to bulk update priorities: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/downloads/queue/reorder", methods=["POST"])
def reorder_queue():
    """Automatically reorder queue based on smart prioritization"""
    try:
        data = request.get_json() or {}
        rules = data.get("rules", {})

        # Default prioritization rules
        default_rules = {
            "prioritize_new_artists": True,  # Higher priority for artists with fewer downloads
            "prioritize_recent": True,  # Higher priority for recently added videos
            "prioritize_short_videos": False,  # Higher priority for shorter videos
            "prioritize_high_quality": True,  # Higher priority for high quality videos
            "failed_retry_priority": 7,  # Priority for failed downloads
            "auto_download_priority": 3,  # Priority for auto-download artists
        }

        # Merge with provided rules
        prioritization_rules = {**default_rules, **rules}

        with get_db() as session:
            from src.database.models import Artist, Download

            # Get all pending and failed downloads
            downloads = (
                session.query(Download)
                .filter(Download.status.in_(["pending", "failed"]))
                .all()
            )

            if not downloads:
                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "No downloads to reorder",
                            "reordered_count": 0,
                        }
                    ),
                    200,
                )

            reordered_count = 0

            for download in downloads:
                old_priority = download.priority
                new_priority = calculate_smart_priority(
                    download, prioritization_rules, session
                )

                if new_priority != old_priority:
                    download.priority = new_priority
                    reordered_count += 1

            session.commit()

            logger.info(
                f"Smart reordering complete: {reordered_count} downloads reordered"
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Smart reordering complete: {reordered_count} downloads reordered",
                        "reordered_count": reordered_count,
                        "rules_applied": prioritization_rules,
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to reorder queue: {e}")
        return jsonify({"error": str(e)}), 500


# Helper functions for download queue management


def get_priority_label(priority):
    """Convert numeric priority to human-readable label"""
    labels = {
        1: "Critical",
        2: "Very High",
        3: "High",
        4: "Above Normal",
        5: "Normal",
        6: "Below Normal",
        7: "Low",
        8: "Very Low",
        9: "Lowest",
        10: "Deferred",
    }
    return labels.get(priority, "Unknown")


def get_priority_levels():
    """Get all available priority levels"""
    return [
        {"value": 1, "label": "Critical", "color": "#dc3545"},
        {"value": 2, "label": "Very High", "color": "#fd7e14"},
        {"value": 3, "label": "High", "color": "#ffc107"},
        {"value": 4, "label": "Above Normal", "color": "#20c997"},
        {"value": 5, "label": "Normal", "color": "#6c757d"},
        {"value": 6, "label": "Below Normal", "color": "#6f42c1"},
        {"value": 7, "label": "Low", "color": "#0dcaf0"},
        {"value": 8, "label": "Very Low", "color": "#198754"},
        {"value": 9, "label": "Lowest", "color": "#0d6efd"},
        {"value": 10, "label": "Deferred", "color": "#495057"},
    ]


def calculate_eta(download):
    """Calculate estimated time remaining for download"""
    if download.status != "downloading" or not download.progress:
        return None

    # This is a placeholder - in a real implementation you'd calculate based on
    # download speed, file size, and current progress
    remaining_percent = 100 - download.progress
    if remaining_percent <= 0:
        return "Almost done"

    # Simple estimation (this would be improved with actual speed data)
    estimated_minutes = remaining_percent * 0.5  # Rough estimate
    if estimated_minutes < 1:
        return "< 1 minute"
    elif estimated_minutes < 60:
        return f"{int(estimated_minutes)} minutes"
    else:
        hours = int(estimated_minutes / 60)
        minutes = int(estimated_minutes % 60)
        return f"{hours}h {minutes}m"


def calculate_queue_statistics(session):
    """Calculate queue statistics"""
    from src.database.models import Download

    stats = {
        "total_downloads": session.query(Download).count(),
        "by_status": {},
        "by_priority": {},
        "estimated_total_time": None,
        "queue_health": "good",
    }

    # Count by status
    status_counts = (
        session.query(Download.status, func.count(Download.id))
        .group_by(Download.status)
        .all()
    )

    for status, count in status_counts:
        stats["by_status"][status] = count

    # Count by priority
    priority_counts = (
        session.query(Download.priority, func.count(Download.id))
        .group_by(Download.priority)
        .all()
    )

    for priority, count in priority_counts:
        stats["by_priority"][priority] = count

    # Determine queue health
    failed_count = stats["by_status"].get("failed", 0)
    total_count = stats["total_downloads"]

    if total_count > 0:
        failed_ratio = failed_count / total_count
        if failed_ratio > 0.3:
            stats["queue_health"] = "poor"
        elif failed_ratio > 0.1:
            stats["queue_health"] = "fair"

    return stats


def calculate_smart_priority(download, rules, session):
    """Calculate smart priority based on various factors"""
    from src.database.models import Artist

    base_priority = 5  # Normal priority

    # Get artist information
    artist = download.artist
    if not artist:
        return base_priority

    # Rule: Prioritize auto-download artists
    if rules.get("prioritize_auto_download") and artist.auto_download:
        base_priority = min(base_priority, rules.get("auto_download_priority", 3))

    # Rule: Prioritize new artists (artists with fewer downloads)
    if rules.get("prioritize_new_artists"):
        artist_download_count = (
            session.query(Download)
            .filter(Download.artist_id == artist.id, Download.status == "completed")
            .count()
        )

        if artist_download_count == 0:
            base_priority = min(base_priority, 2)  # Very high for first download
        elif artist_download_count < 3:
            base_priority = min(base_priority, 3)  # High for few downloads

    # Rule: Handle failed downloads
    if download.status == "failed":
        base_priority = rules.get("failed_retry_priority", 7)

    # Rule: Prioritize recent additions
    if rules.get("prioritize_recent"):
        from datetime import datetime, timedelta

        recent_threshold = datetime.utcnow() - timedelta(hours=24)
        if download.created_at > recent_threshold:
            base_priority = max(1, base_priority - 1)  # Boost priority by 1

    return max(1, min(10, base_priority))  # Clamp to valid range


# Enhanced download control endpoints


@videos_bp.route("/downloads/<int:download_id>/pause", methods=["POST"])
def pause_download(download_id):
    """Pause a specific download"""
    try:
        with get_db() as session:
            from src.database.models import Download

            download = (
                session.query(Download).filter(Download.id == download_id).first()
            )
            if not download:
                return jsonify({"success": False, "error": "Download not found"}), 404

            if download.status != "downloading":
                return (
                    jsonify(
                        {"success": False, "error": "Download is not currently active"}
                    ),
                    400,
                )

            # Update status to paused
            download.status = "paused"
            session.commit()

            # TODO: Implement actual pause functionality with MeTube API
            logger.info(f"Paused download {download_id}: {download.title}")

            return jsonify(
                {"success": True, "message": f"Download paused: {download.title}"}
            )

    except Exception as e:
        logger.error(f"Error pausing download {download_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@videos_bp.route("/downloads/<int:download_id>/resume", methods=["POST"])
def resume_download(download_id):
    """Resume a paused download"""
    try:
        with get_db() as session:
            from src.database.models import Download

            download = (
                session.query(Download).filter(Download.id == download_id).first()
            )
            if not download:
                return jsonify({"success": False, "error": "Download not found"}), 404

            if download.status != "paused":
                return (
                    jsonify({"success": False, "error": "Download is not paused"}),
                    400,
                )

            # Update status to pending for restart
            download.status = "pending"
            session.commit()

            # TODO: Implement actual resume functionality with MeTube API
            logger.info(f"Resumed download {download_id}: {download.title}")

            return jsonify(
                {"success": True, "message": f"Download resumed: {download.title}"}
            )

    except Exception as e:
        logger.error(f"Error resuming download {download_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@videos_bp.route("/downloads/bulk/pause", methods=["POST"])
def pause_all_downloads():
    """Pause all active downloads"""
    try:
        with get_db() as session:
            from src.database.models import Download

            # Find all downloading items
            active_downloads = (
                session.query(Download).filter(Download.status == "downloading").all()
            )

            paused_count = 0
            for download in active_downloads:
                download.status = "paused"
                paused_count += 1

            session.commit()

            # TODO: Implement actual pause functionality with MeTube API
            logger.info(f"Paused {paused_count} downloads")

            return jsonify(
                {
                    "success": True,
                    "message": f"Paused {paused_count} downloads",
                    "paused_count": paused_count,
                }
            )

    except Exception as e:
        logger.error(f"Error pausing all downloads: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@videos_bp.route("/downloads/bulk/resume", methods=["POST"])
def resume_all_downloads():
    """Resume all paused downloads"""
    try:
        with get_db() as session:
            from src.database.models import Download

            # Find all paused items
            paused_downloads = (
                session.query(Download).filter(Download.status == "paused").all()
            )

            resumed_count = 0
            for download in paused_downloads:
                download.status = "pending"  # Reset to pending for restart
                resumed_count += 1

            session.commit()

            # TODO: Implement actual resume functionality with MeTube API
            logger.info(f"Resumed {resumed_count} downloads")

            return jsonify(
                {
                    "success": True,
                    "message": f"Resumed {resumed_count} downloads",
                    "resumed_count": resumed_count,
                }
            )

    except Exception as e:
        logger.error(f"Error resuming all downloads: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@videos_bp.route("/duplicates/detect", methods=["POST"])
def detect_duplicates():
    """Detect potential duplicate videos"""
    try:
        data = request.get_json()
        video_id = data.get("video_id")
        imvdb_id = data.get("imvdb_id")

        if not video_id or not imvdb_id:
            return jsonify({"error": "video_id and imvdb_id are required"}), 400

        with get_db() as session:
            # Find the current video
            current_video = session.query(Video).filter(Video.id == video_id).first()
            if not current_video:
                return jsonify({"error": "Video not found"}), 404

            # Find videos with the same IMVDb ID
            duplicate_videos = (
                session.query(Video)
                .filter(Video.imvdb_id == imvdb_id, Video.id != video_id)
                .all()
            )

            if not duplicate_videos:
                return jsonify({"duplicates_found": False})

            # Format duplicate information
            duplicates = []
            for dup_video in duplicate_videos:
                duplicates.append(
                    {
                        "id": dup_video.id,
                        "title": dup_video.title,
                        "artist_name": dup_video.artist.name
                        if dup_video.artist
                        else None,
                        "status": dup_video.status.value
                        if hasattr(dup_video.status, "value")
                        else dup_video.status,
                        "year": dup_video.year,
                        "url": dup_video.url,
                        "local_path": dup_video.local_path,
                        "thumbnail_url": dup_video.thumbnail_url,
                        "created_at": dup_video.created_at.isoformat(),
                    }
                )

            return jsonify(
                {
                    "duplicates_found": True,
                    "current_video": {
                        "id": current_video.id,
                        "title": current_video.title,
                        "artist_name": current_video.artist.name
                        if current_video.artist
                        else None,
                        "status": current_video.status.value
                        if hasattr(current_video.status, "value")
                        else current_video.status,
                        "year": current_video.year,
                        "url": current_video.url,
                        "local_path": current_video.local_path,
                        "thumbnail_url": current_video.thumbnail_url,
                        "created_at": current_video.created_at.isoformat(),
                    },
                    "duplicates": duplicates,
                    "imvdb_id": imvdb_id,
                }
            )

    except Exception as e:
        logger.error(f"Error detecting duplicates: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/duplicates/merge", methods=["POST"])
def merge_duplicate_videos():
    """Merge duplicate videos based on user choice"""
    try:
        data = request.get_json()
        primary_id = data.get("primary_id")  # Video to keep
        duplicate_ids = data.get("duplicate_ids", [])  # Videos to merge/delete
        merge_strategy = data.get(
            "merge_strategy", "keep_primary"
        )  # 'keep_primary', 'merge_data'

        if not primary_id or not duplicate_ids:
            return jsonify({"error": "primary_id and duplicate_ids are required"}), 400

        with get_db() as session:
            # Get the primary video
            primary_video = session.query(Video).filter(Video.id == primary_id).first()
            if not primary_video:
                return jsonify({"error": "Primary video not found"}), 404

            # Get duplicate videos
            duplicate_videos = (
                session.query(Video).filter(Video.id.in_(duplicate_ids)).all()
            )
            if len(duplicate_videos) != len(duplicate_ids):
                return jsonify({"error": "One or more duplicate videos not found"}), 404

            merged_info = []

            for dup_video in duplicate_videos:
                merge_details = {
                    "merged_video_id": dup_video.id,
                    "merged_title": dup_video.title,
                    "merged_data": {},
                }

                if merge_strategy == "merge_data":
                    # Merge missing data from duplicate to primary
                    if not primary_video.year and dup_video.year:
                        primary_video.year = dup_video.year
                        merge_details["merged_data"]["year"] = dup_video.year

                    if not primary_video.thumbnail_url and dup_video.thumbnail_url:
                        primary_video.thumbnail_url = dup_video.thumbnail_url
                        merge_details["merged_data"][
                            "thumbnail_url"
                        ] = dup_video.thumbnail_url

                    if not primary_video.url and dup_video.url:
                        primary_video.url = dup_video.url
                        merge_details["merged_data"]["url"] = dup_video.url

                    if not primary_video.local_path and dup_video.local_path:
                        primary_video.local_path = dup_video.local_path
                        merge_details["merged_data"][
                            "local_path"
                        ] = dup_video.local_path

                    if not primary_video.imvdb_metadata and dup_video.imvdb_metadata:
                        primary_video.imvdb_metadata = dup_video.imvdb_metadata
                        merge_details["merged_data"]["imvdb_metadata"] = "merged"

                # Delete the duplicate video
                session.delete(dup_video)
                merged_info.append(merge_details)

                logger.info(f"Merged duplicate video {dup_video.id} into {primary_id}")

            session.commit()

            return jsonify(
                {
                    "success": True,
                    "message": f"Successfully merged {len(duplicate_videos)} duplicate videos",
                    "primary_video_id": primary_id,
                    "merged_videos": merged_info,
                    "merge_strategy": merge_strategy,
                }
            )

    except Exception as e:
        logger.error(f"Error merging duplicate videos: {e}")
        return jsonify({"error": str(e)}), 500


@videos_bp.route("/<int:video_id>/update-safe", methods=["PUT"])
def update_video_safe(video_id):
    """Safely update video with duplicate detection"""
    try:
        data = request.get_json()

        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if not video:
                return jsonify({"error": "Video not found"}), 404

            # Check for IMVDb ID conflicts before updating
            new_imvdb_id = data.get("imvdb_id")
            if new_imvdb_id and new_imvdb_id != video.imvdb_id:
                # Check if this IMVDb ID already exists
                existing_video = (
                    session.query(Video)
                    .filter(Video.imvdb_id == new_imvdb_id, Video.id != video_id)
                    .first()
                )

                if existing_video:
                    return (
                        jsonify(
                            {
                                "error": "duplicate_imvdb_id",
                                "duplicate_video": {
                                    "id": existing_video.id,
                                    "title": existing_video.title,
                                    "artist_name": existing_video.artist.name
                                    if existing_video.artist
                                    else None,
                                    "status": existing_video.status.value
                                    if hasattr(existing_video.status, "value")
                                    else existing_video.status,
                                },
                                "suggested_action": "merge",
                            }
                        ),
                        409,
                    )  # Conflict status code

            # If no conflicts, proceed with normal update
            try:
                # Update fields
                if "title" in data:
                    video.title = data["title"]
                if "imvdb_id" in data:
                    video.imvdb_id = data["imvdb_id"]
                if "thumbnail_url" in data:
                    video.thumbnail_url = data["thumbnail_url"]
                if "year" in data:
                    video.year = data["year"]
                if "imvdb_metadata" in data:
                    video.imvdb_metadata = data["imvdb_metadata"]

                video.updated_at = datetime.now()
                session.commit()

                return jsonify({"message": "Video updated successfully"})

            except IntegrityError as e:
                session.rollback()
                if "imvdb_id" in str(e):
                    return (
                        jsonify(
                            {
                                "error": "duplicate_imvdb_id",
                                "message": "IMVDb ID already exists on another video",
                            }
                        ),
                        409,
                    )
                else:
                    return jsonify({"error": str(e)}), 500

    except Exception as e:
        logger.error(f"Error updating video {video_id}: {e}")
        return jsonify({"error": str(e)}), 500
