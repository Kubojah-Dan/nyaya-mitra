"""
NyayaMitra Telemetry & Metrics Collection Engine
Aggregates in-memory request volume, status code distributions, latency percentiles,
circuit breaker events, and operational uptime.
"""

from collections import defaultdict
from datetime import datetime, timezone
import threading
import time
from typing import Any, Optional


class MetricsCollector:
    """Thread-safe telemetry collector for backend API and micro-components."""

    def __init__(self):
        self._lock = threading.Lock()
        self.start_time = time.time()
        
        # Counters
        self.total_requests = 0
        self.status_2xx = 0
        self.status_3xx = 0
        self.status_4xx = 0
        self.status_5xx = 0
        
        # Path breakdown
        self.requests_by_path: dict[str, int] = defaultdict(int)
        
        # Latency samples (rolling window)
        self.latencies_ms: list[float] = []
        self._max_latency_samples = 5000

    def record_request(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        """Records a single inbound API request execution."""
        with self._lock:
            self.total_requests += 1
            
            if 200 <= status_code < 300:
                self.status_2xx += 1
            elif 300 <= status_code < 400:
                self.status_3xx += 1
            elif 400 <= status_code < 500:
                self.status_4xx += 1
            elif status_code >= 500:
                self.status_5xx += 1

            # Strip query params and ID variables for path grouping
            norm_path = path.split("?")[0]
            self.requests_by_path[f"{method} {norm_path}"] += 1

            # Store latency sample
            self.latencies_ms.append(round(duration_ms, 2))
            if len(self.latencies_ms) > self._max_latency_samples:
                # Keep latest samples
                self.latencies_ms = self.latencies_ms[-self._max_latency_samples:]

    def get_summary(self) -> dict[str, Any]:
        """Calculates current telemetry summary including latency percentiles and error rates."""
        with self._lock:
            uptime_sec = round(time.time() - self.start_time, 2)
            error_count = self.status_4xx + self.status_5xx
            error_rate = round(error_count / self.total_requests, 4) if self.total_requests > 0 else 0.0
            rpm = round((self.total_requests / (uptime_sec / 60.0)), 2) if uptime_sec >= 1.0 else 0.0

            if self.latencies_ms:
                sorted_lat = sorted(self.latencies_ms)
                p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
                p90 = sorted_lat[int(len(sorted_lat) * 0.90)]
                p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
                p99 = sorted_lat[int(len(sorted_lat) * 0.99)]
                avg_lat = round(sum(sorted_lat) / len(sorted_lat), 2)
            else:
                p50 = p90 = p95 = p99 = avg_lat = 0.0

            return {
                "uptime_seconds": uptime_sec,
                "uptime_formatted": f"{int(uptime_sec // 3600)}h {int((uptime_sec % 3600) // 60)}m {int(uptime_sec % 60)}s",
                "total_requests": self.total_requests,
                "requests_per_minute": rpm,
                "status_codes": {
                    "2xx": self.status_2xx,
                    "3xx": self.status_3xx,
                    "4xx": self.status_4xx,
                    "5xx": self.status_5xx,
                },
                "error_rate": error_rate,
                "error_percentage": f"{error_rate * 100:.2f}%",
                "latency_ms": {
                    "avg": avg_lat,
                    "p50": p50,
                    "p90": p90,
                    "p95": p95,
                    "p99": p99,
                },
                "top_endpoints": dict(sorted(self.requests_by_path.items(), key=lambda x: x[1], reverse=True)[:10]),
            }

    def reset(self) -> None:
        """Resets all metrics (primarily for test isolation)."""
        with self._lock:
            self.start_time = time.time()
            self.total_requests = 0
            self.status_2xx = 0
            self.status_3xx = 0
            self.status_4xx = 0
            self.status_5xx = 0
            self.requests_by_path.clear()
            self.latencies_ms.clear()


# Global singleton metrics collector
global_metrics = MetricsCollector()
