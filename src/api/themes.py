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
                    "theme_data": None,
                    "light_theme_data": None,  # These use CSS files
                    "light_theme_data": None,  # These use CSS files
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
                {
                    "id": "lcars_ds9",
                    "name": "lcars_ds9",
                    "display_name": "LCARS - DS9",
                    "description": "Star Trek: Deep Space Nine theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                    "light_theme_data": None,
                },
                {
                    "id": "lcars_voy",
                    "name": "lcars_voy",
                    "display_name": "LCARS - Voy",
                    "description": "Star Trek: Voyager theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                    "light_theme_data": None,
                },
                {
                    "id": "lcars_tng_e",
                    "name": "lcars_tng_e",
                    "display_name": "LCARS - TNG-E",
                    "description": "Star Trek: Enterprise theme",
                    "is_built_in": True,
                    "is_public": True,
                    "theme_data": None,
                    "light_theme_data": None,
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
                light_theme_data=data.get("light_theme_data"),
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
            if "light_theme_data" in data:
                theme.light_theme_data = data["light_theme_data"]
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
                light_theme_data=(
                    original_theme.light_theme_data.copy()
                    if original_theme.light_theme_data
                    else None
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
                # Base Colors
                "--bg-primary": "#1a1a1a",
                "--bg-secondary": "#2d2d2d",
                "--bg-tertiary": "#3a3a3a",
                "--bg-modal": "#333333",
                "--bg-card": "#2a2a2a",
                "--bg-hover": "#404040",
                # Text Colors
                "--text-primary": "#ffffff",
                "--text-secondary": "#cccccc",
                "--text-muted": "#888888",
                "--text-accent": "#4a9eff",
                "--text-inverse": "#000000",
                # Border Colors
                "--border-primary": "#444444",
                "--border-secondary": "#555555",
                "--border-focus": "#4a9eff",
                "--border-hover": "#666666",
                # Button Colors
                "--btn-primary-bg": "#4a9eff",
                "--btn-primary-text": "#ffffff",
                "--btn-primary-hover": "#3a8eef",
                "--btn-secondary-bg": "#666666",
                "--btn-secondary-text": "#ffffff",
                "--btn-secondary-hover": "#777777",
                "--btn-danger-bg": "#dc3545",
                "--btn-danger-text": "#ffffff",
                "--btn-danger-hover": "#c82333",
                # Status Colors
                "--success": "#28a745",
                "--warning": "#ffc107",
                "--error": "#dc3545",
                "--info": "#17a2b8",
                # Form Colors
                "--input-bg": "#3a3a3a",
                "--input-text": "#ffffff",
                "--input-border": "#555555",
                "--input-focus": "#4a9eff",
                # Sidebar & Navigation
                "--nav-bg": "#2d2d2d",
                "--nav-text": "#ffffff",
                "--nav-hover": "#404040",
                "--nav-active": "#4a9eff",
                "--sidebar-bg": "#1a1a1a",
                "--sidebar-bg-secondary": "#2d2d2d",
                "--search-bar-bg": "#2d2d2d",
                "--top-bar-bg": "#2d2d2d",
                # Shadow
                "--shadow": "rgba(0, 0, 0, 0.3)",
                "--shadow-hover": "rgba(0, 0, 0, 0.5)",
                # Extended Variables
                "--pageBackground": "#1a1a1a",
                "--textColor": "#ffffff",
                "--borderColor": "#444444",
                "--cardBackgroundColor": "#2a2a2a",
                "--cardShadowColor": "rgba(0, 0, 0, 0.3)",
                "--modalBackgroundColor": "#333333",
                "--modalBackdropBackgroundColor": "rgba(0, 0, 0, 0.5)",
                "--popoverBodyBackgroundColor": "#2d2d2d",
                "--popoverTitleBackgroundColor": "#2d2d2d",
                "--popoverTitleBorderColor": "#444444",
                "--popoverShadowColor": "rgba(0, 0, 0, 0.3)",
                "--tableRowHoverBackgroundColor": "#2d2d2d",
                "--inputBackgroundColor": "#3a3a3a",
                "--inputBorderColor": "#555555",
                "--inputHoverBackgroundColor": "#404040",
                "--inputFocusBorderColor": "#4a9eff",
                "--inputSelectedBackgroundColor": "#404040",
                "--menuItemColor": "#ffffff",
                "--menuItemHoverColor": "#ffffff",
                "--menuItemHoverBackgroundColor": "#404040",
                "--toolbarMenuItemBackgroundColor": "#2d2d2d",
                "--toolbarMenuItemHoverBackgroundColor": "#404040",
                "--albumBackgroundColor": "#2a2a2a",
                "--artistBackgroundColor": "#2a2a2a",
                "--trackBackgroundColor": "#2a2a2a",
                "--calendarBackgroundColor": "#2d2d2d",
                "--calendarBorderColor": "#444444",
                "--calendarTodayBackgroundColor": "#404040",
                "--scrollbarBackgroundColor": "#555555",
                "--scrollbarHoverBackgroundColor": "#666666",
                "--alertDangerBackgroundColor": "#2d2d2d",
                "--alertSuccessBackgroundColor": "#2d2d2d",
                "--alertWarningBackgroundColor": "#2d2d2d",
                "--alertInfoBackgroundColor": "#2d2d2d",
                "--pageHeaderBackgroundColor": "#2d2d2d",
                "--toolbarBackgroundColor": "#2d2d2d",
                "--sidebarActiveBackgroundColor": "#404040",
            },
            "cyber": {
                # Base Colors - Cyberpunk Dark
                "--bg-primary": "#0b0f14",
                "--bg-secondary": "#12181f",
                "--bg-tertiary": "#1a2129",
                "--bg-modal": "#12181f",
                "--bg-card": "#12181f",
                "--bg-hover": "#1e2a33",
                # Text Colors - Cyber Green/Cyan
                "--text-primary": "#e4eaf1",
                "--text-secondary": "#c4d0dd",
                "--text-muted": "#8896a5",
                "--text-accent": "#00fff7",
                "--text-inverse": "#0b0f14",
                # Border Colors - Cyan highlights
                "--border-primary": "#2e3947",
                "--border-secondary": "#3a4754",
                "--border-focus": "#00fff7",
                "--border-hover": "#4a5968",
                # Button Colors - Cyan primary
                "--btn-primary-bg": "#00fff7",
                "--btn-primary-text": "#0b0f14",
                "--btn-primary-hover": "#00e6de",
                "--btn-secondary-bg": "#2e3947",
                "--btn-secondary-text": "#e4eaf1",
                "--btn-secondary-hover": "#3a4754",
                "--btn-danger-bg": "#ff003c",
                "--btn-danger-text": "#ffffff",
                "--btn-danger-hover": "#e6003a",
                # Status Colors - Cyber palette
                "--success": "#00fff7",
                "--warning": "#ffcc00",
                "--error": "#ff003c",
                "--info": "#00fff7",
                # Form Colors
                "--input-bg": "#1a2129",
                "--input-text": "#e4eaf1",
                "--input-border": "#2e3947",
                "--input-focus": "#00fff7",
                # Sidebar & Navigation
                "--nav-bg": "#12181f",
                "--nav-text": "#e4eaf1",
                "--nav-hover": "#1e2a33",
                "--nav-active": "#00fff7",
                "--sidebar-bg": "#0b0f14",
                "--sidebar-bg-secondary": "#12181f",
                "--search-bar-bg": "#1a2129",
                "--top-bar-bg": "#12181f",
                # Shadow - Cyan glow
                "--shadow": "rgba(0, 255, 247, 0.15)",
                "--shadow-hover": "rgba(0, 255, 247, 0.25)",
                # Extended Variables - Cyber theme
                "--pageBackground": "#0b0f14",
                "--textColor": "#e4eaf1",
                "--borderColor": "#2e3947",
                "--cardBackgroundColor": "#12181f",
                "--cardShadowColor": "rgba(0, 255, 247, 0.15)",
                "--modalBackgroundColor": "#12181f",
                "--modalBackdropBackgroundColor": "rgba(11, 15, 20, 0.8)",
                "--popoverBodyBackgroundColor": "#1a2129",
                "--popoverTitleBackgroundColor": "#12181f",
                "--popoverTitleBorderColor": "#2e3947",
                "--popoverShadowColor": "rgba(0, 255, 247, 0.2)",
                "--tableRowHoverBackgroundColor": "#1e2a33",
                "--inputBackgroundColor": "#1a2129",
                "--inputBorderColor": "#2e3947",
                "--inputHoverBackgroundColor": "#1e2a33",
                "--inputFocusBorderColor": "#00fff7",
                "--inputSelectedBackgroundColor": "#1e2a33",
                "--menuItemColor": "#e4eaf1",
                "--menuItemHoverColor": "#00fff7",
                "--menuItemHoverBackgroundColor": "#1e2a33",
                "--toolbarMenuItemBackgroundColor": "#12181f",
                "--toolbarMenuItemHoverBackgroundColor": "#1e2a33",
                "--albumBackgroundColor": "#12181f",
                "--artistBackgroundColor": "#12181f",
                "--trackBackgroundColor": "#12181f",
                "--calendarBackgroundColor": "#1a2129",
                "--calendarBorderColor": "#2e3947",
                "--calendarTodayBackgroundColor": "#1e2a33",
                "--scrollbarBackgroundColor": "#2e3947",
                "--scrollbarHoverBackgroundColor": "#3a4754",
                "--alertDangerBackgroundColor": "#12181f",
                "--alertSuccessBackgroundColor": "#12181f",
                "--alertWarningBackgroundColor": "#12181f",
                "--alertInfoBackgroundColor": "#12181f",
                "--pageHeaderBackgroundColor": "#12181f",
                "--toolbarBackgroundColor": "#12181f",
                "--sidebarActiveBackgroundColor": "#1e2a33",
            },
            "vaporwave": {
                # Base Colors - Vaporwave Dark Purple
                "--bg-primary": "#0d0221",
                "--bg-secondary": "#1a0440",
                "--bg-tertiary": "#2f0f5d",
                "--bg-modal": "#1a0440",
                "--bg-card": "#1a0440",
                "--bg-hover": "#3d1574",
                # Text Colors - Bright whites and pinks
                "--text-primary": "#ffffff",
                "--text-secondary": "#e6d6ff",
                "--text-muted": "#b399ff",
                "--text-accent": "#ff3cac",
                "--text-inverse": "#0d0221",
                # Border Colors - Purple gradients
                "--border-primary": "#2f0f5d",
                "--border-secondary": "#4a1a7a",
                "--border-focus": "#ff3cac",
                "--border-hover": "#5c2491",
                # Button Colors - Pink/Purple
                "--btn-primary-bg": "#ff3cac",
                "--btn-primary-text": "#ffffff",
                "--btn-primary-hover": "#e6359c",
                "--btn-secondary-bg": "#8c1eff",
                "--btn-secondary-text": "#ffffff",
                "--btn-secondary-hover": "#7a1ae6",
                "--btn-danger-bg": "#ff3c00",
                "--btn-danger-text": "#ffffff",
                "--btn-danger-hover": "#e63500",
                # Status Colors - Synthwave palette
                "--success": "#00f0ff",
                "--warning": "#fff600",
                "--error": "#ff3c00",
                "--info": "#8c1eff",
                # Form Colors
                "--input-bg": "#2f0f5d",
                "--input-text": "#ffffff",
                "--input-border": "#4a1a7a",
                "--input-focus": "#ff3cac",
                # Sidebar & Navigation
                "--nav-bg": "#1a0440",
                "--nav-text": "#ffffff",
                "--nav-hover": "#3d1574",
                "--nav-active": "#ff3cac",
                "--sidebar-bg": "#0d0221",
                "--sidebar-bg-secondary": "#1a0440",
                "--search-bar-bg": "#2f0f5d",
                "--top-bar-bg": "#1a0440",
                # Shadow - Pink glow
                "--shadow": "rgba(255, 60, 172, 0.2)",
                "--shadow-hover": "rgba(255, 60, 172, 0.3)",
                # Extended Variables - Vaporwave theme
                "--pageBackground": "#0d0221",
                "--textColor": "#ffffff",
                "--borderColor": "#2f0f5d",
                "--cardBackgroundColor": "#1a0440",
                "--cardShadowColor": "rgba(255, 60, 172, 0.2)",
                "--modalBackgroundColor": "#1a0440",
                "--modalBackdropBackgroundColor": "rgba(13, 2, 33, 0.8)",
                "--popoverBodyBackgroundColor": "#2f0f5d",
                "--popoverTitleBackgroundColor": "#1a0440",
                "--popoverTitleBorderColor": "#4a1a7a",
                "--popoverShadowColor": "rgba(255, 60, 172, 0.3)",
                "--tableRowHoverBackgroundColor": "#3d1574",
                "--inputBackgroundColor": "#2f0f5d",
                "--inputBorderColor": "#4a1a7a",
                "--inputHoverBackgroundColor": "#3d1574",
                "--inputFocusBorderColor": "#ff3cac",
                "--inputSelectedBackgroundColor": "#3d1574",
                "--menuItemColor": "#ffffff",
                "--menuItemHoverColor": "#ff3cac",
                "--menuItemHoverBackgroundColor": "#3d1574",
                "--toolbarMenuItemBackgroundColor": "#1a0440",
                "--toolbarMenuItemHoverBackgroundColor": "#3d1574",
                "--albumBackgroundColor": "#1a0440",
                "--artistBackgroundColor": "#1a0440",
                "--trackBackgroundColor": "#1a0440",
                "--calendarBackgroundColor": "#2f0f5d",
                "--calendarBorderColor": "#4a1a7a",
                "--calendarTodayBackgroundColor": "#3d1574",
                "--scrollbarBackgroundColor": "#4a1a7a",
                "--scrollbarHoverBackgroundColor": "#5c2491",
                "--alertDangerBackgroundColor": "#1a0440",
                "--alertSuccessBackgroundColor": "#1a0440",
                "--alertWarningBackgroundColor": "#1a0440",
                "--alertInfoBackgroundColor": "#1a0440",
                "--pageHeaderBackgroundColor": "#1a0440",
                "--toolbarBackgroundColor": "#1a0440",
                "--sidebarActiveBackgroundColor": "#3d1574",
            },
            "lcars_tng": {
                # Base Colors - LCARS TNG Black/Gold
                "--bg-primary": "#000000",
                "--bg-secondary": "#1a1a1a",
                "--bg-tertiary": "#2d2d2d",
                "--bg-modal": "#1a1a1a",
                "--bg-card": "#1a1a1a",
                "--bg-hover": "#333333",
                # Text Colors - White with gold accent
                "--text-primary": "#ffffff",
                "--text-secondary": "#e6e6e6",
                "--text-muted": "#cccccc",
                "--text-accent": "#fbb03b",
                "--text-inverse": "#000000",
                # Border Colors - Gold highlights
                "--border-primary": "#fbb03b",
                "--border-secondary": "#ff9900",
                "--border-focus": "#ffff66",
                "--border-hover": "#ffcc66",
                # Button Colors - Gold primary
                "--btn-primary-bg": "#fbb03b",
                "--btn-primary-text": "#000000",
                "--btn-primary-hover": "#ff9900",
                "--btn-secondary-bg": "#9933cc",
                "--btn-secondary-text": "#ffffff",
                "--btn-secondary-hover": "#8028b8",
                "--btn-danger-bg": "#ff6699",
                "--btn-danger-text": "#000000",
                "--btn-danger-hover": "#e6528a",
                # Status Colors - LCARS palette
                "--success": "#3399cc",
                "--warning": "#ffff66",
                "--error": "#ff6699",
                "--info": "#cc66ff",
                # Form Colors
                "--input-bg": "#daa520",
                "--input-text": "#ffffff",
                "--input-border": "#fbb03b",
                "--input-focus": "#ffff66",
                # Sidebar & Navigation
                "--nav-bg": "#daa520",
                "--nav-text": "#ffffff",
                "--nav-hover": "#333333",
                "--nav-active": "#fbb03b",
                "--sidebar-bg": "#000000",
                "--sidebar-bg-secondary": "#1a1a1a",
                "--search-bar-bg": "#2d2d2d",
                "--top-bar-bg": "#1a1a1a",
                # Shadow - Gold glow
                "--shadow": "rgba(251, 176, 59, 0.2)",
                "--shadow-hover": "rgba(251, 176, 59, 0.3)",
                # Extended Variables - LCARS TNG theme
                "--pageBackground": "#000000",
                "--textColor": "#ffffff",
                "--borderColor": "#fbb03b",
                "--cardBackgroundColor": "#1a1a1a",
                "--cardShadowColor": "rgba(251, 176, 59, 0.2)",
                "--modalBackgroundColor": "#1a1a1a",
                "--modalBackdropBackgroundColor": "rgba(0, 0, 0, 0.8)",
                "--popoverBodyBackgroundColor": "#2d2d2d",
                "--popoverTitleBackgroundColor": "#1a1a1a",
                "--popoverTitleBorderColor": "#fbb03b",
                "--popoverShadowColor": "rgba(251, 176, 59, 0.3)",
                "--tableRowHoverBackgroundColor": "#333333",
                "--inputBackgroundColor": "#2d2d2d",
                "--inputBorderColor": "#fbb03b",
                "--inputHoverBackgroundColor": "#333333",
                "--inputFocusBorderColor": "#ffff66",
                "--inputSelectedBackgroundColor": "#333333",
                "--menuItemColor": "#ffffff",
                "--menuItemHoverColor": "#fbb03b",
                "--menuItemHoverBackgroundColor": "#333333",
                "--toolbarMenuItemBackgroundColor": "#1a1a1a",
                "--toolbarMenuItemHoverBackgroundColor": "#333333",
                "--albumBackgroundColor": "#1a1a1a",
                "--artistBackgroundColor": "#1a1a1a",
                "--trackBackgroundColor": "#1a1a1a",
                "--calendarBackgroundColor": "#2d2d2d",
                "--calendarBorderColor": "#fbb03b",
                "--calendarTodayBackgroundColor": "#333333",
                "--scrollbarBackgroundColor": "#fbb03b",
                "--scrollbarHoverBackgroundColor": "#ff9900",
                "--alertDangerBackgroundColor": "#1a1a1a",
                "--alertSuccessBackgroundColor": "#1a1a1a",
                "--alertWarningBackgroundColor": "#1a1a1a",
                "--alertInfoBackgroundColor": "#1a1a1a",
                "--pageHeaderBackgroundColor": "#1a1a1a",
                "--toolbarBackgroundColor": "#daa520",
                "--sidebarActiveBackgroundColor": "#333333",
            },
            "lcars_ds9": {
                # Base Colors - LCARS DS9 Black/Orange
                "--bg-primary": "#000000",
                "--bg-secondary": "#1a1a1a",
                "--bg-tertiary": "#2d2d2d",
                "--bg-modal": "#1a1a1a",
                "--bg-card": "#1a1a1a",
                "--bg-hover": "#333333",
                # Text Colors - White with orange accent
                "--text-primary": "#ffffff",
                "--text-secondary": "#e6e6e6",
                "--text-muted": "#888888",
                "--text-accent": "#c04c00",
                "--text-inverse": "#000000",
                # Border Colors - Orange/Blue highlights
                "--border-primary": "#c04c00",
                "--border-secondary": "#2a4b6e",
                "--border-focus": "#e4d000",
                "--border-hover": "#3a7669",
                # Button Colors - Orange primary
                "--btn-primary-bg": "#c04c00",
                "--btn-primary-text": "#ffffff",
                "--btn-primary-hover": "#a64000",
                "--btn-secondary-bg": "#2a4b6e",
                "--btn-secondary-text": "#ffffff",
                "--btn-secondary-hover": "#1e3a57",
                "--btn-danger-bg": "#a80000",
                "--btn-danger-text": "#ffffff",
                "--btn-danger-hover": "#940000",
                # Status Colors - DS9 palette
                "--success": "#3a7669",
                "--warning": "#e4d000",
                "--error": "#a80000",
                "--info": "#2a4b6e",
                # Form Colors
                "--input-bg": "#2d2d2d",
                "--input-text": "#ffffff",
                "--input-border": "#c04c00",
                "--input-focus": "#e4d000",
                # Sidebar & Navigation
                "--nav-bg": "#1a1a1a",
                "--nav-text": "#ffffff",
                "--nav-hover": "#333333",
                "--nav-active": "#c04c00",
                "--sidebar-bg": "#000000",
                "--sidebar-bg-secondary": "#1a1a1a",
                "--search-bar-bg": "#2d2d2d",
                "--top-bar-bg": "#1a1a1a",
                # Shadow - Orange glow
                "--shadow": "rgba(192, 76, 0, 0.2)",
                "--shadow-hover": "rgba(192, 76, 0, 0.3)",
                # Extended Variables - LCARS DS9 theme
                "--pageBackground": "#000000",
                "--textColor": "#ffffff",
                "--borderColor": "#c04c00",
                "--cardBackgroundColor": "#1a1a1a",
                "--cardShadowColor": "rgba(192, 76, 0, 0.2)",
                "--modalBackgroundColor": "#1a1a1a",
                "--modalBackdropBackgroundColor": "rgba(0, 0, 0, 0.8)",
                "--popoverBodyBackgroundColor": "#2d2d2d",
                "--popoverTitleBackgroundColor": "#1a1a1a",
                "--popoverTitleBorderColor": "#c04c00",
                "--popoverShadowColor": "rgba(192, 76, 0, 0.3)",
                "--tableRowHoverBackgroundColor": "#333333",
                "--inputBackgroundColor": "#2d2d2d",
                "--inputBorderColor": "#c04c00",
                "--inputHoverBackgroundColor": "#333333",
                "--inputFocusBorderColor": "#e4d000",
                "--inputSelectedBackgroundColor": "#333333",
                "--menuItemColor": "#ffffff",
                "--menuItemHoverColor": "#c04c00",
                "--menuItemHoverBackgroundColor": "#333333",
                "--toolbarMenuItemBackgroundColor": "#1a1a1a",
                "--toolbarMenuItemHoverBackgroundColor": "#333333",
                "--albumBackgroundColor": "#1a1a1a",
                "--artistBackgroundColor": "#1a1a1a",
                "--trackBackgroundColor": "#1a1a1a",
                "--calendarBackgroundColor": "#2d2d2d",
                "--calendarBorderColor": "#c04c00",
                "--calendarTodayBackgroundColor": "#333333",
                "--scrollbarBackgroundColor": "#c04c00",
                "--scrollbarHoverBackgroundColor": "#a64000",
                "--alertDangerBackgroundColor": "#1a1a1a",
                "--alertSuccessBackgroundColor": "#1a1a1a",
                "--alertWarningBackgroundColor": "#1a1a1a",
                "--alertInfoBackgroundColor": "#1a1a1a",
                "--pageHeaderBackgroundColor": "#1a1a1a",
                "--toolbarBackgroundColor": "#1a1a1a",
                "--sidebarActiveBackgroundColor": "#333333",
            },
            "lcars_voy": {
                # Base Colors - LCARS Voyager Black/Orange
                "--bg-primary": "#000000",
                "--bg-secondary": "#1a1a1a",
                "--bg-tertiary": "#2d2d2d",
                "--bg-modal": "#1a1a1a",
                "--bg-card": "#1a1a1a",
                "--bg-hover": "#333333",
                # Text Colors - White with orange accent
                "--text-primary": "#ffffff",
                "--text-secondary": "#f5e3c3",
                "--text-muted": "#cccccc",
                "--text-accent": "#ffb07c",
                "--text-inverse": "#1a1a1a",
                # Border Colors - Orange/Multi highlights
                "--border-primary": "#ffb07c",
                "--border-secondary": "#ff6b1a",
                "--border-focus": "#f7ea48",
                "--border-hover": "#ff91af",
                # Button Colors - Orange primary
                "--btn-primary-bg": "#ffb07c",
                "--btn-primary-text": "#1a1a1a",
                "--btn-primary-hover": "#ff9959",
                "--btn-secondary-bg": "#a682bd",
                "--btn-secondary-text": "#ffffff",
                "--btn-secondary-hover": "#9570ad",
                "--btn-danger-bg": "#ff91af",
                "--btn-danger-text": "#1a1a1a",
                "--btn-danger-hover": "#ff7a9a",
                # Status Colors - Voyager palette
                "--success": "#4ca4cb",
                "--warning": "#f7ea48",
                "--error": "#ff91af",
                "--info": "#a682bd",
                # Form Colors
                "--input-bg": "#2d2d2d",
                "--input-text": "#ffffff",
                "--input-border": "#ffb07c",
                "--input-focus": "#f7ea48",
                # Sidebar & Navigation
                "--nav-bg": "#1a1a1a",
                "--nav-text": "#ffffff",
                "--nav-hover": "#333333",
                "--nav-active": "#ffb07c",
                "--sidebar-bg": "#000000",
                "--sidebar-bg-secondary": "#1a1a1a",
                "--search-bar-bg": "#2d2d2d",
                "--top-bar-bg": "#1a1a1a",
                # Shadow - Orange glow
                "--shadow": "rgba(255, 176, 124, 0.2)",
                "--shadow-hover": "rgba(255, 176, 124, 0.3)",
                # Extended Variables - LCARS Voyager theme
                "--pageBackground": "#000000",
                "--textColor": "#ffffff",
                "--borderColor": "#ffb07c",
                "--cardBackgroundColor": "#1a1a1a",
                "--cardShadowColor": "rgba(255, 176, 124, 0.2)",
                "--modalBackgroundColor": "#1a1a1a",
                "--modalBackdropBackgroundColor": "rgba(0, 0, 0, 0.8)",
                "--popoverBodyBackgroundColor": "#2d2d2d",
                "--popoverTitleBackgroundColor": "#1a1a1a",
                "--popoverTitleBorderColor": "#ffb07c",
                "--popoverShadowColor": "rgba(255, 176, 124, 0.3)",
                "--tableRowHoverBackgroundColor": "#333333",
                "--inputBackgroundColor": "#2d2d2d",
                "--inputBorderColor": "#ffb07c",
                "--inputHoverBackgroundColor": "#333333",
                "--inputFocusBorderColor": "#f7ea48",
                "--inputSelectedBackgroundColor": "#333333",
                "--menuItemColor": "#ffffff",
                "--menuItemHoverColor": "#ffb07c",
                "--menuItemHoverBackgroundColor": "#333333",
                "--toolbarMenuItemBackgroundColor": "#1a1a1a",
                "--toolbarMenuItemHoverBackgroundColor": "#333333",
                "--albumBackgroundColor": "#1a1a1a",
                "--artistBackgroundColor": "#1a1a1a",
                "--trackBackgroundColor": "#1a1a1a",
                "--calendarBackgroundColor": "#2d2d2d",
                "--calendarBorderColor": "#ffb07c",
                "--calendarTodayBackgroundColor": "#333333",
                "--scrollbarBackgroundColor": "#ffb07c",
                "--scrollbarHoverBackgroundColor": "#ff9959",
                "--alertDangerBackgroundColor": "#1a1a1a",
                "--alertSuccessBackgroundColor": "#1a1a1a",
                "--alertWarningBackgroundColor": "#1a1a1a",
                "--alertInfoBackgroundColor": "#1a1a1a",
                "--pageHeaderBackgroundColor": "#1a1a1a",
                "--toolbarBackgroundColor": "#1a1a1a",
                "--sidebarActiveBackgroundColor": "#333333",
            },
            "lcars_tng_e": {
                # Base Colors - LCARS TNG-E Black/Orange
                "--bg-primary": "#000000",
                "--bg-secondary": "#1a1a1a",
                "--bg-tertiary": "#2d2d2d",
                "--bg-modal": "#1a1a1a",
                "--bg-card": "#1a1a1a",
                "--bg-hover": "#333333",
                # Text Colors - White with orange accent
                "--text-primary": "#ffffff",
                "--text-secondary": "#e6e6e6",
                "--text-muted": "#cccccc",
                "--text-accent": "#d97904",
                "--text-inverse": "#000000",
                # Border Colors - Orange/Multi highlights
                "--border-primary": "#d97904",
                "--border-secondary": "#cc5c6f",
                "--border-focus": "#fff275",
                "--border-hover": "#e6b95a",
                # Button Colors - Orange primary
                "--btn-primary-bg": "#d97904",
                "--btn-primary-text": "#ffffff",
                "--btn-primary-hover": "#c26a03",
                "--btn-secondary-bg": "#a084c4",
                "--btn-secondary-text": "#ffffff",
                "--btn-secondary-hover": "#8f73b3",
                "--btn-danger-bg": "#cc5c6f",
                "--btn-danger-text": "#ffffff",
                "--btn-danger-hover": "#b3515f",
                # Status Colors - Enterprise palette
                "--success": "#4b4e6d",
                "--warning": "#fff275",
                "--error": "#cc5c6f",
                "--info": "#a084c4",
                # Form Colors
                "--input-bg": "#2d2d2d",
                "--input-text": "#ffffff",
                "--input-border": "#d97904",
                "--input-focus": "#fff275",
                # Sidebar & Navigation
                "--nav-bg": "#1a1a1a",
                "--nav-text": "#ffffff",
                "--nav-hover": "#333333",
                "--nav-active": "#d97904",
                "--sidebar-bg": "#000000",
                "--sidebar-bg-secondary": "#1a1a1a",
                "--search-bar-bg": "#2d2d2d",
                "--top-bar-bg": "#1a1a1a",
                # Shadow - Orange glow
                "--shadow": "rgba(217, 121, 4, 0.2)",
                "--shadow-hover": "rgba(217, 121, 4, 0.3)",
                # Extended Variables - LCARS TNG-E theme
                "--pageBackground": "#000000",
                "--textColor": "#ffffff",
                "--borderColor": "#d97904",
                "--cardBackgroundColor": "#1a1a1a",
                "--cardShadowColor": "rgba(217, 121, 4, 0.2)",
                "--modalBackgroundColor": "#1a1a1a",
                "--modalBackdropBackgroundColor": "rgba(0, 0, 0, 0.8)",
                "--popoverBodyBackgroundColor": "#2d2d2d",
                "--popoverTitleBackgroundColor": "#1a1a1a",
                "--popoverTitleBorderColor": "#d97904",
                "--popoverShadowColor": "rgba(217, 121, 4, 0.3)",
                "--tableRowHoverBackgroundColor": "#333333",
                "--inputBackgroundColor": "#2d2d2d",
                "--inputBorderColor": "#d97904",
                "--inputHoverBackgroundColor": "#333333",
                "--inputFocusBorderColor": "#fff275",
                "--inputSelectedBackgroundColor": "#333333",
                "--menuItemColor": "#ffffff",
                "--menuItemHoverColor": "#d97904",
                "--menuItemHoverBackgroundColor": "#333333",
                "--toolbarMenuItemBackgroundColor": "#1a1a1a",
                "--toolbarMenuItemHoverBackgroundColor": "#333333",
                "--albumBackgroundColor": "#1a1a1a",
                "--artistBackgroundColor": "#1a1a1a",
                "--trackBackgroundColor": "#1a1a1a",
                "--calendarBackgroundColor": "#2d2d2d",
                "--calendarBorderColor": "#d97904",
                "--calendarTodayBackgroundColor": "#333333",
                "--scrollbarBackgroundColor": "#d97904",
                "--scrollbarHoverBackgroundColor": "#c26a03",
                "--alertDangerBackgroundColor": "#1a1a1a",
                "--alertSuccessBackgroundColor": "#1a1a1a",
                "--alertWarningBackgroundColor": "#1a1a1a",
                "--alertInfoBackgroundColor": "#1a1a1a",
                "--pageHeaderBackgroundColor": "#1a1a1a",
                "--toolbarBackgroundColor": "#1a1a1a",
                "--sidebarActiveBackgroundColor": "#333333",
            },
        }

        if theme_name not in built_in_themes:
            return jsonify({"error": "Built-in theme not found"}), 404

        # Also provide light theme defaults based on the theme
        light_theme_vars = {}
        if theme_name == "default":
            # Default light theme is already defined in CSS
            light_theme_vars = {
                "--bg-primary": "#ffffff",
                "--bg-secondary": "#f8f9fa", 
                "--bg-tertiary": "#e9ecef",
                "--text-primary": "#212529",
                "--text-secondary": "#495057",
                "--text-accent": "#0066cc",
                "--border-primary": "#dee2e6",
                "--btn-primary-bg": "#0066cc",
                "--sidebar-bg": "#ffffff",
                "--search-bar-bg": "#ffffff",
                "--top-bar-bg": "#f8f9fa",
            }
        else:
            # For other themes, provide lighter variants
            light_theme_vars = built_in_themes[theme_name].copy()
            # Auto-generate lighter colors (this is a simplified approach)
            for key, value in light_theme_vars.items():
                if isinstance(value, str) and value.startswith('#'):
                    # This is a basic lightening - in practice you'd want more sophisticated color manipulation
                    if 'bg-' in key:
                        light_theme_vars[key] = value  # Keep as is for now
                    elif 'text-' in key:
                        light_theme_vars[key] = value  # Keep as is for now

        return jsonify({
            "theme_name": theme_name, 
            "variables": built_in_themes[theme_name],
            "light_variables": light_theme_vars
        })

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


@themes_bp.route("/built-in/<string:theme_name>/edit", methods=["POST"])
@simple_auth_required
def edit_built_in_theme(theme_name):
    """Create a customized version of a built-in theme with user edits"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data is required"}), 400

        user_id = request.current_user.id

        # Built-in theme definitions (reuse from extract endpoint)
        built_in_themes = {
            "default": {
                "display_name": "Default",
                "description": "Default MVidarr theme",
                "variables": {
                    # Base Colors
                    "--bg-primary": "#1a1a1a",
                    "--bg-secondary": "#2d2d2d",
                    "--bg-tertiary": "#3a3a3a",
                    "--bg-modal": "#333333",
                    "--bg-card": "#2a2a2a",
                    "--bg-hover": "#404040",
                    # Text Colors
                    "--text-primary": "#ffffff",
                    "--text-secondary": "#cccccc",
                    "--text-muted": "#888888",
                    "--text-accent": "#4a9eff",
                    "--text-inverse": "#000000",
                    # Border Colors
                    "--border-primary": "#444444",
                    "--border-secondary": "#555555",
                    "--border-focus": "#4a9eff",
                    "--border-hover": "#666666",
                    # Button Colors
                    "--btn-primary-bg": "#4a9eff",
                    "--btn-primary-text": "#ffffff",
                    "--btn-primary-hover": "#3a8eef",
                    "--btn-secondary-bg": "#666666",
                    "--btn-secondary-text": "#ffffff",
                    "--btn-secondary-hover": "#777777",
                    "--btn-danger-bg": "#dc3545",
                    "--btn-danger-text": "#ffffff",
                    "--btn-danger-hover": "#c82333",
                    # Status Colors
                    "--success": "#28a745",
                    "--warning": "#ffc107",
                    "--error": "#dc3545",
                    "--info": "#17a2b8",
                    # Form Colors
                    "--input-bg": "#3a3a3a",
                    "--input-text": "#ffffff",
                    "--input-border": "#555555",
                    "--input-focus": "#4a9eff",
                    # Sidebar & Navigation
                    "--nav-bg": "#2d2d2d",
                    "--nav-text": "#ffffff",
                    "--nav-hover": "#404040",
                    "--nav-active": "#4a9eff",
                    "--sidebar-bg": "#1a1a1a",
                    "--sidebar-bg-secondary": "#2d2d2d",
                    "--search-bar-bg": "#2d2d2d",
                    "--top-bar-bg": "#2d2d2d",
                    # Shadow
                    "--shadow": "rgba(0, 0, 0, 0.3)",
                    "--shadow-hover": "rgba(0, 0, 0, 0.5)",
                    # Extended Variables
                    "--pageBackground": "#1a1a1a",
                    "--textColor": "#ffffff",
                    "--borderColor": "#444444",
                    "--cardBackgroundColor": "#2a2a2a",
                    "--cardShadowColor": "rgba(0, 0, 0, 0.3)",
                    "--modalBackgroundColor": "#333333",
                    "--modalBackdropBackgroundColor": "rgba(0, 0, 0, 0.5)",
                    "--popoverBodyBackgroundColor": "#2d2d2d",
                    "--popoverTitleBackgroundColor": "#2d2d2d",
                    "--popoverTitleBorderColor": "#444444",
                    "--popoverShadowColor": "rgba(0, 0, 0, 0.3)",
                    "--tableRowHoverBackgroundColor": "#2d2d2d",
                    "--inputBackgroundColor": "#3a3a3a",
                    "--inputBorderColor": "#555555",
                    "--inputHoverBackgroundColor": "#404040",
                    "--inputFocusBorderColor": "#4a9eff",
                    "--inputSelectedBackgroundColor": "#404040",
                    "--menuItemColor": "#ffffff",
                    "--menuItemHoverColor": "#ffffff",
                    "--menuItemHoverBackgroundColor": "#404040",
                    "--toolbarMenuItemBackgroundColor": "#2d2d2d",
                    "--toolbarMenuItemHoverBackgroundColor": "#404040",
                    "--albumBackgroundColor": "#2a2a2a",
                    "--artistBackgroundColor": "#2a2a2a",
                    "--trackBackgroundColor": "#2a2a2a",
                    "--calendarBackgroundColor": "#2d2d2d",
                    "--calendarBorderColor": "#444444",
                    "--calendarTodayBackgroundColor": "#404040",
                    "--scrollbarBackgroundColor": "#555555",
                    "--scrollbarHoverBackgroundColor": "#666666",
                    "--alertDangerBackgroundColor": "#2d2d2d",
                    "--alertSuccessBackgroundColor": "#2d2d2d",
                    "--alertWarningBackgroundColor": "#2d2d2d",
                    "--alertInfoBackgroundColor": "#2d2d2d",
                    "--pageHeaderBackgroundColor": "#2d2d2d",
                    "--toolbarBackgroundColor": "#2d2d2d",
                    "--sidebarActiveBackgroundColor": "#404040",
                }
            },
            "cyber": {
                "display_name": "Cyber",
                "description": "Cyberpunk-inspired theme",
                "variables": {
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
                    "--sidebar-bg": "#0a0a0a",
                    "--sidebar-bg-secondary": "#1a1a2e",
                    "--search-bar-bg": "#16213e",
                    "--top-bar-bg": "#1a1a2e",
                }
            },
            "vaporwave": {
                "display_name": "VaporWave",
                "description": "Synthwave/vaporwave aesthetic",
                "variables": {
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
                    "--sidebar-bg": "#0d0221",
                    "--sidebar-bg-secondary": "#1a0933",
                    "--search-bar-bg": "#2d1b69",
                    "--top-bar-bg": "#1a0933",
                }
            },
            "lcars_tng": {
                "display_name": "LCARS - TNG",
                "description": "Star Trek: The Next Generation theme",
                "variables": {
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
                    "--sidebar-bg-secondary": "#1a1a1a",
                    "--search-bar-bg": "#333333",
                    "--top-bar-bg": "#1a1a1a",
                }
            },
            "lcars_ds9": {
                "display_name": "LCARS - DS9",
                "description": "Star Trek: Deep Space Nine theme",
                "variables": {
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
                    "--sidebar-bg": "#000000",
                    "--sidebar-bg-secondary": "#1a1a1a",
                    "--search-bar-bg": "#333333",
                    "--top-bar-bg": "#1a1a1a",
                }
            },
            "lcars_voy": {
                "display_name": "LCARS - Voy",
                "description": "Star Trek: Voyager theme",
                "variables": {
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
                    "--sidebar-bg": "#000000",
                    "--sidebar-bg-secondary": "#1a1a1a",
                    "--search-bar-bg": "#333333",
                    "--top-bar-bg": "#1a1a1a",
                }
            },
            "lcars_tng_e": {
                "display_name": "LCARS - TNG-E",
                "description": "Star Trek: Enterprise theme",
                "variables": {
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
                    "--sidebar-bg": "#000000",
                    "--sidebar-bg-secondary": "#1a1a1a",
                    "--search-bar-bg": "#333333",
                    "--top-bar-bg": "#1a1a1a",
                }
            }
        }

        if theme_name not in built_in_themes:
            return jsonify({"error": "Built-in theme not found"}), 404

        built_in_theme = built_in_themes[theme_name]

        # Validate required fields
        if "name" not in data:
            return jsonify({"error": "Theme name is required"}), 400

        with get_db() as session:
            # Check if theme name already exists
            existing = session.query(CustomTheme).filter_by(name=data["name"]).first()
            if existing:
                return jsonify({"error": "Theme name already exists"}), 400

            # Merge built-in variables with user customizations
            theme_variables = built_in_theme["variables"].copy()
            if "theme_data" in data and isinstance(data["theme_data"], dict):
                theme_variables.update(data["theme_data"])

            # Create new customized theme
            custom_theme = CustomTheme(
                name=data["name"],
                display_name=data.get("display_name", built_in_theme["display_name"]),
                description=data.get("description", built_in_theme["description"]),
                created_by=user_id,
                is_public=data.get("is_public", False),
                is_built_in=False,
                theme_data=theme_variables,
            )

            session.add(custom_theme)
            session.commit()

            logger.info(f"Created custom theme '{custom_theme.name}' based on built-in theme '{theme_name}' by user {user_id}")
            return jsonify(custom_theme.to_dict()), 201

    except Exception as e:
        logger.error(f"Failed to edit built-in theme {theme_name}: {e}")
        return jsonify({"error": str(e)}), 500


@themes_bp.route("/built-in/<string:theme_name>/duplicate", methods=["POST"])
@simple_auth_required
def duplicate_built_in_theme(theme_name):
    """Duplicate a built-in theme for customization"""
    try:
        data = request.get_json() or {}
        user_id = request.current_user.id

        # Built-in theme definitions (reuse from extract endpoint)
        built_in_themes = {
            "default": {"display_name": "Default", "description": "Default MVidarr theme"},
            "cyber": {"display_name": "Cyber", "description": "Cyberpunk-inspired theme"},
            "vaporwave": {"display_name": "VaporWave", "description": "Synthwave/vaporwave aesthetic"},
            "lcars_tng": {"display_name": "LCARS - TNG", "description": "Star Trek: The Next Generation theme"},
            "lcars_ds9": {"display_name": "LCARS - DS9", "description": "Star Trek: Deep Space Nine theme"},
            "lcars_voy": {"display_name": "LCARS - Voy", "description": "Star Trek: Voyager theme"},
            "lcars_tng_e": {"display_name": "LCARS - TNG-E", "description": "Star Trek: Enterprise theme"}
        }

        if theme_name not in built_in_themes:
            return jsonify({"error": "Built-in theme not found"}), 404

        # Extract theme variables from the extract endpoint definition
        extract_response = extract_built_in_theme(theme_name)
        if extract_response[1] != 200:
            return jsonify({"error": "Failed to extract theme variables"}), 500
        
        theme_variables = extract_response[0].get_json()["variables"]

        with get_db() as session:
            built_in_theme = built_in_themes[theme_name]
            
            # Generate unique name for duplicate
            base_name = data.get("name", f"{theme_name}_custom")
            new_name = base_name
            counter = 1

            while session.query(CustomTheme).filter_by(name=new_name).first():
                new_name = f"{base_name}_{counter}"
                counter += 1

            # Create duplicate theme with customizations
            duplicate = CustomTheme(
                name=new_name,
                display_name=data.get("display_name", f"{built_in_theme['display_name']} (Custom)"),
                description=data.get("description", f"Custom version of {built_in_theme['display_name']}"),
                created_by=user_id,
                is_public=False,
                is_built_in=False,
                theme_data=data.get("theme_data", theme_variables),
            )

            session.add(duplicate)
            session.commit()

            logger.info(f"Duplicated built-in theme '{theme_name}' as '{duplicate.name}' by user {user_id}")
            return jsonify(duplicate.to_dict()), 201

    except Exception as e:
        logger.error(f"Failed to duplicate built-in theme {theme_name}: {e}")
        return jsonify({"error": str(e)}), 500
