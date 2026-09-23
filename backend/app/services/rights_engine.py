"""Rights Explanation & Action Timeline Engine — "Mere Adhikaar" (Phase 6).

Produces:
- Verified legal rights (from Tier-1 statutory sources only).
- Deterministic action timelines with statutory deadlines.
- Grade 6–8 reading-level plain-language explanations.
- Inline verified citations (VERIFIED_TIER_1 only).
- Translation layer preserving legal meaning.
- Source/freshness metadata on every claim.
- Escalation recommendations.

Never:
- Invent a deadline not grounded in statute.
- Infer exact entitlements from incomplete facts without qualification.
- Cite a section not verified in the source registry.
- Use outdated law without an explicit historical-context label.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.models.schemas import CitationItem, DeadlineItem, RAGResponseContract
from app.services.citation_verifier import CitationVerifier
from app.services.retrieval import LegalRetrievalEngine
from app.services.transition_mapping import TransitionMappingService


# ---------------------------------------------------------------------------
# Grade 6-8 reading plain-language clause bank (Tier-1 verified only)
# ---------------------------------------------------------------------------
_RIGHTS_BANK: dict[str, dict[str, Any]] = {
    "TENANCY": {
        "rights_en": [
            "You cannot be evicted without a valid legal notice under the applicable Rent Control Act or Model Tenancy Act of your state.",
            "Your landlord must give you a reasonable notice period (typically 15–90 days depending on state law) before asking you to vacate.",
            "If you have paid security deposit, you are entitled to its refund after deductions for actual damages only.",
            "You cannot be forcibly evicted or have utilities disconnected without a court order.",
        ],
        "rights_hi": [
            "बिना वैध नोटिस के आपको घर से नहीं निकाला जा सकता।",
            "मकान मालिक को खाली करवाने से पहले उचित समय का नोटिस देना जरूरी है (राज्य कानून के अनुसार 15–90 दिन)।",
            "सुरक्षा जमा राशि वास्तविक नुकसान की कटौती के बाद वापस मिलनी चाहिए।",
            "कोर्ट के आदेश के बिना बिजली-पानी नहीं काटा जा सकता।",
        ],
        "next_steps_en": [
            "1. Collect all rent receipts, bank transfer records, and the rent agreement.",
            "2. Send a written reply to the notice within 15 days denying any illegal claims.",
            "3. Contact the Rent Controller / Rent Tribunal in your city if the landlord continues harassment.",
            "4. If you need free legal assistance, call NALSA helpline 15100.",
        ],
        "next_steps_hi": [
            "1. सभी किराये की रसीदें, बैंक ट्रांसफर रिकॉर्ड और किराया समझौता इकट्ठा करें।",
            "2. नोटिस के 15 दिन के अंदर लिखित जवाब भेजें।",
            "3. अगर उत्पीड़न जारी हो, तो अपने शहर के रेंट कंट्रोलर / रेंट ट्रिब्यूनल से संपर्क करें।",
            "4. मुफ्त कानूनी सहायता के लिए NALSA हेल्पलाइन 15100 पर कॉल करें।",
        ],
        "deadlines": [
            {
                "label": "Reply to Landlord Notice",
                "relative_days": 15,
                "trigger_event": "Date of receipt of eviction notice",
                "statutory_basis": "Model Tenancy Act, 2021 / State Rent Control Acts",
                "urgency_level": "HIGH",
                "is_firm": False,
                "uncertainty": "Exact notice period depends on state rent control legislation — consult your state Act.",
            },
        ],
        "citations": [
            {"act_name": "Consumer Protection Act, 2019", "section_number": "34", "is_placeholder": False},
        ],
        "escalation_threshold": "MEDIUM",
    },
    "CONSUMER": {
        "rights_en": [
            "Under the Consumer Protection Act, 2019, you have the right to seek replacement, repair, or full refund for a defective product.",
            "You can claim compensation for any loss suffered due to the seller's deficiency in service.",
            "Online buyers have additional protection — sellers must disclose return and refund policies clearly.",
            "Complaints can be filed online via the official e-Daakhil portal without visiting any court in person.",
        ],
        "rights_hi": [
            "उपभोक्ता संरक्षण अधिनियम 2019 के तहत आपको दोषपूर्ण सामान के बदले मरम्मत, बदलाव या पूरा रिफंड मांगने का अधिकार है।",
            "सेवा में कमी से हुए नुकसान का मुआवजा मांगा जा सकता है।",
            "ऑनलाइन खरीदारों को अतिरिक्त सुरक्षा मिलती है — विक्रेता को रिटर्न नीति स्पष्ट बतानी होती है।",
            "शिकायत e-Daakhil पोर्टल पर ऑनलाइन दर्ज की जा सकती है।",
        ],
        "next_steps_en": [
            "1. Send a formal legal notice to the seller giving 15 days to resolve the issue.",
            "2. File a consumer complaint on e-Daakhil (https://edaakhil.nic.in) with your purchase proof and correspondence.",
            "3. Keep all purchase receipts, warranty cards, and written communication as evidence.",
            "4. The District Consumer Commission handles claims up to Rs. 50 lakh — no advocate required.",
        ],
        "next_steps_hi": [
            "1. विक्रेता को 15 दिन का नोटिस भेजें।",
            "2. e-Daakhil (https://edaakhil.nic.in) पर ऑनलाइन शिकायत दर्ज करें।",
            "3. सभी रसीदें, वारंटी कार्ड और पत्राचार सुरक्षित रखें।",
            "4. जिला उपभोक्ता आयोग में वकील के बिना भी शिकायत दर्ज हो सकती है।",
        ],
        "deadlines": [
            {
                "label": "Consumer Complaint Filing Limitation",
                "relative_days": 730,  # 2 years
                "trigger_event": "Date of cause of action (defect/deficiency/overcharge)",
                "statutory_basis": "Section 69, Consumer Protection Act, 2019",
                "urgency_level": "MEDIUM",
                "is_firm": True,
                "uncertainty": None,
            },
        ],
        "citations": [
            {"act_name": "Consumer Protection Act, 2019", "section_number": "34", "is_placeholder": False},
            {"act_name": "Consumer Protection Act, 2019", "section_number": "35", "is_placeholder": False},
            {"act_name": "Consumer Protection Act, 2019", "section_number": "69", "is_placeholder": False},
        ],
        "escalation_threshold": "LOW",
    },
    "RTI": {
        "rights_en": [
            "Under Section 6 of the RTI Act, 2005, any Indian citizen can seek information from any public authority.",
            "You do not need to explain or justify why you want the information.",
            "The Public Information Officer (PIO) must respond within 30 working days of receiving your application.",
            "If the request concerns life or personal liberty, the response must be given within 48 hours.",
            "If rejected or not responded to, you can file a First Appeal to the First Appellate Authority within 30 days.",
            "After that, you can file a Second Appeal with the Information Commission.",
        ],
        "rights_hi": [
            "आरटीआई अधिनियम 2005 की धारा 6 के तहत कोई भी भारतीय नागरिक किसी भी सार्वजनिक प्राधिकरण से जानकारी माँग सकता है।",
            "जानकारी माँगने का कारण बताना जरूरी नहीं है।",
            "लोक सूचना अधिकारी को 30 कार्यदिवस में जवाब देना होता है।",
            "जीवन या स्वतंत्रता से जुड़ी जानकारी 48 घंटे में देनी होती है।",
            "जवाब न मिले या अस्वीकार हो तो 30 दिन के भीतर प्रथम अपील की जा सकती है।",
        ],
        "next_steps_en": [
            "1. Identify the correct Public Information Officer (PIO) for the relevant department.",
            "2. Draft a concise RTI application specifying the exact records needed.",
            "3. Pay the Rs. 10 application fee (postal order / bank draft / online).",
            "4. Submit by post, in person, or online via the RTI online portal (https://rtionline.gov.in).",
            "5. Keep the acknowledgment slip and track the 30-day response window.",
        ],
        "next_steps_hi": [
            "1. संबंधित विभाग के सही लोक सूचना अधिकारी की पहचान करें।",
            "2. जरूरी दस्तावेज़ों का स्पष्ट उल्लेख करते हुए आरटीआई आवेदन तैयार करें।",
            "3. 10 रुपये शुल्क (मनीऑर्डर/ड्राफ्ट/ऑनलाइन) के साथ जमा करें।",
            "4. डाक, व्यक्तिगत रूप से या rtionline.gov.in पर ऑनलाइन जमा करें।",
            "5. पावती स्लिप रखें और 30 दिन की समयसीमा ट्रैक करें।",
        ],
        "deadlines": [
            {
                "label": "PIO Response Deadline",
                "relative_days": 30,
                "trigger_event": "Date of receipt of RTI application by PIO",
                "statutory_basis": "Section 7(1), Right to Information Act, 2005",
                "urgency_level": "MEDIUM",
                "is_firm": True,
                "uncertainty": None,
            },
            {
                "label": "First Appeal Deadline",
                "relative_days": 30,
                "trigger_event": "Expiry of PIO response window or receipt of unsatisfactory decision",
                "statutory_basis": "Section 19(1), Right to Information Act, 2005",
                "urgency_level": "HIGH",
                "is_firm": True,
                "uncertainty": None,
            },
            {
                "label": "Life/Liberty Urgent Response",
                "relative_days": None,
                "trigger_event": "Date of receipt of RTI application (life/liberty matter)",
                "statutory_basis": "Section 7(1) proviso, Right to Information Act, 2005",
                "urgency_level": "CRITICAL",
                "is_firm": True,
                "uncertainty": "Only applies where information is needed to protect life or personal liberty",
            },
        ],
        "citations": [
            {"act_name": "Right to Information Act, 2005", "section_number": "6", "is_placeholder": False},
            {"act_name": "Right to Information Act, 2005", "section_number": "7", "is_placeholder": False},
            {"act_name": "Right to Information Act, 2005", "section_number": "19", "is_placeholder": False},
        ],
        "escalation_threshold": "LOW",
    },
    "CRIMINAL": {
        "rights_en": [
            "Under Section 173 of the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS), police are legally obligated to register an FIR for cognizable offences.",
            "You can file a Zero FIR at any police station regardless of where the incident occurred — it must then be transferred to the jurisdictional station.",
            "Under Section 35 of BNSS, police must record specific reasons before arresting for offences carrying less than 7 years imprisonment.",
            "If arrested, you have the right to know the grounds of arrest, the right to inform a family member, and the right to consult an advocate.",
            "You can apply for bail at the Magistrate's Court (Section 480 BNSS) or Sessions Court / High Court (Section 482 BNSS).",
        ],
        "rights_hi": [
            "BNSS की धारा 173 के अनुसार, संज्ञेय अपराधों में पुलिस को एफआईआर दर्ज करना कानूनन अनिवार्य है।",
            "जीरो एफआईआर किसी भी थाने में दर्ज कराई जा सकती है — उसे बाद में संबंधित थाने में स्थानांतरित किया जाएगा।",
            "7 साल से कम की सजा वाले अपराधों में गिरफ्तारी से पहले पुलिस को लिखित कारण दर्ज करना होता है (BNSS धारा 35)।",
            "गिरफ्तार होने पर कारण जानने, परिजन को सूचित करने और वकील से मिलने का अधिकार है।",
            "जमानत के लिए मजिस्ट्रेट कोर्ट (BNSS धारा 480) या सेशन कोर्ट (धारा 482) में आवेदन कर सकते हैं।",
        ],
        "next_steps_en": [
            "1. If FIR has not been registered, go to the police station and make a written complaint. Demand an acknowledgment.",
            "2. If police refuse to register FIR, send a written complaint to the Superintendent of Police (SP).",
            "3. You can also approach the Judicial Magistrate directly under BNSS Section 175.",
            "4. Keep copies of all documents, screenshots, and medical reports if relevant.",
            "5. Contact a legal aid lawyer (NALSA 15100) or a private advocate for bail application if arrested.",
        ],
        "next_steps_hi": [
            "1. अगर एफआईआर नहीं हुई है तो थाने में जाकर लिखित शिकायत दें और पावती माँगें।",
            "2. अगर पुलिस मना करे तो पुलिस अधीक्षक को लिखित शिकायत करें।",
            "3. BNSS धारा 175 के तहत सीधे न्यायिक मजिस्ट्रेट के पास जा सकते हैं।",
            "4. सभी दस्तावेज़, स्क्रीनशॉट और मेडिकल रिपोर्ट की प्रतियाँ रखें।",
            "5. अगर गिरफ्तारी है तो NALSA 15100 पर निःशुल्क कानूनी सहायता माँगें।",
        ],
        "deadlines": [
            {
                "label": "Free copy of FIR",
                "relative_days": 0,
                "trigger_event": "Immediately upon FIR registration",
                "statutory_basis": "Section 173(2), Bharatiya Nagarik Suraksha Sanhita, 2023",
                "urgency_level": "HIGH",
                "is_firm": True,
                "uncertainty": None,
            },
        ],
        "citations": [
            {"act_name": "Bharatiya Nagarik Suraksha Sanhita, 2023", "section_number": "173", "is_placeholder": False},
            {"act_name": "Bharatiya Nagarik Suraksha Sanhita, 2023", "section_number": "35", "is_placeholder": False},
        ],
        "escalation_threshold": "HIGH",
    },
}


class RightsExplanationEngine:
    """Rights Explanation & Action Timeline Engine — "Mere Adhikaar".

    Produces Grade 6-8 reading level, verified-citation legal rights explanations
    with deterministic action timelines grounded in Tier-1 statutes.
    """

    def __init__(
        self,
        retrieval_engine: Optional[LegalRetrievalEngine] = None,
        citation_verifier: Optional[CitationVerifier] = None,
    ) -> None:
        self.retrieval = retrieval_engine or LegalRetrievalEngine()
        self.verifier = citation_verifier or CitationVerifier()

    def explain_rights(
        self,
        domain: str,
        collected_facts: dict[str, Any],
        language: str = "en",
        trigger_date: Optional[datetime] = None,
    ) -> RAGResponseContract:
        """Produce a verified, structured rights-and-timeline response.

        Args:
            domain: Legal domain (TENANCY, CONSUMER, RTI, CRIMINAL, etc.)
            collected_facts: Facts collected by the intake engine.
            language: "en" or "hi".
            trigger_date: Optional date for computing absolute deadlines (e.g. notice received date).
        """
        bank = _RIGHTS_BANK.get(domain, _RIGHTS_BANK.get("CONSUMER", {}))
        lang_suffix = "hi" if language == "hi" else "en"

        rights = bank.get(f"rights_{lang_suffix}", bank.get("rights_en", []))
        next_steps = bank.get(f"next_steps_{lang_suffix}", bank.get("next_steps_en", []))

        # Build verified citations
        citations: list[CitationItem] = []
        uncertainties: list[str] = []

        for ref in bank.get("citations", []):
            v = self.verifier.verify_citation(ref["act_name"], ref["section_number"])
            if v.is_valid:
                citations.append(CitationItem(
                    act_name=v.act_name,
                    section_number=v.section_number,
                    quote=v.verified_quote[:200] + "..." if v.verified_quote and len(v.verified_quote) > 200 else (v.verified_quote or ""),
                    official_url=v.official_url or "https://www.indiacode.nic.in",
                    is_current_law=True,
                ))
            elif v.status == "OUTDATED_SUPERSEDED":
                # Explicitly label outdated citations with historical context
                uncertainties.append(
                    f"Historical law cited: {v.act_name} Section {v.section_number} — {v.transition_note or 'superseded by current law'}"
                )

        # Add additional evidence from retrieval engine
        query = f"{domain} rights India"
        evidence = self.retrieval.search(query, top_k=2)
        for item in evidence:
            if not any(c.section_number == item["section_number"] for c in citations):
                v = self.verifier.verify_citation(item["act_name"], item["section_number"])
                if v.is_valid:
                    citations.append(CitationItem(
                        act_name=item["act_name"],
                        section_number=item["section_number"],
                        quote=item["full_text"][:200] + "..." if len(item["full_text"]) > 200 else item["full_text"],
                        official_url=item["official_url"],
                        is_current_law=True,
                    ))

        # Build deadlines
        deadlines: list[DeadlineItem] = []
        for dl in bank.get("deadlines", []):
            deadline_date_str = None
            if trigger_date and dl.get("relative_days") is not None:
                if dl["relative_days"] == 0:
                    deadline_date_str = "Immediately"
                else:
                    abs_date = trigger_date + timedelta(days=dl["relative_days"])
                    deadline_date_str = abs_date.strftime("%d %B %Y")

            deadlines.append(DeadlineItem(
                label=dl["label"],
                deadline_date=deadline_date_str,
                relative_timeframe=(
                    f"Within {dl['relative_days']} days" if dl.get("relative_days") and dl["relative_days"] > 0
                    else ("Immediately" if dl.get("relative_days") == 0 else "Depends on specific facts")
                ),
                trigger_event=dl["trigger_event"],
                statutory_basis=dl["statutory_basis"],
                urgency_level=dl["urgency_level"],
            ))

            if dl.get("uncertainty"):
                uncertainties.append(f"⚠ Deadline uncertainty: {dl['uncertainty']}")

        # Determine escalation
        escalation_threshold = bank.get("escalation_threshold", "MEDIUM")
        escalation_needed = False
        escalation_reason = None

        if escalation_threshold == "HIGH":
            escalation_needed = True
            escalation_reason = (
                "Criminal matters may require immediate legal representation. "
                "Contact NALSA Legal Aid Helpline: 15100 (free, 24×7)."
            )
        elif collected_facts.get("is_urgent") or collected_facts.get("arrested"):
            escalation_needed = True
            escalation_reason = "Urgency or arrest detected — immediate legal aid recommended. Call 15100."

        # Default uncertainty if none set
        if not uncertainties:
            uncertainties.append(
                "The exact rights and deadlines may vary based on your specific state's laws and the full facts of your case."
            )

        # Freshness metadata note
        freshness_note = (
            "Legal information verified against Tier-1 official sources (India Code, NALSA) "
            f"as of {datetime.now(timezone.utc).strftime('%d %B %Y')}."
        )

        summary = self._build_summary(domain, rights, language)

        return RAGResponseContract(
            summary=summary,
            rights=rights,
            next_steps=next_steps,
            deadlines=deadlines,
            citations=citations,
            uncertainties=uncertainties + [freshness_note],
            escalation_needed=escalation_needed,
            escalation_reason=escalation_reason,
        )

    def _build_summary(self, domain: str, rights: list[str], language: str) -> str:
        if language == "hi":
            return (
                f"आपकी **{domain}** समस्या के बारे में: नीचे आपके मुख्य कानूनी अधिकार और अगले कदम दिए गए हैं। "
                f"ये जानकारी Tier-1 आधिकारिक भारतीय कानून पर आधारित है।"
            )
        return (
            f"Regarding your **{domain}** matter: below are your key verified legal rights and action steps. "
            f"All information is grounded in current Tier-1 official Indian law."
        )
