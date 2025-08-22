"""
Bulk Operations API endpoints for MVidarr 0.9.7 - Issue #74
Provides comprehensive bulk operations with background processing, progress tracking, and undo/redo.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from flask import Blueprint, g, jsonify, request
from marshmallow import Schema, ValidationError, fields

from src.database.bulk_models import BulkOperationStatus, BulkOperationType
from src.database.connection import get_db
from src.middleware.simple_auth_middleware import auth_required
from src.services.bulk_operations_service import bulk_operations_service
from src.utils.logger import get_logger

bulk_operations_bp = Blueprint("bulk_operations", __name__, url_prefix="/bulk")
logger = get_logger("mvidarr.api.bulk_operations")


# Request/Response schemas for validation
class BulkOperationCreateSchema(Schema):
    """Schema for creating bulk operations"""

    operation_type = fields.Str(required=True)
    operation_name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    target_ids = fields.List(fields.Int(), required=True, validate=lambda x: len(x) > 0)
    operation_params = fields.Dict(missing={})
    is_preview = fields.Bool(missing=False)


class BulkOperationUpdateSchema(Schema):
    """Schema for updating bulk operations"""

    action = fields.Str(
        required=True, validate=lambda x: x in ["start", "cancel", "undo"]
    )


@bulk_operations_bp.route("/operations", methods=["POST"])
@auth_required
def create_bulk_operation():
    """
    Create a new bulk operation

    POST /api/bulk/operations
    {
        "operation_type": "VIDEO_STATUS_UPDATE",
        "operation_name": "Update video status to Downloaded",
        "description": "Bulk update selected videos to Downloaded status",
        "target_ids": [1, 2, 3, 4, 5],
        "operation_params": {
            "new_status": "DOWNLOADED"
        },
        "is_preview": false
    }
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        # Validate request data
        schema = BulkOperationCreateSchema()
        try:
            validated_data = schema.load(request.get_json() or {})
        except ValidationError as e:
            return (
                jsonify({"error": "Invalid request data", "details": e.messages}),
                400,
            )

        # Validate operation type
        try:
            operation_type = BulkOperationType(validated_data["operation_type"])
        except ValueError:
            return (
                jsonify(
                    {
                        "error": f"Invalid operation type: {validated_data['operation_type']}"
                    }
                ),
                400,
            )

        # Validate target_ids limit
        if len(validated_data["target_ids"]) > 1000:
            return jsonify({"error": "Maximum 1000 items per bulk operation"}), 400

        # Create the operation
        operation = bulk_operations_service.create_operation(
            user_id=user_id,
            operation_type=operation_type,
            operation_name=validated_data["operation_name"],
            target_ids=validated_data["target_ids"],
            operation_params=validated_data["operation_params"],
            description=validated_data.get("description"),
            is_preview=validated_data["is_preview"],
        )

        return (
            jsonify(
                {
                    "message": "Bulk operation created successfully",
                    "operation": operation.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Error creating bulk operation: {str(e)}")
        return (
            jsonify({"error": "Failed to create bulk operation", "message": str(e)}),
            500,
        )


@bulk_operations_bp.route("/operations/<int:operation_id>", methods=["GET"])
@auth_required
def get_bulk_operation(operation_id: int):
    """
    Get a specific bulk operation

    GET /api/bulk/operations/123?include_sensitive=true
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        include_sensitive = (
            request.args.get("include_sensitive", "false").lower() == "true"
        )

        operation = bulk_operations_service.get_operation(
            operation_id, include_sensitive
        )

        if not operation:
            return jsonify({"error": "Operation not found"}), 404

        # Check if user owns the operation
        if operation.user_id != user_id:
            return jsonify({"error": "Access denied"}), 403

        # Get latest progress
        with get_db() as db:
            latest_progress = (
                db.query(bulk_operations_service.processor.BulkOperationProgress)
                .filter_by(operation_id=operation_id)
                .order_by(
                    bulk_operations_service.processor.BulkOperationProgress.updated_at.desc()
                )
                .first()
            )

        result = operation.to_dict(include_sensitive=include_sensitive)
        if latest_progress:
            result["latest_progress"] = latest_progress.to_dict()

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting bulk operation: {str(e)}")
        return jsonify({"error": "Failed to get operation", "message": str(e)}), 500


@bulk_operations_bp.route("/operations/<int:operation_id>", methods=["PUT"])
@auth_required
def update_bulk_operation(operation_id: int):
    """
    Update a bulk operation (start, cancel, undo)

    PUT /api/bulk/operations/123
    {
        "action": "start"
    }
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        # Validate request data
        schema = BulkOperationUpdateSchema()
        try:
            validated_data = schema.load(request.get_json() or {})
        except ValidationError as e:
            return (
                jsonify({"error": "Invalid request data", "details": e.messages}),
                400,
            )

        action = validated_data["action"]

        if action == "start":
            success = bulk_operations_service.start_operation(operation_id)
            if success:
                return jsonify({"message": "Operation started successfully"})
            else:
                return jsonify({"error": "Failed to start operation"}), 400

        elif action == "cancel":
            success = bulk_operations_service.cancel_operation(operation_id)
            if success:
                return jsonify({"message": "Operation cancelled successfully"})
            else:
                return jsonify({"error": "Failed to cancel operation"}), 400

        elif action == "undo":
            success = bulk_operations_service.undo_operation(operation_id, user_id)
            if success:
                return jsonify({"message": "Operation undo started successfully"})
            else:
                return jsonify({"error": "Failed to undo operation"}), 400

        else:
            return jsonify({"error": f"Invalid action: {action}"}), 400

    except Exception as e:
        logger.error(f"Error updating bulk operation: {str(e)}")
        return jsonify({"error": "Failed to update operation", "message": str(e)}), 500


@bulk_operations_bp.route("/operations", methods=["GET"])
@auth_required
def list_bulk_operations():
    """
    List bulk operations for the current user

    GET /api/bulk/operations?limit=50&status=COMPLETED
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        limit = min(request.args.get("limit", 50, type=int), 100)
        status_filter = request.args.get("status")

        # Validate status if provided
        status_enum = None
        if status_filter:
            try:
                status_enum = BulkOperationStatus(status_filter)
            except ValueError:
                return jsonify({"error": f"Invalid status: {status_filter}"}), 400

        operations = bulk_operations_service.get_user_operations(
            user_id=user_id, limit=limit, status=status_enum
        )

        return jsonify(
            {
                "operations": [op.to_dict() for op in operations],
                "total": len(operations),
            }
        )

    except Exception as e:
        logger.error(f"Error listing bulk operations: {str(e)}")
        return jsonify({"error": "Failed to list operations", "message": str(e)}), 500


@bulk_operations_bp.route("/operations/<int:operation_id>/progress", methods=["GET"])
@auth_required
def get_operation_progress(operation_id: int):
    """
    Get real-time progress for a bulk operation

    GET /api/bulk/operations/123/progress
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        # Verify user owns the operation
        operation = bulk_operations_service.get_operation(operation_id)
        if not operation or operation.user_id != user_id:
            return jsonify({"error": "Operation not found or access denied"}), 404

        with get_db() as db:
            # Get all progress updates for this operation
            from src.database.bulk_models import BulkOperationProgress

            progress_updates = (
                db.query(BulkOperationProgress)
                .filter_by(operation_id=operation_id)
                .order_by(BulkOperationProgress.updated_at.desc())
                .limit(10)
                .all()
            )

        return jsonify(
            {
                "operation_id": operation_id,
                "current_status": operation.status.value,
                "progress_percentage": operation.progress_percentage,
                "processed_items": operation.processed_items,
                "total_items": operation.total_items,
                "successful_items": operation.successful_items,
                "failed_items": operation.failed_items,
                "progress_updates": [
                    progress.to_dict() for progress in progress_updates
                ],
            }
        )

    except Exception as e:
        logger.error(f"Error getting operation progress: {str(e)}")
        return jsonify({"error": "Failed to get progress", "message": str(e)}), 500


@bulk_operations_bp.route("/operations/<int:operation_id>/audit", methods=["GET"])
@auth_required
def get_operation_audit(operation_id: int):
    """
    Get audit trail for a bulk operation

    GET /api/bulk/operations/123/audit?limit=100
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        limit = min(request.args.get("limit", 100, type=int), 500)

        # Verify user owns the operation
        operation = bulk_operations_service.get_operation(operation_id)
        if not operation or operation.user_id != user_id:
            return jsonify({"error": "Operation not found or access denied"}), 404

        with get_db() as db:
            from src.database.bulk_models import BulkOperationAudit

            audit_entries = (
                db.query(BulkOperationAudit)
                .filter_by(operation_id=operation_id)
                .order_by(BulkOperationAudit.timestamp.desc())
                .limit(limit)
                .all()
            )

        return jsonify(
            {
                "operation_id": operation_id,
                "audit_entries": [entry.to_dict() for entry in audit_entries],
                "total_entries": len(audit_entries),
            }
        )

    except Exception as e:
        logger.error(f"Error getting operation audit: {str(e)}")
        return jsonify({"error": "Failed to get audit trail", "message": str(e)}), 500


@bulk_operations_bp.route("/templates", methods=["GET"])
@auth_required
def list_operation_templates():
    """
    List available bulk operation templates

    GET /api/bulk/templates?operation_type=VIDEO_STATUS_UPDATE
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        operation_type_filter = request.args.get("operation_type")

        with get_db() as db:
            from src.database.bulk_models import BulkOperationTemplate

            query = db.query(BulkOperationTemplate).filter(
                (BulkOperationTemplate.user_id == user_id)
                | (BulkOperationTemplate.is_public == True)
                | (BulkOperationTemplate.is_system == True)
            )

            if operation_type_filter:
                try:
                    operation_type = BulkOperationType(operation_type_filter)
                    query = query.filter(
                        BulkOperationTemplate.operation_type == operation_type
                    )
                except ValueError:
                    return (
                        jsonify(
                            {
                                "error": f"Invalid operation type: {operation_type_filter}"
                            }
                        ),
                        400,
                    )

            templates = query.order_by(
                BulkOperationTemplate.is_system.desc(),
                BulkOperationTemplate.usage_count.desc(),
                BulkOperationTemplate.name,
            ).all()

        return jsonify(
            {
                "templates": [template.to_dict() for template in templates],
                "total": len(templates),
            }
        )

    except Exception as e:
        logger.error(f"Error listing operation templates: {str(e)}")
        return jsonify({"error": "Failed to list templates", "message": str(e)}), 500


@bulk_operations_bp.route("/preview", methods=["POST"])
@auth_required
def preview_bulk_operation():
    """
    Preview a bulk operation without executing it

    POST /api/bulk/preview
    {
        "operation_type": "VIDEO_STATUS_UPDATE",
        "target_ids": [1, 2, 3],
        "operation_params": {
            "new_status": "DOWNLOADED"
        }
    }
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        data = request.get_json() or {}

        # Validate operation type
        try:
            operation_type = BulkOperationType(data.get("operation_type", ""))
        except ValueError:
            return jsonify({"error": "Invalid operation type"}), 400

        target_ids = data.get("target_ids", [])
        if not target_ids or len(target_ids) > 1000:
            return jsonify({"error": "Invalid target_ids (max 1000)"}), 400

        operation_params = data.get("operation_params", {})

        # Create preview operation
        operation = bulk_operations_service.create_operation(
            user_id=user_id,
            operation_type=operation_type,
            operation_name=f"Preview: {operation_type.value}",
            target_ids=target_ids,
            operation_params=operation_params,
            is_preview=True,
        )

        # Start preview processing
        if bulk_operations_service.start_operation(operation.id):
            # Get results
            operation = bulk_operations_service.get_operation(
                operation.id, include_sensitive=True
            )
            return jsonify(
                {
                    "preview_results": operation.preview_results,
                    "operation": operation.to_dict(include_sensitive=True),
                }
            )
        else:
            return jsonify({"error": "Failed to process preview"}), 500

    except Exception as e:
        logger.error(f"Error previewing bulk operation: {str(e)}")
        return jsonify({"error": "Failed to preview operation", "message": str(e)}), 500


@bulk_operations_bp.route("/stats", methods=["GET"])
@auth_required
def get_bulk_operation_stats():
    """
    Get bulk operation statistics for the current user

    GET /api/bulk/stats?days=30
    """
    try:
        user_id = getattr(g, "current_user_id", None)
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401

        days = min(request.args.get("days", 30, type=int), 365)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with get_db() as db:
            from sqlalchemy import func

            from src.database.bulk_models import BulkOperation

            # Basic stats
            total_operations = (
                db.query(BulkOperation)
                .filter(
                    BulkOperation.user_id == user_id,
                    BulkOperation.created_at >= cutoff_date,
                )
                .count()
            )

            # Status breakdown
            status_stats = (
                db.query(BulkOperation.status, func.count(BulkOperation.id))
                .filter(
                    BulkOperation.user_id == user_id,
                    BulkOperation.created_at >= cutoff_date,
                )
                .group_by(BulkOperation.status)
                .all()
            )

            # Operation type breakdown
            type_stats = (
                db.query(BulkOperation.operation_type, func.count(BulkOperation.id))
                .filter(
                    BulkOperation.user_id == user_id,
                    BulkOperation.created_at >= cutoff_date,
                )
                .group_by(BulkOperation.operation_type)
                .all()
            )

            # Item processing stats
            total_items_processed = (
                db.query(func.sum(BulkOperation.processed_items))
                .filter(
                    BulkOperation.user_id == user_id,
                    BulkOperation.created_at >= cutoff_date,
                )
                .scalar()
                or 0
            )

            total_items_successful = (
                db.query(func.sum(BulkOperation.successful_items))
                .filter(
                    BulkOperation.user_id == user_id,
                    BulkOperation.created_at >= cutoff_date,
                )
                .scalar()
                or 0
            )

        return jsonify(
            {
                "period_days": days,
                "total_operations": total_operations,
                "total_items_processed": total_items_processed,
                "total_items_successful": total_items_successful,
                "success_rate": (
                    (total_items_successful / total_items_processed * 100)
                    if total_items_processed > 0
                    else 0
                ),
                "status_breakdown": {
                    status.value: count for status, count in status_stats
                },
                "operation_type_breakdown": {
                    op_type.value: count for op_type, count in type_stats
                },
            }
        )

    except Exception as e:
        logger.error(f"Error getting bulk operation stats: {str(e)}")
        return jsonify({"error": "Failed to get statistics", "message": str(e)}), 500
