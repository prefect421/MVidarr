"""
Health check API endpoints
"""

import json
import subprocess
from pathlib import Path

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


@health_bp.route("/version", methods=["GET"])
def get_version_info():
    """Get version information including version number and git commit"""
    try:
        # Get version from src/__init__.py
        from src import __version__

        version_info = {
            "version": __version__,
            "git_commit": "unknown",
            "git_branch": "unknown",
        }

        try:
            # Try to get git commit hash
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
            )
            if result.returncode == 0:
                version_info["git_commit"] = result.stdout.strip()
        except Exception:
            pass

        try:
            # Try to get git branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent,
            )
            if result.returncode == 0:
                version_info["git_branch"] = result.stdout.strip()
        except Exception:
            pass

        # Try to read version.json as fallback
        try:
            version_json_path = Path(__file__).parent.parent.parent / "version.json"
            if version_json_path.exists():
                with open(version_json_path) as f:
                    version_data = json.load(f)
                    if version_info["git_commit"] == "unknown":
                        version_info["git_commit"] = version_data.get(
                            "git_commit", "unknown"
                        )
        except Exception:
            pass

        return jsonify(version_info), 200

    except Exception as e:
        logger.error(f"Version info retrieval failed: {e}")
        return jsonify({"error": str(e)}), 500
