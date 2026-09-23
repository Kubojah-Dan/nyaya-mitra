from typing import Any, Optional

from app.sources.base import SourceAdapter
from app.sources.ecourts import ECourtsAdapter
from app.sources.india_code import IndiaCodeAdapter
from app.sources.nalsa_directory import NALSADirectoryAdapter
from app.sources.tele_law import TeleLawAdapter


class SourceRegistry:
    """Central registry orchestrating all official legal source adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, SourceAdapter] = {}
        # Register default Tier-1 official adapters
        self.register(IndiaCodeAdapter())
        self.register(NALSADirectoryAdapter())
        self.register(ECourtsAdapter())
        self.register(TeleLawAdapter())

    def register(self, adapter: SourceAdapter) -> None:
        self._adapters[adapter.metadata.source_code] = adapter

    def get_adapter(self, source_code: str) -> Optional[SourceAdapter]:
        return self._adapters.get(source_code)

    def list_adapters(self) -> list[dict[str, Any]]:
        results = []
        for code, adapter in self._adapters.items():
            results.append({
                "source_code": code,
                "name": adapter.metadata.name,
                "tier": adapter.metadata.tier,
                "publisher": adapter.metadata.publisher,
                "source_url": adapter.metadata.source_url,
                "jurisdiction": adapter.metadata.jurisdiction,
                "circuit_state": adapter.circuit_breaker.state.value,
                "last_hash": adapter.last_hash,
                "last_fetched_at": adapter.last_fetched_at.isoformat() if adapter.last_fetched_at else None,
            })
        return results

    async def check_all_health(self) -> dict[str, Any]:
        report = {}
        all_healthy = True
        for code, adapter in self._adapters.items():
            is_healthy = await adapter.health_check()
            if not is_healthy:
                all_healthy = False
            report[code] = {
                "healthy": is_healthy,
                "circuit_state": adapter.circuit_breaker.state.value,
                "tier": adapter.metadata.tier,
            }
        return {"overall_status": "HEALTHY" if all_healthy else "DEGRADED", "sources": report}


# Global singleton registry instance
_source_registry: Optional[SourceRegistry] = None


def get_source_registry() -> SourceRegistry:
    global _source_registry
    if _source_registry is None:
        _source_registry = SourceRegistry()
    return _source_registry
