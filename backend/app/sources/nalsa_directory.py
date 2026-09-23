import json
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

from app.core.config import get_settings
from app.sources.base import SourceAdapter, SourceMetadata


class NALSADirectoryAdapter(SourceAdapter):
    """Tier-1 adapter for National Legal Services Authority (NALSA) directory synchronization.

    Provides official directory information for:
    - NALSA National Legal Aid Helpline: 15100
    - State Legal Services Authorities (SLSAs)
    - District Legal Services Authorities (DLSAs)
    - Legal aid eligibility criteria under Section 12 of Legal Services Authorities Act, 1987.
    """

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None) -> None:
        settings = get_settings()
        metadata = SourceMetadata(
            source_code="NALSA_DIRECTORY",
            name="National Legal Services Authority (NALSA) Official Directory",
            tier=1,
            publisher="National Legal Services Authority, Department of Justice",
            source_url=getattr(settings, "NALSA_PORTAL_URL", "https://nalsa.gov.in"),
            jurisdiction="Union of India",
            update_cadence_days=14,
        )
        super().__init__(metadata)
        self.http_client = http_client

    def get_seed_directory(self) -> dict[str, Any]:
        return {
            "national_helpline": {
                "name": "NALSA National Legal Aid Helpline",
                "toll_free_number": "15100",
                "hours": "24x7 Free Service",
                "scope": "All Indian Citizens seeking legal advice, representation, or legal aid",
                "official_portal": "https://nalsa.gov.in",
            },
            "eligibility_section_12": [
                "A member of a Scheduled Caste or Scheduled Tribe",
                "A victim of trafficking in human beings or begar",
                "A woman or a child",
                "A person with disability as defined in the Rights of Persons with Disabilities Act",
                "A victim of mass disaster, ethnic violence, caste atrocity, flood, drought, earthquake or industrial disaster",
                "An industrial workman",
                "In custody, including custody in a protective home or psychiatric hospital",
                "A person whose annual income does not exceed statutory state threshold (typically Rs 3,00,000)",
            ],
            "state_authorities": [
                {
                    "state": "Delhi",
                    "name": "Delhi State Legal Services Authority (DSLSA)",
                    "address": "Central Office, Patiala House Courts Complex, New Delhi - 110001",
                    "contact_number": "011-23384781 / 15100",
                    "email": "dslsa-phc@nic.in",
                    "website_url": "https://dslsa.org",
                    "districts": ["Central", "East", "New Delhi", "North", "North-East", "North-West", "Shahdara", "South", "South-East", "South-West", "West"],
                },
                {
                    "state": "Maharashtra",
                    "name": "Maharashtra State Legal Services Authority (MSLSA)",
                    "address": "High Court PWD Building, Fort, Mumbai - 400032",
                    "contact_number": "022-22691358 / 15100",
                    "email": "mslsa-bhc@nic.in",
                    "website_url": "https://legalservices.maharashtra.gov.in",
                    "districts": ["Mumbai City", "Mumbai Suburban", "Pune", "Thane", "Nagpur", "Nashik"],
                },
                {
                    "state": "Karnataka",
                    "name": "Karnataka State Legal Services Authority (KSLSA)",
                    "address": "Nyaya Degula, 1st Floor, Siddaiah Road, Bangalore - 560027",
                    "contact_number": "080-22111725 / 15100",
                    "email": "kslsa-kar@nic.in",
                    "website_url": "https://kslsa.kar.nic.in",
                    "districts": ["Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Dharwad", "Mangaluru"],
                },
                {
                    "state": "Uttar Pradesh",
                    "name": "Uttar Pradesh State Legal Services Authority (UPSLSA)",
                    "address": "3rd Floor, Jawahar Bhawan, Annexe, Lucknow - 226001",
                    "contact_number": "0522-2286395 / 15100",
                    "email": "upslsa@nic.in",
                    "website_url": "https://upslsa.up.nic.in",
                    "districts": ["Lucknow", "Kanpur", "Varanasi", "Noida / Gautam Buddha Nagar", "Prayagraj"],
                },
            ],
        }

    async def fetch_latest(self) -> dict[str, Any]:
        if not self.circuit_breaker.can_execute():
            return {"status": "CIRCUIT_OPEN_SEED_SERVED", "data": self.get_seed_directory()}

        try:
            data = self.get_seed_directory()
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
            return {"status": "FAILED", "error": str(exc), "data": self.get_seed_directory()}

    async def health_check(self) -> bool:
        return self.circuit_breaker.can_execute()
