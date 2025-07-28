"""
Settings API endpoints
"""

from flask import Blueprint, jsonify, request

from src.services.settings_service import settings
from src.utils.logger import get_logger

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")
logger = get_logger("mvidarr.api.settings")


@settings_bp.route("/", methods=["GET"])
def get_all_settings():
    """Get all application settings"""
    try:
        settings_dict = settings.get_all()

        return jsonify({"settings": settings_dict, "count": len(settings_dict)}), 200

    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/<string:key>", methods=["GET"])
def get_setting(key):
    """Get a specific setting by key"""
    try:
        all_settings = settings.get_all()

        if key not in all_settings:
            return jsonify({"error": "Setting not found"}), 404

        setting_data = all_settings[key]
        return (
            jsonify(
                {
                    "key": key,
                    "value": setting_data["value"],
                    "description": setting_data["description"],
                    "updated_at": setting_data["updated_at"],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get setting '{key}': {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/<string:key>", methods=["PUT"])
def update_setting(key):
    """Update a specific setting"""
    try:
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({"error": "Value is required"}), 400

        description = data.get("description", "")

        if settings.set(key, data["value"], description):
            # Auto-reload Spotify service if Spotify settings are updated
            if key.startswith("spotify_"):
                try:
                    from src.services.spotify_service import spotify_service

                    logger.info(f"Reloading Spotify service after updating {key}")
                    spotify_service.reload_settings()
                    logger.info(
                        f"Spotify service successfully reloaded after updating {key}. New redirect URI: {spotify_service.redirect_uri}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to reload Spotify service after updating {key}: {e}"
                    )
                    # Continue with the response even if reload fails

            # Handle authentication setting change
            elif key == "require_authentication":
                logger.info(f"Authentication requirement changed to: {data['value']}")
                logger.info(
                    "Application restart required for authentication changes to take effect"
                )

            return (
                jsonify(
                    {
                        "key": key,
                        "value": data["value"],
                        "description": description,
                        "updated_at": "now",
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Failed to update setting"}), 500

    except Exception as e:
        logger.error(f"Failed to update setting '{key}': {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/<string:key>", methods=["DELETE"])
def delete_setting(key):
    """Delete a specific setting"""
    try:
        if settings.delete(key):
            return jsonify({"message": f"Setting '{key}' deleted"}), 200
        else:
            return jsonify({"error": "Setting not found"}), 404

    except Exception as e:
        logger.error(f"Failed to delete setting '{key}': {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/bulk", methods=["PUT"])
def update_multiple_settings():
    """Update multiple settings at once"""
    try:
        data = request.get_json()
        if not data or "settings" not in data:
            return jsonify({"error": "Settings data is required"}), 400

        # Convert values to strings for the settings service
        settings_data = {key: str(value) for key, value in data["settings"].items()}

        if settings.set_multiple(settings_data):
            updated_settings = []
            for key, value in settings_data.items():
                updated_settings.append({"key": key, "value": value})

            # Auto-reload Spotify service if any Spotify settings were updated
            spotify_settings_updated = any(
                key.startswith("spotify_") for key in settings_data.keys()
            )
            if spotify_settings_updated:
                try:
                    from src.services.spotify_service import spotify_service

                    updated_spotify_keys = [
                        key
                        for key in settings_data.keys()
                        if key.startswith("spotify_")
                    ]
                    logger.info(
                        f"Reloading Spotify service after bulk update of: {updated_spotify_keys}"
                    )
                    spotify_service.reload_settings()
                    logger.info(
                        f"Spotify service successfully reloaded after bulk update. New redirect URI: {spotify_service.redirect_uri}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to reload Spotify service after bulk update: {e}"
                    )
                    # Continue with the response even if reload fails

            return (
                jsonify(
                    {
                        "updated_settings": updated_settings,
                        "count": len(updated_settings),
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Failed to update settings"}), 500

    except Exception as e:
        logger.error(f"Failed to update multiple settings: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/restart", methods=["POST"])
def restart_application():
    """Restart the application"""
    try:
        import os
        import subprocess
        import threading

        logger.info("Application restart requested via web interface")

        def restart_worker():
            try:
                # Give time for the response to be sent
                import time

                time.sleep(1)

                # Check if systemd service is available and prefer it
                try:
                    result = subprocess.run(
                        ["systemctl", "is-active", "mvidarr.service"],
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0 and result.stdout.strip() == "active":
                        logger.info("Using systemd service restart")
                        # Use management script which has sudo configured properly
                        script_path = os.path.join(
                            os.getcwd(), "scripts", "manage_service.sh"
                        )
                        if os.path.exists(script_path):
                            logger.info("Using management script for systemd restart")
                            subprocess.run([script_path, "restart"], check=True)
                            logger.info(
                                "Systemd service restart initiated successfully via management script"
                            )
                            return
                        else:
                            # Direct systemd call (may require sudo configuration)
                            subprocess.run(
                                ["systemctl", "restart", "mvidarr.service"], check=True
                            )
                            logger.info(
                                "Systemd service restart initiated successfully"
                            )
                            return
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Systemd restart failed: {e}")
                except Exception as e:
                    logger.warning(f"Systemd check failed: {e}")

                # Fallback to management script
                script_path = os.path.join(os.getcwd(), "scripts", "manage_service.sh")
                if os.path.exists(script_path):
                    logger.info("Using management script to restart service")
                    subprocess.run([script_path, "restart"], check=True)
                    return

                # Use the improved restart script
                script_path = os.path.join(
                    os.getcwd(), "scripts", "improved_restart.py"
                )
                if os.path.exists(script_path):
                    logger.info("Using improved Python restart script")
                    # Run the restart script in background with detailed logging
                    with open("/tmp/mvidarr_restart_output.log", "w") as log_file:
                        subprocess.Popen(
                            ["python3", script_path],
                            stdout=log_file,
                            stderr=subprocess.STDOUT,
                            start_new_session=True,
                        )
                    return

                # Fallback to original restart script
                script_path = os.path.join(os.getcwd(), "scripts", "restart_app.py")
                if os.path.exists(script_path):
                    logger.info("Using original Python restart script")
                    subprocess.Popen(["python3", script_path], start_new_session=True)
                    return

                # Last resort: terminate current process
                logger.warning("No restart script found, using direct termination")
                os.kill(os.getpid(), 15)  # SIGTERM

            except Exception as e:
                logger.error(f"Restart worker failed: {e}")
                # Last resort: terminate current process
                try:
                    os.kill(os.getpid(), 15)
                except Exception as kill_error:
                    logger.error(f"Failed to terminate process: {kill_error}")

        # Start restart in background thread
        restart_thread = threading.Thread(target=restart_worker)
        restart_thread.daemon = True
        restart_thread.start()

        return (
            jsonify(
                {
                    "message": "Application restart initiated. Please wait 10-15 seconds and refresh the page."
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to restart application: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/restart-systemd", methods=["POST"])
def restart_systemd_service():
    """Alternative restart endpoint that works directly with systemd (bypasses auth for emergency use)"""
    try:
        import os
        import subprocess
        import threading

        logger.info("Emergency systemd restart requested")

        def systemd_restart_worker():
            try:
                import time

                time.sleep(1)

                # Use management script for systemd restart
                script_path = os.path.join(os.getcwd(), "scripts", "manage_service.sh")
                if os.path.exists(script_path):
                    logger.info("Using management script for emergency systemd restart")
                    subprocess.run([script_path, "restart"], check=True)
                    logger.info("Emergency systemd restart completed successfully")
                else:
                    logger.error("Management script not found for emergency restart")

            except Exception as e:
                logger.error(f"Emergency restart failed: {e}")

        # Start restart in background thread
        restart_thread = threading.Thread(target=systemd_restart_worker)
        restart_thread.daemon = True
        restart_thread.start()

        return (
            jsonify(
                {
                    "message": "Emergency systemd restart initiated. Service will restart shortly."
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Emergency restart failed: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/scheduler/status", methods=["GET"])
def get_scheduler_status():
    """Get current scheduler status and configuration"""
    try:
        from src.services.scheduler_service import scheduler_service

        schedule_info = scheduler_service.get_schedule_info()

        return (
            jsonify(
                {
                    "scheduler": {
                        "running": scheduler_service.running,
                        "schedule_info": schedule_info,
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/scheduler/start", methods=["POST"])
def start_scheduler():
    """Start the scheduler service"""
    try:
        from src.services.scheduler_service import scheduler_service

        if scheduler_service.running:
            return jsonify({"message": "Scheduler is already running"}), 200

        scheduler_service.start()

        return jsonify({"message": "Scheduler started successfully"}), 200

    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/scheduler/stop", methods=["POST"])
def stop_scheduler():
    """Stop the scheduler service"""
    try:
        from src.services.scheduler_service import scheduler_service

        if not scheduler_service.running:
            return jsonify({"message": "Scheduler is not running"}), 200

        scheduler_service.stop()

        return jsonify({"message": "Scheduler stopped successfully"}), 200

    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/scheduler/reload", methods=["POST"])
def reload_scheduler():
    """Reload scheduler configuration from settings"""
    try:
        from src.services.scheduler_service import scheduler_service

        scheduler_service.reload_schedule()

        return (
            jsonify({"message": "Scheduler configuration reloaded successfully"}),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to reload scheduler: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/scheduler/trigger", methods=["POST"])
def trigger_scheduled_download():
    """Manually trigger a scheduled download"""
    try:
        from src.services.scheduler_service import scheduler_service

        # Get max videos setting
        from src.services.settings_service import SettingsService

        max_videos = SettingsService.get_int("auto_download_max_videos", 50)

        # Import and run the download function
        from src.api.videos import download_all_wanted_videos_internal

        result = download_all_wanted_videos_internal(limit=max_videos)

        if result.get("success"):
            return (
                jsonify(
                    {
                        "message": "Manual download triggered successfully",
                        "result": result,
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Manual download failed", "result": result}), 500

    except Exception as e:
        logger.error(f"Failed to trigger scheduled download: {e}")
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/database-config", methods=["GET"])
def get_database_config():
    """Get current database configuration (read-only)"""
    try:
        import os

        from src.config.config import Config

        # Load environment variables to get current database config
        Config.load_env()

        db_config = {
            "db_host": os.environ.get("DB_HOST", "localhost"),
            "db_port": os.environ.get("DB_PORT", "3306"),
            "db_name": os.environ.get("DB_NAME", "mvidarr"),
            "db_user": os.environ.get("DB_USER", "mvidarr"),
            "db_password": "***hidden***",  # Don't expose password
            "db_pool_size": os.environ.get("DB_POOL_SIZE", "10"),
            "db_pool_overflow": os.environ.get("DB_MAX_OVERFLOW", "20"),
            "db_pool_recycle": os.environ.get("DB_POOL_RECYCLE", "3600"),
            "db_pool_timeout": os.environ.get("DB_POOL_TIMEOUT", "30"),
        }

        return jsonify({"database_config": db_config}), 200

    except Exception as e:
        logger.error(f"Failed to get database config: {e}")
        return jsonify({"error": str(e)}), 500
