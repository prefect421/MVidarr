"""
Authentication API endpoints for MVidarr
Provides login, logout, OAuth, and user session management.
"""

from flask import Blueprint, jsonify, redirect, render_template, request
from flask import session as flask_session
from flask import url_for

from src.database.models import UserRole
from src.services.audit_service import (
    AuditEventType,
    AuditService,
    log_login_failed,
    log_login_success,
    log_logout,
    log_oauth_login_failed,
    log_oauth_login_success,
)
from src.services.auth_service import (
    AuthenticationError,
    AuthorizationError,
    AuthService,
)
from src.services.oauth_service import oauth_service
from src.utils.auth_decorators import admin_required, login_required
from src.utils.logger import get_logger

logger = get_logger("mvidarr.auth.api")

# Create authentication blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET"])
def login_page():
    """Show login page"""
    try:
        # Check if user is already authenticated
        session_token = flask_session.get("session_token")
        if session_token:
            user = AuthService.get_user_by_session_token(session_token)
            if user:
                # User is already logged in, redirect to dashboard
                return redirect("/")

        # Get available OAuth providers
        oauth_providers = {}
        try:
            if oauth_service.is_oauth_enabled():
                oauth_providers = oauth_service.get_available_providers()
        except Exception as e:
            logger.warning(f"Failed to get OAuth providers: {e}")

        # Show login page
        return render_template(
            "auth/login.html",
            oauth_providers=oauth_providers,
            error=request.args.get("error"),
        )

    except Exception as e:
        logger.error(f"Login page error: {e}")
        return render_template(
            "auth/login.html", oauth_providers={}, error="Failed to load login page"
        )


@auth_bp.route("/login", methods=["POST"])
def login():
    """User login endpoint"""
    try:
        # Get login credentials
        data = request.get_json() if request.is_json else request.form
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            log_login_failed(username or "unknown", "Missing credentials")
            return jsonify({"error": "Username and password are required"}), 400

        # Authenticate user
        ip_address = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        user_agent = request.headers.get("User-Agent")

        (
            success,
            message,
            user_data,
            session_obj,
            requires_2fa,
        ) = AuthService.authenticate_user(username, password, ip_address, user_agent)

        if success and user_data:
            # Check if 2FA is required
            if requires_2fa:
                # Store partial session for 2FA verification
                flask_session["temp_user_id"] = user_data["id"]
                flask_session["temp_login_time"] = (
                    user_data["last_login"].isoformat()
                    if user_data["last_login"]
                    else None
                )

                if request.is_json:
                    return jsonify(
                        {
                            "success": False,
                            "requires_2fa": True,
                            "message": "Two-factor authentication required",
                            "user_id": user_data["id"],
                        }
                    )
                else:
                    # Redirect to 2FA verification page
                    return redirect(url_for("two_factor.verify_login"))

            elif session_obj:
                # Complete login - store session token (session_obj is now a dict)
                flask_session["session_token"] = session_obj["session_token"]
                flask_session["user_id"] = user_data["id"]

                # Clear any temporary 2FA session data
                flask_session.pop("temp_user_id", None)
                flask_session.pop("temp_login_time", None)

                # Log successful login (create a minimal user-like object for logging)
                from types import SimpleNamespace

                user_for_logging = SimpleNamespace(
                    id=user_data["id"],
                    username=user_data["username"],
                    email=user_data["email"],
                )
                log_login_success(user_for_logging)

                # Handle different response types
                if request.is_json:
                    # Return JSON response for API calls
                    return jsonify(
                        {
                            "success": True,
                            "message": "Login successful",
                            "user": {
                                "id": user_data["id"],
                                "username": user_data["username"],
                                "email": user_data["email"],
                                "role": user_data["role"],
                                "can_admin": user_data["role"] == "ADMIN",
                                "can_modify": user_data["role"]
                                in ["ADMIN", "MANAGER", "USER"],
                                "can_delete": user_data["role"] in ["ADMIN", "MANAGER"],
                            },
                            "session": {"token": session_obj["session_token"]},
                        }
                    )
                else:
                    # Safe redirect for form submissions
                    next_url = request.args.get("next", "/")
                    from src.utils.security import safe_redirect

                    return safe_redirect(next_url)

        # Login failed
        log_login_failed(username, message)

        if request.is_json:
            return jsonify({"error": message}), 401
        else:
            # Redirect back to login page with error
            return redirect(url_for("auth.login_page", error=message))

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed due to internal error"}), 500


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """User logout endpoint"""
    try:
        user = request.current_user
        session_token = flask_session.get("session_token")

        if session_token:
            # Revoke session
            AuthService.logout_user(session_token)

        # Clear Flask session
        flask_session.clear()

        # Log logout
        log_logout(user)

        return jsonify({"success": True, "message": "Logged out successfully"})

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"error": "Logout failed"}), 500


@auth_bp.route("/oauth/<provider>/login")
def oauth_login(provider):
    """Initiate OAuth login flow"""
    try:
        success, auth_url, state = oauth_service.initiate_oauth_flow(provider)

        if success:
            AuditService.log_oauth_event(
                AuditEventType.OAUTH_LOGIN_INITIATED,
                f"OAuth login flow initiated",
                provider=provider,
                success=True,
            )

            return jsonify({"auth_url": auth_url, "state": state})
        else:
            log_oauth_login_failed(
                provider, auth_url
            )  # auth_url contains error message
            return jsonify({"error": auth_url}), 400

    except Exception as e:
        logger.error(f"OAuth login initiation error: {e}")
        log_oauth_login_failed(provider, str(e))
        return jsonify({"error": "OAuth login failed"}), 500


@auth_bp.route("/oauth/<provider>/callback")
def oauth_callback(provider):
    """Handle OAuth callback"""
    try:
        code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")

        if error:
            log_oauth_login_failed(provider, f"OAuth provider error: {error}")
            return jsonify({"error": f"OAuth error: {error}"}), 400

        if not code or not state:
            log_oauth_login_failed(provider, "Missing authorization code or state")
            return jsonify({"error": "Missing authorization code or state"}), 400

        # Handle OAuth callback
        success, message, user, session_obj = oauth_service.handle_oauth_callback(
            provider, code, state
        )

        if success and user and session_obj:
            # Store session token (session_obj is now a dict for consistency)
            session_token = (
                session_obj["session_token"]
                if isinstance(session_obj, dict)
                else session_obj.session_token
            )
            flask_session["session_token"] = session_token
            flask_session["user_id"] = user.id

            # Log successful OAuth login
            log_oauth_login_success(user, provider)

            return jsonify(
                {
                    "success": True,
                    "message": "OAuth login successful",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role.value,
                        "can_admin": user.can_access_admin(),
                        "can_modify": user.can_modify_content(),
                        "can_delete": user.can_delete_content(),
                    },
                }
            )
        else:
            log_oauth_login_failed(provider, message)
            return jsonify({"error": message}), 401

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        log_oauth_login_failed(provider, str(e))
        return jsonify({"error": "OAuth authentication failed"}), 500


@auth_bp.route("/session", methods=["GET"])
@login_required
def get_session_info():
    """Get current session information"""
    try:
        user = request.current_user
        session_token = flask_session.get("session_token")

        if not session_token:
            return jsonify({"error": "No active session"}), 401

        # Get session info from database
        from src.database.connection import get_db
        from src.database.models import UserSession

        with get_db() as db_session:
            user_session = (
                db_session.query(UserSession)
                .filter_by(session_token=session_token)
                .first()
            )

            if not user_session:
                return jsonify({"error": "Session not found"}), 401

            return jsonify(
                {
                    "session": user_session.to_dict(),
                    "user": user.to_dict(),
                    "permissions": {
                        "can_admin": user.can_access_admin(),
                        "can_modify": user.can_modify_content(),
                        "can_delete": user.can_delete_content(),
                        "can_manage_users": user.can_manage_users(),
                    },
                }
            )

    except Exception as e:
        logger.error(f"Session info error: {e}")
        return jsonify({"error": "Failed to get session info"}), 500


@auth_bp.route("/check", methods=["GET"])
def check_auth():
    """Check authentication status"""
    try:
        # First check for full authentication system session token
        session_token = flask_session.get("session_token")

        if session_token:
            user_data = AuthService.get_user_by_session_token(session_token)

            if user_data:
                return jsonify(
                    {
                        "authenticated": True,
                        "user": {
                            "id": user_data["id"],
                            "username": user_data["username"],
                            "email": user_data["email"],
                            "role": user_data["role"],
                            "can_admin": user_data["can_access_admin"],
                            "can_modify": user_data["can_modify_content"],
                            "can_delete": user_data["can_delete_content"],
                        },
                    }
                )

        # Check for simple authentication (from dynamic auth middleware)
        is_authenticated = flask_session.get("authenticated", False)
        username = flask_session.get("username")
        role = flask_session.get("role", "user")

        if is_authenticated and username:
            # Map simple role to capabilities
            can_admin = role.lower() == "admin"
            can_modify = role.lower() in ["admin", "manager", "user"]
            can_delete = role.lower() in ["admin", "manager"]

            return jsonify(
                {
                    "authenticated": True,
                    "user": {
                        "id": 1,  # Simple auth doesn't have real user IDs
                        "username": username,
                        "email": f"{username}@mvidarr.local",
                        "role": role.upper(),
                        "can_admin": can_admin,
                        "can_modify": can_modify,
                        "can_delete": can_delete,
                    },
                }
            )

        return jsonify({"authenticated": False})

    except Exception as e:
        logger.error(f"Auth check error: {e}")
        return jsonify({"authenticated": False, "error": "Check failed"}), 500


@auth_bp.route("/credentials", methods=["GET"])
def get_credentials():
    """Get current stored username for simple auth (password not returned)"""
    try:
        from src.services.simple_auth_service import SimpleAuthService

        username, has_credentials = SimpleAuthService.get_credentials()
        return jsonify({"username": username, "has_credentials": has_credentials})
    except Exception as e:
        logger.error(f"Get credentials error: {e}")
        return jsonify({"error": "Failed to get credentials"}), 500


@auth_bp.route("/credentials", methods=["POST"])
def update_credentials():
    """Update username and password for simple auth"""
    try:
        from src.services.simple_auth_service import SimpleAuthService

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        success, message = SimpleAuthService.set_credentials(username, password)

        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"error": message}), 400

    except Exception as e:
        logger.error(f"Update credentials error: {e}")
        return jsonify({"error": "Failed to update credentials"}), 500


@auth_bp.route("/credentials/reset", methods=["POST"])
def reset_credentials():
    """Reset authentication credentials to defaults (admin/mvidarr)"""
    try:
        from src.database.init_db import ensure_default_credentials

        # Force reset to defaults
        success = ensure_default_credentials(force_reset=True)

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": "Credentials reset to defaults",
                    "username": "admin",
                    "password": "mvidarr",
                }
            )
        else:
            return jsonify({"error": "Failed to reset credentials"}), 500

    except Exception as e:
        logger.error(f"Reset credentials error: {e}")
        return jsonify({"error": "Failed to reset credentials"}), 500


# Register the blueprint with the app
def register_auth_routes(app):
    """Register authentication routes with Flask app"""
    app.register_blueprint(auth_bp)
    logger.info("Authentication routes registered")
