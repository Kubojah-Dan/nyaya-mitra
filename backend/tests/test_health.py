from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint provides API discovery metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "NyayaMitra" in data["name"]
    assert "version" in data
    assert data["health"] == "/api/v1/health"


def test_health_check_endpoint():
    """Verify /api/v1/health endpoint reports operational status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert data["components"]["api"] == "healthy"
    assert "database" in data["components"]
    assert "cache" in data["components"]


def test_correlation_id_and_security_headers():
    """Verify security headers and correlation ID propagation."""
    custom_cid = "test-corr-id-12345"
    response = client.get("/api/v1/health", headers={"X-Correlation-ID": custom_cid})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_cid
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")
