"""
Tests for quality monitoring functionality
"""

import pytest
from datetime import datetime, timedelta
from api.monitoring.quality_monitor import (
    QualityMonitor,
    MetricsCollector,
    QualitySnapshot,
    QualityAlert
)


@pytest.fixture
def quality_monitor():
    """Create quality monitor instance"""
    return QualityMonitor(
        window_size=10,
        accuracy_threshold=0.95,
        latency_p95_threshold=200.0,
        cache_hit_rate_threshold=0.5
    )


@pytest.fixture
def metrics_collector():
    """Create metrics collector instance"""
    return MetricsCollector()


def test_quality_monitor_initialization(quality_monitor):
    """Test quality monitor initialization"""
    assert quality_monitor.window_size == 10
    assert quality_monitor.accuracy_threshold == 0.95
    assert quality_monitor.latency_p95_threshold == 200.0


def test_record_query(quality_monitor):
    """Test recording query metrics"""
    quality_monitor.record_query(
        accuracy=0.96,
        latency_ms=50.0,
        cache_hit=True,
        error=False
    )
    
    metrics = quality_monitor.get_current_metrics()
    
    assert metrics["accuracy"] == 0.96
    assert metrics["sample_size"] == 1


def test_get_current_metrics_empty(quality_monitor):
    """Test getting metrics with no data"""
    metrics = quality_monitor.get_current_metrics()
    
    assert metrics["accuracy"] == 0.0
    assert metrics["sample_size"] == 0


def test_get_current_metrics_with_data(quality_monitor):
    """Test getting metrics with data"""
    # Record multiple queries
    for i in range(5):
        quality_monitor.record_query(
            accuracy=0.9 + i * 0.01,
            latency_ms=50.0 + i * 10,
            cache_hit=i % 2 == 0
        )
    
    metrics = quality_monitor.get_current_metrics()
    
    assert metrics["sample_size"] == 5
    assert 0.9 <= metrics["accuracy"] <= 0.95
    assert metrics["cache_hit_rate"] == 0.6  # 3 hits out of 5


def test_set_baseline(quality_monitor):
    """Test setting baseline metrics"""
    # Record some queries
    for _ in range(5):
        quality_monitor.record_query(accuracy=0.96, latency_ms=50.0)
    
    quality_monitor.set_baseline()
    
    assert quality_monitor._baseline_accuracy is not None
    assert quality_monitor._baseline_latency is not None
    assert quality_monitor._baseline_accuracy > 0.95


def test_take_snapshot(quality_monitor):
    """Test taking metric snapshots"""
    # Record queries
    quality_monitor.record_query(accuracy=0.96, latency_ms=50.0)
    
    snapshot = quality_monitor.take_snapshot()
    
    assert isinstance(snapshot, QualitySnapshot)
    assert snapshot.accuracy == 0.96
    assert len(quality_monitor._snapshots) == 1


def test_accuracy_degradation_alert(quality_monitor):
    """Test accuracy degradation alert"""
    # Record queries with low accuracy
    for _ in range(10):
        quality_monitor.record_query(
            accuracy=0.90,  # Below 0.95 threshold
            latency_ms=50.0
        )
    
    alerts = quality_monitor.get_alerts()
    
    # Should have accuracy degradation alert
    assert len(alerts) > 0
    assert any(a.alert_type == "accuracy_degradation" for a in alerts)


def test_latency_degradation_alert(quality_monitor):
    """Test latency degradation alert"""
    # Record queries with high latency
    for _ in range(10):
        quality_monitor.record_query(
            accuracy=0.96,
            latency_ms=250.0  # Above 200ms threshold
        )
    
    alerts = quality_monitor.get_alerts()
    
    # Should have latency degradation alert
    assert len(alerts) > 0
    assert any(a.alert_type == "latency_degradation" for a in alerts)


def test_get_alerts_filtered(quality_monitor):
    """Test getting filtered alerts"""
    # Create alerts with different severities
    quality_monitor._create_alert(
        "test_critical", "critical", "Critical issue", 0.8, 0.95
    )
    quality_monitor._create_alert(
        "test_warning", "warning", "Warning issue", 0.9, 0.95
    )
    
    # Get only critical alerts
    critical_alerts = quality_monitor.get_alerts(severity="critical")
    
    assert len(critical_alerts) == 1
    assert critical_alerts[0].severity == "critical"


def test_get_trends(quality_monitor):
    """Test getting quality trends"""
    # Take multiple snapshots
    for i in range(5):
        quality_monitor.record_query(accuracy=0.95 + i * 0.01, latency_ms=50.0)
        quality_monitor.take_snapshot()
    
    trends = quality_monitor.get_trends(hours=24)
    
    assert "accuracy" in trends
    assert "latency_p95" in trends
    assert trends["snapshots_count"] == 5


def test_calculate_health_score(quality_monitor):
    """Test health score calculation"""
    # Perfect metrics
    metrics = {
        "accuracy": 0.98,
        "latency_p95": 50.0,
        "cache_hit_rate": 0.8,
        "error_rate": 0.0
    }
    
    score = quality_monitor._calculate_health_score(metrics)
    
    assert score >= 90  # Should be excellent


def test_health_status(quality_monitor):
    """Test health status classification"""
    assert quality_monitor._get_health_status(95) == "excellent"
    assert quality_monitor._get_health_status(80) == "good"
    assert quality_monitor._get_health_status(65) == "fair"
    assert quality_monitor._get_health_status(50) == "poor"
    assert quality_monitor._get_health_status(30) == "critical"


def test_generate_report(quality_monitor):
    """Test generating quality report"""
    # Record some queries
    for _ in range(5):
        quality_monitor.record_query(accuracy=0.96, latency_ms=50.0)
    
    quality_monitor.set_baseline()
    
    report = quality_monitor.generate_report()
    
    assert "health_score" in report
    assert "status" in report
    assert "current_metrics" in report
    assert "baseline" in report
    assert report["status"] in ["excellent", "good", "fair", "poor", "critical"]


def test_clear_alerts(quality_monitor):
    """Test clearing alerts"""
    quality_monitor._create_alert("test", "info", "Test alert", 0.9, 0.95)
    
    assert len(quality_monitor._alerts) == 1
    
    quality_monitor.clear_alerts()
    
    assert len(quality_monitor._alerts) == 0


def test_reset_monitor(quality_monitor):
    """Test resetting monitor"""
    # Add some data
    quality_monitor.record_query(accuracy=0.96, latency_ms=50.0)
    quality_monitor.take_snapshot()
    quality_monitor.set_baseline()
    
    quality_monitor.reset()
    
    assert len(quality_monitor._accuracy_window) == 0
    assert len(quality_monitor._snapshots) == 0
    assert quality_monitor._baseline_accuracy is None


def test_metrics_collector_record_search(metrics_collector):
    """Test recording search metrics"""
    metrics_collector.record_search(
        latency_seconds=0.05,
        accuracy=0.96,
        cache_hit=True,
        error=False
    )
    
    metrics = metrics_collector.get_metrics_dict()
    
    assert metrics["queries_total"] == 1
    assert metrics["average_accuracy"] == 0.96
    assert metrics["cache_hit_rate"] == 1.0


def test_metrics_collector_latency_buckets(metrics_collector):
    """Test latency bucket distribution"""
    # Record queries with different latencies
    metrics_collector.record_search(0.005, 0.96, False)  # 5ms
    metrics_collector.record_search(0.030, 0.96, False)  # 30ms
    metrics_collector.record_search(0.150, 0.96, False)  # 150ms
    
    metrics = metrics_collector.get_metrics_dict()
    
    assert "0-10ms" in metrics["latency_distribution"]
    assert "10-50ms" in metrics["latency_distribution"]
    assert "100-200ms" in metrics["latency_distribution"]


def test_metrics_collector_prometheus_format(metrics_collector):
    """Test Prometheus metrics export"""
    metrics_collector.record_search(0.05, 0.96, True)
    
    prometheus_text = metrics_collector.get_prometheus_metrics()
    
    assert "retrieval_accuracy" in prometheus_text
    assert "retrieval_cache_hit_rate" in prometheus_text
    assert "retrieval_queries_total" in prometheus_text
    assert "# HELP" in prometheus_text
    assert "# TYPE" in prometheus_text


def test_quality_snapshot_dataclass():
    """Test QualitySnapshot dataclass"""
    snapshot = QualitySnapshot(
        timestamp=datetime.now(),
        accuracy=0.96,
        latency_p50=30.0,
        latency_p95=80.0,
        latency_p99=120.0,
        cache_hit_rate=0.7,
        error_rate=0.01,
        total_queries=100
    )
    
    assert snapshot.accuracy == 0.96
    assert snapshot.total_queries == 100


def test_quality_alert_dataclass():
    """Test QualityAlert dataclass"""
    alert = QualityAlert(
        alert_type="accuracy_degradation",
        severity="critical",
        message="Accuracy dropped",
        current_value=0.90,
        threshold=0.95,
        timestamp=datetime.now()
    )
    
    assert alert.alert_type == "accuracy_degradation"
    assert alert.severity == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
