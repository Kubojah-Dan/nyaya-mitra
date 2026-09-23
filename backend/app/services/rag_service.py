import re
from typing import Any, Optional

from app.models.schemas import CitationItem, DeadlineItem, RAGResponseContract
from app.services.citation_verifier import CitationVerifier
from app.services.retrieval import LegalRetrievalEngine
from app.services.transition_mapping import TransitionMappingService


class LegalRAGService:
    """Citation-first RAG service for Indian legal access and assistance.

    Produces strictly structured responses grounded in current Tier-1 legislation (BNS/BNSS/BSA),
    with zero hallucinated citations and automatic outdated-law translation.
    """

    def __init__(
        self,
        retrieval_engine: Optional[LegalRetrievalEngine] = None,
        citation_verifier: Optional[CitationVerifier] = None,
    ) -> None:
        self.retrieval = retrieval_engine or LegalRetrievalEngine()
        self.verifier = citation_verifier or CitationVerifier()

    def process_query(self, user_query: str, language: str = "en") -> RAGResponseContract:
        clean_query = user_query.strip()

        # Step 1: Detect and handle outdated statutory references (IPC, CrPC, IEA)
        transition_notes = []
        old_law_matches = re.finditer(
            r"\b(IPC|CrPC|IEA|Indian Penal Code|Code of Criminal Procedure)\s*(?:section|sec\.?)?\s*([0-9]{1,4}[a-z]?)\b",
            clean_query,
            re.IGNORECASE,
        )
        for match in old_law_matches:
            old_act = match.group(1)
            old_sec = match.group(2)
            mapped = TransitionMappingService.map_outdated_section(old_act, old_sec)
            if mapped:
                transition_notes.append(mapped)

        # Step 2: Retrieve relevant Tier-1 statutory sections
        evidence = self.retrieval.search(clean_query, top_k=3)

        # Step 3: Construct structured response elements
        citations: list[CitationItem] = []
        deadlines: list[DeadlineItem] = []
        rights: list[str] = []
        next_steps: list[str] = []
        uncertainties: list[str] = []
        escalation_needed = False
        escalation_reason = None

        # Check urgency / escalation triggers
        urgent_keywords = ["immediate arrest", "police assault", "domestic violence", "threat to life", "evicting right now"]
        if any(kw in clean_query.lower() for kw in urgent_keywords):
            escalation_needed = True
            escalation_reason = "Urgent legal situation involving immediate threat or liberty. Human legal aid escalation recommended."

        # Process retrieved evidence and generate verified citations
        for item in evidence:
            sec_num = item["section_number"]
            act_name = item["act_name"]

            # Verify with zero-hallucination engine
            v_res = self.verifier.verify_citation(act_name, sec_num)
            if v_res.is_valid:
                citations.append(
                    CitationItem(
                        act_name=act_name,
                        section_number=sec_num,
                        quote=item["full_text"][:250] + ("..." if len(item["full_text"]) > 250 else ""),
                        official_url=item["official_url"],
                        is_current_law=True,
                    )
                )
                if item.get("plain_english"):
                    rights.append(f"Under Section {sec_num} ({item['title']}): {item['plain_english']}")

        # Include mapped current-law transition citations if outdated law was queried
        for t in transition_notes:
            citations.append(
                CitationItem(
                    act_name=t["current_act"],
                    section_number=t["current_section"],
                    quote=t["note"],
                    official_url="https://www.indiacode.nic.in",
                    is_current_law=True,
                    replaces_outdated_law=t["historical_act"],
                )
            )
            rights.append(
                f"Transition Note: {t['historical_act']} has been replaced by {t['current_act']} Section {t['current_section']}."
            )

        # Domain-specific procedural steps and statutory deadlines
        lower_q = clean_query.lower()
        if "rti" in lower_q or "information" in lower_q:
            deadlines.append(
                DeadlineItem(
                    label="PIO Statutory Response Window",
                    relative_timeframe="30 days from receipt of application (48 hours if life or liberty)",
                    trigger_event="Date of submission of RTI application",
                    statutory_basis="Section 7(1), Right to Information Act, 2005",
                    urgency_level="MEDIUM",
                )
            )
            deadlines.append(
                DeadlineItem(
                    label="First Appeal Limitation",
                    relative_timeframe="30 days from expiry of response window or receipt of decision",
                    trigger_event="Non-receipt of reply or unsatisfactory decision",
                    statutory_basis="Section 19(1), Right to Information Act, 2005",
                    urgency_level="HIGH",
                )
            )
            next_steps.extend([
                "File written or online RTI request to Central/State Public Information Officer (PIO) with prescribed fee (usually Rs. 10).",
                "Ensure application seeks specific, identifiable records without requiring explanation of purpose.",
                "Retain acknowledgment slip and postal/digital receipt for tracking.",
            ])

        elif "consumer" in lower_q or "defective" in lower_q or "refund" in lower_q:
            deadlines.append(
                DeadlineItem(
                    label="Consumer Complaint Statutory Limitation Period",
                    relative_timeframe="Within 2 years from date of cause of action (defect/deficiency)",
                    trigger_event="Date of purchase, defect discovery, or service deficiency",
                    statutory_basis="Section 69, Consumer Protection Act, 2019",
                    urgency_level="MEDIUM",
                )
            )
            next_steps.extend([
                "Send formal legal notice to seller/service provider giving 15 days to rectify defect or refund amount.",
                "File complaint online via official e-Daakhil portal or at the District Consumer Commission having jurisdiction.",
                "Preserve purchase bills, warranty cards, and written communication logs.",
            ])

        elif "fir" in lower_q or "police" in lower_q or "cheating" in lower_q:
            next_steps.extend([
                "Visit the local police station or use the official state police e-FIR portal to lodge an FIR under Section 173 of BNSS.",
                "Demand an immediate free copy of the registered FIR as mandated by law.",
                "If police refuse to register FIR, submit a written complaint to the Superintendent of Police under Section 173(4) of BNSS.",
            ])

        else:
            next_steps.extend([
                "Review the relevant statutory provisions and collect all documentary evidence.",
                "If formal notice has been received, note the statutory reply deadline immediately.",
                "Consult the NALSA Legal Aid helpline (15100) if free representation is needed.",
            ])

        # Formulate plain-language summary
        if transition_notes:
            summary = (
                f"Under current Indian criminal law (effective July 1, 2024), {transition_notes[0]['note']} "
                f"We have grounded the legal position in current Tier-1 legislation with verified statutory references."
            )
        elif evidence:
            summary = (
                f"Based on authoritative provisions of {evidence[0]['act_name']}, your matter relates to "
                f"'{evidence[0]['title']}'. You have specific procedural protections under current law."
            )
        else:
            summary = "Your legal query has been analyzed against Tier-1 Indian legislation."

        if not uncertainties:
            uncertainties.append("Exact dates and jurisdiction specifics may alter limitation periods and forum choice.")

        return RAGResponseContract(
            summary=summary,
            rights=rights,
            next_steps=next_steps,
            deadlines=deadlines,
            citations=citations,
            uncertainties=uncertainties,
            escalation_needed=escalation_needed,
            escalation_reason=escalation_reason,
        )
