from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from app.sources.registry import get_source_registry

router = APIRouter(prefix="/sources", tags=["Official Legal Sources"])


@router.get("/registry")
async def get_registered_sources():
    """List all registered Tier-1 and Tier-2 official source connectors and their status."""
    registry = get_source_registry()
    adapters = registry.list_adapters()
    return JSONResponse({"total_sources": len(adapters), "sources": adapters})


@router.get("/health")
async def get_sources_health():
    """Check health and circuit breaker state of all registered upstream connectors."""
    registry = get_source_registry()
    health_report = await registry.check_all_health()
    return JSONResponse(health_report)


@router.get("/{source_code}/provenance")
async def get_source_provenance(source_code: str, item_id: str = "general"):
    """Retrieve full audit provenance for an item or statutory claim."""
    registry = get_source_registry()
    adapter = registry.get_adapter(source_code.upper())
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source_code}' not found")
    return JSONResponse(adapter.get_provenance(item_id))
