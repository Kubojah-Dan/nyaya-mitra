"""Domain classifier for NyayaMitra intake engine.

Maps raw user input to one of the supported legal domains with a confidence
score and detected keyword evidence. Supports English and Hindi input,
including colloquial Hinglish (mixed Hindi-English).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DomainClassificationResult:
    primary_domain: str
    secondary_domain: Optional[str] = None
    confidence: float = 0.0
    rationale: str = ""
    detected_keywords: list[str] = field(default_factory=list)
    is_urgent: bool = False
    urgency_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Domain keyword catalogue (English + Hindi / Hinglish)
# ---------------------------------------------------------------------------
_DOMAIN_RULES: list[dict] = [
    {
        "domain": "TENANCY",
        "keywords_en": [
            "eviction", "evict", "tenant", "landlord", "rent", "lease",
            "notice to vacate", "vacate", "rental agreement", "deposit",
            "security deposit", "house rent", "flat rent", "rent arrears",
            "model tenancy", "rent control", "makan", "kiraya", "makaan",
            "property dispute",
        ],
        "keywords_hi": [
            "किराया", "मकान", "मकान मालिक", "किरायेदार", "खाली करो", "बेदखली",
            "जमा राशि", "किराये का समझौता",
        ],
    },
    {
        "domain": "CONSUMER",
        "keywords_en": [
            "defective product", "defective goods", "consumer complaint",
            "refund", "replacement", "warranty", "guarantee", "service deficiency",
            "e-commerce", "online purchase", "ecommerce", "cheating by seller",
            "overcharging", "medical negligence", "bank complaint", "insurance claim",
            "consumer forum", "consumer court", "e-daakhil", "ncdrc", "district commission",
            "flipkart", "amazon", "return reject", "sabun nikla", "order", "parcel", "delivery",
        ],
        "keywords_hi": [
            "खराब सामान", "धोखाधड़ी", "वापसी", "रिफंड", "वारंटी", "उपभोक्ता",
            "शिकायत", "बीमा", "बैंक", "ऑनलाइन खरीद", "फ्रिज", "खराब हो गया",
        ],
    },
    {
        "domain": "LEGAL_AID",
        "keywords_en": [
            "legal aid", "free lawyer", "free legal aid", "dlsa", "slsa", "nalsa",
            "section 12", "court lawyer", "free advocate", "government lawyer",
            "daily wage", "construction worker", "jail legal aid", "under trial",
            "undertrial", "tele-law",
        ],
        "keywords_hi": [
            "मुफ्त वकील", "सरकारी वकील", "कानूनी सहायता", "निःशुल्क", "डीएलएसए", "नालसा",
            "मुफ्त में मिलता है", "मुफ्त में वकील", "सरकारी वकील मुफ्त",
        ],
    },
    {
        "domain": "RTI",
        "keywords_en": [
            "rti", "right to information", "information act", "public information",
            "government record", "pio", "public information officer",
            "transparency", "government data", "cic", "information commission",
        ],
        "keywords_hi": [
            "सूचना का अधिकार", "आरटीआई", "सरकारी जानकारी", "सूचना आयोग",
        ],
    },
    {
        "domain": "CRIMINAL",
        "keywords_en": [
            "fir", "first information report", "police complaint", "arrest",
            "bail", "cheating", "fraud", "theft", "robbery", "assault",
            "harassment", "domestic violence", "criminal case", "bns",
            "ipc", "cognizable offence", "non-bailable", "custody",
            "magistrate", "charge sheet", "accused", "victim",
            "zero fir", "e-fir", "cybercrime", "online fraud",
        ],
        "keywords_hi": [
            "एफआईआर", "गिरफ्तारी", "जमानत", "धोखाधड़ी", "चोरी", "हमला",
            "पुलिस", "आरोपी", "पीड़ित", "साइबर क्राइम", "डोमेस्टिक वायलेंस",
        ],
    },
    {
        "domain": "CYBER",
        "keywords_en": [
            "cybercrime", "online fraud", "phishing", "hacking", "account hacked",
            "otp fraud", "upi fraud", "banking fraud", "identity theft",
            "social media harassment", "deepfake", "sextortion", "cyber cell",
        ],
        "keywords_hi": [
            "साइबर क्राइम", "ऑनलाइन धोखाधड़ी", "हैकिंग", "ओटीपी फ्रॉड",
        ],
    },
    {
        "domain": "LABOUR",
        "keywords_en": [
            "wrongful termination", "unfair dismissal", "salary not paid",
            "provident fund", "pf", "esic", "gratuity", "bonus",
            "employment", "labour court", "industrial tribunal",
            "workplace harassment", "retrenchment", "overtime",
        ],
        "keywords_hi": [
            "नौकरी", "वेतन", "बर्खास्तगी", "पीएफ", "ग्रेच्युटी", "श्रम न्यायालय",
        ],
    },
]

# Urgency triggers
_URGENCY_PATTERNS = [
    (r"\b(immediate arrest|arrest ho raha|gir\w* raha|police aa gayi)\b", "Immediate arrest or police enforcement threatened"),
    (r"\b(domestic violence|maar peet|beating|assault|attacked|jaan ka khatara)\b", "Physical violence or threat to life/safety"),
    (r"\b(tomorrow|kal|aaj|today|24 hours|48 hours|urgent|emergency|abhi)\b", "Extremely short deadline or urgent situation"),
    (r"\b(suicide|self harm|khatam kar)\b", "Mental health crisis or self-harm signal"),
    (r"\b(eviction.{0,20}tonight|tonight.{0,20}eviction|lock out|locked out)\b", "Imminent unlawful eviction"),
]


def classify_domain(user_input: str) -> DomainClassificationResult:
    """Classify the primary and secondary legal domain for a user query.

    Supports English, Hindi, and Hinglish input. Returns domain, confidence,
    keywords found, and urgency flags.
    """
    lower_input = user_input.lower()

    domain_scores: dict[str, float] = {}
    domain_keywords_found: dict[str, list[str]] = {}

    for rule in _DOMAIN_RULES:
        domain = rule["domain"]
        score = 0.0
        found: list[str] = []
        all_keywords = rule.get("keywords_en", []) + rule.get("keywords_hi", [])

        for kw in all_keywords:
            if kw.lower() in lower_input:
                score += 1.0
                found.append(kw)

        if score > 0:
            domain_scores[domain] = score
            domain_keywords_found[domain] = found

    if not domain_scores:
        return DomainClassificationResult(
            primary_domain="GENERAL",
            confidence=0.3,
            rationale="No specific legal domain keywords detected",
        )

    sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
    primary_domain, top_score = sorted_domains[0]
    secondary_domain = sorted_domains[1][0] if len(sorted_domains) > 1 else None

    # Confidence normalised: 1+ keyword hit = 0.6+, more hits give higher confidence
    confidence = min(0.6 + (top_score - 1) * 0.1, 0.98)

    # Urgency detection
    is_urgent = False
    urgency_reason = None
    for pattern, reason in _URGENCY_PATTERNS:
        if re.search(pattern, lower_input, re.IGNORECASE):
            is_urgent = True
            urgency_reason = reason
            break

    return DomainClassificationResult(
        primary_domain=primary_domain,
        secondary_domain=secondary_domain,
        confidence=confidence,
        rationale=f"Matched domain keywords: {', '.join(domain_keywords_found.get(primary_domain, []))}",
        detected_keywords=domain_keywords_found.get(primary_domain, []),
        is_urgent=is_urgent,
        urgency_reason=urgency_reason,
    )
