"""Guided Intake Engine — "Samjho Mera Problem" (Phase 5).

Implements a multi-turn state machine that:
1. Classifies the legal domain.
2. Identifies the minimum set of missing facts needed for a useful legal response.
3. Generates 3–5 high-value clarifying questions (skipping facts already stated).
4. Tracks confidence and urgency.
5. Produces a "Here's what I understood…" confirmation summary for user review.
6. Supports correction after summary confirmation and answers follow-up legal questions.
7. Persists minimum required state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Optional

from app.services.domain_classifier import DomainClassificationResult, classify_domain
from app.services.language_utils import detect_language, normalize_input
from app.services.rights_engine import RightsExplanationEngine


class IntakeStage(str, Enum):
    INITIAL = "INITIAL"
    DOMAIN_CLASSIFIED = "DOMAIN_CLASSIFIED"
    FACTS_GATHERING = "FACTS_GATHERING"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    CORRECTION_MODE = "CORRECTION_MODE"
    READY_FOR_ADVICE = "READY_FOR_ADVICE"
    ESCALATED = "ESCALATED"


# ---------------------------------------------------------------------------
# Domain-specific required facts catalogue
# ---------------------------------------------------------------------------
_REQUIRED_FACTS: dict[str, list[dict[str, str]]] = {
    "TENANCY": [
        {"key": "city_state", "question_en": "Which city or state is the property located in?", "question_hi": "संपत्ति किस शहर या राज्य में है?"},
        {"key": "notice_received", "question_en": "Have you received a written eviction or rent notice? If yes, what does it say?", "question_hi": "क्या आपको कोई लिखित नोटिस मिला है? अगर हाँ, तो उसमें क्या लिखा है?"},
        {"key": "rent_agreement", "question_en": "Do you have a registered or written rent agreement?", "question_hi": "क्या आपके पास कोई लिखित किराया समझौता है?"},
        {"key": "rent_paid", "question_en": "Are rent payments up to date, and do you have receipts or bank transfer proofs?", "question_hi": "क्या किराये का भुगतान नियमित है? क्या आपके पास रसीद या बैंक ट्रांसफर का प्रमाण है?"},
        {"key": "deposit_amount", "question_en": "What is the security deposit amount, and was it paid?", "question_hi": "सुरक्षा जमा राशि कितनी है और क्या वह दी गई थी?"},
    ],
    "CONSUMER": [
        {"key": "purchase_platform", "question_en": "Where did you buy the product or service — online or from a shop?", "question_hi": "आपने यह सामान या सेवा कहाँ से खरीदी — ऑनलाइन या दुकान से?"},
        {"key": "purchase_date", "question_en": "On what date did you make the purchase?", "question_hi": "आपने कब यह खरीदारी की?"},
        {"key": "defect_description", "question_en": "Describe the exact defect or problem you experienced.", "question_hi": "आप जो खराबी या समस्या हुई उसे विस्तार से बताइए।"},
        {"key": "complained_to_seller", "question_en": "Have you already complained to the seller or company? What response did you receive?", "question_hi": "क्या आपने विक्रेता या कंपनी में पहले शिकायत की थी? क्या जवाब मिला?"},
        {"key": "amount_paid", "question_en": "What was the total amount you paid for the product or service?", "question_hi": "आपने कुल कितना भुगतान किया?"},
    ],
    "RTI": [
        {"key": "public_authority", "question_en": "Which government department or public authority do you want information from?", "question_hi": "आप किस सरकारी विभाग से जानकारी माँगना चाहते हैं?"},
        {"key": "information_type", "question_en": "What specific records or documents are you seeking?", "question_hi": "आप कौन से खास दस्तावेज़ या जानकारी माँगना चाहते हैं?"},
        {"key": "rti_filed_before", "question_en": "Have you already filed an RTI application? If yes, when and did you receive a reply?", "question_hi": "क्या आपने पहले से आरटीआई दर्ज की है? अगर हाँ, तो कब और क्या जवाब मिला?"},
        {"key": "state_or_central", "question_en": "Is this a central government authority or a state government authority?", "question_hi": "क्या यह केंद्र सरकार का विभाग है या राज्य सरकार का?"},
    ],
    "CRIMINAL": [
        {"key": "incident_description", "question_en": "Briefly describe what happened — the incident, when, and where.", "question_hi": "संक्षेप में बताइए कि क्या हुआ, कब और कहाँ।"},
        {"key": "fir_registered", "question_en": "Has an FIR been registered? If yes, at which police station and what is the FIR number?", "question_hi": "क्या एफआईआर दर्ज हुई है? अगर हाँ, तो किस थाने में और एफआईआर नंबर क्या है?"},
        {"key": "are_you_victim_or_accused", "question_en": "Are you the victim/complainant or the accused person?", "question_hi": "क्या आप पीड़ित/शिकायतकर्ता हैं या आरोपी हैं?"},
        {"key": "arrested", "question_en": "Has anyone been arrested? Are you currently in custody or facing immediate arrest?", "question_hi": "क्या कोई गिरफ्तार हुआ है? क्या आप अभी हिरासत में हैं या गिरफ्तारी की तत्काल आशंका है?"},
        {"key": "state_of_incident", "question_en": "In which state did the incident take place?", "question_hi": "घटना किस राज्य में हुई?"},
    ],
    "CYBER": [
        {"key": "incident_type", "question_en": "What type of cybercrime occurred — OTP fraud, account hacking, sextortion, or other?", "question_hi": "किस प्रकार का साइबर क्राइम हुआ — ओटीपी फ्रॉड, अकाउंट हैकिंग, या कुछ और?"},
        {"key": "amount_lost", "question_en": "Did you lose any money? If yes, approximately how much?", "question_hi": "क्या कोई राशि गई है? अगर हाँ, तो लगभग कितनी?"},
        {"key": "reported_to_cybercell", "question_en": "Have you already reported this to the cyber cell or helpline 1930?", "question_hi": "क्या आपने पहले से साइबर सेल या हेल्पलाइन 1930 में शिकायत की है?"},
        {"key": "state", "question_en": "Which state are you located in?", "question_hi": "आप किस राज्य में हैं?"},
    ],
    "LABOUR": [
        {"key": "employment_type", "question_en": "Were you a permanent employee, contract worker, or daily-wage worker?", "question_hi": "क्या आप स्थायी कर्मचारी थे, ठेका मजदूर, या दिहाड़ी मजदूर?"},
        {"key": "termination_reason", "question_en": "What reason was given for termination or non-payment?", "question_hi": "बर्खास्तगी या वेतन न देने का क्या कारण बताया गया?"},
        {"key": "duration_worked", "question_en": "How long did you work at this organization?", "question_hi": "आपने इस संस्थान में कितने समय तक काम किया?"},
        {"key": "dues_amount", "question_en": "What is the approximate amount of dues (salary/PF/gratuity/bonus) owed to you?", "question_hi": "आपका लगभग कितना बकाया है (वेतन/पीएफ/ग्रेच्युटी/बोनस)?"},
    ],
    "GENERAL": [
        {"key": "problem_description", "question_en": "Please describe your legal problem in as much detail as possible.", "question_hi": "कृपया अपनी कानूनी समस्या के बारे में जितना हो सके विस्तार से बताएं।"},
        {"key": "state", "question_en": "Which state are you located in?", "question_hi": "आप किस राज्य में हैं?"},
        {"key": "timeline", "question_en": "When did this problem start and what has happened so far?", "question_hi": "यह समस्या कब शुरू हुई और अब तक क्या हुआ है?"},
    ],
}

# Urgency escalation messages
_URGENCY_MESSAGES = {
    "en": (
        "⚠️ **Urgent Situation Detected.** Based on what you've described, this may require "
        "immediate legal assistance. Please call the **NALSA National Legal Aid Helpline: 15100** "
        "(free, 24×7). We will also continue helping you here."
    ),
    "hi": (
        "⚠️ **जरूरी स्थिति पहचानी गई।** आपकी बात से लगता है कि आपको तत्काल कानूनी सहायता की "
        "जरूरत है। कृपया **NALSA राष्ट्रीय कानूनी सहायता हेल्पलाइन: 15100** पर कॉल करें "
        "(निःशुल्क, 24×7)। हम यहाँ भी आपकी सहायता जारी रखेंगे।"
    ),
}


@dataclass
class IntakeTurn:
    """A single turn of the intake conversation."""
    role: str  # "user" | "system"
    content: str
    facts_extracted: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntakeSession:
    """Full multi-turn intake state, minimally stored."""
    session_id: str
    stage: IntakeStage = IntakeStage.INITIAL
    language: str = "en"
    domain: str = "GENERAL"
    domain_confidence: float = 0.0
    collected_facts: dict[str, Any] = field(default_factory=dict)
    missing_fact_keys: list[str] = field(default_factory=list)
    turns: list[IntakeTurn] = field(default_factory=list)
    is_urgent: bool = False
    urgency_reason: Optional[str] = None
    pending_question_keys: list[str] = field(default_factory=list)
    questions_asked: list[str] = field(default_factory=list)
    confirmed: bool = False


class GuidedIntakeEngine:
    """Guided intake engine implementing the "Samjho Mera Problem" flow.

    State machine transitions:
    INITIAL → DOMAIN_CLASSIFIED → FACTS_GATHERING
            → AWAITING_CONFIRMATION → READY_FOR_ADVICE
            (optionally → CORRECTION_MODE → AWAITING_CONFIRMATION)
            (urgency → ESCALATED at any point)
    """

    MAX_QUESTIONS_PER_TURN = 2  # Ask at most 2 at once to avoid overwhelming users

    def __init__(self, session_id: str) -> None:
        self.state = IntakeSession(session_id=session_id)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_turn(self, user_input: str) -> dict[str, Any]:
        """Process a single user turn and return the engine's response."""
        normalized = normalize_input(user_input)
        lang = detect_language(user_input)
        if self.state.stage == IntakeStage.INITIAL:
            self.state.language = lang

        self.state.turns.append(IntakeTurn(role="user", content=user_input))

        # Check for urgency at every turn
        classification = classify_domain(normalized)
        if classification.is_urgent and not self.state.is_urgent:
            self.state.is_urgent = True
            self.state.urgency_reason = classification.urgency_reason

        # Route to appropriate handler
        if self.state.stage == IntakeStage.INITIAL:
            return self._handle_initial(normalized, classification)
        elif self.state.stage == IntakeStage.DOMAIN_CLASSIFIED:
            return self._handle_domain_classified(normalized)
        elif self.state.stage == IntakeStage.FACTS_GATHERING:
            return self._handle_facts_gathering(normalized, user_input)
        elif self.state.stage == IntakeStage.AWAITING_CONFIRMATION:
            return self._handle_confirmation(normalized, user_input)
        elif self.state.stage == IntakeStage.CORRECTION_MODE:
            return self._handle_correction(normalized, user_input)
        elif self.state.stage == IntakeStage.READY_FOR_ADVICE:
            return self._handle_ready_for_advice(normalized, user_input)
        else:
            return self._handle_ready_for_advice(normalized, user_input)

    def get_current_state(self) -> dict[str, Any]:
        """Return a serializable snapshot of the current intake state."""
        return {
            "session_id": self.state.session_id,
            "stage": self.state.stage.value,
            "language": self.state.language,
            "domain": self.state.domain,
            "domain_confidence": self.state.domain_confidence,
            "collected_facts": self.state.collected_facts,
            "missing_fact_keys": self.state.missing_fact_keys,
            "is_urgent": self.state.is_urgent,
            "urgency_reason": self.state.urgency_reason,
            "confirmed": self.state.confirmed,
        }

    # ------------------------------------------------------------------
    # Stage handlers
    # ------------------------------------------------------------------

    def _handle_initial(self, normalized: str, classification: DomainClassificationResult) -> dict[str, Any]:
        self.state.domain = classification.primary_domain
        self.state.domain_confidence = classification.confidence
        self.state.stage = IntakeStage.DOMAIN_CLASSIFIED

        # Extract any facts already provided in the opening message
        self._extract_implicit_facts(normalized)

        # Build missing fact list
        required = _REQUIRED_FACTS.get(self.state.domain, _REQUIRED_FACTS["GENERAL"])
        self.state.missing_fact_keys = [
            r["key"] for r in required if r["key"] not in self.state.collected_facts
        ]
        self.state.pending_question_keys = self.state.missing_fact_keys.copy()
        self.state.stage = IntakeStage.FACTS_GATHERING

        questions = self._pick_next_questions()
        response_lines = self._build_understanding_preamble()
        response_lines.extend(questions)

        msg = "\n\n".join(response_lines)
        self.state.turns.append(IntakeTurn(role="system", content=msg))
        return self._format_response(msg, questions, urgent=self.state.is_urgent)

    def _handle_domain_classified(self, normalized: str) -> dict[str, Any]:
        return self._handle_facts_gathering(normalized, normalized)

    def _handle_facts_gathering(self, normalized: str, original: str) -> dict[str, Any]:
        lower = normalized.lower()

        # 1. Check if user is asking a legal question or requesting advice directly
        is_legal_question = (
            "?" in original or
            any(w in lower for w in [
                "what", "how", "can i", "why", "who", "kya", "kaise", "kab", "rights", "rule",
                "law", "dhara", "section", "refund", "time", "notice", "limitation", "edaakhil", "process"
            ])
        )

        # 2. Extract facts from this turn
        facts_before = set(self.state.collected_facts.keys())
        self._extract_implicit_facts(normalized)
        new_facts = set(self.state.collected_facts.keys()) - facts_before

        # 3. If user provided conversational answers that weren't caught by regex, map to pending slots
        if not new_facts and self.state.pending_question_keys and len(original.strip()) > 2 and not is_legal_question:
            # Map up to 2 pending keys to the user's response
            assigned_key = self.state.pending_question_keys[0]
            clean_val = original.strip().replace("\n", " ")[:80]
            self.state.collected_facts[assigned_key] = clean_val
            new_facts.add(assigned_key)

        # Remove answered keys from pending list
        self.state.pending_question_keys = [
            k for k in self.state.pending_question_keys
            if k not in self.state.collected_facts
        ]

        # 4. If user asked a direct question, answer it immediately
        if is_legal_question:
            advice = self._generate_direct_advice(lower, original)
            if self.state.pending_question_keys and len(self.state.collected_facts) < 2:
                next_q = self._pick_next_questions()
                if next_q:
                    advice += "\n\n" + ("To give you specific deadlines, please tell me:" if self.state.language == "en" else "सटीक समयसीमा बताने के लिए कृपया यह भी बताएं:") + "\n\n" + "\n\n".join(next_q)
                    self.state.turns.append(IntakeTurn(role="system", content=advice))
                    return self._format_response(advice, next_q, urgent=self.state.is_urgent)

            self.state.turns.append(IntakeTurn(role="system", content=advice))
            return self._format_response(advice, [], stage=self.state.stage.value, urgent=self.state.is_urgent)

        # 5. If all facts gathered (or 3+ key facts present), move to confirmation summary
        if not self.state.pending_question_keys or len(self.state.collected_facts) >= 3:
            self.state.stage = IntakeStage.AWAITING_CONFIRMATION
            summary = self._build_confirmation_summary()
            self.state.turns.append(IntakeTurn(role="system", content=summary))
            return self._format_response(summary, [], stage="AWAITING_CONFIRMATION", urgent=self.state.is_urgent)

        # 6. Otherwise acknowledge recorded facts and present next question(s)
        questions = self._pick_next_questions()
        ack = (
            "Got it! I have recorded your details.\n\n"
            if self.state.language == "en"
            else "समझ गया! मैंने यह जानकारी दर्ज कर ली है।\n\n"
        )
        msg = ack + "\n\n".join(questions)
        self.state.turns.append(IntakeTurn(role="system", content=msg))
        return self._format_response(msg, questions, urgent=self.state.is_urgent)

    def _handle_confirmation(self, normalized: str, original: str) -> dict[str, Any]:
        lower = normalized.lower()

        # Word-boundary matching to avoid "not correct" matching "correct"
        positive_confirms = [r"\byes\b", r"\bhaan\b", r"\bha\b", r"\btheek\b", r"\bsahi\b",
                             r"\bconfirm\b", r"\bok\b", r"\bokay\b", r"\bright\b", r"\bcorrect\b"]
        correction_signals = [r"\bno\b", r"\bnahi\b", r"\bwrong\b", r"\bincorrect\b",
                              r"\bchange\b", r"not right", r"not correct"]

        is_positive = any(bool(re.search(p, lower)) for p in positive_confirms)
        is_correction = any(bool(re.search(p, lower)) for p in correction_signals)

        # Negation detection — "not correct/right" overrides positive
        has_negation = bool(re.search(r"\bnot?\s+(correct|right|true|accurate)\b", lower))
        if has_negation:
            is_positive = False
            is_correction = True

        if is_positive and not is_correction:
            self.state.confirmed = True
            self.state.stage = IntakeStage.READY_FOR_ADVICE
            advice = self._generate_direct_advice(lower, original)
            msg = (
                ("✅ **Details Confirmed!**\n\n" + advice)
                if self.state.language == "en"
                else ("✅ **विवरण की पुष्टि हुई!**\n\n" + advice)
            )
        elif is_correction:
            self.state.stage = IntakeStage.CORRECTION_MODE
            msg = (
                "No problem! Please tell me which detail is incorrect (e.g. amount, date, or platform) and I'll update it immediately."
                if self.state.language == "en"
                else "कोई बात नहीं! कृपया बताएं कि कौन सा विवरण गलत है और मैं उसे तुरंत अपडेट कर दूँगा।"
            )
        else:
            # Check if user asked a follow-up question
            advice = self._generate_direct_advice(lower, original)
            msg = advice

        self.state.turns.append(IntakeTurn(role="system", content=msg))
        return self._format_response(msg, [], stage=self.state.stage.value, urgent=self.state.is_urgent)

    def _handle_correction(self, normalized: str, original: str) -> dict[str, Any]:
        # Accept correction as a fact update
        self._extract_implicit_facts(normalized)
        # Re-check missing facts
        required = _REQUIRED_FACTS.get(self.state.domain, _REQUIRED_FACTS["GENERAL"])
        self.state.missing_fact_keys = [
            r["key"] for r in required if r["key"] not in self.state.collected_facts
        ]
        self.state.stage = IntakeStage.AWAITING_CONFIRMATION
        summary = self._build_confirmation_summary()
        self.state.turns.append(IntakeTurn(role="system", content=summary))
        return self._format_response(summary, [], stage="AWAITING_CONFIRMATION", urgent=self.state.is_urgent)

    def _handle_ready_for_advice(self, normalized: str, original: str) -> dict[str, Any]:
        lower = normalized.lower()
        advice = self._generate_direct_advice(lower, original)
        self.state.turns.append(IntakeTurn(role="system", content=advice))
        return self._format_response(advice, [], stage=self.state.stage.value, urgent=self.state.is_urgent)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_implicit_facts(self, text: str) -> None:
        """Heuristic fact extraction from free text — marks facts as collected."""
        lower = text.lower()
        domain = self.state.domain

        # --- Universal Amount Extraction ---
        amt_match = re.search(r"(?:rs\.?|inr|₹|amount\s+of\s+rs\.?)\s*([\d,]+)", lower)
        if amt_match:
            num = amt_match.group(1).replace(",", "")
            self.state.collected_facts["amount_paid"] = f"₹{int(num):,}"
        elif any(w in lower for w in ["₹", "rs", "rupee", "thousand", "lakh"]):
            num_match = re.search(r"\b(\d{3,7})\b", lower)
            if num_match:
                self.state.collected_facts["amount_paid"] = f"₹{int(num_match.group(1)):,}"

        # --- Universal Date Extraction ---
        date_patterns = [
            r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+\d{4})?)\b",
            r"\b((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)\b",
            r"\b(yesterday|last\s+week|last\s+month|\d+\s+days?\s+ago|\d+\s+months?\s+ago)\b",
        ]
        for dp in date_patterns:
            dm = re.search(dp, lower)
            if dm:
                self.state.collected_facts["purchase_date"] = dm.group(1).title()
                break

        # --- Domain-Specific Extractions ---
        if domain in ("CONSUMER", "CYBER"):
            # Purchase Platform
            if any(p in lower for p in ["flipkart", "amazon", "meesho", "myntra", "online", "website", "app", "ecommerce", "e-commerce"]):
                platform_name = "Online"
                for brand in ["Flipkart", "Amazon", "Meesho", "Myntra", "Swiggy", "Zomato", "Blinkit", "Zepto"]:
                    if brand.lower() in lower:
                        platform_name = f"Online ({brand})"
                        break
                self.state.collected_facts["purchase_platform"] = platform_name
            elif any(p in lower for p in ["shop", "store", "showroom", "dealer", "retailer", "market", "offline", "dukaan"]):
                self.state.collected_facts["purchase_platform"] = "Local Retail Shop / Offline"

            # Defect Description
            if any(w in lower for w in ["broken", "defective", "defect", "compressor", "damaged", "leak", "not working", "faulty", "poor quality", "substandard"]):
                if "compressor" in lower or "refrigerator" in lower or "fridge" in lower:
                    self.state.collected_facts["defect_description"] = "Broken compressor / cooling failure"
                else:
                    self.state.collected_facts["defect_description"] = "Defective unit / non-functional product"

            # Complaint Status
            if any(w in lower for w in ["refusing", "refused", "no reply", "no response", "complained", "customer care", "denied", "rejected"]):
                self.state.collected_facts["complained_to_seller"] = "Complained to seller (refused replacement/refund)"

        elif domain == "TENANCY":
            if any(w in lower for w in ["written", "agreement", "lease", "contract", "samjhota"]):
                self.state.collected_facts["rent_agreement"] = "Written tenancy agreement exists"
            elif any(w in lower for w in ["oral", "verbal", "no agreement", "bina agreement"]):
                self.state.collected_facts["rent_agreement"] = "Oral/Verbal tenancy (no formal contract)"

            if any(w in lower for w in ["receipt", "bank", "transfer", "upi", "paid", "payment", "on time"]):
                self.state.collected_facts["rent_paid"] = "Rent paid on time / receipts or UPI proof available"

            if any(w in lower for w in ["15 days", "notice", "eviction notice", "whatsapp", "notic"]):
                self.state.collected_facts["notice_received"] = "Eviction notice received"

            if "deposit" in lower or "security" in lower:
                self.state.collected_facts["deposit_amount"] = "Security deposit paid"

        elif domain == "RTI":
            if any(w in lower for w in ["municipality", "municipal", "mcd", "police", "pwd", "railway", "board", "university", "department"]):
                for auth in ["Municipal Corporation", "Police Department", "PWD", "Railways", "Education Board"]:
                    if auth.lower() in lower:
                        self.state.collected_facts["public_authority"] = auth
                        break
                self.state.collected_facts.setdefault("public_authority", "Public Authority / Department")

            if any(w in lower for w in ["road", "tender", "fund", "repair", "marksheet", "exam", "file", "status"]):
                self.state.collected_facts["information_type"] = "Official records / tender & fund utilization records"

            if any(w in lower for w in ["filed", "applied", "already", "days ago"]):
                self.state.collected_facts["rti_filed_before"] = "RTI application previously submitted"
            elif any(w in lower for w in ["first time", "want to file", "how to file"]):
                self.state.collected_facts["rti_filed_before"] = "First time filing"

        elif domain == "CRIMINAL":
            if any(w in lower for w in ["fir", "f.i.r", "registered", "darj"]):
                self.state.collected_facts["fir_registered"] = "FIR registered"
            elif any(w in lower for w in ["refused", "no fir", "not registered"]):
                self.state.collected_facts["fir_registered"] = "FIR not yet registered by police"

            if any(w in lower for w in ["victim", "pidit", "complainant", "shikayatkarta"]):
                self.state.collected_facts["are_you_victim_or_accused"] = "Victim / Complainant"
            elif any(w in lower for w in ["accused", "aaropit", "suspect", "calling me", "notice"]):
                self.state.collected_facts["are_you_victim_or_accused"] = "Accused / Person of Interest"

            if any(w in lower for w in ["arrest", "custody", "jail", "lockup", "police station"]):
                self.state.collected_facts["arrested"] = "Threat of arrest or police inquiry"

        # State / city extraction (with strict word-boundary matching)
        indian_states = [
            ("delhi", "Delhi"),
            ("mumbai", "Mumbai, Maharashtra"),
            ("maharashtra", "Maharashtra"),
            ("karnataka", "Karnataka"),
            ("bengaluru", "Bengaluru, Karnataka"),
            ("uttar pradesh", "Uttar Pradesh"),
            ("rajasthan", "Rajasthan"),
            ("gujarat", "Gujarat"),
            ("hyderabad", "Hyderabad, Telangana"),
            ("telangana", "Telangana"),
            ("tamil nadu", "Tamil Nadu"),
            ("chennai", "Chennai, Tamil Nadu"),
            ("kolkata", "Kolkata, West Bengal"),
            ("west bengal", "West Bengal"),
            ("punjab", "Punjab"),
            ("haryana", "Haryana"),
            ("bihar", "Bihar"),
            ("jharkhand", "Jharkhand"),
            ("madhya pradesh", "Madhya Pradesh"),
        ]
        for pattern, full_name in indian_states:
            if re.search(r"\b" + re.escape(pattern) + r"\b", lower):
                self.state.collected_facts.setdefault("city_state", full_name)
                self.state.collected_facts.setdefault("state", full_name)
                break

    def _generate_direct_advice(self, lower_text: str, original_text: str) -> str:
        """Generate direct, grounded statutory advice in response to user questions or upon confirmation."""
        domain = self.state.domain
        lang = self.state.language

        # Call the verified Rights Engine for comprehensive legal grounding
        rights_engine = RightsExplanationEngine()
        rights_resp = rights_engine.explain_rights(
            domain=domain,
            collected_facts=self.state.collected_facts,
            language=lang,
        )

        statutory_summary = ""
        if rights_resp.statutory_rights:
            statutory_summary = "\n".join(
                f"• **{r.right_name}** ({r.statutory_basis}): {r.description}"
                for r in rights_resp.statutory_rights[:3]
            )
        elif rights_resp.rights:
            statutory_summary = "\n".join(f"• {r}" for r in rights_resp.rights[:3])

        steps_summary = "\n".join(
            f"{step}" for step in (rights_resp.practical_steps or rights_resp.next_steps)[:4]
        )

        if lang == "hi":
            advice = (
                f"⚖️ **कानूनी विश्लेषण ({domain}):**\n\n"
                f"{statutory_summary}\n\n"
                f"📌 **आपके लिए अगले कदम:**\n"
                f"{steps_summary}\n\n"
                f"💡 **सुझाव:** आप ऊपर दिए गए **'Mere Adhikaar' (मेरे अधिकार)** टैब पर क्लिक करके पूरी समयसीमा देख सकते हैं, या **'Mera Document'** से तुरंत कानूनी नोटिस तैयार कर सकते हैं।"
            )
        else:
            advice = (
                f"⚖️ **Legal Analysis & Your Statutory Rights ({domain}):**\n\n"
                f"{statutory_summary}\n\n"
                f"📌 **Recommended Action Steps:**\n"
                f"{steps_summary}\n\n"
                f"💡 **Next Step:** You can view full limitation rules in the **'Mere Adhikaar (Rights & Timelines)'** tab, or draft a formal legal demand notice using the **'Mera Document'** tab."
            )

        return advice

    def _pick_next_questions(self) -> list[str]:
        """Pick the next batch of at most MAX_QUESTIONS_PER_TURN questions."""
        required = _REQUIRED_FACTS.get(self.state.domain, _REQUIRED_FACTS["GENERAL"])
        key_to_question = {r["key"]: r for r in required}

        questions: list[str] = []
        for key in self.state.pending_question_keys:
            if len(questions) >= self.MAX_QUESTIONS_PER_TURN:
                break
            if key in self.state.collected_facts:
                continue
            rule = key_to_question.get(key)
            if rule:
                q = rule["question_hi"] if self.state.language == "hi" else rule["question_en"]
                questions.append(f"• {q}")
                self.state.questions_asked.append(key)

        return questions

    def _build_understanding_preamble(self) -> list[str]:
        """Build the 'Here's what I understood' opening block."""
        if self.state.language == "hi":
            parts = [
                f"🤔 **मैंने यह समझा:**\n"
                f"— विषय: **{self.state.domain}** (विश्वास: {int(self.state.domain_confidence * 100)}%)"
            ]
            if self.state.collected_facts:
                for k, v in self.state.collected_facts.items():
                    parts.append(f"— {k}: {v}")
            parts.append("\nकुछ और जानकारी चाहिए:")
        else:
            parts = [
                f"🤔 **Here's what I understood:**\n"
                f"— Topic: **{self.state.domain}** (confidence: {int(self.state.domain_confidence * 100)}%)"
            ]
            if self.state.collected_facts:
                for k, v in self.state.collected_facts.items():
                    parts.append(f"— {k}: {v}")
            parts.append("\nI need a few more details:")

        if self.state.is_urgent:
            parts.insert(0, _URGENCY_MESSAGES.get(self.state.language, _URGENCY_MESSAGES["en"]))

        return parts

    def _build_confirmation_summary(self) -> str:
        """Build the 'Here's what I understood' confirmation message."""
        lang = self.state.language
        facts_text = "\n".join(
            f"  — {k.replace('_', ' ').title()}: {v}" for k, v in self.state.collected_facts.items()
        )

        if lang == "hi":
            summary = (
                f"📋 **यह है जो मैंने समझा — कृपया पुष्टि करें:**\n\n"
                f"**विषय:** {self.state.domain}\n"
                f"{facts_text}\n\n"
                "क्या यह विवरण सही है? (हाँ / नहीं — या कोई भी कानूनी सवाल पूछें)"
            )
        else:
            summary = (
                f"📋 **Here's what I understood — please confirm:**\n\n"
                f"**Topic:** {self.state.domain}\n"
                f"{facts_text}\n\n"
                "Is this correct? (Yes / No — or ask any legal question to proceed)"
            )

        if self.state.is_urgent:
            summary = _URGENCY_MESSAGES.get(lang, _URGENCY_MESSAGES["en"]) + "\n\n" + summary

        return summary

    def _format_response(
        self,
        message: str,
        questions: list[str],
        stage: Optional[str] = None,
        urgent: bool = False,
    ) -> dict[str, Any]:
        return {
            "message": message,
            "bot_response": message,
            "session_id": self.state.session_id,
            "stage": stage or self.state.stage.value,
            "domain": self.state.domain,
            "domain_confidence": self.state.domain_confidence,
            "collected_facts": dict(self.state.collected_facts),
            "pending_questions": questions,
            "next_questions": questions,
            "is_urgent": urgent,
            "urgency_reason": self.state.urgency_reason,
            "language": self.state.language,
            "confirmed": self.state.confirmed,
            "can_generate_document": self.state.stage in (IntakeStage.AWAITING_CONFIRMATION, IntakeStage.READY_FOR_ADVICE),
        }
