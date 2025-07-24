"""
User Profile Management API for MVidarr
Provides self-service user account management functionality.
"""

import json
from datetime import datetime, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from src.database.connection import get_db
from src.database.models import User
from src.services.audit_service import AuditService
from src.services.auth_service import AuthService
from src.utils.auth_decorators import login_required
from src.utils.logger import get_logger

logger = get_logger("mvidarr.profile")

# Create profile blueprint
profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/")
@login_required
def profile_page():
    """User profile management page"""
    try:
        user = request.current_user

        # Parse user preferences
        preferences = {}
        if user.preferences:
            try:
                preferences = (
                    json.loads(user.preferences)
                    if isinstance(user.preferences, str)
                    else user.preferences
                )
            except (json.JSONDecodeError, TypeError):
                preferences = {}

        return render_template(
            "profile/profile.html", user=user, preferences=preferences
        )

    except Exception as e:
        logger.error(f"Profile page error: {e}")
        flash(f"Error loading profile: {e}", "error")
        return redirect(url_for("main.index"))


@profile_bp.route("/api/info")
@login_required
def get_profile_info():
    """Get current user profile information"""
    try:
        user = request.current_user

        # Parse preferences
        preferences = {}
        if user.preferences:
            try:
                preferences = (
                    json.loads(user.preferences)
                    if isinstance(user.preferences, str)
                    else user.preferences
                )
            except (json.JSONDecodeError, TypeError):
                preferences = {}

        profile_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_email_verified": user.is_email_verified,
            "two_factor_enabled": user.two_factor_enabled,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "last_login_ip": user.last_login_ip,
            "password_changed_at": user.password_changed_at.isoformat()
            if user.password_changed_at
            else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "preferences": preferences,
        }

        return jsonify({"success": True, "profile": profile_data})

    except Exception as e:
        logger.error(f"Get profile info error: {e}")
        return jsonify({"error": "Failed to retrieve profile information"}), 500


@profile_bp.route("/api/update", methods=["POST"])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        user = request.current_user
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        updated_fields = []

        with get_db() as session:
            db_user = session.query(User).filter_by(id=user.id).first()
            if not db_user:
                return jsonify({"error": "User not found"}), 404

            # Update email if provided
            if "email" in data:
                new_email = data["email"].strip()
                if new_email != db_user.email:
                    # Check if email is already in use
                    existing_user = (
                        session.query(User).filter_by(email=new_email).first()
                    )
                    if existing_user and existing_user.id != db_user.id:
                        return (
                            jsonify({"error": "Email address is already in use"}),
                            400,
                        )

                    db_user.email = new_email
                    db_user.is_email_verified = False  # Reset verification status
                    updated_fields.append("email")

            # Update preferences if provided
            if "preferences" in data:
                preferences = data["preferences"]
                if isinstance(preferences, dict):
                    db_user.preferences = json.dumps(preferences)
                    updated_fields.append("preferences")

            # Update timezone preference
            if "timezone" in data:
                current_prefs = {}
                if db_user.preferences:
                    try:
                        current_prefs = (
                            json.loads(db_user.preferences)
                            if isinstance(db_user.preferences, str)
                            else db_user.preferences
                        )
                    except (json.JSONDecodeError, TypeError):
                        current_prefs = {}

                current_prefs["timezone"] = data["timezone"]
                db_user.preferences = json.dumps(current_prefs)
                updated_fields.append("timezone")

            # Update language preference
            if "language" in data:
                current_prefs = {}
                if db_user.preferences:
                    try:
                        current_prefs = (
                            json.loads(db_user.preferences)
                            if isinstance(db_user.preferences, str)
                            else db_user.preferences
                        )
                    except (json.JSONDecodeError, TypeError):
                        current_prefs = {}

                current_prefs["language"] = data["language"]
                db_user.preferences = json.dumps(current_prefs)
                updated_fields.append("language")

            # Update notification preferences
            if "notifications" in data:
                current_prefs = {}
                if db_user.preferences:
                    try:
                        current_prefs = (
                            json.loads(db_user.preferences)
                            if isinstance(db_user.preferences, str)
                            else db_user.preferences
                        )
                    except (json.JSONDecodeError, TypeError):
                        current_prefs = {}

                current_prefs["notifications"] = data["notifications"]
                db_user.preferences = json.dumps(current_prefs)
                updated_fields.append("notifications")

            db_user.updated_at = datetime.now(timezone.utc)
            session.commit()

        # Log profile update
        AuditService.log_user_action(
            "update_profile",
            user=user,
            additional_data={
                "updated_fields": updated_fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(f"Profile updated for user {user.username}: {updated_fields}")

        return jsonify(
            {
                "success": True,
                "message": "Profile updated successfully",
                "updated_fields": updated_fields,
            }
        )

    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return jsonify({"error": "Failed to update profile"}), 500


@profile_bp.route("/api/change-password", methods=["POST"])
@login_required
def change_password():
    """Change user password"""
    try:
        user = request.current_user
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        confirm_password = data.get("confirm_password", "")

        # Validate input
        if not current_password:
            return jsonify({"error": "Current password is required"}), 400

        if not new_password:
            return jsonify({"error": "New password is required"}), 400

        if new_password != confirm_password:
            return jsonify({"error": "New passwords do not match"}), 400

        # Verify current password
        if not check_password_hash(user.password_hash, current_password):
            # Log failed password change attempt
            AuditService.log_security_event(
                "password_change_failed",
                user=user,
                additional_data={
                    "reason": "incorrect_current_password",
                    "ip_address": request.remote_addr,
                    "user_agent": request.headers.get("User-Agent", "Unknown"),
                },
            )
            return jsonify({"error": "Current password is incorrect"}), 400

        # Validate new password strength
        password_validation = AuthService.validate_password_strength(new_password)
        if not password_validation["valid"]:
            return (
                jsonify(
                    {
                        "error": "Password does not meet security requirements",
                        "requirements": password_validation["requirements"],
                    }
                ),
                400,
            )

        # Update password
        with get_db() as session:
            db_user = session.query(User).filter_by(id=user.id).first()
            if not db_user:
                return jsonify({"error": "User not found"}), 404

            # Generate new password hash
            db_user.password_hash = generate_password_hash(new_password)
            db_user.password_changed_at = datetime.now(timezone.utc)
            db_user.updated_at = datetime.now(timezone.utc)

            # Reset failed login attempts on successful password change
            db_user.failed_login_attempts = 0
            db_user.locked_until = None

            session.commit()

        # Log successful password change
        AuditService.log_user_action(
            "password_changed",
            user=user,
            additional_data={
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent", "Unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Revoke all other sessions for security
        AuthService.revoke_all_user_sessions_except_current(
            user.id, request.headers.get("Authorization", "")
        )

        logger.info(f"Password changed successfully for user {user.username}")

        return jsonify(
            {
                "success": True,
                "message": "Password changed successfully. All other sessions have been logged out for security.",
            }
        )

    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({"error": "Failed to change password"}), 500


@profile_bp.route("/api/sessions")
@login_required
def get_user_sessions():
    """Get current user's active sessions"""
    try:
        user = request.current_user

        from src.database.models import SessionStatus, UserSession

        with get_db() as session:
            sessions = (
                session.query(UserSession)
                .filter_by(user_id=user.id, status=SessionStatus.ACTIVE)
                .order_by(UserSession.last_activity.desc())
                .all()
            )

            session_data = []
            current_session_token = request.headers.get("Authorization", "").replace(
                "Bearer ", ""
            )

            for sess in sessions:
                is_current = sess.session_token == current_session_token
                session_info = {
                    "id": sess.id,
                    "ip_address": sess.ip_address,
                    "user_agent": sess.user_agent,
                    "created_at": sess.created_at.isoformat()
                    if sess.created_at
                    else None,
                    "last_activity": sess.last_activity.isoformat()
                    if sess.last_activity
                    else None,
                    "expires_at": sess.expires_at.isoformat()
                    if sess.expires_at
                    else None,
                    "is_current": is_current,
                }
                session_data.append(session_info)

        return jsonify(
            {
                "success": True,
                "sessions": session_data,
                "total_sessions": len(session_data),
            }
        )

    except Exception as e:
        logger.error(f"Get user sessions error: {e}")
        return jsonify({"error": "Failed to retrieve sessions"}), 500


@profile_bp.route("/api/sessions/<int:session_id>/revoke", methods=["POST"])
@login_required
def revoke_session(session_id):
    """Revoke a specific user session"""
    try:
        user = request.current_user
        current_session_token = request.headers.get("Authorization", "").replace(
            "Bearer ", ""
        )

        from src.database.models import SessionStatus, UserSession

        with get_db() as session:
            user_session = (
                session.query(UserSession)
                .filter_by(id=session_id, user_id=user.id)
                .first()
            )

            if not user_session:
                return jsonify({"error": "Session not found"}), 404

            # Prevent revoking current session
            if user_session.session_token == current_session_token:
                return (
                    jsonify(
                        {"error": "Cannot revoke current session. Use logout instead."}
                    ),
                    400,
                )

            # Revoke the session
            user_session.status = SessionStatus.REVOKED
            session.commit()

        # Log session revocation
        AuditService.log_user_action(
            "session_revoked",
            user=user,
            additional_data={
                "revoked_session_id": session_id,
                "ip_address": request.remote_addr,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(f"Session {session_id} revoked by user {user.username}")

        return jsonify({"success": True, "message": "Session revoked successfully"})

    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        return jsonify({"error": "Failed to revoke session"}), 500


@profile_bp.route("/api/export", methods=["GET"])
@login_required
def export_profile_data():
    """Export user profile data"""
    try:
        user = request.current_user

        # Parse preferences
        preferences = {}
        if user.preferences:
            try:
                preferences = (
                    json.loads(user.preferences)
                    if isinstance(user.preferences, str)
                    else user.preferences
                )
            except (json.JSONDecodeError, TypeError):
                preferences = {}

        # Get user sessions
        from src.database.models import UserSession

        with get_db() as session:
            sessions = session.query(UserSession).filter_by(user_id=user.id).all()
            session_data = []

            for sess in sessions:
                session_info = {
                    "created_at": sess.created_at.isoformat()
                    if sess.created_at
                    else None,
                    "last_activity": sess.last_activity.isoformat()
                    if sess.last_activity
                    else None,
                    "ip_address": sess.ip_address,
                    "status": sess.status.value,
                }
                session_data.append(session_info)

        export_data = {
            "profile": {
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "password_changed_at": user.password_changed_at.isoformat()
                if user.password_changed_at
                else None,
                "preferences": preferences,
            },
            "sessions": session_data,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "export_version": "1.0",
        }

        # Log data export
        AuditService.log_user_action(
            "profile_data_exported",
            user=user,
            additional_data={
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "ip_address": request.remote_addr,
            },
        )

        return jsonify({"success": True, "data": export_data})

    except Exception as e:
        logger.error(f"Export profile data error: {e}")
        return jsonify({"error": "Failed to export profile data"}), 500


# Register the blueprint
def register_profile_routes(app):
    """Register profile routes with Flask app"""
    app.register_blueprint(profile_bp)
    logger.info("Profile management routes registered")
