import re
from typing import Any, Optional

from app.services.transition_mapping import TransitionMappingService
from app.sources.india_code import IndiaCodeAdapter


class CitationVerificationResult:
    def __init__(
        self,
        is_valid: bool,
        act_name: str,
        section_number: str,
        status: str,
        verified_quote: Optional[str] = None,
        official_url: Optional[str] = None,
        transition_note: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        self.is_valid = is_valid
        self.act_name = act_name
        self.section_number = section_number
        self.status = status  # VERIFIED_TIER_1, OUTDATED_SUPERSEDED, HALLUCINATED_INVALID
        self.verified_quote = verified_quote
        self.official_url = official_url
        self.transition_note = transition_note
        self.error_message = error_message

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "act_name": self.act_name,
            "section_number": self.section_number,
            "status": self.status,
            "verified_quote": self.verified_quote,
            "official_url": self.official_url,
            "transition_note": self.transition_note,
            "error_message": self.error_message,
        }


class CitationVerifier:
    """Zero-hallucination verification engine.

    Validates every citation against authoritative Tier-1 statutes.
    Detects fabricated sections, non-existent acts, and outdated/repealed laws.
    """

    def __init__(self, india_code_adapter: Optional[IndiaCodeAdapter] = None) -> None:
        self.india_code = india_code_adapter or IndiaCodeAdapter()
        self._seed_data = self.india_code.get_seed_legislation()

    def verify_citation(self, act_name: str, section_number: str) -> CitationVerificationResult:
        clean_act = act_name.strip()
        clean_sec = str(section_number).strip().replace("Section", "").replace("sec.", "").strip()

        # Check if the citation is referencing outdated law (IPC, CrPC, IEA)
        transition = TransitionMappingService.map_outdated_section(clean_act, clean_sec)
        if transition:
            return CitationVerificationResult(
                is_valid=False,
                act_name=clean_act,
                section_number=clean_sec,
                status="OUTDATED_SUPERSEDED",
                transition_note=transition["note"],
                error_message=(
                    f"{clean_act} Section {clean_sec} is outdated/repealed. "
                    f"Current enforceable law is {transition['current_act']} Section {transition['current_section']}."
                ),
            )

        # Match against Tier-1 active legal acts in India Code
        matched_act_code = None
        for act_code, act_data in self._seed_data.items():
            if act_data["act_name"].lower() in clean_act.lower() or act_code.lower() in clean_act.lower():
                matched_act_code = act_code
                break

        if not matched_act_code:
            return CitationVerificationResult(
                is_valid=False,
                act_name=clean_act,
                section_number=clean_sec,
                status="HALLUCINATED_INVALID",
                error_message=f"Statute '{act_name}' not found in Tier-1 official legislation registry.",
            )

        act_record = self._seed_data[matched_act_code]
        clean_sec_base = re.sub(r"\(.*?\)", "", clean_sec).strip()
        # Match section number
        for sec in act_record["sections"]:
            sec_num = sec["section_number"].strip()
            sec_num_base = re.sub(r"\(.*?\)", "", sec_num).strip()
            if sec_num == clean_sec or sec_num == clean_sec_base or sec_num_base == clean_sec_base:
                return CitationVerificationResult(
                    is_valid=True,
                    act_name=act_record["act_name"],
                    section_number=clean_sec,
                    status="VERIFIED_TIER_1",
                    verified_quote=sec["full_text"],
                    official_url=f"https://www.indiacode.nic.in/handle/123456789/{act_record['act_code']}",
                )

        # Section was not found in the act
        return CitationVerificationResult(
            is_valid=False,
            act_name=act_record["act_name"],
            section_number=clean_sec,
            status="HALLUCINATED_INVALID",
            error_message=f"Section {clean_sec} does not exist in {act_record['act_name']}.",
        )

    def extract_and_verify_all(self, text: str) -> list[CitationVerificationResult]:
        """Scans response text for statutory references and verifies each one."""
        pattern = r"(?:Section|Sec\.)\s*([0-9A-Za-z]+)\s*(?:of\s+the\s+|of\s+|,\s*)([A-Za-z\s,]+(?:Act|Sanhita|Adhiniyam)[^,\.\n]*)"
        matches = re.finditer(pattern, text, re.IGNORECASE)
        results = []
        for match in matches:
            sec_num = match.group(1).strip()
            act_name = match.group(2).strip()
            results.append(self.verify_citation(act_name, sec_num))
        return results
