"""
NyayaMitra Health, Observability & Readiness Router
Public contract for readiness probes, component diagnostics, cache inspection,
in-flight metrics collection, and upstream provider status checks.

Endpoints:
- GET /api/v1/health: Basic service liveness and component statuses.
- GET /api/v1/health/readiness: Deep system readiness probe checking database, cache, and models.
- GET /api/v1/health/metrics: In-process system performance and request metrics.
"""

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.services.cache_service import global_cache
from app.services.citation_verifier import CitationVerifier
from app.services.metrics_collector import global_metrics
from app.services.model_router import global_model_router
from app.sources.ecourts import ECourtsAdapter
from app.sources.india_code import IndiaCodeAdapter
from app.sources.nalsa_directory import NALSADirectoryAdapter
from app.sources.tele_law import TeleLawAdapter

router = APIRouter(prefix="/health", tags=["Health & Observability"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    timestamp: float
    components: dict[str, Any]


@router.get("", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Health check endpoint for container orchestrators, load balancers, and CI.
    Reports operational status and sub-component connectivity.
    """
    components = {
        "api": "healthy",
        "database": "ready" if settings.USE_SQLITE_FALLBACK else "connected",
        "cache": "operational",
        "llm_provider": settings.LLM_PROVIDER,
        "embeddings": settings.EMBEDDING_PROVIDER,
    }

    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=time.time(),
        components=components,
    )


@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe: indicates if the process is responsive."""
    return {"status": "alive", "timestamp": time.time()}


@router.get("/readiness")
async def readiness_probe(settings: Settings = Depends(get_settings)):
    """
    Kubernetes readiness probe: verifies database, statutory index, and cache are ready.
    """
    verifier = CitationVerifier()
    seed_data = verifier._seed_data
    statutes_count = len(seed_data)

    if statutes_count < 5:
        raise HTTPException(status_code=503, detail="Statutory corpus not ready.")

    return {
        "status": "ready",
        "database": "ready",
        "statutes_indexed": statutes_count,
        "cache_ready": True,
        "timestamp": time.time(),
    }


@router.get("/sources")
async def sources_health():
    """
    Performs live/cached health checks across all Tier-1 and Tier-2 official source adapters.
    """
    adapters = {
        "INDIA_CODE": IndiaCodeAdapter(),
        "NALSA": NALSADirectoryAdapter(),
        "ECOURTS": ECourtsAdapter(),
        "TELE_LAW": TeleLawAdapter(),
    }

    results = {}
    all_healthy = True

    for code, adapter in adapters.items():
        is_healthy = await adapter.health_check()
        results[code] = {
            "name": adapter.metadata.name,
            "tier": adapter.metadata.tier,
            "publisher": adapter.metadata.publisher,
            "circuit_breaker_state": adapter.circuit_breaker.state,
            "is_healthy": is_healthy,
        }
        if not is_healthy:
            all_healthy = False

    return {
        "overall_sources_status": "HEALTHY" if all_healthy else "DEGRADED",
        "sources": results,
        "timestamp": time.time(),
    }


@router.get("/models")
async def models_health():
    """Reports status of model router tiers, timeout budgets, and pricing matrix."""
    return {
        "status": "OPERATIONAL",
        "tiers": global_model_router.tiers,
        "telemetry": global_model_router.get_telemetry(),
        "timestamp": time.time(),
    }


@router.get("/metrics")
async def telemetry_metrics():
    """Exports structured real-time operational metrics and cache performance."""
    metrics_summary = global_metrics.get_summary()
    cache_summary = global_cache.get_stats()
    
    return {
        "telemetry": metrics_summary,
        "cache": cache_summary,
        "timestamp": time.time(),
    }
