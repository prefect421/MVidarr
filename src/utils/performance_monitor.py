"""
API Performance Monitoring Utilities
Provides decorators and tools to monitor API endpoint performance
"""

import functools
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("mvidarr.performance")


class PerformanceStats:
    """Thread-safe performance statistics collector"""

    def __init__(self):
        self.stats: Dict[str, List[float]] = {}
        self.request_counts: Dict[str, int] = {}

    def record_time(self, endpoint: str, response_time: float):
        """Record response time for an endpoint"""
        if endpoint not in self.stats:
            self.stats[endpoint] = []
            self.request_counts[endpoint] = 0

        self.stats[endpoint].append(response_time)
        self.request_counts[endpoint] += 1

        # Keep only last 100 measurements to prevent memory bloat
        if len(self.stats[endpoint]) > 100:
            self.stats[endpoint] = self.stats[endpoint][-100:]

    def get_stats(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get performance statistics for an endpoint"""
        if endpoint not in self.stats or not self.stats[endpoint]:
            return None

        times = self.stats[endpoint]
        return {
            "endpoint": endpoint,
            "total_requests": self.request_counts[endpoint],
            "recent_samples": len(times),
            "avg_response_time": sum(times) / len(times),
            "min_response_time": min(times),
            "max_response_time": max(times),
            "latest_response_time": times[-1],
        }

    def get_all_stats(self) -> List[Dict[str, Any]]:
        """Get performance statistics for all monitored endpoints"""
        return [
            self.get_stats(endpoint)
            for endpoint in self.stats.keys()
            if self.stats[endpoint]
        ]

    def get_slow_endpoints(self, threshold_ms: float = 500) -> List[Dict[str, Any]]:
        """Get endpoints that are slower than threshold"""
        slow_endpoints = []
        for endpoint_stats in self.get_all_stats():
            if endpoint_stats["avg_response_time"] > threshold_ms / 1000:
                slow_endpoints.append(endpoint_stats)

        # Sort by average response time (slowest first)
        return sorted(
            slow_endpoints, key=lambda x: x["avg_response_time"], reverse=True
        )


# Global performance statistics collector
perf_stats = PerformanceStats()


def monitor_performance(endpoint_name: Optional[str] = None):
    """
    Decorator to monitor API endpoint performance

    Usage:
        @monitor_performance("search_videos")
        def search_videos():
            # endpoint implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        nonlocal endpoint_name
        if endpoint_name is None:
            endpoint_name = f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                response_time = end_time - start_time

                # Record the performance data
                perf_stats.record_time(endpoint_name, response_time)

                # Log slow responses
                if response_time > 1.0:  # Log responses over 1 second
                    logger.warning(
                        f"Slow API response: {endpoint_name} took {response_time:.3f}s"
                    )
                elif response_time > 0.5:  # Log responses over 500ms
                    logger.info(
                        f"API response: {endpoint_name} took {response_time:.3f}s"
                    )
                else:
                    logger.debug(
                        f"API response: {endpoint_name} took {response_time:.3f}s"
                    )

        return wrapper

    return decorator


def get_performance_report() -> Dict[str, Any]:
    """Generate a comprehensive performance report"""
    all_stats = perf_stats.get_all_stats()
    slow_endpoints = perf_stats.get_slow_endpoints(500)  # 500ms threshold

    if not all_stats:
        return {
            "summary": {
                "message": "No API performance data available",
                "total_endpoints_monitored": 0,
                "total_requests_processed": 0,
                "slow_endpoints_count": 0,
            },
            "slow_endpoints": [],
            "all_endpoints": [],
            "generated_at": datetime.now().isoformat(),
        }

    # Calculate summary statistics
    avg_times = [stat["avg_response_time"] for stat in all_stats]
    total_requests = sum(stat["total_requests"] for stat in all_stats)

    report = {
        "summary": {
            "total_endpoints_monitored": len(all_stats),
            "total_requests_processed": total_requests,
            "slow_endpoints_count": len(slow_endpoints),
            "overall_avg_response_time": sum(avg_times) / len(avg_times),
            "slowest_endpoint": max(all_stats, key=lambda x: x["avg_response_time"]),
            "fastest_endpoint": min(all_stats, key=lambda x: x["avg_response_time"]),
        },
        "slow_endpoints": slow_endpoints,
        "all_endpoints": sorted(
            all_stats, key=lambda x: x["avg_response_time"], reverse=True
        ),
        "generated_at": datetime.now().isoformat(),
    }

    return report


def log_performance_summary():
    """Log a performance summary to help identify issues"""
    report = get_performance_report()

    if report["summary"]["total_endpoints_monitored"] == 0:
        logger.info("No API performance data to report")
        return

    summary = report["summary"]
    logger.info(f"=== API Performance Summary ===")
    logger.info(f"Monitored Endpoints: {summary['total_endpoints_monitored']}")
    logger.info(f"Total Requests: {summary['total_requests_processed']}")
    logger.info(f"Average Response Time: {summary['overall_avg_response_time']:.3f}s")
    logger.info(f"Slow Endpoints (>500ms): {summary['slow_endpoints_count']}")

    if summary["slow_endpoints_count"] > 0:
        logger.warning("🐌 SLOW ENDPOINTS DETECTED:")
        for endpoint in report["slow_endpoints"][:5]:  # Top 5 slowest
            logger.warning(
                f"  {endpoint['endpoint']}: {endpoint['avg_response_time']:.3f}s avg "
                f"({endpoint['total_requests']} requests)"
            )

    fastest = summary["fastest_endpoint"]
    slowest = summary["slowest_endpoint"]
    logger.info(
        f"⚡ Fastest: {fastest['endpoint']} ({fastest['avg_response_time']:.3f}s)"
    )
    logger.info(
        f"🐌 Slowest: {slowest['endpoint']} ({slowest['avg_response_time']:.3f}s)"
    )
