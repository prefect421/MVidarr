"""
Video Quality Management API endpoints for Issue #110
"""

from flask import Blueprint, jsonify, request

from src.services.video_quality_service import video_quality_service
from src.utils.logger import get_logger

video_quality_bp = Blueprint("video_quality", __name__, url_prefix="/video-quality")
logger = get_logger("mvidarr.api.video_quality")


@video_quality_bp.route("/preferences", methods=["GET"])
def get_quality_preferences():
    """Get quality preferences for a user or system defaults"""
    try:
        user_id = request.args.get("user_id", type=int)
        preferences = video_quality_service.get_user_quality_preferences(user_id)

        return jsonify({"success": True, "preferences": preferences})

    except Exception as e:
        logger.error(f"Error getting quality preferences: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/preferences", methods=["POST"])
def set_quality_preferences():
    """Set quality preferences for a user or globally"""
    try:
        data = request.get_json()
        if not data or "preferences" not in data:
            return jsonify({"error": "preferences object is required"}), 400

        preferences = data["preferences"]
        user_id = data.get("user_id")

        success = video_quality_service.set_user_quality_preferences(
            preferences, user_id
        )

        if success:
            return jsonify(
                {"success": True, "message": "Quality preferences updated successfully"}
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to validate or save preferences",
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Error setting quality preferences: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/format-string", methods=["GET"])
def get_ytdlp_format_string():
    """Get yt-dlp format string based on quality preferences"""
    try:
        user_id = request.args.get("user_id", type=int)
        artist_id = request.args.get("artist_id", type=int)

        format_string = video_quality_service.generate_ytdlp_format_string(
            user_id, artist_id
        )

        return jsonify({"success": True, "format_string": format_string})

    except Exception as e:
        logger.error(f"Error getting yt-dlp format string: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/analyze/<int:video_id>", methods=["GET"])
def analyze_video_quality(video_id):
    """Analyze the quality of a specific video"""
    try:
        from src.database.connection import get_db
        from src.database.models import Video

        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if not video:
                return jsonify({"error": "Video not found"}), 404

            analysis = video_quality_service.analyze_video_quality(video)

            return jsonify(
                {"success": True, "video_id": video_id, "analysis": analysis}
            )

    except Exception as e:
        logger.error(f"Error analyzing video quality for video {video_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/upgradeable", methods=["GET"])
def find_upgradeable_videos():
    """Find videos that could benefit from quality upgrades"""
    try:
        user_id = request.args.get("user_id", type=int)
        limit = int(request.args.get("limit", 0))  # 0 means no limit

        upgradeable_videos = video_quality_service.find_upgradeable_videos(
            user_id, limit
        )

        return jsonify(
            {
                "success": True,
                "upgradeable_videos": upgradeable_videos,
                "count": len(upgradeable_videos),
            }
        )

    except Exception as e:
        logger.error(f"Error finding upgradeable videos: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/upgrade/<int:video_id>", methods=["POST"])
def upgrade_video_quality(video_id):
    """Upgrade a video to higher quality"""
    try:
        data = request.get_json() or {}
        user_id = data.get("user_id")

        result = video_quality_service.upgrade_video_quality(video_id, user_id)

        status_code = 200 if result.get("success") else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error upgrading video {video_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/bulk-upgrade", methods=["POST"])
def bulk_upgrade_videos():
    """Upgrade multiple videos to higher quality"""
    try:
        data = request.get_json()
        if not data or "video_ids" not in data:
            return jsonify({"error": "video_ids array is required"}), 400

        video_ids = data["video_ids"]
        user_id = data.get("user_id")

        if not isinstance(video_ids, list) or not video_ids:
            return jsonify({"error": "video_ids must be a non-empty array"}), 400

        result = video_quality_service.bulk_upgrade_videos(video_ids, user_id)

        status_code = 200 if result.get("success") else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error bulk upgrading videos: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/statistics", methods=["GET"])
def get_quality_statistics():
    """Get system-wide video quality statistics"""
    # Add debugging
    try:
        from flask import current_app
        current_app.logger.info("Statistics endpoint called")
        stats = video_quality_service.get_quality_statistics()
        current_app.logger.info("Statistics retrieved successfully")
        
        # Ensure all values are JSON serializable
        def clean_for_json(obj):
            if isinstance(obj, dict):
                return {str(k) if k is not None else "unknown": clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif obj is None:
                return "none"
            else:
                return obj
        
        cleaned_stats = clean_for_json(stats)
        current_app.logger.info("Statistics cleaned for JSON serialization")
        return jsonify({"success": True, "statistics": cleaned_stats})
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        from flask import current_app
        current_app.logger.error(f"Error getting quality statistics: {e}")
        current_app.logger.error(f"Full traceback: {error_trace}")
        return jsonify({"success": False, "error": str(e)}), 500

@video_quality_bp.route("/test-statistics", methods=["GET"])  
def test_quality_statistics():
    """Get system-wide video quality statistics"""
    try:
        stats = video_quality_service.get_quality_statistics()

        return jsonify({"success": True, "statistics": stats})

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error getting quality statistics: {e}")
        logger.error(f"Full traceback: {error_trace}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/artist-preferences/<int:artist_id>", methods=["GET"])
def get_artist_quality_preferences(artist_id):
    """Get quality preferences for a specific artist"""
    try:
        preferences = video_quality_service._get_artist_quality_preferences(artist_id)

        return jsonify(
            {"success": True, "artist_id": artist_id, "preferences": preferences}
        )

    except Exception as e:
        logger.error(f"Error getting artist quality preferences: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/artist-preferences/<int:artist_id>", methods=["POST"])
def set_artist_quality_preferences(artist_id):
    """Set quality preferences for a specific artist"""
    try:
        data = request.get_json()
        if not data or "preferences" not in data:
            return jsonify({"error": "preferences object is required"}), 400

        preferences = data["preferences"]
        success = video_quality_service.set_artist_quality_preferences(
            artist_id, preferences
        )

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": f"Quality preferences set for artist {artist_id}",
                }
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Failed to validate or save artist preferences",
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Error setting artist quality preferences: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/quality-levels", methods=["GET"])
def get_available_quality_levels():
    """Get available quality levels and their descriptions"""
    try:
        from src.services.video_quality_service import QualityLevel

        quality_levels = []
        for level in QualityLevel:
            quality_levels.append(
                {
                    "value": level.value,
                    "height": level.to_height(),
                    "description": (
                        f"{level.value} ({level.to_height()}p)"
                        if level.value != "best"
                        else "Best Available"
                    ),
                }
            )

        return jsonify({"success": True, "quality_levels": quality_levels})

    except Exception as e:
        logger.error(f"Error getting quality levels: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@video_quality_bp.route("/check-all-qualities", methods=["POST"])
def check_all_video_qualities():
    """Manually trigger quality checks for multiple videos"""
    try:
        data = request.get_json() or {}
        limit = data.get("limit")  # None means check all videos
        only_unchecked = data.get("only_unchecked", True)
        
        from src.services.youtube_quality_check_service import youtube_quality_check_service
        
        limit_msg = f"up to {limit}" if limit else "all"
        logger.info(f"Starting manual quality check for {limit_msg} videos (only_unchecked={only_unchecked})")
        
        # Run the quality check
        summary = youtube_quality_check_service.check_all_videos(
            limit=limit, 
            only_unchecked=only_unchecked
        )
        
        logger.info(f"Quality check completed: {summary}")
        
        return jsonify({
            "success": True,
            "summary": summary,
            "message": f"Quality check completed: {summary['successful_checks']}/{summary['total_checked']} videos checked successfully"
        })

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error running quality check: {e}")
        logger.error(f"Full traceback: {error_trace}")
        return jsonify({"success": False, "error": str(e)}), 500
