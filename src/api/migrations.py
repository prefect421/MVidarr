"""
Database migration API endpoints for MVidarr
Provides endpoints for managing database schema changes.
"""

from flask import Blueprint, jsonify

from src.database.migrations import (
    get_migration_status,
    rollback_migration,
    run_migrations,
)
from src.middleware.simple_auth_middleware import auth_required
from src.utils.logger import get_logger

logger = get_logger("mvidarr.api.migrations")

migrations_bp = Blueprint("migrations", __name__, url_prefix="/migrations")


@migrations_bp.route("/status", methods=["GET"])
@auth_required
def get_migrations_status():
    """Get current migration status"""
    try:
        status = get_migration_status()
        return jsonify({"success": True, "status": status}), 200

    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        return jsonify({"error": str(e)}), 500


@migrations_bp.route("/run", methods=["POST"])
@auth_required
def run_pending_migrations():
    """Run all pending migrations"""
    try:
        results = run_migrations()

        if results["success"]:
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Migrations completed successfully",
                        "applied_migrations": results["applied_migrations"],
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Some migrations failed",
                        "applied_migrations": results["applied_migrations"],
                        "errors": results["errors"],
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        return jsonify({"error": str(e)}), 500


@migrations_bp.route("/rollback/<version>", methods=["POST"])
@auth_required
def rollback_migration_endpoint(version):
    """Rollback a specific migration"""
    try:
        success = rollback_migration(version)

        if success:
            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Migration {version} rolled back successfully",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Failed to rollback migration {version}",
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Failed to rollback migration {version}: {e}")
        return jsonify({"error": str(e)}), 500
