"""
API Endpoint Protection Configuration for MVidarr
Applies authentication and authorization decorators to existing API endpoints.
"""

from src.database.models import UserRole
from src.utils.auth_decorators import (admin_required,
                                       check_content_permissions,
                                       log_user_action, login_required,
                                       manager_required, role_required,
                                       user_required)
from src.utils.logger import get_logger

logger = get_logger("mvidarr.api.protection")


def apply_authentication_protection(app):
    """
    Apply authentication protection to existing API endpoints

    Protection Levels:
    - Public: No authentication required (health checks, auth endpoints)
    - User: Basic authentication required (viewing content)
    - Manager: Manager role or higher (content modification, bulk operations)
    - Admin: Admin role required (system settings, user management)
    """

    logger.info("Applying authentication protection to API endpoints...")

    # Get all registered endpoints
    endpoints = []
    for rule in app.url_map.iter_rules():
        endpoint = app.view_functions.get(rule.endpoint)
        if endpoint:
            endpoints.append((rule, endpoint))

    protected_count = 0

    for rule, endpoint in endpoints:
        endpoint_name = rule.endpoint
        rule_str = str(rule)
        methods = list(rule.methods - {"HEAD", "OPTIONS"})

        # Skip already protected endpoints
        if hasattr(endpoint, "_auth_protected"):
            continue

        # Apply protection based on endpoint patterns
        protection_applied = False

        # PUBLIC ENDPOINTS (No authentication required)
        public_patterns = [
            "/auth/",  # Authentication endpoints
            "/health",  # Health check
            "/api/health",  # API health check
            "/static/",  # Static files
            "/favicon.ico",  # Favicon
        ]

        if any(pattern in rule_str for pattern in public_patterns):
            logger.debug(f"Endpoint {rule_str} marked as PUBLIC")
            continue

        # ADMIN ENDPOINTS (Admin role required)
        admin_patterns = [
            "/api/settings",  # System settings
            "/api/users",  # User management
            "/restart",  # System restart
            "/api/system",  # System management
            "/admin/",  # Admin interface
        ]

        if any(pattern in rule_str for pattern in admin_patterns):
            logger.info(f"Protecting ADMIN endpoint: {rule_str}")
            endpoint = admin_required(log_user_action(f"accessed {rule_str}")(endpoint))
            protection_applied = True

        # MANAGER ENDPOINTS (Manager role or higher required)
        elif any(
            pattern in rule_str
            for pattern in [
                "/api/videos",  # Video management
                "/api/artists",  # Artist management
                "/api/downloads",  # Download management
                "/bulk",  # Bulk operations
                "/delete",  # Delete operations
            ]
        ) and any(method in methods for method in ["POST", "PUT", "DELETE"]):
            logger.info(f"Protecting MANAGER endpoint: {rule_str} {methods}")
            endpoint = manager_required(
                log_user_action(f"modified content via {rule_str}")(endpoint)
            )
            protection_applied = True

        # USER ENDPOINTS (Basic authentication required)
        elif rule_str.startswith("/api/"):
            logger.info(f"Protecting USER endpoint: {rule_str}")
            endpoint = login_required(log_user_action(f"accessed {rule_str}")(endpoint))
            protection_applied = True

        # WEB INTERFACE ENDPOINTS (Basic authentication required)
        elif not any(pattern in rule_str for pattern in ["/static/", "/favicon.ico"]):
            logger.info(f"Protecting WEB endpoint: {rule_str}")
            endpoint = login_required(endpoint)
            protection_applied = True

        if protection_applied:
            # Mark endpoint as protected
            endpoint._auth_protected = True

            # Update the view function in the app
            app.view_functions[endpoint_name] = endpoint
            protected_count += 1

    logger.info(f"Authentication protection applied to {protected_count} endpoints")

    return protected_count


def get_endpoint_protection_summary(app):
    """
    Get a summary of endpoint protection status

    Returns:
        dict: Summary of protected vs unprotected endpoints
    """
    summary = {
        "total_endpoints": 0,
        "protected_endpoints": 0,
        "public_endpoints": 0,
        "protection_details": [],
    }

    for rule in app.url_map.iter_rules():
        if rule.endpoint in app.view_functions:
            summary["total_endpoints"] += 1
            endpoint = app.view_functions[rule.endpoint]

            rule_str = str(rule)
            methods = list(rule.methods - {"HEAD", "OPTIONS"})

            # Check if endpoint is protected
            is_protected = hasattr(endpoint, "_auth_protected")

            # Determine if it should be public
            public_patterns = [
                "/auth/",
                "/health",
                "/api/health",
                "/static/",
                "/favicon.ico",
            ]
            is_public = any(pattern in rule_str for pattern in public_patterns)

            if is_protected:
                summary["protected_endpoints"] += 1
                protection_level = "Unknown"

                # Try to determine protection level
                if hasattr(endpoint, "__name__"):
                    if "admin_required" in str(endpoint):
                        protection_level = "Admin"
                    elif "manager_required" in str(endpoint):
                        protection_level = "Manager"
                    elif "login_required" in str(endpoint):
                        protection_level = "User"

                summary["protection_details"].append(
                    {
                        "endpoint": rule_str,
                        "methods": methods,
                        "protection": protection_level,
                        "status": "Protected",
                    }
                )
            elif is_public:
                summary["public_endpoints"] += 1
                summary["protection_details"].append(
                    {
                        "endpoint": rule_str,
                        "methods": methods,
                        "protection": "Public",
                        "status": "Public",
                    }
                )
            else:
                summary["protection_details"].append(
                    {
                        "endpoint": rule_str,
                        "methods": methods,
                        "protection": "None",
                        "status": "Unprotected",
                    }
                )

    return summary


# Specific endpoint protection functions for granular control
def protect_artist_endpoints(app):
    """Apply specific protection to artist management endpoints"""

    # Artist viewing - User level
    protect_endpoint(app, "artists.get_artists", login_required)
    protect_endpoint(app, "artists.get_artist", login_required)

    # Artist modification - Manager level
    protect_endpoint(app, "artists.create_artist", manager_required)
    protect_endpoint(app, "artists.update_artist", manager_required)
    protect_endpoint(app, "artists.delete_artist", manager_required)

    # Artist bulk operations - Manager level
    protect_endpoint(app, "artists.bulk_update", manager_required)
    protect_endpoint(app, "artists.bulk_delete", manager_required)


def protect_video_endpoints(app):
    """Apply specific protection to video management endpoints"""

    # Video viewing - User level
    protect_endpoint(app, "videos.get_videos", login_required)
    protect_endpoint(app, "videos.get_video", login_required)
    protect_endpoint(app, "videos.stream_video", login_required)

    # Video modification - Manager level
    protect_endpoint(app, "videos.update_video", manager_required)
    protect_endpoint(app, "videos.delete_video", manager_required)
    protect_endpoint(app, "videos.download_video", manager_required)

    # Video bulk operations - Manager level
    protect_endpoint(app, "videos.bulk_download", manager_required)
    protect_endpoint(app, "videos.bulk_delete", manager_required)


def protect_settings_endpoints(app):
    """Apply specific protection to settings endpoints"""

    # Settings viewing - User level (basic settings)
    protect_endpoint(app, "settings.get_setting", login_required)

    # Settings modification - Admin level
    protect_endpoint(app, "settings.get_all_settings", admin_required)
    protect_endpoint(app, "settings.update_setting", admin_required)
    protect_endpoint(app, "settings.delete_setting", admin_required)
    protect_endpoint(app, "settings.restart_application", admin_required)


def protect_endpoint(app, endpoint_name, decorator):
    """
    Apply a decorator to a specific endpoint

    Args:
        app: Flask application
        endpoint_name: Name of the endpoint (e.g., 'artists.get_artists')
        decorator: Decorator to apply
    """
    if endpoint_name in app.view_functions:
        original_function = app.view_functions[endpoint_name]

        if not hasattr(original_function, "_auth_protected"):
            protected_function = decorator(original_function)
            protected_function._auth_protected = True
            app.view_functions[endpoint_name] = protected_function

            logger.info(f"Applied {decorator.__name__} protection to {endpoint_name}")
        else:
            logger.debug(f"Endpoint {endpoint_name} already protected")
    else:
        logger.warning(f"Endpoint {endpoint_name} not found in application")


def create_endpoint_protection_report(app):
    """
    Create a comprehensive report of endpoint protection status

    Returns:
        dict: Detailed protection report
    """
    summary = get_endpoint_protection_summary(app)

    # Group endpoints by protection level
    by_protection = {}
    unprotected = []

    for detail in summary["protection_details"]:
        protection = detail["protection"]
        if protection == "None":
            unprotected.append(detail)
        else:
            if protection not in by_protection:
                by_protection[protection] = []
            by_protection[protection].append(detail)

    report = {
        "summary": {
            "total_endpoints": summary["total_endpoints"],
            "protected_endpoints": summary["protected_endpoints"],
            "public_endpoints": summary["public_endpoints"],
            "unprotected_endpoints": len(unprotected),
            "protection_coverage": round(
                (summary["protected_endpoints"] + summary["public_endpoints"])
                / summary["total_endpoints"]
                * 100,
                2,
            )
            if summary["total_endpoints"] > 0
            else 0,
        },
        "by_protection_level": by_protection,
        "unprotected_endpoints": unprotected,
        "recommendations": [],
    }

    # Add recommendations
    if unprotected:
        report["recommendations"].append(
            f"Consider protecting {len(unprotected)} unprotected endpoints"
        )

    if report["summary"]["protection_coverage"] < 100:
        report["recommendations"].append(
            "Review endpoint protection to achieve 100% coverage"
        )

    return report
