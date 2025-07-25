"""
Health check API endpoints
"""

from flask import Blueprint, jsonify

from src.database.connection import get_db
from src.database.init_db import check_database_health
from src.utils.logger import get_logger

health_bp = Blueprint("health", __name__, url_prefix="/health")
logger = get_logger("mvidarr.api.health")


@health_bp.route("", methods=["GET"])  # This creates /api/health endpoint
def health_check():
    """Simple health check endpoint for Docker health checks"""
    try:
        # Quick database connectivity check
        from sqlalchemy import text

        with get_db() as session:
            session.execute(text("SELECT 1"))

        return jsonify({"status": "healthy", "service": "mvidarr"}), 200

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@health_bp.route("/status", methods=["GET"])
def get_health_status():
    """Get overall system health status"""
    try:
        status = {
            "status": "healthy",
            "components": {"database": "healthy", "api": "healthy"},
            "timestamp": None,
        }

        # Check database health
        if not check_database_health():
            status["components"]["database"] = "unhealthy"
            status["status"] = "unhealthy"

        # Add timestamp
        from datetime import datetime

        status["timestamp"] = datetime.utcnow().isoformat()

        return jsonify(status), 200 if status["status"] == "healthy" else 503

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            503,
        )


@health_bp.route("/database", methods=["GET"])
def check_database():
    """Check database connectivity and health"""
    try:
        if check_database_health():
            return (
                jsonify(
                    {
                        "status": "healthy",
                        "message": "Database is accessible and healthy",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {"status": "unhealthy", "message": "Database health check failed"}
                ),
                503,
            )

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@health_bp.route("/imvdb", methods=["GET"])
def check_imvdb():
    """Check IMVDB API connectivity"""
    try:
        from src.services.imvdb_service import imvdb_service

        result = imvdb_service.test_connection()

        status_code = 200 if result["status"] == "success" else 503
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"IMVDB health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@health_bp.route("/metube", methods=["GET"])
def check_metube():
    """Check yt-dlp Web UI connectivity"""
    try:
        from src.services.ytdlp_service import ytdlp_service

        result = ytdlp_service.test_connection()

        status_code = 200 if result["status"] == "success" else 503
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"yt-dlp Web UI health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503
