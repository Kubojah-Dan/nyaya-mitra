"""
NyayaMitra Prompt Injection & Jailbreak Defense Service
Scans input queries, messages, and uploaded text for adversarial manipulation,
system prompt extraction, roleplay escapes, and citation spoofing.
"""

from datetime import datetime, timezone
import logging
import re
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger("nyayamitra.prompt_guard")


class PromptSafetyResult(BaseModel):
    is_safe: bool
    risk_level: str  # SAFE, LOW, MEDIUM, HIGH, CRITICAL
    detected_patterns: list[str] = Field(default_factory=list)
    sanitized_text: str
    remediation_action: str  # ALLOW, SANITIZE, BLOCK
    explanation: str
    timestamp: str


class PromptGuardService:
    """Detects and mitigates prompt injection attacks, jailbreaks, and adversarial overrides."""

    INJECTION_SIGNATURES = [
        # 1. System Prompt Overrides & Instruction Reset
        (r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|directions|rules|prompts)", "SYSTEM_OVERRIDE_IGNORE_INSTRUCTIONS"),
        (r"disregard\s+(?:all\s+)?(?:previous|prior|system)\s+(?:rules|instructions|constraints)", "SYSTEM_OVERRIDE_DISREGARD_RULES"),
        (r"forget\s+(?:all\s+)?(?:previous|prior|everything)?\s*(?:safety\s+)?(?:rules|instructions|prompts|you\s+were\s+told)", "SYSTEM_OVERRIDE_FORGET"),
        (r"override\s+(?:system|safety|security)\s+(?:prompt|instructions|settings)", "SYSTEM_OVERRIDE_EXPLICIT"),
        (r"system\s+(?:directive|instruction|command)\s*:", "SYSTEM_DIRECTIVE_INJECTION"),
        
        # 2. Jailbreak Modes & Roleplay Escapes
        (r"\b(?:dan\s+mode|developer\s+mode\s+enabled|jailbreak\s+mode|unrestricted\s+mode)\b", "JAILBREAK_MODE_TRIGGER"),
        (r"pretend\s+(?:you\s+are|to\s+be)\s+(?:an?\s+)?(?:unfiltered|unrestricted|evil|rogue|godmode|ai\s+without)", "ROLEPLAY_ESCAPE_ATTEMPT"),
        (r"act\s+as\s+(?:an?\s+)?(?:evil|unrestricted|lawless|dark)\s+(?:lawyer|ai|assistant)", "ROLEPLAY_MALICIOUS_PERSONA"),
        (r"you\s+are\s+no\s+longer\s+(?:bound\s+by|restricted\s+by|an\s+ai|nyayamitra)", "RESTRICTION_REMOVAL_ATTEMPT"),
        (r"without\s+(?:ethical|safety|legal)\s+(?:boundaries|guidelines|restrictions|rules)", "SAFETY_BYPASS_ATTEMPT"),
        
        # 3. Delimiter Injection & Special Tokens
        (r"<\s*\|\s*(?:im_start|im_end|system|user|assistant)\s*\|\s*>", "SPECIAL_TOKEN_DELIMITER_INJECTION"),
        (r"\[\s*\/?(?:INST|SYS|SYSTEM)\s*\]", "SPECIAL_TOKEN_BRACKET_INJECTION"),
        (r"---+\s*(?:BEGIN|START)\s+(?:SYSTEM|PROMPT|INSTRUCTIONS|SYSTEM\s+INSTRUCTIONS)\s*---+", "DELIMITER_HEADER_INJECTION"),
        (r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "SCRIPT_CODE_INJECTION"),
        (r"os\.system\s*\(|subprocess\.Popen\s*\(|rm\s+-rf", "COMMAND_EXECUTION_INJECTION"),
        
        # 4. System Prompt Exfiltration
        (r"(?:print|output|show|reveal|display|leak)\s+(?:your\s+)?(?:system\s+prompt|initial\s+instructions|hidden\s+rules|developer\s+prompt|database\s+connection)", "PROMPT_EXFILTRATION_ATTEMPT"),
        (r"what\s+(?:are|were)\s+your\s+(?:exact\s+)?(?:initial\s+instructions|system\s+prompt)", "PROMPT_EXFILTRATION_QUERY"),
        
        # 5. Citation Spoofing & Statutory Poisoning
        (r"pretend\s+the\s+law\s+says\s+(?:murder|theft|violence)\s+is\s+(?:legal|permitted|allowed)", "STATUTE_POISONING_ATTEMPT"),
        (r"cite\s+(?:fake|fictitious|made[- ]up)\s+(?:section|act|law)", "CITATION_FABRICATION_REQUEST"),
    ]

    @classmethod
    def scan_text(cls, text: str) -> PromptSafetyResult:
        """Alias for analyze_prompt."""
        return cls.analyze_prompt(text)

    @classmethod
    def scan_prompt(cls, text: str) -> PromptSafetyResult:
        """Alias for analyze_prompt."""
        return cls.analyze_prompt(text)

    @classmethod
    def analyze_prompt(cls, text: str) -> PromptSafetyResult:
        """
        Evaluates input text for injection risks and recommends safe remediation.
        """
        if not text or not text.strip():
            now_iso = datetime.now(timezone.utc).isoformat()
            return PromptSafetyResult(
                is_safe=True,
                risk_level="SAFE",
                detected_patterns=[],
                sanitized_text="",
                remediation_action="ALLOW",
                explanation="Input is empty or whitespace.",
                timestamp=now_iso,
            )

        detected = []
        text_lower = text.lower()

        for pattern, sig_name in cls.INJECTION_SIGNATURES:
            if re.search(pattern, text_lower, re.IGNORECASE):
                detected.append(sig_name)

        now_iso = datetime.now(timezone.utc).isoformat()

        if not detected:
            return PromptSafetyResult(
                is_safe=True,
                risk_level="SAFE",
                detected_patterns=[],
                sanitized_text=text,
                remediation_action="ALLOW",
                explanation="No adversarial prompt injection patterns detected.",
                timestamp=now_iso,
            )

        # Risk classification
        critical_sigs = {"JAILBREAK_MODE_TRIGGER", "SPECIAL_TOKEN_DELIMITER_INJECTION", "SYSTEM_OVERRIDE_IGNORE_INSTRUCTIONS"}
        has_critical = any(d in critical_sigs for d in detected)

        if has_critical or len(detected) >= 2:
            risk_level = "CRITICAL" if has_critical else "HIGH"
            action = "BLOCK"
            explanation = f"High-risk prompt injection detected ({', '.join(detected)}). Request blocked for safety."
            sanitized = "[ADVERSARIAL_CONTENT_REDACTED]"
        else:
            risk_level = "MEDIUM"
            action = "SANITIZE"
            explanation = f"Potential prompt manipulation detected ({', '.join(detected)}). Content sanitized."
            sanitized = cls._sanitize_text(text)

        logger.warning(
            f"PromptGuard Flagged: risk={risk_level} action={action} signatures={detected}"
        )

        return PromptSafetyResult(
            is_safe=False,
            risk_level=risk_level,
            detected_patterns=detected,
            sanitized_text=sanitized,
            remediation_action=action,
            explanation=explanation,
            timestamp=now_iso,
        )

    @classmethod
    def _sanitize_text(cls, text: str) -> str:
        """Neutralizes injection attempts while preserving standard legal queries."""
        cleaned = text
        for pattern, _ in cls.INJECTION_SIGNATURES:
            cleaned = re.sub(pattern, "[sanitized_instruction]", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()


# Alias for backward compatibility
PromptGuard = PromptGuardService

