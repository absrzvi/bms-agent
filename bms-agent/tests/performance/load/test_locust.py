"""Locust load test validating ≤100 ms p95 latency under 1,000 users."""

from __future__ import annotations

import os
from typing import Dict, Tuple

from locust import HttpUser, LoadTestShape, between, events, task


TARGET_P95_MS = float(os.getenv("BMS_TARGET_P95_MS", "100"))
TARGET_AVG_MS = float(os.getenv("BMS_TARGET_AVG_MS", "50"))
DEFAULT_QUERY = os.getenv("BMS_PERFORMANCE_QUERY", "emergency brake vlan")
API_KEY = os.getenv("BMS_API_KEY")


def _headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    return headers


class SearchUser(HttpUser):
    """Simulates concurrent clients issuing semantic and hybrid queries."""

    wait_time = between(0.05, 0.2)  # 50–200 ms between requests

    def __init__(self, environment):  # pragma: no cover - exercised via Locust
        super().__init__(environment)
        self.headers = _headers()

    @task(3)
    def semantic_search(self):  # pragma: no cover - exercised via Locust
        payload = {"query": DEFAULT_QUERY, "limit": 5}
        self.client.post(
            "/api/v1/search/semantic",
            json=payload,
            headers=self.headers,
            name="semantic",
        )

    @task(1)
    def hybrid_search(self):  # pragma: no cover - exercised via Locust
        payload = {
            "query": DEFAULT_QUERY,
            "limit": 5,
            "candidate_multiplier": 3,
            "vector_weight": 0.6,
            "keyword_weight": 0.4,
        }
        self.client.post(
            "/api/v1/search/hybrid",
            json=payload,
            headers=self.headers,
            name="hybrid",
        )


class ThousandUserSpike(LoadTestShape):  # pragma: no cover - exercised via Locust
    """Ramps to 1,000 users and sustains load for the validation window."""

    stages: Tuple[Tuple[int, int, int], ...] = (
        (60, 250, 25),   # ramp to 250 users over 60 s
        (120, 750, 50),  # continue ramp to 750 users over next 60 s
        (180, 1000, 50),  # reach 1,000 users by 180 s
        (420, 1000, 0),  # sustain 1,000 users until 7 minutes overall
    )

    def tick(self):
        run_time = self.get_run_time()
        for stage_time, users, spawn_rate in self.stages:
            if run_time < stage_time:
                return (users, spawn_rate)
        return (None, None)


def _check_thresholds(environment) -> None:
    failures = []
    for name in ("semantic", "hybrid"):
        stats = environment.stats.get("POST", name)
        if not stats:
            failures.append(f"No metrics captured for {name} endpoint")
            continue

        p95 = stats.get_response_time_percentile(0.95)
        avg = stats.avg_response_time
        if p95 > TARGET_P95_MS:
            failures.append(f"{name} p95 {p95:.2f} ms exceeded target {TARGET_P95_MS:.2f} ms")
        if avg > TARGET_AVG_MS:
            failures.append(f"{name} average {avg:.2f} ms exceeded target {TARGET_AVG_MS:.2f} ms")

    if failures:
        for msg in failures:
            environment.process_exit_code = 1
            environment.logger.error(msg)
    else:
        environment.logger.info(
            "Latency targets met (p95 ≤ %.2f ms, avg ≤ %.2f ms) for semantic and hybrid endpoints",
            TARGET_P95_MS,
            TARGET_AVG_MS,
        )


@events.quitting.add_listener  # pragma: no cover - exercised via Locust
def evaluate_results(environment, **_):
    """Validate latency thresholds once the test run finishes."""

    _check_thresholds(environment)
