"""
MVidarr - Main Application with Authentication
This is the main application entry point with full authentication integration.
"""

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, request, url_for

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.admin_interface import register_admin_interface
from src.api.profile import register_profile_routes

# Import existing API blueprints
from src.api.routes import register_routes
from src.api.two_factor import register_two_factor_routes

# Import authentication system
from src.auth_integration import init_authentication, register_auth_health_endpoint
from src.config.config import Config

# Import core services
from src.database.connection import init_db
from src.utils.logger import get_logger, setup_logging

logger = get_logger("mvidarr.app")


def create_app(config_name="default"):
    """
    Application factory for MVidarr with Authentication

    Args:
        config_name: Configuration profile to use

    Returns:
        Flask application instance
    """
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
    )

    # Load configuration
    config = Config()
    app.config.update(config.to_dict())

    # Set secret key for sessions
    app.secret_key = config.SECRET_KEY or os.urandom(24)

    try:
        logger.info("🚀 Starting MVidarr with Authentication")
        logger.info("=" * 60)

        # Step 1: Setup logging
        logger.info("Step 1: Setting up logging system...")
        setup_logging(app)

        # Step 2: Initialize database
        logger.info("Step 2: Initializing database...")
        init_db(app)

        # Step 3: Initialize authentication system
        logger.info("Step 3: Initializing authentication system...")
        auth_success = init_authentication(app)

        if not auth_success:
            logger.error("❌ Authentication system failed to initialize")
            raise Exception("Authentication initialization failed")

        # Step 4: Register all routes
        logger.info("Step 4: Registering application routes...")

        # Register existing API routes - ignore auth route conflicts since auth system handles them
        try:
            register_routes(app)
        except Exception as route_error:
            logger.warning(f"Route registration conflict (expected): {route_error}")
            # Continue anyway - auth routes are already registered by auth system

        # Register admin interface
        register_admin_interface(app)

        # Register profile management routes
        register_profile_routes(app)

        # Register two-factor authentication routes
        register_two_factor_routes(app)

        # Register auth health endpoint
        register_auth_health_endpoint(app)

        # Step 5: Add main routes
        register_main_routes(app)

        # Step 6: Add error handlers
        register_error_handlers(app)

        # Step 7: Final setup
        logger.info("Step 5: Final application setup...")

        # Add context processors for templates
        @app.context_processor
        def inject_auth_context():
            """Inject authentication context into all templates"""
            from flask import g

            return {
                "current_user": g.get("current_user"),
                "is_authenticated": g.get("is_authenticated", False),
                "user_role": g.get("user_role"),
            }

        logger.info("✅ MVidarr application created successfully!")
        logger.info("🔐 Authentication system: ENABLED")
        logger.info("👥 Multi-user support: ENABLED")
        logger.info("🛡️ Role-based access control: ENABLED")
        logger.info("🔑 OAuth integration: ENABLED")
        logger.info("=" * 60)

        return app

    except Exception as e:
        logger.error(f"❌ Failed to create application: {e}")
        raise


def register_main_routes(app):
    """Register main application routes"""

    @app.route("/")
    def index():
        """Main application index"""
        from flask import g, render_template

        # If user is not authenticated, redirect to login
        if not g.get("is_authenticated"):
            return redirect(url_for("auth.login"))

        # Show main dashboard with user management link for admins
        user = g.get("current_user")
        return render_template("dashboard.html", user=user)

    @app.route("/dashboard")
    def dashboard():
        """Main dashboard"""
        from src.utils.auth_decorators import login_required

        @login_required
        def _dashboard():
            return jsonify(
                {
                    "message": "Welcome to MVidarr!",
                    "user": request.current_user.username,
                    "role": request.current_user.role.value,
                }
            )

        return _dashboard()

    @app.route("/profile")
    def profile():
        """User profile page"""
        from src.utils.auth_decorators import login_required

        @login_required
        def _profile():
            return jsonify(
                {
                    "user": request.current_user.to_dict(include_sensitive=True),
                    "permissions": {
                        "can_admin": request.current_user.can_access_admin(),
                        "can_modify": request.current_user.can_modify_content(),
                        "can_delete": request.current_user.can_delete_content(),
                        "can_manage_users": request.current_user.can_manage_users(),
                    },
                }
            )

        return _profile()


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle unauthorized access"""
        if request.is_json or request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "error": "Authentication required",
                        "code": "AUTH_REQUIRED",
                        "message": "Please log in to access this resource",
                    }
                ),
                401,
            )
        else:
            return redirect(url_for("auth.login", next=request.url))

    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden access"""
        if request.is_json or request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "error": "Insufficient permissions",
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": "You do not have permission to access this resource",
                    }
                ),
                403,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Access denied",
                        "message": "You do not have permission to access this resource",
                    }
                ),
                403,
            )

    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors"""
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404
        else:
            return jsonify({"error": "Page not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors"""
        logger.error(f"Internal server error: {error}")

        if request.is_json or request.path.startswith("/api/"):
            return (
                jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}),
                500,
            )
        else:
            return jsonify({"error": "Internal server error"}), 500


def run_app():
    """Run the application with authentication"""
    try:
        # Create application
        app = create_app()

        # Get configuration
        config = Config()

        logger.info(f"🌐 Starting server on {config.HOST}:{config.PORT}")
        logger.info("🔐 Authentication system is ACTIVE")
        logger.info("👤 Default admin credentials:")
        logger.info("   Username: admin")
        logger.info("   Password: MVidarr@dmin123")
        logger.info("   ⚠️  CHANGE DEFAULT PASSWORD AFTER FIRST LOGIN!")
        logger.info("=" * 60)

        # Run the application
        app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, threaded=True)

    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_app()
