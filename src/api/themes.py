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
        logger.info(f"Loading themes for user {user_id}")

        with get_db() as session:
            # Get all themes that are either public, built-in, or created by the current user
            try:
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
                logger.info(f"Found {len(themes)} custom themes in database")
            except Exception as db_error:
                logger.error(f"Database error querying themes: {db_error}")
                # Continue with empty themes list if database query fails
                themes = []

            # Built-in CSS themes (these are loaded from CSS files, not database)
            built_in_themes = [
                {
                    "id": "default",
                    "name": "default",
                    "display_name": "Default",
                    "description": "Default MVidarr theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                    "light_theme_data": None,
                },
                {
                    "id": "cyber",
                    "name": "cyber",
                    "display_name": "Cyber",
                    "description": "Cyberpunk-inspired theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                    "light_theme_data": None,
                },
                {
                    "id": "vaporwave",
                    "name": "vaporwave",
                    "display_name": "VaporWave",
                    "description": "Synthwave/vaporwave aesthetic",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                    "light_theme_data": None,
                },
                {
                    "id": "lcars_tng",
                    "name": "lcars_tng",
                    "display_name": "LCARS - TNG",
                    "description": "Star Trek: The Next Generation theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                    "light_theme_data": None,
                },
            ]

            # Convert custom themes to dict format safely
            custom_themes = []
            custom_theme_names = set()  # Track which built-in themes have been customized
            
            for theme in themes:
                try:
                    theme_dict = theme.to_dict()
                    custom_themes.append(theme_dict)
                    if theme.is_built_in:
                        custom_theme_names.add(theme.name)
                except Exception as theme_error:
                    logger.error(f"Error converting theme {theme.id} to dict: {theme_error}")
                    continue
            
            # Filter out built-in themes that have database records (avoid duplicates)
            filtered_built_in_themes = [
                theme for theme in built_in_themes 
                if theme["name"] not in custom_theme_names
            ]
            
            logger.info(f"Successfully converted {len(custom_themes)} custom themes")
            logger.info(f"Filtered {len(filtered_built_in_themes)} built-in themes (avoiding {len(custom_theme_names)} duplicates)")
            
            all_themes = filtered_built_in_themes + custom_themes  
            logger.info(f"Returning {len(all_themes)} total themes")

            return jsonify({"themes": all_themes, "total": len(all_themes)})

    except Exception as e:
        logger.error(f"Error loading themes: {e}")
        return jsonify({"error": "Failed to load themes", "details": str(e)}), 500


@themes_bp.route("", methods=["POST"])
@simple_auth_required
def create_theme():
    """Create a new custom theme"""
    try:
        data = request.get_json()
        user_id = request.current_user.id

        # Validate required fields
        if not data.get("name"):
            return jsonify({"error": "Theme name is required"}), 400
        if not data.get("display_name"):
            return jsonify({"error": "Display name is required"}), 400
        if not data.get("theme_data"):
            return jsonify({"error": "Theme data is required"}), 400

        with get_db() as session:
            # Check if theme name already exists
            existing = session.query(CustomTheme).filter_by(name=data["name"]).first()
            if existing:
                return jsonify({"error": "Theme name already exists"}), 409

            # Create new theme
            theme = CustomTheme(
                name=data["name"],
                display_name=data["display_name"],
                description=data.get("description", ""),
                created_by=user_id,
                is_public=data.get("is_public", False),
                is_built_in=False,
                theme_data=data["theme_data"],
                light_theme_data=data.get("light_theme_data")
            )

            session.add(theme)
            session.commit()

            logger.info(f"Created theme '{theme.name}' by user {user_id}")
            return jsonify(theme.to_dict()), 201

    except Exception as e:
        logger.error(f"Error creating theme: {e}")
        return jsonify({"error": "Failed to create theme", "details": str(e)}), 500


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

            # Check permissions
            if not theme.is_public and not theme.is_built_in and theme.created_by != user_id:
                return jsonify({"error": "Access denied"}), 403

            return jsonify(theme.to_dict())

    except Exception as e:
        logger.error(f"Error getting theme {theme_id}: {e}")
        return jsonify({"error": "Failed to get theme", "details": str(e)}), 500


@themes_bp.route("/<int:theme_id>", methods=["PUT"])
@simple_auth_required
def update_theme(theme_id):
    """Update a custom theme"""
    try:
        data = request.get_json()
        user_id = request.current_user.id

        with get_db() as session:
            theme = session.query(CustomTheme).filter_by(id=theme_id).first()
            if not theme:
                return jsonify({"error": "Theme not found"}), 404

            # Check permissions - only creator can edit (unless admin)
            if theme.created_by != user_id and not getattr(request.current_user, 'is_admin', False):
                return jsonify({"error": "Access denied"}), 403

            # Update theme fields if provided
            if "display_name" in data:
                theme.display_name = data["display_name"]
            if "description" in data:
                theme.description = data["description"]
            if "theme_data" in data:
                theme.theme_data = data["theme_data"]
            if "light_theme_data" in data:
                theme.light_theme_data = data["light_theme_data"]
            if "is_public" in data:
                theme.is_public = data["is_public"]

            session.commit()
            logger.info(f"Updated theme '{theme.name}' by user {user_id}")
            return jsonify(theme.to_dict())

    except Exception as e:
        logger.error(f"Error updating theme {theme_id}: {e}")
        return jsonify({"error": "Failed to update theme", "details": str(e)}), 500


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

            # Check permissions - only creator can delete (unless admin)
            if theme.created_by != user_id and not getattr(request.current_user, 'is_admin', False):
                return jsonify({"error": "Access denied"}), 403

            # Don't allow deleting built-in themes
            if theme.is_built_in:
                return jsonify({"error": "Cannot delete built-in themes"}), 400

            theme_name = theme.name
            session.delete(theme)
            session.commit()

            logger.info(f"Deleted theme '{theme_name}' by user {user_id}")
            return jsonify({"message": "Theme deleted successfully"})

    except Exception as e:
        logger.error(f"Error deleting theme {theme_id}: {e}")
        return jsonify({"error": "Failed to delete theme", "details": str(e)}), 500


@themes_bp.route("/<int:theme_id>/duplicate", methods=["POST"])
@simple_auth_required
def duplicate_theme(theme_id):
    """Duplicate an existing theme"""
    try:
        data = request.get_json()
        user_id = request.current_user.id

        with get_db() as session:
            original_theme = session.query(CustomTheme).filter_by(id=theme_id).first()
            if not original_theme:
                return jsonify({"error": "Theme not found"}), 404

            # Check permissions for original theme
            if not original_theme.is_public and not original_theme.is_built_in and original_theme.created_by != user_id:
                return jsonify({"error": "Access denied"}), 403

            # Get new theme name from request or generate one
            new_name = data.get("name", f"{original_theme.name}_copy")
            new_display_name = data.get("display_name", f"{original_theme.display_name} (Copy)")

            # Check if new name already exists
            existing = session.query(CustomTheme).filter_by(name=new_name).first()
            if existing:
                return jsonify({"error": "Theme name already exists"}), 409

            # Create duplicate
            new_theme = CustomTheme(
                name=new_name,
                display_name=new_display_name,
                description=data.get("description", original_theme.description),
                created_by=user_id,
                is_public=data.get("is_public", False), 
                is_built_in=False,  # Duplicates are never built-in
                theme_data=original_theme.theme_data.copy() if original_theme.theme_data else {},
                light_theme_data=original_theme.light_theme_data.copy() if original_theme.light_theme_data else None
            )

            session.add(new_theme)
            session.commit()

            logger.info(f"Duplicated theme '{original_theme.name}' as '{new_name}' by user {user_id}")
            return jsonify(new_theme.to_dict()), 201

    except Exception as e:
        logger.error(f"Error duplicating theme {theme_id}: {e}")
        return jsonify({"error": "Failed to duplicate theme", "details": str(e)}), 500


@themes_bp.route("/apply", methods=["POST"])
@simple_auth_required
def apply_theme():
    """Apply a theme to the current user"""
    try:
        data = request.get_json()
        theme_name = data.get("theme_name")
        
        if not theme_name:
            return jsonify({"error": "Theme name is required"}), 400
        
        # Save theme preference using settings service
        try:
            from src.services.settings_service import SettingsService
            SettingsService.set("ui_theme", theme_name)
            logger.info(f"Applied theme '{theme_name}' for user {request.current_user.id}")
            return jsonify({"message": f"Theme '{theme_name}' applied successfully"})
        except Exception as settings_error:
            logger.error(f"Error saving theme preference: {settings_error}")
            return jsonify({"error": "Failed to save theme preference"}), 500
            
    except Exception as e:
        logger.error(f"Error applying theme: {e}")
        return jsonify({"error": "Failed to apply theme", "details": str(e)}), 500


@themes_bp.route("/current", methods=["GET"])
@simple_auth_required
def get_current_theme():
    """Get the currently applied theme"""
    try:
        from src.services.settings_service import SettingsService
        current_theme = SettingsService.get("ui_theme", "default")
        return jsonify({"current_theme": current_theme})
    except Exception as e:
        logger.error(f"Error getting current theme: {e}")
        return jsonify({"error": "Failed to get current theme", "details": str(e)}), 500


# Note: Built-in theme extraction/editing functionality has been simplified
# Old LCARS themes (DS9, Voy, TNG-E) have been removed
# Built-in themes now primarily use CSS files rather than hardcoded definitions

@themes_bp.route("/built-in/<theme_name>/extract", methods=["POST"])
@simple_auth_required
def extract_built_in_theme(theme_name):
    """Extract CSS variables from built-in themes (simplified version)"""
    try:
        # Simplified built-in theme definitions - only the essential ones
        built_in_themes = {
            "default": {
                # Default theme variables
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
                "--sidebar-bg": "#1a1a1a",
                "--search-bar-bg": "#333333",
                "--top-bar-bg": "#1a1a1a",
            },
            "cyber": {
                # Cyber theme variables
                "--bg-primary": "#000000",
                "--bg-secondary": "#0d1117",
                "--bg-tertiary": "#161b22",
                "--text-primary": "#00fff7",
                "--text-secondary": "#7dd3fc",
                "--text-accent": "#00fff7",
                "--btn-primary-bg": "#00fff7",
                "--btn-primary-text": "#000000",
                "--border-primary": "#00fff7",
                "--success": "#00ff00",
                "--warning": "#ffff00",
                "--error": "#ff0000",
                "--info": "#00ffff",
                "--sidebar-bg": "#000000",
                "--search-bar-bg": "#161b22",
                "--top-bar-bg": "#0d1117",
            },
            "vaporwave": {
                # VaporWave theme variables
                "--bg-primary": "#1a0d26",
                "--bg-secondary": "#2d1b3d",
                "--bg-tertiary": "#3d2852",
                "--text-primary": "#ff3cac",
                "--text-secondary": "#d4a5f2",
                "--text-accent": "#ff3cac",
                "--btn-primary-bg": "#ff3cac",
                "--btn-primary-text": "#ffffff",
                "--border-primary": "#ff3cac",
                "--success": "#00ff94",
                "--warning": "#ffee00",
                "--error": "#ff073a",
                "--info": "#0abdc6",
                "--sidebar-bg": "#1a0d26",
                "--search-bar-bg": "#3d2852",
                "--top-bar-bg": "#2d1b3d",
            },
            "lcars_tng": {
                # LCARS TNG theme variables
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
                "--sidebar-bg": "#000000",
                "--search-bar-bg": "#333333",
                "--top-bar-bg": "#1a1a1a",
            }
        }

        if theme_name not in built_in_themes:
            return jsonify({"error": "Built-in theme not found"}), 404

        return jsonify({
            "theme_name": theme_name,
            "variables": built_in_themes[theme_name],
            "light_variables": {}  # Simplified - no light variants for now
        })

    except Exception as e:
        logger.error(f"Error extracting built-in theme {theme_name}: {e}")
        return jsonify({"error": "Failed to extract theme", "details": str(e)}), 500
