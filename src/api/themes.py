"""
API endpoints for theme management and customization
"""

import logging
from functools import wraps

from flask import Blueprint, jsonify, request, session
from sqlalchemy import or_

from src.database.connection import get_db
from src.database.models import CustomTheme, User

logger = logging.getLogger(__name__)

themes_bp = Blueprint("themes", __name__)


def simple_auth_required(f):
    """
    Simple authentication decorator compatible with MVidarr's simple auth system
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated using simple auth session
        if not session.get("authenticated", False):
            return (
                jsonify(
                    {"error": "Authentication required", "login_url": "/simple-login"}
                ),
                401,
            )

        # Get username from session and find user
        username = session.get("username", "admin")

        try:
            with get_db() as db_session:
                user = db_session.query(User).filter_by(username=username).first()
                if not user:
                    # Create a mock admin user for compatibility
                    class MockUser:
                        def __init__(self, username):
                            self.id = 1
                            self.username = username
                            self.is_admin = True

                    user = MockUser(username)

                # Add user to request context for compatibility
                request.current_user = user
                return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"Error in simple auth: {e}")

            # Fallback to mock user
            class MockUser:
                def __init__(self, username):
                    self.id = 1
                    self.username = username
                    self.is_admin = True

            request.current_user = MockUser(username)
            return f(*args, **kwargs)

    return decorated_function


@themes_bp.route("", methods=["GET"])
@simple_auth_required
def get_themes():
    """Get all available themes (built-in and custom)"""
    try:
        user_id = request.current_user.id

        with get_db() as session:
            # Get all themes that are either public, built-in, or created by the current user
            themes = (
                session.query(CustomTheme)
                .filter(
                    or_(
                        CustomTheme.is_public == True,
                        CustomTheme.is_built_in == True,
                        CustomTheme.created_by == user_id,
                    )
                )
                .all()
            )

            # Also include built-in CSS themes
            built_in_themes = [
                {
                    "id": "default",
                    "name": "default",
                    "display_name": "Default",
                    "description": "Default MVidarr theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,  # These use CSS files
                },
                {
                    "id": "cyber",
                    "name": "cyber",
                    "display_name": "Cyber",
                    "description": "Cyberpunk-inspired theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                },
                {
                    "id": "vaporwave",
                    "name": "vaporwave",
                    "display_name": "VaporWave",
                    "description": "Synthwave/vaporwave aesthetic",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                },
                {
                    "id": "lcars_tng",
                    "name": "lcars_tng",
                    "display_name": "LCARS - TNG",
                    "description": "Star Trek: The Next Generation theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                },
                {
                    "id": "lcars_ds9",
                    "name": "lcars_ds9",
                    "display_name": "LCARS - DS9",
                    "description": "Star Trek: Deep Space Nine theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                },
                {
                    "id": "lcars_voy",
                    "name": "lcars_voy",
                    "display_name": "LCARS - Voy",
                    "description": "Star Trek: Voyager theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                },
                {
                    "id": "lcars_tng_e",
                    "name": "lcars_tng_e",
                    "display_name": "LCARS - TNG-E",
                    "description": "Star Trek: Enterprise theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                },
            ]

            custom_themes = [theme.to_dict() for theme in themes]
            all_themes = built_in_themes + custom_themes

            return jsonify({"themes": all_themes, "total": len(all_themes)})

    except Exception as e:
        logger.error(f"Failed to get themes: {e}")
        return jsonify({"error": str(e)}), 500


@themes_bp.route("", methods=["POST"])
@simple_auth_required
def create_theme():
    """Create a new custom theme"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data is required"}), 400

        required_fields = ["name", "display_name", "theme_data"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Field '{field}' is required"}), 400

        user_id = request.current_user.id

        with get_db() as session:
            # Check if theme name already exists
            existing = session.query(CustomTheme).filter_by(name=data["name"]).first()
            if existing:
                return jsonify({"error": "Theme name already exists"}), 400

            # Create new theme
            theme = CustomTheme(
                name=data["name"],
                display_name=data["display_name"],
                description=data.get("description", ""),
                created_by=user_id,
                is_public=data.get("is_public", False),
                is_built_in=False,
                theme_data=data["theme_data"],
            )

            session.add(theme)
            session.commit()

            logger.info(f"Created custom theme '{theme.name}' by user {user_id}")
            return jsonify(theme.to_dict()), 201

    except Exception as e:
        logger.error(f"Failed to create theme: {e}")
        return jsonify({"error": str(e)}), 500


@themes_bp.route("/<int:theme_id>", methods=["GET"])
@simple_auth_required
def get_theme(theme_id):
    """Get a specific theme by ID"""
    try:
        user_id = request.current_user.id

        with get_db() as session:
            theme = session.query(CustomTheme).filter_by(id=theme_id).first()

            if not theme:
                return jsonify({"error": "Theme not found"}), 404

            # Check if user has access to this theme
            if not (
                theme.is_public or theme.is_built_in or theme.created_by == user_id
            ):
                return jsonify({"error": "Access denied"}), 403

            return jsonify(theme.to_dict())

    except Exception as e:
        logger.error(f"Failed to get theme {theme_id}: {e}")
        return jsonify({"error": str(e)}), 500


@themes_bp.route("/<int:theme_id>", methods=["PUT"])
@simple_auth_required
def update_theme(theme_id):
    """Update a custom theme"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data is required"}), 400

        user_id = request.current_user.id

        with get_db() as session:
            theme = session.query(CustomTheme).filter_by(id=theme_id).first()

            if not theme:
                return jsonify({"error": "Theme not found"}), 404

            # Only allow theme creator or admin to edit
            if theme.created_by != user_id and not request.current_user.is_admin:
                return jsonify({"error": "Permission denied"}), 403

            # Don't allow editing built-in themes
            if theme.is_built_in:
                return jsonify({"error": "Cannot edit built-in themes"}), 400

            # Update fields
            if "display_name" in data:
                theme.display_name = data["display_name"]
            if "description" in data:
                theme.description = data["description"]
            if "theme_data" in data:
                theme.theme_data = data["theme_data"]
            if "is_public" in data and request.current_user.is_admin:
                theme.is_public = data["is_public"]

            session.commit()

            logger.info(f"Updated custom theme '{theme.name}' by user {user_id}")
            return jsonify(theme.to_dict())

    except Exception as e:
        logger.error(f"Failed to update theme {theme_id}: {e}")
        return jsonify({"error": str(e)}), 500


@themes_bp.route("/<int:theme_id>", methods=["DELETE"])
@simple_auth_required
def delete_theme(theme_id):
    """Delete a custom theme"""
    try:
        user_id = request.current_user.id

        with get_db() as session:
            theme = session.query(CustomTheme).filter_by(id=theme_id).first()

            if not theme:
                return jsonify({"error": "Theme not found"}), 404

            # Only allow theme creator or admin to delete
            if theme.created_by != user_id and not request.current_user.is_admin:
                return jsonify({"error": "Permission denied"}), 403

            # Don't allow deleting built-in themes
            if theme.is_built_in:
                return jsonify({"error": "Cannot delete built-in themes"}), 400

            theme_name = theme.name
            session.delete(theme)
            session.commit()

            logger.info(f"Deleted custom theme '{theme_name}' by user {user_id}")
            return jsonify({"message": "Theme deleted successfully"})

    except Exception as e:
        logger.error(f"Failed to delete theme {theme_id}: {e}")
        return jsonify({"error": str(e)}), 500


@themes_bp.route("/<int:theme_id>/duplicate", methods=["POST"])
@simple_auth_required
def duplicate_theme(theme_id):
    """Duplicate an existing theme for customization"""
    try:
        data = request.get_json() or {}
        user_id = request.current_user.id

        with get_db() as session:
            original_theme = session.query(CustomTheme).filter_by(id=theme_id).first()

            if not original_theme:
                return jsonify({"error": "Theme not found"}), 404

            # Check if user has access to this theme
            if not (
                original_theme.is_public
                or original_theme.is_built_in
                or original_theme.created_by == user_id
            ):
                return jsonify({"error": "Access denied"}), 403

            # Generate unique name for duplicate
            base_name = data.get("name", f"{original_theme.name}_copy")
            new_name = base_name
            counter = 1

            while session.query(CustomTheme).filter_by(name=new_name).first():
                new_name = f"{base_name}_{counter}"
                counter += 1

            # Create duplicate theme
            duplicate = CustomTheme(
                name=new_name,
                display_name=data.get(
                    "display_name", f"{original_theme.display_name} (Copy)"
                ),
                description=data.get(
                    "description", f"Copy of {original_theme.display_name}"
                ),
                created_by=user_id,
                is_public=False,  # Duplicates are private by default
                is_built_in=False,
                theme_data=(
                    original_theme.theme_data.copy()
                    if original_theme.theme_data
                    else {}
                ),
            )

            session.add(duplicate)
            session.commit()

            logger.info(
                f"Duplicated theme '{original_theme.name}' as '{duplicate.name}' by user {user_id}"
            )
            return jsonify(duplicate.to_dict()), 201

    except Exception as e:
        logger.error(f"Failed to duplicate theme {theme_id}: {e}")
        return jsonify({"error": str(e)}), 500


@themes_bp.route("/built-in/<string:theme_name>/extract", methods=["POST"])
@simple_auth_required
def extract_built_in_theme(theme_name):
    """Extract CSS variables from a built-in theme for customization"""
    try:
        # This endpoint would parse the CSS file and extract the theme variables
        # For now, return a basic structure that can be customized

        built_in_themes = {
            "default": {
                "--bg-primary": "#1a1a1a",
                "--bg-secondary": "#2d2d2d",
                "--bg-tertiary": "#3a3a3a",
                "--text-primary": "#ffffff",
                "--text-secondary": "#cccccc",
                "--text-accent": "#4a9eff",
                "--btn-primary-bg": "#4a9eff",
                "--btn-primary-text": "#ffffff",
                "--border-primary": "#444444",
                "--success": "#28a745",
                "--warning": "#ffc107",
                "--error": "#dc3545",
                "--info": "#17a2b8",
            },
            "cyber": {
                "--bg-primary": "#0a0a0a",
                "--bg-secondary": "#1a1a2e",
                "--bg-tertiary": "#16213e",
                "--text-primary": "#00ff00",
                "--text-secondary": "#00cccc",
                "--text-accent": "#ff00ff",
                "--btn-primary-bg": "#00ff00",
                "--btn-primary-text": "#000000",
                "--border-primary": "#00ff00",
                "--success": "#00ff00",
                "--warning": "#ffff00",
                "--error": "#ff0000",
                "--info": "#00ffff",
            },
            "vaporwave": {
                "--bg-primary": "#0d0221",
                "--bg-secondary": "#1a0933",
                "--bg-tertiary": "#2d1b69",
                "--text-primary": "#ffffff",
                "--text-secondary": "#e0b3ff",
                "--text-accent": "#ff3cac",
                "--btn-primary-bg": "#ff3cac",
                "--btn-primary-text": "#ffffff",
                "--border-primary": "#662d91",
                "--success": "#00ff88",
                "--warning": "#ffaa00",
                "--error": "#ff0080",
                "--info": "#00ddff",
            },
            "lcars_tng": {
                "--bg-primary": "#000000",
                "--bg-secondary": "#1a1a1a",
                "--bg-tertiary": "#333333",
                "--text-primary": "#ffffff",
                "--text-secondary": "#cccccc",
                "--text-accent": "#fbb03b",
                "--btn-primary-bg": "#fbb03b",
                "--btn-primary-text": "#000000",
                "--border-primary": "#fbb03b",
                "--success": "#00ff00",
                "--warning": "#ffff00",
                "--error": "#ff0000",
                "--info": "#00ffff",
            },
            "lcars_ds9": {
                "--bg-primary": "#000000",
                "--bg-secondary": "#1a1a1a",
                "--bg-tertiary": "#333333",
                "--text-primary": "#ffffff",
                "--text-secondary": "#cccccc",
                "--text-accent": "#c04c00",
                "--btn-primary-bg": "#c04c00",
                "--btn-primary-text": "#ffffff",
                "--border-primary": "#c04c00",
                "--success": "#00ff00",
                "--warning": "#ffff00",
                "--error": "#ff0000",
                "--info": "#00ffff",
            },
            "lcars_voy": {
                "--bg-primary": "#000000",
                "--bg-secondary": "#1a1a1a",
                "--bg-tertiary": "#333333",
                "--text-primary": "#ffffff",
                "--text-secondary": "#cccccc",
                "--text-accent": "#ffb07c",
                "--btn-primary-bg": "#ffb07c",
                "--btn-primary-text": "#1a1a1a",
                "--border-primary": "#ffb07c",
                "--success": "#00ff00",
                "--warning": "#ffff00",
                "--error": "#ff0000",
                "--info": "#00ffff",
            },
            "lcars_tng_e": {
                "--bg-primary": "#000000",
                "--bg-secondary": "#1a1a1a",
                "--bg-tertiary": "#333333",
                "--text-primary": "#ffffff",
                "--text-secondary": "#cccccc",
                "--text-accent": "#d97904",
                "--btn-primary-bg": "#d97904",
                "--btn-primary-text": "#ffffff",
                "--border-primary": "#d97904",
                "--success": "#00ff00",
                "--warning": "#ffff00",
                "--error": "#ff0000",
                "--info": "#00ffff",
            },
        }

        if theme_name not in built_in_themes:
            return jsonify({"error": "Built-in theme not found"}), 404

        return jsonify(
            {"theme_name": theme_name, "variables": built_in_themes[theme_name]}
        )

    except Exception as e:
        logger.error(f"Failed to extract built-in theme {theme_name}: {e}")
        return jsonify({"error": str(e)}), 500


@themes_bp.route("/apply", methods=["POST"])
@simple_auth_required
def apply_theme():
    """Apply a theme for the current user"""
    try:
        data = request.get_json()
        if not data or "theme_name" not in data:
            return jsonify({"error": "Theme name is required"}), 400

        theme_name = data["theme_name"]
        user_id = request.current_user.id

        # Import settings service to save theme preference
        from src.services.settings_service import SettingsService
        
        # Save the theme preference
        if SettingsService.set("ui_theme", theme_name, "User interface theme selection"):
            logger.info(f"Applied theme '{theme_name}' for user {user_id}")
            return jsonify({
                "message": f"Theme '{theme_name}' applied successfully",
                "theme": theme_name
            }), 200
        else:
            return jsonify({"error": "Failed to save theme preference"}), 500

    except Exception as e:
        logger.error(f"Failed to apply theme: {e}")
        return jsonify({"error": str(e)}), 500


@themes_bp.route("/current", methods=["GET"])
@simple_auth_required
def get_current_theme():
    """Get the current user's applied theme"""
    try:
        # Import settings service to get current theme
        from src.services.settings_service import SettingsService
        
        current_theme = SettingsService.get("ui_theme", "default")
        
        return jsonify({
            "current_theme": current_theme
        }), 200

    except Exception as e:
        logger.error(f"Failed to get current theme: {e}")
        return jsonify({"error": str(e)}), 500
