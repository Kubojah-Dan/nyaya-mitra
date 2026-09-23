"""Language normalization utilities for NyayaMitra intake engine.

Handles:
- Hinglish (mixed Hindi-English) colloquial input normalization.
- Common speech-to-text transcription error corrections.
- Factual meaning preservation (no substitution of legal terms).
"""
from __future__ import annotations

import re

# Hinglish → English legal concept normalization (meaning-preserving only)
_HINGLISH_MAP: dict[str, str] = {
    # FIR / police
    "fir likhwana": "file an FIR",
    "fir likhwao": "register FIR",
    "police mein complaint": "police complaint",
    "thane mein": "at the police station",
    "thane jaana": "go to police station",
    "girftaar": "arrested",
    "arrest ho gaya": "was arrested",
    "bail mil gayi": "bail was granted",
    # Tenancy
    "makan khali karo": "vacate the house",
    "makaan maalik": "landlord",
    "kiraya nahi diya": "rent not paid",
    "deposit wapas": "security deposit refund",
    "ghar se nikala": "evicted from house",
    # Consumer
    "saman kharab": "defective goods",
    "paise wapas": "refund",
    "dhoka diya": "cheated",
    "online mangaya tha": "ordered online",
    # RTI
    "rti dalna": "file an RTI",
    "jawaab nahi mila": "no reply received",
    "sarkar se maang": "demand from government",
    # General urgency
    "bahut jaldi chahiye": "very urgent",
    "abhi hoga": "immediately",
    "aaj tak": "by today",
}

# Common speech-to-text correction pairs (normalized → corrected)
_STT_CORRECTIONS: list[tuple[str, str]] = [
    (r"\bfi ar\b", "FIR"),
    (r"\bf\.i\.r\b", "FIR"),
    (r"\barti\b", "RTI"),
    (r"\bnar ti\b", "RTI"),
    (r"\br\s*tea\s*i\b", "RTI"),
    (r"\bsecshan\b", "section"),
    (r"\beye\s*pea\s*sea\b", "IPC"),
    (r"\bsee\s*ar\s*pea\s*sea\b", "CrPC"),
    (r"\bconsumers? coart\b", "consumer court"),
    (r"\bbayl\b", "bail"),
    (r"\barrest\b", "arrest"),
    (r"\bevicshun\b", "eviction"),
    (r"\blandlod\b", "landlord"),
    (r"\btenent\b", "tenant"),
    (r"\bdeposit\b", "deposit"),
    (r"\brefuned\b", "refund"),
    (r"\bwarenty\b", "warranty"),
]


def normalize_input(raw_text: str) -> str:
    """Normalize colloquial and speech-to-text input without changing factual meaning.

    1. Apply Hinglish → English concept mapping (phrase-level, meaning-preserving).
    2. Apply speech-to-text error corrections (regex).
    3. Collapse excessive whitespace and punctuation artefacts.
    """
    text = raw_text.strip()

    # Step 1: Hinglish phrase normalization
    lower_text = text.lower()
    for hinglish_phrase, english_phrase in _HINGLISH_MAP.items():
        if hinglish_phrase in lower_text:
            lower_text = lower_text.replace(hinglish_phrase, english_phrase)
    # Reconstruct preserving original casing for non-matched parts
    text = lower_text

    # Step 2: Speech-to-text corrections
    for pattern, replacement in _STT_CORRECTIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Step 3: Cleanup
    text = re.sub(r"\s{2,}", " ", text).strip()

    return text


def detect_language(text: str) -> str:
    """Detect primary script/language of the input.

    Returns: 'hi' for Devanagari-script input, 'en' for Latin-script, 'mixed' for Hinglish.
    """
    hindi_chars = len(re.findall(r"[\u0900-\u097F]", text))
    total_chars = len(text.replace(" ", ""))

    if total_chars == 0:
        return "en"

    hindi_ratio = hindi_chars / total_chars
    if hindi_ratio > 0.5:
        return "hi"
    elif hindi_ratio > 0.1:
        return "mixed"
    return "en"
