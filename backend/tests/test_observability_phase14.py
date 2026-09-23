"""
Automated Pytest Suite for Phase 14:
Production Readiness, Observability, Telemetry & Health Probes
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.observability import mask_sensitive_pii
from app.services.metrics_collector import MetricsCollector, global_metrics


@pytest.fixture
def client():
    return TestClient(app)


def test_pii_masking_in_trace_logs():
    """Verify Aadhaar, PAN, phone numbers, and emails are properly masked."""
    raw = "User 9876543210 with Aadhaar 1234 5678 9012 and PAN ABCDE1234F emailed test@example.com"
    masked = mask_sensitive_pii(raw)
    
    assert "9876543210" not in masked
    assert "[PHONE_REDACTED]" in masked
    assert "1234 5678 9012" not in masked
    assert "[AADHAAR_REDACTED]" in masked
    assert "ABCDE1234F" not in masked
    assert "[PAN_REDACTED]" in masked
    assert "test@example.com" not in masked
    assert "[EMAIL_REDACTED]" in masked


def test_correlation_id_and_server_timing_headers(client: TestClient):
    """Verify X-Correlation-ID and Server-Timing headers are injected into HTTP responses."""
    # 1. Custom correlation ID provided by client
    custom_cid = "corr-test-custom-12345"
    res1 = client.get("/api/v1/health", headers={"X-Correlation-ID": custom_cid})
    assert res1.status_code == 200
    assert res1.headers.get("X-Correlation-ID") == custom_cid
    assert "X-Request-ID" in res1.headers
    assert "Server-Timing" in res1.headers
    assert "app;dur=" in res1.headers["Server-Timing"]

    # 2. Auto-generated correlation ID
    res2 = client.get("/api/v1/health")
    assert res2.status_code == 200
    assert res2.headers.get("X-Correlation-ID").startswith("corr-")


def test_liveness_probe_endpoint(client: TestClient):
    """Verify Kubernetes liveness probe returns 200 OK."""
    res = client.get("/api/v1/health/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_probe_endpoint(client: TestClient):
    """Verify Kubernetes readiness probe verifies database and statutory baseline."""
    res = client.get("/api/v1/health/readiness")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["statutes_indexed"] >= 5
    assert data["cache_ready"] is True


def test_sources_health_endpoint(client: TestClient):
    """Verify all 4 source adapters report health and circuit breaker status."""
    res = client.get("/api/v1/health/sources")
    assert res.status_code == 200
    data = res.json()
    assert data["overall_sources_status"] in ("HEALTHY", "DEGRADED")
    sources = data["sources"]
    assert "INDIA_CODE" in sources
    assert "NALSA" in sources
    assert "ECOURTS" in sources
    assert "TELE_LAW" in sources
    assert sources["INDIA_CODE"]["tier"] == 1
    assert sources["INDIA_CODE"]["circuit_breaker_state"] in ("CLOSED", "HALF_OPEN", "OPEN")


def test_models_health_endpoint(client: TestClient):
    """Verify model router status and telemetry reporting."""
    res = client.get("/api/v1/health/models")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "FAST" in data["tiers"]
    assert "BALANCED" in data["tiers"]
    assert "REASONING" in data["tiers"]
    assert "telemetry" in data


def test_metrics_collector_and_endpoint(client: TestClient):
    """Verify MetricsCollector aggregates request status codes and exports metrics."""
    collector = MetricsCollector()
    collector.record_request("GET", "/api/v1/health", 200, 5.2)
    collector.record_request("POST", "/api/v1/intake", 200, 12.4)
    collector.record_request("GET", "/api/v1/unknown", 404, 1.1)

    summary = collector.get_summary()
    assert summary["total_requests"] == 3
    assert summary["status_codes"]["2xx"] == 2
    assert summary["status_codes"]["4xx"] == 1
    assert summary["error_rate"] == round(1 / 3, 4)
    assert summary["latency_ms"]["avg"] > 0.0

    # Test HTTP endpoint
    res = client.get("/api/v1/health/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "telemetry" in data
    assert "cache" in data
