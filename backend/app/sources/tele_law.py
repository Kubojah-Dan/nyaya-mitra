import json
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

from app.core.config import get_settings
from app.sources.base import SourceAdapter, SourceMetadata


class TeleLawAdapter(SourceAdapter):
    """Tier-1 adapter for Tele-Law: Mainstreaming Legal Aid through Common Services Centers (CSC).

    Provides guidance for video/audio consultations with Panel Lawyers:
    - Department of Justice & Ministry of Electronics and Information Technology (MeitY)
    - Free for eligible beneficiaries under Section 12 of LSA Act (women, SC/ST, children, low income)
    - Mobile app / CSC center touchpoint routing
    """

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None) -> None:
        settings = get_settings()
        metadata = SourceMetadata(
            source_code="TELE_LAW",
            name="Tele-Law Program (Department of Justice, Government of India)",
            tier=1,
            publisher="Department of Justice, Ministry of Law and Justice",
            source_url=getattr(settings, "TELE_LAW_URL", "https://www.tele-law.in"),
            jurisdiction="Union of India",
            update_cadence_days=30,
        )
        super().__init__(metadata)
        self.http_client = http_client

    def get_program_details(self) -> dict[str, Any]:
        return {
            "overview": {
                "name": "Tele-Law Citizen Scheme",
                "objective": "Pre-litigation legal advice through video-conferencing / telephone connecting citizens with panel lawyers",
                "nodal_agency": "Department of Justice in collaboration with CSC e-Governance Services India Ltd",
                "official_portal": "https://www.tele-law.in",
                "mobile_app": "Tele-Law on Google Play Store",
            },
            "fee_structure": {
                "section_12_eligible": "100% Free of cost (Women, SC/ST, Children, Victims of Trafficking/Disaster, Disabled, Undertrials, Low-Income)",
                "general_category": "Nominal consultation fee of Rs 30 (often waived during special legal aid camps)",
            },
            "steps_to_access": [
                "Visit nearest Common Service Center (CSC) / Digital Seva Kendra, OR download Tele-Law Citizen App.",
                "Register mobile number with OTP verification.",
                "Enter brief description of dispute (Family, Land, Tenancy, Consumer, Criminal FIR).",
                "Select preferred date, time slot, and language preference (Hindi, English, or Regional Language).",
                "Connect with Panel Lawyer via video call or telephone audio bridge at scheduled time.",
            ],
        }

    async def fetch_latest(self) -> dict[str, Any]:
        if not self.circuit_breaker.can_execute():
            return {"status": "CIRCUIT_OPEN_SEED_SERVED", "data": self.get_program_details()}

        try:
            data = self.get_program_details()
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
            return {"status": "FAILED", "error": str(exc), "data": self.get_program_details()}

    async def health_check(self) -> bool:
        return self.circuit_breaker.can_execute()
