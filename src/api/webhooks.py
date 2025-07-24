"""
Webhook API endpoints for event-driven notifications
"""

from flask import Blueprint, jsonify, request

from src.services.webhook_service import (
    WebhookEndpoint,
    WebhookEventType,
    webhook_service,
)
from src.utils.logger import get_logger

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/webhooks")
logger = get_logger("mvidarr.api.webhooks")


@webhooks_bp.route("/", methods=["GET"])
def get_webhooks():
    """Get all webhook endpoints"""
    try:
        endpoints = webhook_service.get_endpoints()
        return jsonify({"webhooks": endpoints, "count": len(endpoints)}), 200

    except Exception as e:
        logger.error(f"Failed to get webhooks: {e}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/", methods=["POST"])
def create_webhook():
    """Create a new webhook endpoint"""
    try:
        data = request.get_json()

        if not data or "url" not in data:
            return jsonify({"error": "URL is required"}), 400

        # Validate event types
        events = []
        if "events" in data:
            for event_str in data["events"]:
                try:
                    events.append(WebhookEventType(event_str))
                except ValueError:
                    return jsonify({"error": f"Invalid event type: {event_str}"}), 400

        endpoint = WebhookEndpoint(
            url=data["url"],
            secret=data.get("secret"),
            events=events,
            enabled=data.get("enabled", True),
            max_retries=data.get("max_retries", 3),
            timeout=data.get("timeout", 30),
            headers=data.get("headers", {}),
        )

        success = webhook_service.add_endpoint(endpoint)

        if success:
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Webhook endpoint created successfully",
                        "url": endpoint.url,
                    }
                ),
                201,
            )
        else:
            return jsonify({"error": "Failed to create webhook endpoint"}), 400

    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/<path:url>", methods=["PUT"])
def update_webhook(url):
    """Update webhook endpoint configuration"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate event types if provided
        if "events" in data:
            try:
                # Convert event strings to enum values for validation
                event_values = []
                for event_str in data["events"]:
                    WebhookEventType(event_str)  # Validate
                    event_values.append(event_str)
                data["events"] = event_values
            except ValueError as e:
                return jsonify({"error": f"Invalid event type: {e}"}), 400

        success = webhook_service.update_endpoint(url, data)

        if success:
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Webhook endpoint updated successfully",
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Webhook endpoint not found"}), 404

    except Exception as e:
        logger.error(f"Failed to update webhook: {e}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/<path:url>", methods=["DELETE"])
def delete_webhook(url):
    """Delete webhook endpoint"""
    try:
        success = webhook_service.remove_endpoint(url)

        if success:
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Webhook endpoint deleted successfully",
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Webhook endpoint not found"}), 404

    except Exception as e:
        logger.error(f"Failed to delete webhook: {e}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/test", methods=["POST"])
def test_webhook():
    """Test webhook endpoint"""
    try:
        data = request.get_json()

        if not data or "url" not in data:
            return jsonify({"error": "URL is required"}), 400

        url = data["url"]
        secret = data.get("secret")

        result = webhook_service.test_endpoint(url, secret)

        return jsonify({"test_result": result, "url": url}), 200

    except Exception as e:
        logger.error(f"Failed to test webhook: {e}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/events", methods=["GET"])
def get_event_types():
    """Get available webhook event types"""
    try:
        event_types = webhook_service.get_event_types()
        return jsonify({"event_types": event_types, "count": len(event_types)}), 200

    except Exception as e:
        logger.error(f"Failed to get event types: {e}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/trigger", methods=["POST"])
def trigger_webhook():
    """Trigger a webhook event manually (for testing)"""
    try:
        data = request.get_json()

        if not data or "event_type" not in data:
            return jsonify({"error": "event_type is required"}), 400

        try:
            event_type = WebhookEventType(data["event_type"])
        except ValueError:
            return jsonify({"error": f'Invalid event type: {data["event_type"]}'}), 400

        event_data = data.get("data", {})
        metadata = data.get("metadata", {})

        # Add test flag to metadata
        metadata["test_trigger"] = True
        metadata["triggered_by"] = "api"

        webhook_service.trigger_event(event_type, event_data, metadata)

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Webhook event {event_type.value} triggered successfully",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to trigger webhook: {e}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/validate", methods=["POST"])
def validate_webhook():
    """Validate webhook configuration"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        validation_errors = []

        # Validate URL
        if "url" not in data:
            validation_errors.append("URL is required")
        elif not data["url"].startswith(("http://", "https://")):
            validation_errors.append("URL must start with http:// or https://")

        # Validate event types
        if "events" in data:
            for event_str in data["events"]:
                try:
                    WebhookEventType(event_str)
                except ValueError:
                    validation_errors.append(f"Invalid event type: {event_str}")

        # Validate max_retries
        if "max_retries" in data:
            try:
                max_retries = int(data["max_retries"])
                if max_retries < 0 or max_retries > 10:
                    validation_errors.append("max_retries must be between 0 and 10")
            except ValueError:
                validation_errors.append("max_retries must be a number")

        # Validate timeout
        if "timeout" in data:
            try:
                timeout = int(data["timeout"])
                if timeout < 1 or timeout > 300:
                    validation_errors.append(
                        "timeout must be between 1 and 300 seconds"
                    )
            except ValueError:
                validation_errors.append("timeout must be a number")

        # Validate headers
        if "headers" in data:
            if not isinstance(data["headers"], dict):
                validation_errors.append("headers must be a dictionary")

        if validation_errors:
            return jsonify({"valid": False, "errors": validation_errors}), 400
        else:
            return (
                jsonify({"valid": True, "message": "Webhook configuration is valid"}),
                200,
            )

    except Exception as e:
        logger.error(f"Failed to validate webhook: {e}")
        return jsonify({"error": str(e)}), 500


@webhooks_bp.route("/stats", methods=["GET"])
def get_webhook_stats():
    """Get webhook statistics"""
    try:
        endpoints = webhook_service.get_endpoints()

        stats = {
            "total_endpoints": len(endpoints),
            "enabled_endpoints": len([ep for ep in endpoints if ep["enabled"]]),
            "disabled_endpoints": len([ep for ep in endpoints if not ep["enabled"]]),
            "event_types_used": set(),
            "endpoints_by_event": {},
        }

        for endpoint in endpoints:
            for event in endpoint["events"]:
                stats["event_types_used"].add(event)
                if event not in stats["endpoints_by_event"]:
                    stats["endpoints_by_event"][event] = 0
                stats["endpoints_by_event"][event] += 1

        stats["event_types_used"] = list(stats["event_types_used"])

        return jsonify({"stats": stats}), 200

    except Exception as e:
        logger.error(f"Failed to get webhook stats: {e}")
        return jsonify({"error": str(e)}), 500
