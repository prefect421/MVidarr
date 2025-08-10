"""
Enhanced Docker-Native Scheduler API
REST API for the enhanced scheduler service with container support
"""

from flask import Blueprint, jsonify, request

from src.middleware.simple_auth_middleware import auth_required
from src.services.enhanced_scheduler_service import enhanced_scheduler_service
from src.utils.logger import get_logger

enhanced_scheduler_bp = Blueprint("enhanced_scheduler", __name__)
logger = get_logger("mvidarr.api.enhanced_scheduler")


@enhanced_scheduler_bp.route("/enhanced-scheduler/status", methods=["GET"])
@auth_required
def get_enhanced_scheduler_status():
    """Get comprehensive enhanced scheduler status"""
    try:
        status = enhanced_scheduler_service.get_status()
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting enhanced scheduler status: {e}")
        return jsonify({"error": str(e)}), 500


@enhanced_scheduler_bp.route("/enhanced-scheduler/start", methods=["POST"])
@auth_required
def start_enhanced_scheduler():
    """Start the enhanced scheduler service"""
    try:
        enhanced_scheduler_service.start()
        return jsonify({"message": "Enhanced scheduler started successfully"}), 200
    except Exception as e:
        logger.error(f"Error starting enhanced scheduler: {e}")
        return jsonify({"error": str(e)}), 500


@enhanced_scheduler_bp.route("/enhanced-scheduler/stop", methods=["POST"])
@auth_required
def stop_enhanced_scheduler():
    """Stop the enhanced scheduler service"""
    try:
        enhanced_scheduler_service.stop()
        return jsonify({"message": "Enhanced scheduler stopped successfully"}), 200
    except Exception as e:
        logger.error(f"Error stopping enhanced scheduler: {e}")
        return jsonify({"error": str(e)}), 500


@enhanced_scheduler_bp.route("/enhanced-scheduler/reload", methods=["POST"])
@auth_required
def reload_enhanced_scheduler():
    """Reload enhanced scheduler configuration"""
    try:
        enhanced_scheduler_service.reload_schedule()
        return jsonify({"message": "Enhanced scheduler reloaded successfully"}), 200
    except Exception as e:
        logger.error(f"Error reloading enhanced scheduler: {e}")
        return jsonify({"error": str(e)}), 500


@enhanced_scheduler_bp.route("/enhanced-scheduler/trigger/download", methods=["POST"])
@auth_required
def trigger_enhanced_download():
    """Manually trigger a download task"""
    try:
        result = enhanced_scheduler_service.trigger_download_now()
        status_code = 200 if result["success"] else 500
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error triggering enhanced download: {e}")
        return jsonify({"error": str(e)}), 500


@enhanced_scheduler_bp.route("/enhanced-scheduler/trigger/discovery", methods=["POST"])
@auth_required
def trigger_enhanced_discovery():
    """Manually trigger a discovery task"""
    try:
        result = enhanced_scheduler_service.trigger_discovery_now()
        status_code = 200 if result["success"] else 500
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error triggering enhanced discovery: {e}")
        return jsonify({"error": str(e)}), 500


@enhanced_scheduler_bp.route("/enhanced-scheduler/health", methods=["GET"])
def get_enhanced_scheduler_health():
    """Health check endpoint (no auth required for monitoring)"""
    try:
        status = enhanced_scheduler_service.get_status()

        # Determine health based on scheduler status
        is_healthy = (
            status["running"] and status["thread_alive"] and status["jobs_count"] > 0
        )

        health_status = "healthy" if is_healthy else "unhealthy"
        http_code = 200 if is_healthy else 503

        health_response = {
            "status": health_status,
            "timestamp": status.get("last_health_check"),
            "details": {
                "scheduler_running": status["running"],
                "thread_alive": status["thread_alive"],
                "jobs_count": status["jobs_count"],
                "last_download": status.get("last_run_times", {}).get("download"),
                "last_discovery": status.get("last_run_times", {}).get("discovery"),
            },
        }

        return jsonify(health_response), http_code

    except Exception as e:
        logger.error(f"Error in enhanced scheduler health check: {e}")
        return jsonify({"status": "error", "error": str(e), "timestamp": None}), 503


@enhanced_scheduler_bp.route("/enhanced-scheduler/config", methods=["GET"])
@auth_required
def get_enhanced_scheduler_config():
    """Get enhanced scheduler environment configuration"""
    try:
        status = enhanced_scheduler_service.get_status()
        return (
            jsonify(
                {
                    "environment_config": status.get("environment_config", {}),
                    "scheduler_info": {
                        "jobs_count": status["jobs_count"],
                        "scheduled_jobs": status.get("scheduled_jobs", []),
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error getting enhanced scheduler config: {e}")
        return jsonify({"error": str(e)}), 500


@enhanced_scheduler_bp.route("/enhanced-scheduler/logs", methods=["GET"])
@auth_required
def get_enhanced_scheduler_logs():
    """Get recent scheduler log entries"""
    try:
        # Get query parameters
        limit = request.args.get("limit", 100, type=int)
        level = request.args.get("level", "INFO").upper()

        # In a real implementation, this would read from log files
        # For now, return placeholder data
        logs = {
            "message": "Log retrieval not implemented",
            "note": "Check Docker logs with: docker logs <container_id>",
            "parameters": {"limit": limit, "level": level},
        }

        return jsonify(logs), 200
    except Exception as e:
        logger.error(f"Error getting enhanced scheduler logs: {e}")
        return jsonify({"error": str(e)}), 500
