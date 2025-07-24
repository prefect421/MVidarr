"""
Video organization API endpoints
"""

from flask import Blueprint, jsonify, request

from src.services.video_organization_service import video_organizer
from src.utils.logger import get_logger

video_org_bp = Blueprint(
    "video_organization", __name__, url_prefix="/video-organization"
)
logger = get_logger("mvidarr.api.video_organization")


@video_org_bp.route("/organize-all", methods=["POST"])
def organize_all_videos():
    """Organize all videos in downloads directory"""
    try:
        result = video_organizer.organize_all_downloads()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Organized {result['successful']} of {result['total_files']} videos",
                    "summary": result,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to organize all videos: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_org_bp.route("/organize/<filename>", methods=["POST"])
def organize_single_video(filename):
    """Organize a specific video file"""
    try:
        result = video_organizer.organize_single_file(filename)

        if result["success"]:
            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Successfully organized {filename}",
                        "result": result,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify({"success": False, "error": result["error"], "result": result}),
                400,
            )

    except Exception as e:
        logger.error(f"Failed to organize video {filename}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_org_bp.route("/artists", methods=["GET"])
def get_artist_directories():
    """Get list of artist directories and video counts"""
    try:
        artists = video_organizer.get_artist_directories()

        return (
            jsonify(
                {
                    "artists": artists,
                    "count": len(artists),
                    "total_videos": sum(artist["video_count"] for artist in artists),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get artist directories: {e}")
        return jsonify({"error": str(e)}), 500


@video_org_bp.route("/downloads/scan", methods=["GET"])
def scan_downloads():
    """Scan downloads directory for video files"""
    try:
        video_files = video_organizer.scan_downloads_directory()

        # Convert Path objects to strings
        file_list = [str(f.name) for f in video_files]

        return jsonify({"files": file_list, "count": len(file_list)}), 200

    except Exception as e:
        logger.error(f"Failed to scan downloads directory: {e}")
        return jsonify({"error": str(e)}), 500


@video_org_bp.route("/cleanup", methods=["POST"])
def cleanup_empty_directories():
    """Remove empty artist directories"""
    try:
        removed_count = video_organizer.cleanup_empty_directories()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Removed {removed_count} empty directories",
                    "removed_count": removed_count,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to cleanup directories: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_org_bp.route("/preview/<filename>", methods=["GET"])
def preview_organization(filename):
    """Preview how a file would be organized without actually moving it"""
    try:
        from pathlib import Path

        from src.utils.filename_cleanup import FilenameCleanup

        # Clean the filename
        cleaned_filename = FilenameCleanup.clean_filename(filename)

        # Extract artist and title
        artist, title = FilenameCleanup.extract_artist_and_title(cleaned_filename)

        preview = {
            "original_filename": filename,
            "cleaned_filename": cleaned_filename,
            "artist": artist,
            "title": title,
            "can_organize": bool(artist and title),
        }

        if artist and title:
            # Generate the target path
            music_videos_dir = video_organizer.get_music_videos_path()
            artist_folder = FilenameCleanup.sanitize_folder_name(artist)
            final_filename = FilenameCleanup.generate_clean_filename(
                artist, title, Path(filename).suffix
            )

            preview.update(
                {
                    "artist_folder": artist_folder,
                    "final_filename": final_filename,
                    "target_path": str(
                        music_videos_dir / artist_folder / final_filename
                    ),
                }
            )

        return jsonify(preview), 200

    except Exception as e:
        logger.error(f"Failed to preview organization for {filename}: {e}")
        return jsonify({"error": str(e)}), 500


@video_org_bp.route("/reorganize-existing", methods=["POST"])
def reorganize_existing_videos():
    """Reorganize existing videos in the music videos directory"""
    try:
        result = video_organizer.reorganize_existing_videos()

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Reorganized {result['successful']} of {result['total_files']} videos",
                    "summary": result,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to reorganize existing videos: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_org_bp.route("/existing/scan", methods=["GET"])
def scan_existing_videos():
    """Scan existing music videos directory for video files"""
    try:
        video_files = video_organizer.scan_existing_music_videos()

        # Convert Path objects to strings and get relative paths
        file_list = []
        music_videos_path = video_organizer.get_music_videos_path()

        for f in video_files:
            try:
                # Get relative path from music videos directory
                relative_path = f.relative_to(music_videos_path)
                file_list.append(str(relative_path))
            except ValueError:
                # If file is not under music videos directory, use full path
                file_list.append(str(f))

        return (
            jsonify(
                {
                    "files": file_list,
                    "count": len(file_list),
                    "music_videos_path": str(music_videos_path),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to scan existing videos: {e}")
        return jsonify({"error": str(e)}), 500


@video_org_bp.route("/status", methods=["GET"])
def get_organization_status():
    """Get current organization status and statistics"""
    try:
        # Scan downloads
        downloads = video_organizer.scan_downloads_directory()

        # Scan existing videos
        existing_videos = video_organizer.scan_existing_music_videos()

        # Get artists
        artists = video_organizer.get_artist_directories()

        # Ensure directories exist
        video_organizer.ensure_directories_exist()

        status = {
            "downloads_path": str(video_organizer.get_downloads_path()),
            "music_videos_path": str(video_organizer.get_music_videos_path()),
            "pending_downloads": len(downloads),
            "existing_videos": len(existing_videos),
            "artist_count": len(artists),
            "total_organized_videos": sum(artist["video_count"] for artist in artists),
            "directories_exist": True,
        }

        return jsonify(status), 200

    except Exception as e:
        logger.error(f"Failed to get organization status: {e}")
        return jsonify({"error": str(e)}), 500
