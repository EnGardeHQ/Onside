"""
Performance Monitoring Middleware

Provides comprehensive performance monitoring for FastAPI including:
- Request/response timing
- Slow request detection and logging
- Endpoint performance metrics
- Database query profiling
- Memory usage tracking
- Prometheus metrics export
"""
import time
import logging
import psutil
import asyncio
from typing import Callable, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
import json

logger = logging.getLogger(__name__)


class PerformanceStats:
    """Track performance statistics for endpoints."""

    def __init__(self, max_samples: int = 1000):
        """Initialize performance stats.

        Args:
            max_samples: Maximum number of samples to keep per endpoint
        """
        self.max_samples = max_samples
        self.endpoint_times: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_samples)
        )
        self.endpoint_counts: Dict[str, int] = defaultdict(int)
        self.slow_requests: deque = deque(maxlen=100)  # Keep last 100 slow requests
        self.error_counts: Dict[str, int] = defaultdict(int)

    def record_request(
        self,
        endpoint: str,
        method: str,
        duration: float,
        status_code: int,
        slow_threshold: float = 1.0
    ):
        """Record a request's performance metrics.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            duration: Request duration in seconds
            status_code: HTTP status code
            slow_threshold: Threshold for slow request logging (seconds)
        """
        key = f"{method}:{endpoint}"
        self.endpoint_times[key].append(duration)
        self.endpoint_counts[key] += 1

        # Track errors
        if status_code >= 400:
            self.error_counts[key] += 1

        # Track slow requests
        if duration >= slow_threshold:
            self.slow_requests.append({
                'endpoint': endpoint,
                'method': method,
                'duration': duration,
                'status_code': status_code,
                'timestamp': datetime.utcnow().isoformat()
            })

    def get_endpoint_stats(self, endpoint: str, method: str) -> Dict:
        """Get statistics for a specific endpoint.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Returns:
            Dictionary with endpoint statistics
        """
        key = f"{method}:{endpoint}"
        times = list(self.endpoint_times[key])

        if not times:
            return {
                'endpoint': endpoint,
                'method': method,
                'count': 0
            }

        times_sorted = sorted(times)
        count = len(times)

        return {
            'endpoint': endpoint,
            'method': method,
            'count': self.endpoint_counts[key],
            'avg_duration': sum(times) / count,
            'min_duration': min(times),
            'max_duration': max(times),
            'p50_duration': times_sorted[count // 2],
            'p95_duration': times_sorted[int(count * 0.95)] if count > 20 else times_sorted[-1],
            'p99_duration': times_sorted[int(count * 0.99)] if count > 100 else times_sorted[-1],
            'error_count': self.error_counts[key],
            'error_rate': self.error_counts[key] / self.endpoint_counts[key] * 100
        }

    def get_all_stats(self) -> List[Dict]:
        """Get statistics for all endpoints.

        Returns:
            List of endpoint statistics
        """
        stats = []
        for key in self.endpoint_times.keys():
            method, endpoint = key.split(':', 1)
            stats.append(self.get_endpoint_stats(endpoint, method))

        # Sort by total time spent (avg * count)
        stats.sort(
            key=lambda x: x.get('avg_duration', 0) * x.get('count', 0),
            reverse=True
        )

        return stats

    def get_slow_requests(self) -> List[Dict]:
        """Get recent slow requests.

        Returns:
            List of slow request records
        """
        return list(self.slow_requests)


class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring API performance.

    Features:
    - Request timing with high precision
    - Slow request detection and logging
    - Per-endpoint metrics aggregation
    - Memory usage tracking
    - Database query profiling integration
    """

    def __init__(
        self,
        app: FastAPI,
        slow_threshold: float = 1.0,
        enable_memory_tracking: bool = True,
        log_slow_requests: bool = True
    ):
        """Initialize performance monitor.

        Args:
            app: FastAPI application instance
            slow_threshold: Threshold for slow request logging (seconds)
            enable_memory_tracking: Enable memory usage tracking
            log_slow_requests: Log slow requests to logger
        """
        super().__init__(app)
        self.slow_threshold = slow_threshold
        self.enable_memory_tracking = enable_memory_tracking
        self.log_slow_requests = log_slow_requests
        self.stats = PerformanceStats()
        self.process = psutil.Process() if enable_memory_tracking else None

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request and track performance.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response from the application
        """
        # Start timing
        start_time = time.perf_counter()
        start_memory = None

        if self.enable_memory_tracking and self.process:
            try:
                mem_info = self.process.memory_info()
                start_memory = mem_info.rss / 1024 / 1024  # MB
            except Exception as e:
                logger.warning(f"Error tracking memory: {e}")

        # Process request
        response = None
        error_occurred = False

        try:
            response = await call_next(request)
        except Exception as e:
            error_occurred = True
            logger.error(f"Error processing request: {e}")
            raise
        finally:
            # Calculate duration
            duration = time.perf_counter() - start_time

            # Get endpoint path
            endpoint = request.url.path
            method = request.method

            # Get status code
            status_code = response.status_code if response else 500

            # Record metrics
            self.stats.record_request(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=status_code,
                slow_threshold=self.slow_threshold
            )

            # Log slow requests
            if self.log_slow_requests and duration >= self.slow_threshold:
                memory_delta = ""
                if start_memory and self.process:
                    try:
                        end_memory = self.process.memory_info().rss / 1024 / 1024
                        memory_delta = f", Memory: {start_memory:.1f}MB -> {end_memory:.1f}MB (Δ{end_memory - start_memory:+.1f}MB)"
                    except Exception:
                        pass

                logger.warning(
                    f"SLOW REQUEST: {method} {endpoint} - "
                    f"Duration: {duration:.3f}s, "
                    f"Status: {status_code}"
                    f"{memory_delta}"
                )

            # Add timing headers to response
            if response:
                response.headers["X-Process-Time"] = f"{duration:.3f}"
                if start_memory and self.process:
                    try:
                        end_memory = self.process.memory_info().rss / 1024 / 1024
                        response.headers["X-Memory-Usage"] = f"{end_memory:.1f}"
                    except Exception:
                        pass

        return response

    def get_stats(self) -> Dict:
        """Get performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoints': self.stats.get_all_stats(),
            'slow_requests': self.stats.get_slow_requests(),
            'system': self._get_system_stats()
        }

    def _get_system_stats(self) -> Dict:
        """Get system resource statistics.

        Returns:
            Dictionary with system metrics
        """
        stats = {}

        if self.process:
            try:
                mem_info = self.process.memory_info()
                stats['memory'] = {
                    'rss_mb': mem_info.rss / 1024 / 1024,
                    'vms_mb': mem_info.vms / 1024 / 1024,
                }

                cpu_percent = self.process.cpu_percent(interval=0.1)
                stats['cpu'] = {
                    'percent': cpu_percent,
                    'num_threads': self.process.num_threads()
                }
            except Exception as e:
                logger.warning(f"Error getting system stats: {e}")

        # System-wide stats
        try:
            stats['system'] = {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent
            }
        except Exception as e:
            logger.warning(f"Error getting system-wide stats: {e}")

        return stats


# Database query profiler integration
class DatabaseQueryProfiler:
    """Profile database queries for performance analysis."""

    def __init__(self):
        """Initialize query profiler."""
        self.queries: deque = deque(maxlen=1000)
        self.slow_query_threshold = 0.1  # 100ms

    def record_query(
        self,
        query: str,
        duration: float,
        params: Optional[Dict] = None
    ):
        """Record a database query.

        Args:
            query: SQL query string
            duration: Query duration in seconds
            params: Query parameters
        """
        record = {
            'query': query[:500],  # Truncate long queries
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat(),
            'slow': duration >= self.slow_query_threshold
        }

        if params:
            record['params'] = str(params)[:200]

        self.queries.append(record)

        # Log slow queries
        if duration >= self.slow_query_threshold:
            logger.warning(
                f"SLOW QUERY: {duration:.3f}s - {query[:200]}"
            )

    def get_slow_queries(self) -> List[Dict]:
        """Get recent slow queries.

        Returns:
            List of slow query records
        """
        return [q for q in self.queries if q['slow']]

    def get_stats(self) -> Dict:
        """Get query statistics.

        Returns:
            Dictionary with query metrics
        """
        if not self.queries:
            return {
                'total_queries': 0,
                'slow_queries': 0
            }

        durations = [q['duration'] for q in self.queries]
        slow_count = sum(1 for q in self.queries if q['slow'])

        return {
            'total_queries': len(self.queries),
            'slow_queries': slow_count,
            'slow_query_rate': slow_count / len(self.queries) * 100,
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'min_duration': min(durations)
        }


# Global instances
_performance_monitor: Optional[PerformanceMonitorMiddleware] = None
_db_profiler: Optional[DatabaseQueryProfiler] = None


def get_performance_monitor() -> Optional[PerformanceMonitorMiddleware]:
    """Get the global performance monitor instance.

    Returns:
        PerformanceMonitorMiddleware instance or None
    """
    return _performance_monitor


def set_performance_monitor(monitor: PerformanceMonitorMiddleware):
    """Set the global performance monitor instance.

    Args:
        monitor: PerformanceMonitorMiddleware instance
    """
    global _performance_monitor
    _performance_monitor = monitor


def get_db_profiler() -> DatabaseQueryProfiler:
    """Get or create the database query profiler.

    Returns:
        DatabaseQueryProfiler instance
    """
    global _db_profiler
    if _db_profiler is None:
        _db_profiler = DatabaseQueryProfiler()
    return _db_profiler
