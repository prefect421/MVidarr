"""
MVidarr Flask Application with Simple Authentication
Single-user authentication system for simple username/password access
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask, g, redirect, request, session, url_for

# Import all existing API blueprints
from src.api.artists import artists_bp
from src.api.health import health_bp
from src.api.settings import settings_bp
from src.api.simple_auth import register_simple_auth_routes
from src.api.videos import videos_bp
from src.config.config import Config
from src.database.connection import init_db
from src.middleware.simple_auth_middleware import init_simple_auth_middleware
from src.services.settings_service import SettingsService
from src.services.simple_auth_service import SimpleAuthService
from src.utils.logger import get_logger, setup_logging


def create_app():
    """Application factory for simple authentication app"""

    app = Flask(
        __name__,
        template_folder=str(project_root / "frontend" / "templates"),
        static_folder=str(project_root / "frontend" / "static"),
    )

    # Load configuration
    config = Config()
    app.config.update(config.to_dict())

    # Initialize database
    init_db(app)

    # Initialize logging
    setup_logging(app)
    logger = get_logger("mvidarr.app")

    # Configure session settings
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
    app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Initialize simple authentication middleware
    init_simple_auth_middleware(app)

    # Register authentication routes
    register_simple_auth_routes(app)

    # Register all existing API blueprints
    app.register_blueprint(artists_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(health_bp)

    # Import and register main routes
    from src.api.routes import register_routes

    register_routes(app)

    @app.before_request
    def before_request():
        """Set up request context"""
        g.require_auth = SettingsService.get_bool("require_authentication", False)
        g.current_user = (
            SimpleAuthService.get_current_username() if g.require_auth else "anonymous"
        )
        g.is_authenticated = (
            SimpleAuthService.is_authenticated() if g.require_auth else True
        )

    @app.context_processor
    def inject_auth_status():
        """Inject authentication status into templates"""
        return {
            "require_auth": g.get("require_auth", False),
            "current_user": g.get("current_user", "anonymous"),
            "is_authenticated": g.get("is_authenticated", True),
        }

    # Custom error handlers
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle unauthorized access"""
        if request.is_json or request.path.startswith("/api/"):
            return {"error": "Authentication required"}, 401
        else:
            return redirect(url_for("simple_auth.login_page"))

    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors"""
        logger.error(f"Internal server error: {error}")
        if request.is_json or request.path.startswith("/api/"):
            return {"error": "Internal server error"}, 500
        else:
            return "Internal Server Error", 500

    logger.info("MVidarr app with simple authentication created")
    return app


def run_app():
    """Run the Flask application with simple authentication"""

    try:
        app = create_app()

        # Get host and port from settings
        host = SettingsService.get("app_host", "0.0.0.0")
        port = SettingsService.get_int("app_port", 5000)
        debug = SettingsService.get_bool("debug_mode", False)

        logger = get_logger("mvidarr.app")
        logger.info(f"Starting MVidarr with Simple Authentication on {host}:{port}")

        if debug:
            logger.warning("Debug mode is enabled - do not use in production!")

        # Initialize default credentials if needed
        username, has_credentials = SimpleAuthService.get_credentials()
        if not has_credentials:
            (
                created,
                username,
                password,
                message,
            ) = SimpleAuthService.initialize_default_credentials()
            if created:
                logger.info(f"Default credentials created: {username}/{password}")

        app.run(host=host, port=port, debug=debug, threaded=True)

    except Exception as e:
        logger = get_logger("mvidarr.app")
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    run_app()
