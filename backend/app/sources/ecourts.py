import json
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

from app.core.config import get_settings
from app.sources.base import SourceAdapter, SourceMetadata


class ECourtsAdapter(SourceAdapter):
    """Tier-1 adapter for eCourts Services and judicial process navigation.

    Provides compliant navigation guidance for:
    - CNR (Case Number Record) 16-character alphanumeric structure
    - Case Status tracking via official eCourts Services portal & app
    - District Court / High Court jurisdiction routing
    - Cause lists and certified copy procedural guidelines

    Note: Strictly complies with non-scraping guidelines by providing verified
    structural metadata, official API guidance, and deep link navigation without
    unauthorized automated CAPTCHA bypassing.
    """

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None) -> None:
        settings = get_settings()
        metadata = SourceMetadata(
            source_code="ECOURTS",
            name="eCourts Services (e-Committee, Supreme Court of India)",
            tier=1,
            publisher="e-Committee, Supreme Court of India / National Informatics Centre (NIC)",
            source_url=getattr(settings, "ECOURTS_PORTAL_URL", "https://ecourts.gov.in"),
            jurisdiction="Union of India",
            update_cadence_days=30,
        )
        super().__init__(metadata)
        self.http_client = http_client

    def get_navigation_guidelines(self) -> dict[str, Any]:
        return {
            "cnr_structure": {
                "length": 16,
                "description": "Unique 16-character alphanumeric Case Number Record",
                "format": "SSDDNN-CCCCCC-YYYY (State Code, District Code, Court Code, Case Number, Year)",
                "example": "DLCT01-001234-2026",
                "purpose": "Universal identifier for tracking case status across any District or High Court in India",
            },
            "official_portals": {
                "district_courts": "https://services.ecourts.gov.in/ecourtindia_v6/",
                "high_courts": "https://hcservices.ecourts.gov.in/hcservices/",
                "supreme_court": "https://main.sci.gov.in/case-status",
                "mobile_app": "eCourts Services App (Android & iOS)",
            },
            "procedure_guides": {
                "case_status_by_cnr": "Go to services.ecourts.gov.in -> Enter 16-digit CNR Number -> View complete case history, next date of hearing, and uploaded interim orders.",
                "certified_copies": "Apply through e-Copying portal of respective High Court/District Court with case number and requisite fee.",
                "e_filing": "Available on efiling.ecourts.gov.in for registered advocates and party-in-person.",
            },
        }

    async def fetch_latest(self) -> dict[str, Any]:
        if not self.circuit_breaker.can_execute():
            return {"status": "CIRCUIT_OPEN_SEED_SERVED", "data": self.get_navigation_guidelines()}

        try:
            data = self.get_navigation_guidelines()
            serialized = json.dumps(data, sort_keys=True)
            content_hash = self.compute_hash(serialized)
            self.last_hash = content_hash
            self.last_fetched_at = datetime.now(timezone.utc)
            self.circuit_breaker.record_success()
            return {
                "status": "SUCCESS",
                "content_hash": content_hash,
                "fetched_at": self.last_fetched_at.isoformat(),
                "data": data,
            }
        except Exception as exc:
            self.circuit_breaker.record_failure()
            return {"status": "FAILED", "error": str(exc), "data": self.get_navigation_guidelines()}

    async def health_check(self) -> bool:
        return self.circuit_breaker.can_execute()
