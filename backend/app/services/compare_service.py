"""
NyayaMitra Legal Document Comparison Engine
Performs structural, textual, and semantic difference analysis between two legal texts or documents.
Integrates deterministic diffing with GenAI semantic synthesis (Model Router REASONING tier)
and strict non-fabrication citation verifiers.
"""

from datetime import datetime, timezone
import difflib
import logging
import re
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.services.model_router import global_model_router
from app.services.prompt_guard import PromptGuardService

logger = logging.getLogger("nyayamitra.compare_service")


class SectionDelta(BaseModel):
    section_id: str
    section_a: str
    section_b: str
    delta_type: str  # ADDED, REMOVED, MODIFIED, UNCHANGED
    description: str
    text_a: str = ""
    text_b: str = ""
    citations: list[str] = Field(default_factory=list)


class DocumentCompareRequest(BaseModel):
    document_a: str
    document_b: str
    title_a: Optional[str] = "Original Document (A)"
    title_b: Optional[str] = "Revised Document (B)"
    language: Optional[str] = "en"
    session_id: Optional[str] = None


class DocumentCompareResponse(BaseModel):
    success: bool
    summary: str
    total_sections_a: int
    total_sections_b: int
    added_count: int
    removed_count: int
    modified_count: int
    unchanged_count: int
    deltas: list[SectionDelta]
    added_sections: list[str]
    removed_sections: list[str]
    modified_sections: list[str]
    citations: list[str]
    warnings: list[str]
    model_used: str
    tier: str
    fallback_used: bool
    status: str
    compared_at: str
    disclaimer: str


class CompareService:
    """
    Orchestrates legal document comparison:
    1. Prompt sanitization & PII safety envelope
    2. Structural clause/section segmentation
    3. Deterministic sequence alignment and text diffing
    4. GenAI semantic legal impact explanation
    5. Statutory verification and non-fabrication envelope
    """

    LEGAL_DISCLAIMER_EN = (
        "This comparison identifies textual and semantic differences for informational purposes. "
        "It does not determine the legal validity, enforceability, or legal effect of either document. "
        "Verify important changes with a qualified legal professional."
    )
    LEGAL_DISCLAIMER_HI = (
        "यह तुलना केवल सूचनात्मक उद्देश्यों के लिए शाब्दिक और अर्थगत अंतरों की पहचान करती है। "
        "यह किसी भी दस्तावेज़ की कानूनी वैधता या प्रभाव का निर्धारण नहीं करती है। "
        "महत्वपूर्ण परिवर्तनों के लिए किसी योग्य कानूनी विशेषज्ञ या DLSA से परामर्श लें।"
    )

    @classmethod
    def split_into_sections(cls, text: str) -> list[dict[str, Any]]:
        """
        Splits text into structured numbered sections or meaningful paragraphs.
        Matches clauses like '1.', 'Clause 1', 'Section 2', 'Article 3', '(a)', roman numerals, or double newlines.
        """
        if not text or not text.strip():
            return []

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return []

        sections: list[dict[str, Any]] = []
        current_heading = "Preamble / General Terms"
        current_lines: list[str] = []
        section_idx = 1

        heading_pattern = re.compile(
            r"^(?:(?:Section|Clause|Article|Point|Rule|Para|Paragraph)\s*(\d+|[A-ZIVXLCDM]+)|\d+[\.\)]|[A-ZIVXLCDM]+[\.\)])\s*(.*)",
            re.IGNORECASE,
        )

        for line in lines:
            match = heading_pattern.match(line)
            if match and len(current_lines) > 0:
                body = " ".join(current_lines).strip()
                sections.append({
                    "section_id": f"sec-{section_idx}",
                    "heading": current_heading,
                    "text": body,
                })
                section_idx += 1
                current_heading = line[:80]
                current_lines = [line]
            else:
                if match and len(current_lines) == 0:
                    current_heading = line[:80]
                current_lines.append(line)

        if current_lines:
            sections.append({
                "section_id": f"sec-{section_idx}",
                "heading": current_heading,
                "text": " ".join(current_lines).strip(),
            })

        return sections

    @classmethod
    def compare(cls, req: DocumentCompareRequest) -> DocumentCompareResponse:
        """Executes complete legal comparison between Document A and Document B."""
        # 1. Safety & Prompt Injection Check
        safety_a = PromptGuardService.analyze_prompt(req.document_a)
        safety_b = PromptGuardService.analyze_prompt(req.document_b)
        sanitized_a = safety_a.sanitized_text
        sanitized_b = safety_b.sanitized_text

        if not sanitized_a.strip() or not sanitized_b.strip():
            now_iso = datetime.now(timezone.utc).isoformat()
            return DocumentCompareResponse(
                success=False,
                summary="Both documents must contain text to perform a comparison.",
                total_sections_a=0,
                total_sections_b=0,
                added_count=0,
                removed_count=0,
                modified_count=0,
                unchanged_count=0,
                deltas=[],
                added_sections=[],
                removed_sections=[],
                modified_sections=[],
                citations=[],
                warnings=["Empty input provided for one or both documents."],
                model_used="deterministic-baseline",
                tier="FAST",
                fallback_used=False,
                status="ERROR",
                compared_at=now_iso,
                disclaimer=cls.LEGAL_DISCLAIMER_HI if req.language == "hi" else cls.LEGAL_DISCLAIMER_EN,
            )

        # 2. Structural Segmentation
        secs_a = cls.split_into_sections(sanitized_a)
        secs_b = cls.split_into_sections(sanitized_b)

        # 3. Deterministic Diffing & Alignment
        deltas: list[SectionDelta] = []
        added_titles: list[str] = []
        removed_titles: list[str] = []
        modified_titles: list[str] = []

        dict_a = {s["heading"].strip().lower(): s for s in secs_a}
        dict_b = {s["heading"].strip().lower(): s for s in secs_b}

        all_headings = list(dict.fromkeys(
            [s["heading"].strip().lower() for s in secs_a] +
            [s["heading"].strip().lower() for s in secs_b]
        ))

        for idx, key in enumerate(all_headings, start=1):
            in_a = dict_a.get(key)
            in_b = dict_b.get(key)

            if in_a and not in_b:
                delta = SectionDelta(
                    section_id=f"sec-diff-{idx}",
                    section_a=in_a["heading"],
                    section_b="[Deleted / Not Present]",
                    delta_type="REMOVED",
                    description=f"Section '{in_a['heading']}' present in {req.title_a} was removed in {req.title_b}.",
                    text_a=in_a["text"],
                    text_b="",
                )
                deltas.append(delta)
                removed_titles.append(in_a["heading"])
            elif in_b and not in_a:
                delta = SectionDelta(
                    section_id=f"sec-diff-{idx}",
                    section_a="[Not Present / Newly Added]",
                    section_b=in_b["heading"],
                    delta_type="ADDED",
                    description=f"New section '{in_b['heading']}' added in {req.title_b}.",
                    text_a="",
                    text_b=in_b["text"],
                )
                deltas.append(delta)
                added_titles.append(in_b["heading"])
            elif in_a and in_b:
                text_a = in_a["text"]
                text_b = in_b["text"]

                if text_a.strip() == text_b.strip():
                    delta = SectionDelta(
                        section_id=f"sec-diff-{idx}",
                        section_a=in_a["heading"],
                        section_b=in_b["heading"],
                        delta_type="UNCHANGED",
                        description="Content is identical in both documents.",
                        text_a=text_a,
                        text_b=text_b,
                    )
                    deltas.append(delta)
                else:
                    # Modified: calculate quick ratio and describe change
                    ratio = difflib.SequenceMatcher(None, text_a, text_b).ratio()
                    desc = cls._summarize_modification(text_a, text_b, req.language or "en")
                    delta = SectionDelta(
                        section_id=f"sec-diff-{idx}",
                        section_a=in_a["heading"],
                        section_b=in_b["heading"],
                        delta_type="MODIFIED",
                        description=desc,
                        text_a=text_a,
                        text_b=text_b,
                    )
                    deltas.append(delta)
                    modified_titles.append(in_b["heading"])

        # If heading matching yielded too few sections, fallback to paragraph diff
        if len(deltas) == 0:
            diff_ratio = difflib.SequenceMatcher(None, sanitized_a, sanitized_b).ratio()
            delta_type = "UNCHANGED" if diff_ratio > 0.99 else "MODIFIED"
            deltas.append(SectionDelta(
                section_id="sec-diff-1",
                section_a=req.title_a or "Document A",
                section_b=req.title_b or "Document B",
                delta_type=delta_type,
                description=f"Overall similarity ratio: {round(diff_ratio * 100, 1)}%.",
                text_a=sanitized_a[:500],
                text_b=sanitized_b[:500],
            ))

        added_count = len([d for d in deltas if d.delta_type == "ADDED"])
        removed_count = len([d for d in deltas if d.delta_type == "REMOVED"])
        modified_count = len([d for d in deltas if d.delta_type == "MODIFIED"])
        unchanged_count = len([d for d in deltas if d.delta_type == "UNCHANGED"])

        # 4. Synthesize Plain-Language Summary with Model Router (REASONING tier)
        summary_prompt = (
            f"Analyze legal differences between Document A ({req.title_a}) and Document B ({req.title_b}):\n\n"
            f"Summary stats: {added_count} added, {removed_count} removed, {modified_count} modified, {unchanged_count} unchanged.\n"
            f"Modified sections: {', '.join(modified_titles[:5]) or 'None'}\n"
            f"Added sections: {', '.join(added_titles[:5]) or 'None'}\n"
            f"Removed sections: {', '.join(removed_titles[:5]) or 'None'}\n\n"
            f"Sample diffs:\n" + "\n".join([f"- [{d.delta_type}] {d.section_b or d.section_a}: {d.description}" for d in deltas[:4]])
        )

        def deterministic_summary() -> str:
            if req.language == "hi":
                return (
                    f"दस्तावेज़ तुलना सारांश: {modified_count} संशोधित, {added_count} जोड़े गए, और {removed_count} हटाए गए अनुभाग पाए गए। "
                    f"कुल {len(deltas)} अनुभागों की जाँच की गई।"
                )
            return (
                f"Document comparison completed: found {modified_count} modified section(s), "
                f"{added_count} added section(s), {removed_count} removed section(s), and {unchanged_count} unchanged section(s). "
                f"Key changes are highlighted in the structured diff below."
            )

        ai_result = global_model_router.route_task(
            task_type="DOCUMENT_COMPARE",
            prompt=summary_prompt,
            fallback_deterministic_fn=deterministic_summary,
        )

        now_iso = datetime.now(timezone.utc).isoformat()
        disclaimer = cls.LEGAL_DISCLAIMER_HI if req.language == "hi" else cls.LEGAL_DISCLAIMER_EN

        # Look for statutory citations present in the texts (e.g., BNS, BNSS, CPC, Section X)
        citations = cls._extract_statutory_citations(sanitized_a + " " + sanitized_b)

        return DocumentCompareResponse(
            success=True,
            summary=ai_result.content if ai_result.status == "SUCCESS" else deterministic_summary(),
            total_sections_a=len(secs_a),
            total_sections_b=len(secs_b),
            added_count=added_count,
            removed_count=removed_count,
            modified_count=modified_count,
            unchanged_count=unchanged_count,
            deltas=deltas,
            added_sections=added_titles,
            removed_sections=removed_titles,
            modified_sections=modified_titles,
            citations=citations,
            warnings=["Please verify critical obligations, liability limits, and notice deadlines before signing."],
            model_used=ai_result.model_used,
            tier=ai_result.tier,
            fallback_used=ai_result.fallback_used,
            status=ai_result.status,
            compared_at=now_iso,
            disclaimer=disclaimer,
        )

    @classmethod
    def _summarize_modification(cls, text_a: str, text_b: str, lang: str) -> str:
        """Extracts specific numeric, deadline, or obligation variations between two text snippets."""
        # Check for numbers / days / rupee changes
        nums_a = re.findall(r"\b\d+(?:\.\d+)?\b", text_a)
        nums_b = re.findall(r"\b\d+(?:\.\d+)?\b", text_b)

        if nums_a and nums_b and nums_a != nums_b:
            return f"Values changed from [{', '.join(nums_a[:3])}] in Doc A to [{', '.join(nums_b[:3])}] in Doc B."

        # Quick word-level difference
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        added_words = list(words_b - words_a)[:4]
        removed_words = list(words_a - words_b)[:4]

        details = []
        if added_words:
            details.append(f"added key terms ({', '.join(added_words)})")
        if removed_words:
            details.append(f"removed terms ({', '.join(removed_words)})")

        if details:
            return f"Wording updated: {'; '.join(details)}."

        return "Language and clause stipulations were revised."

    @classmethod
    def _extract_statutory_citations(cls, text: str) -> list[str]:
        """Extracts references to known Indian acts and sections without hallucination."""
        matches = set()
        patterns = [
            r"(?:Section\s+\d+[A-Z]?(?:\s*\(\d+\))?)\s+of\s+(?:the\s+)?(?:BNS|BNSS|BSA|IPC|CrPC|CPC|LSAA|RTI|Consumer Protection Act)[^\.\,\;\n]*",
            r"\b(?:BNS|BNSS|BSA)\s+2023\b",
            r"\bSection\s+12(?:\s*\([a-z]\))?\s+(?:of\s+)?(?:the\s+)?Legal Services Authorities Act\b",
            r"\bSection\s+138\s+(?:of\s+)?(?:the\s+)?NI Act\b",
        ]
        for pat in patterns:
            found = re.findall(pat, text, re.IGNORECASE)
            for f in found:
                matches.add(f.strip())

        return sorted(list(matches))
