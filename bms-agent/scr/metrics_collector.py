"""
Metrics Collection for BMS Agent API
Provides in-memory metrics tracking with rolling windows
"""
import time
import threading
from collections import deque
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    In-memory metrics collector with rolling window storage.

    Tracks:
    - Request count
    - Latency percentiles (p50, p95, p99)
    - Error rates
    - Queue depths (for async processing)

    Uses a rolling window of last N requests to prevent memory growth.
    """

    def __init__(self, window_size: int = 1000):
        """
        Initialize metrics collector.

        Args:
            window_size: Number of requests to keep in memory (default 1000)
        """
        self.window_size = window_size
        self._lock = threading.Lock()

        # Rolling window storage
        self._requests: deque = deque(maxlen=window_size)

        # Counters
        self._total_requests = 0
        self._total_errors = 0

        # Queue depth tracking (for async processing)
        self._current_queue_depth = 0
        self._max_queue_depth = 0

        logger.info(f"MetricsCollector initialized with window_size={window_size}")

    def record_request(
        self,
        latency_ms: float,
        is_error: bool = False,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> None:
        """
        Record a completed request with its metrics.

        Args:
            latency_ms: Request latency in milliseconds
            is_error: Whether the request resulted in an error
            endpoint: Optional endpoint path for debugging
            status_code: Optional HTTP status code
        """
        with self._lock:
            request_data = {
                "timestamp": time.time(),
                "latency_ms": latency_ms,
                "is_error": is_error,
                "endpoint": endpoint,
                "status_code": status_code
            }

            self._requests.append(request_data)
            self._total_requests += 1

            if is_error:
                self._total_errors += 1

    def record_queue_depth(self, depth: int) -> None:
        """
        Update current queue depth for async processing.

        Args:
            depth: Current number of items in processing queue
        """
        with self._lock:
            self._current_queue_depth = depth
            if depth > self._max_queue_depth:
                self._max_queue_depth = depth

    def get_metrics(self) -> Dict:
        """
        Compute and return current metrics.

        Returns:
            Dictionary with:
            - request_count: Total requests in current window
            - latency_p50_ms: 50th percentile latency
            - latency_p95_ms: 95th percentile latency
            - latency_p99_ms: 99th percentile latency
            - error_rate: Proportion of errors (0.0-1.0)
            - queue_depth: Current async processing queue depth
            - max_queue_depth: Maximum queue depth seen
            - total_requests: Total requests since startup
            - total_errors: Total errors since startup
        """
        with self._lock:
            if not self._requests:
                return {
                    "request_count": 0,
                    "latency_p50_ms": 0.0,
                    "latency_p95_ms": 0.0,
                    "latency_p99_ms": 0.0,
                    "error_rate": 0.0,
                    "queue_depth": self._current_queue_depth,
                    "max_queue_depth": self._max_queue_depth,
                    "total_requests": self._total_requests,
                    "total_errors": self._total_errors
                }

            # Extract latencies from rolling window
            latencies = [req["latency_ms"] for req in self._requests]
            latencies_sorted = sorted(latencies)

            # Count errors in current window
            window_errors = sum(1 for req in self._requests if req["is_error"])
            window_requests = len(self._requests)

            # Compute percentiles
            p50 = self._percentile(latencies_sorted, 50)
            p95 = self._percentile(latencies_sorted, 95)
            p99 = self._percentile(latencies_sorted, 99)

            return {
                "request_count": window_requests,
                "latency_p50_ms": round(p50, 2),
                "latency_p95_ms": round(p95, 2),
                "latency_p99_ms": round(p99, 2),
                "error_rate": round(window_errors / window_requests, 4) if window_requests > 0 else 0.0,
                "queue_depth": self._current_queue_depth,
                "max_queue_depth": self._max_queue_depth,
                "total_requests": self._total_requests,
                "total_errors": self._total_errors
            }

    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """
        Calculate percentile from sorted values.

        Args:
            sorted_values: List of values in ascending order
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not sorted_values:
            return 0.0

        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = f + 1

        if c >= len(sorted_values):
            return sorted_values[-1]

        d0 = sorted_values[f] * (c - k)
        d1 = sorted_values[c] * (k - f)

        return d0 + d1

    def reset(self) -> None:
        """
        Reset all metrics (useful for testing).
        """
        with self._lock:
            self._requests.clear()
            self._total_requests = 0
            self._total_errors = 0
            self._current_queue_depth = 0
            self._max_queue_depth = 0
            logger.info("MetricsCollector reset")

    def get_endpoint_breakdown(self) -> Dict[str, int]:
        """
        Get request count breakdown by endpoint.

        Returns:
            Dictionary mapping endpoint paths to request counts
        """
        with self._lock:
            breakdown = {}
            for req in self._requests:
                endpoint = req.get("endpoint", "unknown")
                breakdown[endpoint] = breakdown.get(endpoint, 0) + 1
            return breakdown


# Singleton instance for easy import
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(window_size: int = 1000) -> MetricsCollector:
    """
    Get or create the global metrics collector instance.

    Args:
        window_size: Rolling window size (only used on first call)

    Returns:
        MetricsCollector singleton
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(window_size=window_size)
    return _metrics_collector


# Context manager for automatic latency tracking
class RequestTimer:
    """
    Context manager for automatic request timing and metrics recording.

    Usage:
        with RequestTimer(endpoint="/api/v1/search"):
            # ... handle request ...
            pass
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        collector: Optional[MetricsCollector] = None
    ):
        """
        Initialize request timer.

        Args:
            endpoint: Optional endpoint path
            collector: Optional custom collector (uses global if None)
        """
        self.endpoint = endpoint
        self.collector = collector or get_metrics_collector()
        self.start_time = None
        self.is_error = False
        self.status_code = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metrics."""
        if self.start_time is not None:
            elapsed_ms = (time.time() - self.start_time) * 1000

            # Mark as error if exception occurred
            if exc_type is not None:
                self.is_error = True
                self.status_code = 500

            self.collector.record_request(
                latency_ms=elapsed_ms,
                is_error=self.is_error,
                endpoint=self.endpoint,
                status_code=self.status_code
            )

        # Don't suppress exceptions
        return False

    def set_status(self, status_code: int):
        """
        Set HTTP status code for this request.

        Args:
            status_code: HTTP status code
        """
        self.status_code = status_code
        if status_code >= 400:
            self.is_error = True
