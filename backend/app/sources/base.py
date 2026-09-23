import abc
import hashlib
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # Normal operation, requests allowed
    OPEN = "OPEN"          # Failure threshold reached, requests blocked
    HALF_OPEN = "HALF_OPEN"# Testing upstream recovery


class CircuitBreaker:
    """Circuit breaker for resilient external source connector integration."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            return True
        return False


class SourceMetadata:
    def __init__(
        self,
        source_code: str,
        name: str,
        tier: int,
        publisher: str,
        source_url: str,
        jurisdiction: str = "Union of India",
        update_cadence_days: int = 7,
    ) -> None:
        self.source_code = source_code
        self.name = name
        self.tier = tier  # 1=Primary Authoritative, 2=Official Secondary, 3=Trusted Secondary
        self.publisher = publisher
        self.source_url = source_url
        self.jurisdiction = jurisdiction
        self.update_cadence_days = update_cadence_days


class SourceAdapter(abc.ABC):
    """Abstract Base Class for all compliant official source adapters."""

    def __init__(self, metadata: SourceMetadata) -> None:
        self.metadata = metadata
        self.circuit_breaker = CircuitBreaker()
        self.last_hash: Optional[str] = None
        self.last_fetched_at: Optional[datetime] = None

    @abc.abstractmethod
    async def fetch_latest(self) -> dict[str, Any]:
        """Fetch latest authoritative content or delta from source."""
        pass

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Verify upstream accessibility and compliant response."""
        pass

    def compute_hash(self, content: str | bytes) -> str:
        """Compute SHA-256 content hash for change detection."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def detect_changes(self, new_hash: str) -> bool:
        """Returns True if the new content hash differs from the stored hash."""
        if self.last_hash is None:
            return True
        return self.last_hash != new_hash

    def get_provenance(self, item_id: str) -> dict[str, Any]:
        """Answer 'Where did this fact come from?' with full audit metadata."""
        return {
            "source_code": self.metadata.source_code,
            "source_name": self.metadata.name,
            "tier": self.metadata.tier,
            "publisher": self.metadata.publisher,
            "official_url": self.metadata.source_url,
            "jurisdiction": self.metadata.jurisdiction,
            "item_id": item_id,
            "verified_at": (self.last_fetched_at or datetime.now(timezone.utc)).isoformat(),
            "content_hash": self.last_hash or "unverified",
        }
