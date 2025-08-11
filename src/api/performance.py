"""
API Performance Monitoring Endpoints
Provides endpoints to view and analyze API performance data
"""

from flask import Blueprint, jsonify, request

from src.utils.logger import get_logger
from src.utils.performance_monitor import (
    get_performance_report,
    log_performance_summary,
)

logger = get_logger("mvidarr.api.performance")

performance_bp = Blueprint("performance", __name__, url_prefix="/api/performance")


@performance_bp.route("/stats", methods=["GET"])
def get_performance_stats():
    """Get comprehensive API performance statistics"""
    try:
        report = get_performance_report()

        # Filter by threshold if requested
        threshold = request.args.get("threshold", type=float)
        if threshold:
            report["filtered_endpoints"] = [
                endpoint
                for endpoint in report["all_endpoints"]
                if endpoint["avg_response_time"] > threshold / 1000
            ]

        return jsonify(report), 200

    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/slow", methods=["GET"])
def get_slow_endpoints():
    """Get endpoints that are slower than specified threshold"""
    try:
        threshold = request.args.get("threshold", 500, type=int)  # Default 500ms
        report = get_performance_report()

        slow_endpoints = [
            endpoint
            for endpoint in report["all_endpoints"]
            if endpoint["avg_response_time"] > threshold / 1000
        ]

        return (
            jsonify(
                {
                    "threshold_ms": threshold,
                    "slow_endpoints_count": len(slow_endpoints),
                    "slow_endpoints": slow_endpoints,
                    "analysis": {
                        "critical_endpoints": [
                            e for e in slow_endpoints if e["avg_response_time"] > 1.0
                        ],
                        "needs_attention": [
                            e
                            for e in slow_endpoints
                            if 0.5 < e["avg_response_time"] <= 1.0
                        ],
                        "minor_issues": [
                            e for e in slow_endpoints if e["avg_response_time"] <= 0.5
                        ],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get slow endpoints: {e}")
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/summary", methods=["GET"])
def get_performance_summary():
    """Get a concise performance summary"""
    try:
        report = get_performance_report()

        if not report.get("summary"):
            return (
                jsonify(
                    {
                        "message": "No performance data available yet",
                        "recommendation": "Make some API requests to collect performance data",
                    }
                ),
                200,
            )

        summary = report["summary"]

        # Generate recommendations based on performance data
        recommendations = []
        if summary["slow_endpoints_count"] > 0:
            recommendations.append(
                f"Consider optimizing {summary['slow_endpoints_count']} slow endpoints"
            )

        if summary["overall_avg_response_time"] > 1.0:
            recommendations.append(
                "Overall API performance is slow - review database queries and caching"
            )
        elif summary["overall_avg_response_time"] > 0.5:
            recommendations.append(
                "API performance is acceptable but could be improved"
            )
        else:
            recommendations.append("API performance is good")

        return (
            jsonify(
                {
                    "performance_summary": summary,
                    "recommendations": recommendations,
                    "top_slow_endpoints": report["slow_endpoints"][:3],  # Top 3 slowest
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/log-summary", methods=["POST"])
def trigger_performance_log():
    """Manually trigger performance summary logging"""
    try:
        log_performance_summary()
        return jsonify({"message": "Performance summary logged successfully"}), 200

    except Exception as e:
        logger.error(f"Failed to log performance summary: {e}")
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/health", methods=["GET"])
def performance_health():
    """Check if performance monitoring is working"""
    try:
        report = get_performance_report()

        status = "healthy"
        issues = []

        if report["summary"]["total_endpoints_monitored"] == 0:
            status = "no_data"
            issues.append("No endpoints are being monitored yet")

        elif (
            report["summary"]["slow_endpoints_count"]
            > report["summary"]["total_endpoints_monitored"] / 2
        ):
            status = "degraded"
            issues.append("More than 50% of endpoints are slow")

        elif report["summary"]["overall_avg_response_time"] > 2.0:
            status = "degraded"
            issues.append("Overall response time is very slow (>2s)")

        return (
            jsonify(
                {
                    "status": status,
                    "monitored_endpoints": report["summary"][
                        "total_endpoints_monitored"
                    ],
                    "slow_endpoints": report["summary"]["slow_endpoints_count"],
                    "overall_avg_time": report["summary"]["overall_avg_response_time"],
                    "issues": issues,
                    "message": "Performance monitoring is active",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Performance health check failed: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500
