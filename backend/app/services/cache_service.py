"""
NyayaMitra High-Performance Response & Semantic Caching Engine
Provides sub-millisecond cached responses for repeated legal queries, domain classifications,
and statutory section retrievals with TTL expiry and LRU eviction.
"""

from collections import OrderedDict
from datetime import datetime, timezone
import hashlib
import json
import logging
import threading
import time
from typing import Any, Optional

logger = logging.getLogger("nyayamitra.cache")


class CacheEntry:
    def __init__(self, key: str, value: Any, ttl_seconds: int = 3600):
        self.key = key
        self.value = value
        self.ttl_seconds = ttl_seconds
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.hits = 0

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds <= 0:
            return False  # Never expires
        return (time.time() - self.created_at) > self.ttl_seconds


class ResponseCacheService:
    """
    Thread-safe, LRU-evicting in-memory response cache.
    Designed to serve common citizen legal queries (e.g. RTI process, Tenant notice period,
    cheating penalties) with zero LLM/RAG latency.
    """

    def __init__(self, max_size: int = 2000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        
        # Telemetry metrics
        self.total_lookups = 0
        self.total_hits = 0
        self.total_misses = 0
        self.total_evictions = 0
        self.total_invalidations = 0
        self._redis: Any = None

    def is_available(self) -> bool:
        """Indicates if the cache engine is available."""
        return True

    @staticmethod
    def generate_cache_key(namespace: str, payload: Any) -> str:
        """Generates deterministic SHA-256 cache key from namespace and payload."""
        if isinstance(payload, str):
            normalized = payload.strip().lower()
        elif isinstance(payload, dict):
            normalized = json.dumps(payload, sort_keys=True)
        else:
            normalized = str(payload)
        
        digest = hashlib.sha256(f"{namespace}:{normalized}".encode("utf-8")).hexdigest()
        return f"{namespace}:{digest[:16]}"

    def get(self, namespace: str, payload: Any) -> Optional[Any]:
        """Retrieves cached item if present and unexpired."""
        key = self.generate_cache_key(namespace, payload)
        with self._lock:
            self.total_lookups += 1
            if key not in self._cache:
                self.total_misses += 1
                return None

            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                self.total_misses += 1
                return None

            # LRU move to end
            self._cache.move_to_end(key)
            entry.last_accessed = time.time()
            entry.hits += 1
            self.total_hits += 1
            return entry.value

    def set(self, namespace: str, payload: Any, value: Any, ttl_seconds: Optional[int] = None) -> str:
        """Stores value in cache, evicting oldest item if size limit reached."""
        key = self.generate_cache_key(namespace, payload)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            elif len(self._cache) >= self.max_size:
                # Evict LRU item (first item)
                oldest_key, _ = self._cache.popitem(last=False)
                self.total_evictions += 1
                logger.debug(f"Cache capacity reached; evicted key {oldest_key}")

            self._cache[key] = CacheEntry(key=key, value=value, ttl_seconds=ttl)
            return key

    def invalidate_namespace(self, namespace: str) -> int:
        """Invalidates all cache entries matching namespace (e.g. after statutory update)."""
        count = 0
        with self._lock:
            keys_to_delete = [k for k in self._cache if k.startswith(f"{namespace}:")]
            for k in keys_to_delete:
                del self._cache[k]
                count += 1
            self.total_invalidations += count
        return count

    def clear(self) -> None:
        """Clears all cache entries."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Returns live cache hit/miss and efficiency metrics."""
        with self._lock:
            hit_ratio = round(self.total_hits / self.total_lookups, 4) if self.total_lookups > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "total_lookups": self.total_lookups,
                "total_hits": self.total_hits,
                "total_misses": self.total_misses,
                "hit_ratio": hit_ratio,
                "hit_percentage": f"{hit_ratio * 100:.1f}%",
                "total_evictions": self.total_evictions,
                "total_invalidations": self.total_invalidations,
            }


# Global singleton instance for the backend process
global_cache = ResponseCacheService()
