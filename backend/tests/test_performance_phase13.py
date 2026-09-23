"""
Automated Pytest Suite for Phase 13:
Performance, Cost, Reliability Engineering & Cache Verification
"""

import time
import pytest

from app.services.cache_service import ResponseCacheService
from app.services.model_router import ModelRouterService, ModelTierConfig


def test_cache_set_and_get():
    """Verify basic cache insertion, retrieval, and hit tracking."""
    cache = ResponseCacheService(max_size=10, default_ttl=60)
    
    key = cache.set("TEST", "query 1", {"result": "val1"})
    assert key.startswith("TEST:")
    
    # Cache hit
    val = cache.get("TEST", "query 1")
    assert val == {"result": "val1"}
    
    # Cache miss
    miss = cache.get("TEST", "non-existent")
    assert miss is None
    
    stats = cache.get_stats()
    assert stats["total_lookups"] == 2
    assert stats["total_hits"] == 1
    assert stats["total_misses"] == 1
    assert stats["hit_ratio"] == 0.5


def test_cache_ttl_expiration():
    """Verify expired cache items are automatically evicted."""
    cache = ResponseCacheService(max_size=10, default_ttl=1)  # 1 second TTL
    
    cache.set("TTL_TEST", "item1", "value1", ttl_seconds=1)
    assert cache.get("TTL_TEST", "item1") == "value1"
    
    # Sleep past expiration
    time.sleep(1.1)
    
    assert cache.get("TTL_TEST", "item1") is None
    stats = cache.get_stats()
    assert stats["total_misses"] >= 1


def test_cache_lru_eviction():
    """Verify that exceeding max_size evicts the least recently used item."""
    cache = ResponseCacheService(max_size=3, default_ttl=60)
    
    cache.set("LRU", "k1", "v1")
    cache.set("LRU", "k2", "v2")
    cache.set("LRU", "k3", "v3")
    
    # Access k1 to make k2 the LRU item
    cache.get("LRU", "k1")
    
    # Insert 4th item; should evict k2
    cache.set("LRU", "k4", "v4")
    
    assert cache.get("LRU", "k1") == "v1"
    assert cache.get("LRU", "k2") is None  # Evicted!
    assert cache.get("LRU", "k3") == "v3"
    assert cache.get("LRU", "k4") == "v4"
    
    stats = cache.get_stats()
    assert stats["total_evictions"] == 1


def test_cache_namespace_invalidation():
    """Verify invalidating a specific namespace removes only its entries."""
    cache = ResponseCacheService(max_size=10, default_ttl=60)
    
    cache.set("ACT_BNS", "sec_103", "Murder punishment")
    cache.set("ACT_BNS", "sec_303", "Theft punishment")
    cache.set("ACT_RTI", "sec_7", "30 days response")
    
    count = cache.invalidate_namespace("ACT_BNS")
    assert count == 2
    
    assert cache.get("ACT_BNS", "sec_103") is None
    assert cache.get("ACT_RTI", "sec_7") == "30 days response"


def test_model_router_tier_dispatch_and_cost():
    """Verify model router selects proper tiers and computes accurate costs."""
    router = ModelRouterService()
    
    # FAST tier
    res_fast = router.route_task(task_type="CLASSIFY", prompt="My landlord evicted me")
    assert res_fast.tier == "FAST"
    assert res_fast.model_used == "gemini-2.0-flash"
    assert res_fast.estimated_cost_inr > 0.0
    assert res_fast.fallback_used is False
    
    # BALANCED tier
    res_bal = router.route_task(task_type="RIGHTS_EXPLANATION", prompt="Explain consumer dispute rights")
    assert res_bal.tier == "BALANCED"
    assert res_bal.model_used == "gemini-2.0-pro"
    
    # REASONING tier
    res_reas = router.route_task(task_type="COMPLEX_SYNTHESIS", prompt="Multi-party statutory analysis")
    assert res_reas.tier == "REASONING"
    assert res_reas.model_used == "gemini-1.5-pro"
    
    telemetry = router.get_telemetry()
    assert telemetry["total_routed_calls"] == 3
    assert telemetry["total_cost_inr"] > 0.0


def test_model_router_fallback_chain():
    """Verify fallback execution when primary model provider errors out."""
    router = ModelRouterService()
    
    def failing_primary_mock(model_name: str, prompt: str) -> str:
        if "gemini" in model_name:
            raise ConnectionError("Primary Gemini API timeout")
        return f"Fallback successful with {model_name}"

    res = router.route_task(
        task_type="CLASSIFY",
        prompt="Sample query",
        mock_provider_fn=failing_primary_mock,
    )
    
    assert res.status == "FALLBACK_SUCCESS"
    assert res.fallback_used is True
    assert res.model_used == "llama3-70b-8192"
    assert "Fallback successful" in res.content


def test_model_router_deterministic_seed_fallback():
    """Verify deterministic fallback when both primary and secondary providers fail."""
    router = ModelRouterService()
    
    def total_outage_mock(model_name: str, prompt: str) -> str:
        raise RuntimeError("Total upstream provider failure")

    def deterministic_seed_fn() -> str:
        return "Deterministic statutory baseline information."

    res = router.route_task(
        task_type="RIGHTS_EXPLANATION",
        prompt="Sample query",
        mock_provider_fn=total_outage_mock,
        fallback_deterministic_fn=deterministic_seed_fn,
    )
    
    assert res.status == "DETERMINISTIC_FALLBACK"
    assert res.model_used == "deterministic-seed-baseline"
    assert res.content == "Deterministic statutory baseline information."
    assert res.estimated_cost_inr == 0.0
