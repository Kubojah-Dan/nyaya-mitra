"""
NyayaMitra Document Outline & Navigation Service
Generates structured, hierarchical section outlines from legal documents (contracts, notices,
acts, summons, pleadings) to enable instant in-document jump navigation and screen-reader indexing.
"""

import logging
import re
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("nyayamitra.outline_service")


class OutlineSection(BaseModel):
    section_id: str
    heading: str
    start_char: int
    end_char: int
    level: int = 1
    summary: str = ""
    children: list["OutlineSection"] = Field(default_factory=list)


class DocumentOutlineResponse(BaseModel):
    document_id: Optional[str] = None
    title: str
    total_sections: int
    sections: list[OutlineSection]


class OutlineService:
    """
    Parses unstructured and structured legal text into an accessible outline hierarchy.
    Handles standard Indian legal numbering (Clauses, Sections, Articles, Roman numerals, Sub-clauses).
    """

    HEADING_PATTERNS = [
        # 1. Standard numbered clauses: "1. Parties", "1.1 Background", "Section 12", "Clause 4(a)"
        re.compile(
            r"^(?P<prefix>(?:Section|Clause|Article|Point|Rule|Chapter|Part|Para|Paragraph)\s*[\dA-Za-z\.\-\(\)]+|\d+\.(?:\d+)*|\([a-z\d]+\))\s*[:\.\-]?\s*(?P<title>[^\n\r]+)",
            re.IGNORECASE | re.MULTILINE,
        ),
        # 2. ALL CAPS headings: "BACKGROUND AND FACTS", "TERMS AND CONDITIONS"
        re.compile(
            r"^(?P<title>[A-Z0-9\s,\-\/\(\)]{4,80})$",
            re.MULTILINE,
        ),
    ]

    @classmethod
    def slugify(cls, text: str) -> str:
        """Creates clean DOM-safe element IDs for in-page section scrolling."""
        cleaned = re.sub(r"[^\w\s\-]", "", text.lower())
        slug = re.sub(r"[\s_]+", "-", cleaned).strip("-")
        return slug[:50] or "section"

    @classmethod
    def generate_outline(
        cls,
        text: str,
        document_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> DocumentOutlineResponse:
        """
        Parses text and returns hierarchical section tree.
        """
        resolved_title = title or "Legal Document"
        if not text or not text.strip():
            return DocumentOutlineResponse(
                document_id=document_id,
                title=resolved_title,
                total_sections=0,
                sections=[],
            )

        lines = text.splitlines(keepends=True)
        
        # Track offsets
        current_offset = 0
        matches: list[dict[str, Any]] = []

        line_pattern = re.compile(
            r"^(?:(?:Section|Clause|Article|Point|Rule|Para|Paragraph)\s*([\dA-Za-z\.\-\(\)]+)|\d+(?:\.\d+)*\b|\([a-z\d]+\))\s*[:\.\-]?\s*(.*)",
            re.IGNORECASE,
        )

        all_caps_pattern = re.compile(r"^[A-Z][A-Z0-9\s,\-\/\(\)]{3,60}$")

        for line in lines:
            line_str = line.strip()
            line_len = len(line)
            
            if line_str:
                reg_m = line_pattern.match(line_str)
                if reg_m:
                    heading_text = line_str
                    level = 1
                    if "." in (reg_m.group(1) or "") or line_str.startswith("("):
                        level = 2
                    matches.append({
                        "heading": heading_text,
                        "start_char": current_offset,
                        "level": level,
                    })
                elif all_caps_pattern.match(line_str) and len(line_str.split()) < 10 and not line_str.startswith("HTTP"):
                    matches.append({
                        "heading": line_str.title(),
                        "start_char": current_offset,
                        "level": 1,
                    })

            current_offset += line_len

        # If no explicit headings matched, divide text into natural paragraph sections
        if not matches:
            paragraphs = [p for p in text.split("\n\n") if p.strip()]
            cur_p_offset = 0
            for i, p in enumerate(paragraphs, start=1):
                p_len = len(p)
                first_line = p.strip().splitlines()[0][:60]
                matches.append({
                    "heading": f"Section {i}: {first_line}...",
                    "start_char": cur_p_offset,
                    "level": 1,
                })
                cur_p_offset += p_len + 2

        # Build end_char positions and nested tree
        raw_sections: list[OutlineSection] = []
        for i, item in enumerate(matches):
            next_start = int(matches[i + 1]["start_char"]) if i + 1 < len(matches) else len(text)
            start_pos = int(item["start_char"])
            item_heading = str(item["heading"])
            sec_id = f"sec-{i + 1}-{cls.slugify(item_heading)}"
            section_content = text[start_pos:next_start].strip()
            
            # Extract 1-sentence synopsis
            first_sentence = section_content.split(". ")[0].replace("\n", " ").strip()
            summary = first_sentence[:120] + ("..." if len(first_sentence) > 120 else "")

            raw_sections.append(
                OutlineSection(
                    section_id=sec_id,
                    heading=item_heading,
                    start_char=start_pos,
                    end_char=next_start,
                    level=int(item["level"]),
                    summary=summary,
                    children=[],
                )
            )

        # Nest level 2 sections under previous level 1 sections
        root_sections: list[OutlineSection] = []
        current_root: Optional[OutlineSection] = None

        for sec in raw_sections:
            if sec.level == 1:
                root_sections.append(sec)
                current_root = sec
            else:
                if current_root is not None:
                    current_root.children.append(sec)
                else:
                    root_sections.append(sec)
                    current_root = sec

        return DocumentOutlineResponse(
            document_id=document_id,
            title=resolved_title,
            total_sections=len(raw_sections),
            sections=root_sections,
        )
