import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.sources.base import CircuitBreaker, CircuitState
from app.sources.india_code import IndiaCodeAdapter
from app.sources.nalsa_directory import NALSADirectoryAdapter
from app.sources.registry import SourceRegistry, get_source_registry


@pytest.mark.asyncio
async def test_source_registry_registration():
    registry = SourceRegistry()
    adapters = registry.list_adapters()
    assert len(adapters) == 4
    source_codes = {a["source_code"] for a in adapters}
    assert "INDIA_CODE" in source_codes
    assert "NALSA_DIRECTORY" in source_codes
    assert "ECOURTS" in source_codes
    assert "TELE_LAW" in source_codes


@pytest.mark.asyncio
async def test_india_code_seed_and_hash():
    adapter = IndiaCodeAdapter()
    res = await adapter.fetch_latest()
    assert res["status"] == "SUCCESS"
    assert "content_hash" in res
    assert len(res["content_hash"]) == 64
    assert "BNS_2023" in res["data"]
    assert "BNSS_2023" in res["data"]
    assert "CPA_2019" in res["data"]
    assert "RTI_2005" in res["data"]

    # Test change detection
    assert adapter.detect_changes("different_hash") is True
    assert adapter.detect_changes(res["content_hash"]) is False


@pytest.mark.asyncio
async def test_nalsa_directory_and_provenance():
    adapter = NALSADirectoryAdapter()
    res = await adapter.fetch_latest()
    assert res["status"] == "SUCCESS"
    assert res["data"]["national_helpline"]["toll_free_number"] == "15100"

    # Test exit condition: Where did this fact come from?
    provenance = adapter.get_provenance("helpline_15100")
    assert provenance["source_code"] == "NALSA_DIRECTORY"
    assert provenance["tier"] == 1
    assert provenance["publisher"] == "National Legal Services Authority, Department of Justice"
    assert "https://nalsa.gov.in" in provenance["official_url"]


def test_circuit_breaker_transitions():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=0.1)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # Record first failure
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # Record second failure -> Tripped to OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

    # Wait for recovery timeout -> Transition to HALF_OPEN
    import time
    time.sleep(0.12)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Success in half open restores CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_sources_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Registry
        res = await client.get("/api/v1/sources/registry")
        assert res.status_code == 200
        data = res.json()
        assert data["total_sources"] >= 4

        # Health
        res = await client.get("/api/v1/sources/health")
        assert res.status_code == 200
        health_data = res.json()
        assert health_data["overall_status"] in ("HEALTHY", "DEGRADED")
        assert "INDIA_CODE" in health_data["sources"]

        # Provenance endpoint
        res = await client.get("/api/v1/sources/INDIA_CODE/provenance?item_id=bns_sec_318")
        assert res.status_code == 200
        prov = res.json()
        assert prov["source_code"] == "INDIA_CODE"
        assert prov["tier"] == 1
