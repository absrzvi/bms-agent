"""
Retrieval Quality Monitoring
Continuous monitoring of retrieval quality with degradation detection
"""

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class QualitySnapshot:
    """Snapshot of quality metrics at a point in time"""
    timestamp: datetime
    accuracy: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    cache_hit_rate: float
    error_rate: float
    total_queries: int


@dataclass
class QualityAlert:
    """Quality degradation alert"""
    alert_type: str
    severity: str  # critical, warning, info
    message: str
    current_value: float
    threshold: float
    timestamp: datetime


class QualityMonitor:
    """
    Monitor retrieval quality in real-time
    Detect degradation and trigger alerts
    """
    
    def __init__(
        self,
        window_size: int = 100,
        accuracy_threshold: float = 0.95,
        latency_p95_threshold: float = 200.0,
        cache_hit_rate_threshold: float = 0.5,
        degradation_threshold: float = 0.05
    ):
        """
        Initialize quality monitor
        
        Args:
            window_size: Rolling window size for metrics
            accuracy_threshold: Minimum acceptable accuracy
            latency_p95_threshold: Maximum acceptable p95 latency (ms)
            cache_hit_rate_threshold: Minimum acceptable cache hit rate
            degradation_threshold: Threshold for degradation detection (5% drop)
        """
        self.window_size = window_size
        self.accuracy_threshold = accuracy_threshold
        self.latency_p95_threshold = latency_p95_threshold
        self.cache_hit_rate_threshold = cache_hit_rate_threshold
        self.degradation_threshold = degradation_threshold
        
        # Rolling windows for metrics
        self._accuracy_window = deque(maxlen=window_size)
        self._latency_window = deque(maxlen=window_size)
        self._cache_hits = deque(maxlen=window_size)
        self._errors = deque(maxlen=window_size)
        
        # Historical snapshots
        self._snapshots: List[QualitySnapshot] = []
        self._alerts: List[QualityAlert] = []
        
        # Baseline metrics
        self._baseline_accuracy: Optional[float] = None
        self._baseline_latency: Optional[float] = None
        
        logger.info("✅ Quality monitor initialized")
    
    def record_query(
        self,
        accuracy: float,
        latency_ms: float,
        cache_hit: bool = False,
        error: bool = False
    ):
        """
        Record a query execution
        
        Args:
            accuracy: Query accuracy (0.0-1.0)
            latency_ms: Query latency in milliseconds
            cache_hit: Whether query was served from cache
            error: Whether query resulted in error
        """
        self._accuracy_window.append(accuracy)
        self._latency_window.append(latency_ms)
        self._cache_hits.append(1 if cache_hit else 0)
        self._errors.append(1 if error else 0)
        
        # Check for degradation
        self._check_degradation()
    
    def _check_degradation(self):
        """Check for quality degradation and trigger alerts"""
        if len(self._accuracy_window) < self.window_size // 2:
            return  # Not enough data
        
        current_metrics = self.get_current_metrics()
        
        # Check accuracy degradation
        if current_metrics["accuracy"] < self.accuracy_threshold:
            self._create_alert(
                alert_type="accuracy_degradation",
                severity="critical",
                message=f"Accuracy dropped below threshold: {current_metrics['accuracy']:.2%} < {self.accuracy_threshold:.2%}",
                current_value=current_metrics["accuracy"],
                threshold=self.accuracy_threshold
            )
        
        # Check latency degradation
        if current_metrics["latency_p95"] > self.latency_p95_threshold:
            self._create_alert(
                alert_type="latency_degradation",
                severity="warning",
                message=f"P95 latency exceeded threshold: {current_metrics['latency_p95']:.1f}ms > {self.latency_p95_threshold:.1f}ms",
                current_value=current_metrics["latency_p95"],
                threshold=self.latency_p95_threshold
            )
        
        # Check cache hit rate
        if current_metrics["cache_hit_rate"] < self.cache_hit_rate_threshold:
            self._create_alert(
                alert_type="cache_performance",
                severity="info",
                message=f"Cache hit rate below threshold: {current_metrics['cache_hit_rate']:.2%} < {self.cache_hit_rate_threshold:.2%}",
                current_value=current_metrics["cache_hit_rate"],
                threshold=self.cache_hit_rate_threshold
            )
        
        # Check for sudden degradation vs baseline
        if self._baseline_accuracy is not None:
            accuracy_drop = self._baseline_accuracy - current_metrics["accuracy"]
            if accuracy_drop > self.degradation_threshold:
                self._create_alert(
                    alert_type="sudden_degradation",
                    severity="critical",
                    message=f"Accuracy dropped {accuracy_drop:.2%} from baseline",
                    current_value=current_metrics["accuracy"],
                    threshold=self._baseline_accuracy
                )
    
    def _create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        current_value: float,
        threshold: float
    ):
        """Create quality alert"""
        alert = QualityAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold=threshold,
            timestamp=datetime.now()
        )
        
        self._alerts.append(alert)
        
        # Log alert
        log_func = logger.critical if severity == "critical" else logger.warning
        log_func(f"🚨 Quality Alert [{severity.upper()}]: {message}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current quality metrics"""
        if not self._accuracy_window:
            return {
                "accuracy": 0.0,
                "latency_p50": 0.0,
                "latency_p95": 0.0,
                "latency_p99": 0.0,
                "cache_hit_rate": 0.0,
                "error_rate": 0.0,
                "sample_size": 0
            }
        
        # Calculate metrics
        accuracy = statistics.mean(self._accuracy_window)
        
        latencies = sorted(self._latency_window)
        latency_p50 = self._percentile(latencies, 0.50)
        latency_p95 = self._percentile(latencies, 0.95)
        latency_p99 = self._percentile(latencies, 0.99)
        
        cache_hit_rate = sum(self._cache_hits) / len(self._cache_hits) if self._cache_hits else 0.0
        error_rate = sum(self._errors) / len(self._errors) if self._errors else 0.0
        
        return {
            "accuracy": accuracy,
            "latency_p50": latency_p50,
            "latency_p95": latency_p95,
            "latency_p99": latency_p99,
            "cache_hit_rate": cache_hit_rate,
            "error_rate": error_rate,
            "sample_size": len(self._accuracy_window)
        }
    
    @staticmethod
    def _percentile(sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0
        
        index = int(len(sorted_values) * percentile)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def set_baseline(self):
        """Set current metrics as baseline"""
        current = self.get_current_metrics()
        self._baseline_accuracy = current["accuracy"]
        self._baseline_latency = current["latency_p95"]
        
        logger.info(f"✅ Baseline set: accuracy={self._baseline_accuracy:.2%}, latency_p95={self._baseline_latency:.1f}ms")
    
    def take_snapshot(self):
        """Take a snapshot of current metrics"""
        current = self.get_current_metrics()
        
        snapshot = QualitySnapshot(
            timestamp=datetime.now(),
            accuracy=current["accuracy"],
            latency_p50=current["latency_p50"],
            latency_p95=current["latency_p95"],
            latency_p99=current["latency_p99"],
            cache_hit_rate=current["cache_hit_rate"],
            error_rate=current["error_rate"],
            total_queries=current["sample_size"]
        )
        
        self._snapshots.append(snapshot)
        
        # Keep only last 1000 snapshots
        if len(self._snapshots) > 1000:
            self._snapshots = self._snapshots[-1000:]
        
        return snapshot
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[QualityAlert]:
        """
        Get quality alerts
        
        Args:
            severity: Filter by severity (critical, warning, info)
            since: Get alerts since this timestamp
            limit: Maximum number of alerts
            
        Returns:
            List of alerts
        """
        alerts = self._alerts
        
        # Filter by severity
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Filter by time
        if since:
            alerts = [a for a in alerts if a.timestamp >= since]
        
        # Sort by timestamp (newest first)
        alerts = sorted(alerts, key=lambda x: x.timestamp, reverse=True)
        
        return alerts[:limit]
    
    def get_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get quality trends over time
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Trend analysis
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_snapshots = [s for s in self._snapshots if s.timestamp >= cutoff]
        
        if not recent_snapshots:
            return {"error": "No snapshots in time range"}
        
        # Calculate trends
        accuracies = [s.accuracy for s in recent_snapshots]
        latencies_p95 = [s.latency_p95 for s in recent_snapshots]
        cache_hit_rates = [s.cache_hit_rate for s in recent_snapshots]
        
        return {
            "time_range_hours": hours,
            "snapshots_count": len(recent_snapshots),
            "accuracy": {
                "mean": statistics.mean(accuracies),
                "min": min(accuracies),
                "max": max(accuracies),
                "trend": "improving" if accuracies[-1] > accuracies[0] else "degrading"
            },
            "latency_p95": {
                "mean": statistics.mean(latencies_p95),
                "min": min(latencies_p95),
                "max": max(latencies_p95),
                "trend": "improving" if latencies_p95[-1] < latencies_p95[0] else "degrading"
            },
            "cache_hit_rate": {
                "mean": statistics.mean(cache_hit_rates),
                "min": min(cache_hit_rates),
                "max": max(cache_hit_rates),
                "trend": "improving" if cache_hit_rates[-1] > cache_hit_rates[0] else "degrading"
            }
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        current = self.get_current_metrics()
        recent_alerts = self.get_alerts(limit=10)
        
        # Calculate health score (0-100)
        health_score = self._calculate_health_score(current)
        
        return {
            "health_score": health_score,
            "status": self._get_health_status(health_score),
            "current_metrics": current,
            "baseline": {
                "accuracy": self._baseline_accuracy,
                "latency_p95": self._baseline_latency
            },
            "recent_alerts": [
                {
                    "type": a.alert_type,
                    "severity": a.severity,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in recent_alerts
            ],
            "total_snapshots": len(self._snapshots),
            "monitoring_window": self.window_size
        }
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall health score (0-100)"""
        score = 100.0
        
        # Accuracy component (40% weight)
        if metrics["accuracy"] < self.accuracy_threshold:
            accuracy_penalty = (self.accuracy_threshold - metrics["accuracy"]) * 40
            score -= accuracy_penalty
        
        # Latency component (30% weight)
        if metrics["latency_p95"] > self.latency_p95_threshold:
            latency_ratio = metrics["latency_p95"] / self.latency_p95_threshold
            latency_penalty = min((latency_ratio - 1.0) * 30, 30)
            score -= latency_penalty
        
        # Cache hit rate component (20% weight)
        if metrics["cache_hit_rate"] < self.cache_hit_rate_threshold:
            cache_penalty = (self.cache_hit_rate_threshold - metrics["cache_hit_rate"]) * 20
            score -= cache_penalty
        
        # Error rate component (10% weight)
        error_penalty = metrics["error_rate"] * 10
        score -= error_penalty
        
        return max(0.0, min(100.0, score))
    
    @staticmethod
    def _get_health_status(health_score: float) -> str:
        """Get health status from score"""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 60:
            return "fair"
        elif health_score >= 40:
            return "poor"
        else:
            return "critical"
    
    def clear_alerts(self):
        """Clear all alerts"""
        count = len(self._alerts)
        self._alerts.clear()
        logger.info(f"Cleared {count} alerts")
    
    def reset(self):
        """Reset all monitoring data"""
        self._accuracy_window.clear()
        self._latency_window.clear()
        self._cache_hits.clear()
        self._errors.clear()
        self._snapshots.clear()
        self._alerts.clear()
        self._baseline_accuracy = None
        self._baseline_latency = None
        logger.info("Quality monitor reset")


class MetricsCollector:
    """
    Collect metrics for Prometheus export
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self._metrics = {
            "retrieval_accuracy_total": 0.0,
            "retrieval_latency_seconds": {},
            "retrieval_cache_hits_total": 0,
            "retrieval_cache_misses_total": 0,
            "retrieval_errors_total": 0,
            "retrieval_queries_total": 0
        }
    
    def record_search(
        self,
        latency_seconds: float,
        accuracy: float,
        cache_hit: bool,
        error: bool = False
    ):
        """Record search metrics"""
        self._metrics["retrieval_queries_total"] += 1
        self._metrics["retrieval_accuracy_total"] += accuracy
        
        if cache_hit:
            self._metrics["retrieval_cache_hits_total"] += 1
        else:
            self._metrics["retrieval_cache_misses_total"] += 1
        
        if error:
            self._metrics["retrieval_errors_total"] += 1
        
        # Store latency for histogram
        bucket = self._get_latency_bucket(latency_seconds)
        self._metrics["retrieval_latency_seconds"][bucket] = \
            self._metrics["retrieval_latency_seconds"].get(bucket, 0) + 1
    
    @staticmethod
    def _get_latency_bucket(latency_seconds: float) -> str:
        """Get latency bucket for histogram"""
        latency_ms = latency_seconds * 1000
        
        if latency_ms < 10:
            return "0-10ms"
        elif latency_ms < 50:
            return "10-50ms"
        elif latency_ms < 100:
            return "50-100ms"
        elif latency_ms < 200:
            return "100-200ms"
        elif latency_ms < 500:
            return "200-500ms"
        else:
            return "500ms+"
    
    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Accuracy
        avg_accuracy = (
            self._metrics["retrieval_accuracy_total"] / 
            self._metrics["retrieval_queries_total"]
            if self._metrics["retrieval_queries_total"] > 0 else 0.0
        )
        lines.append(f"# HELP retrieval_accuracy Average retrieval accuracy")
        lines.append(f"# TYPE retrieval_accuracy gauge")
        lines.append(f"retrieval_accuracy {avg_accuracy:.4f}")
        
        # Cache hit rate
        total_cache_ops = (
            self._metrics["retrieval_cache_hits_total"] + 
            self._metrics["retrieval_cache_misses_total"]
        )
        cache_hit_rate = (
            self._metrics["retrieval_cache_hits_total"] / total_cache_ops
            if total_cache_ops > 0 else 0.0
        )
        lines.append(f"# HELP retrieval_cache_hit_rate Cache hit rate")
        lines.append(f"# TYPE retrieval_cache_hit_rate gauge")
        lines.append(f"retrieval_cache_hit_rate {cache_hit_rate:.4f}")
        
        # Total queries
        lines.append(f"# HELP retrieval_queries_total Total number of queries")
        lines.append(f"# TYPE retrieval_queries_total counter")
        lines.append(f"retrieval_queries_total {self._metrics['retrieval_queries_total']}")
        
        # Errors
        lines.append(f"# HELP retrieval_errors_total Total number of errors")
        lines.append(f"# TYPE retrieval_errors_total counter")
        lines.append(f"retrieval_errors_total {self._metrics['retrieval_errors_total']}")
        
        return "\n".join(lines)
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """Get metrics as dictionary"""
        total_cache_ops = (
            self._metrics["retrieval_cache_hits_total"] + 
            self._metrics["retrieval_cache_misses_total"]
        )
        
        return {
            "queries_total": self._metrics["retrieval_queries_total"],
            "average_accuracy": (
                self._metrics["retrieval_accuracy_total"] / 
                self._metrics["retrieval_queries_total"]
                if self._metrics["retrieval_queries_total"] > 0 else 0.0
            ),
            "cache_hit_rate": (
                self._metrics["retrieval_cache_hits_total"] / total_cache_ops
                if total_cache_ops > 0 else 0.0
            ),
            "errors_total": self._metrics["retrieval_errors_total"],
            "latency_distribution": self._metrics["retrieval_latency_seconds"]
        }


# Global quality monitor instance
_quality_monitor = QualityMonitor()
_metrics_collector = MetricsCollector()


def get_quality_monitor() -> QualityMonitor:
    """Get global quality monitor instance"""
    return _quality_monitor


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    return _metrics_collector
