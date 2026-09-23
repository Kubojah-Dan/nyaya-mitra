"""
NyayaMitra Deadline Guardian Service
Extracts, tracks, computes, and alerts on legal deadlines, statutory timeframes,
and court hearing dates, with calendar (.ics) generation.
"""

from datetime import datetime, timedelta, timezone
import logging
import re
from typing import Any, Optional

logger = logging.getLogger("nyayamitra.deadlines")

MONTH_MAP = {
    "jan": 1, "january": 1, "जनवरी": 1,
    "feb": 2, "february": 2, "फरवरी": 2,
    "mar": 3, "march": 3, "मार्च": 3,
    "apr": 4, "april": 4, "अप्रैल": 4,
    "may": 5, "मई": 5,
    "jun": 6, "june": 6, "जून": 6,
    "jul": 7, "july": 7, "जुलाई": 7,
    "aug": 8, "august": 8, "अगस्त": 8,
    "sep": 9, "september": 9, "सितंबर": 9,
    "oct": 10, "october": 10, "अक्टूबर": 10,
    "nov": 11, "november": 11, "नवंबर": 11,
    "dec": 12, "december": 12, "दिसंबर": 12,
}


class DeadlineGuardian:
    """Extracts, validates, and manages legal deadlines and calendar exports."""

    @classmethod
    def extract_deadlines(
        cls,
        text: str,
        reference_date: Optional[datetime] = None,
        page_count: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Extracts all dates and relative limitation deadlines with source snippets.
        """
        if not text or not text.strip():
            return []

        ref_date = reference_date or datetime.now(timezone.utc)
        deadlines: list[dict[str, Any]] = []

        # Split text into lines or pseudo-pages for snippet context
        pages = text.split("--- Page Break ---")
        if not pages:
            pages = [text]

        for p_idx, page_content in enumerate(pages, start=1):
            # 1. Look for explicit court dates / hearing dates
            hearing_matches = cls._find_hearing_dates(page_content, p_idx)
            deadlines.extend(hearing_matches)

            # 2. Look for statutory periods / timeframes (e.g. "within 15 days", "within 30 days")
            period_matches = cls._find_relative_periods(page_content, p_idx, ref_date)
            deadlines.extend(period_matches)

            # 3. Look for explicit ISO/DD-MM-YYYY dates associated with legal triggers
            explicit_matches = cls._find_explicit_dates(page_content, p_idx)
            deadlines.extend(explicit_matches)

        # Deduplicate based on label and value
        unique_deadlines = []
        seen = set()
        for dl in deadlines:
            key = (dl["label"], dl["value"])
            if key not in seen:
                seen.add(key)
                unique_deadlines.append(dl)

        return unique_deadlines

    @classmethod
    def _find_hearing_dates(cls, text: str, page_number: int) -> list[dict[str, Any]]:
        results = []
        patterns = [
            r"(?:appear\s+(?:on|before)|next\s+date\s+of\s+hearing|listed\s+on|posted\s+to|fixed\s+for|peshi\s+tarikh|तारीख\s+पेशी)(?:\s+[a-zA-Z\s]{0,25}?\s+on)?[:\s]+(\d{1,2}(?:st|nd|rd|th)?[\s\/\-\.](?:[A-Za-z]+|\d{1,2})[\s\/\-\.]\d{4})",
            r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर)\s+\d{4})\b",
        ]

        for pat in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                date_str = match.group(1) if match.groups() else match.group(0)
                parsed_dt = cls._parse_date_string(date_str)
                if parsed_dt:
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    snippet = text[start:end].strip().replace("\n", " ")

                    iso_val = parsed_dt.strftime("%Y-%m-%d")
                    urgency = cls.compute_urgency(parsed_dt)

                    results.append({
                        "label": "Court Appearance / Hearing Date",
                        "value": iso_val,
                        "source_text": snippet,
                        "page_number": page_number,
                        "confidence": 0.95,
                        "assumptions": "Extracted directly from court listing or appearance notice.",
                        "requires_verification": False,
                        "urgency_level": urgency,
                        "statutory_basis": "Court Summons / Notice Order",
                    })

        return results

    @classmethod
    def _find_relative_periods(
        cls, text: str, page_number: int, ref_date: datetime
    ) -> list[dict[str, Any]]:
        results = []
        patterns = [
            (
                r"\b(?:within|before|inside)\s+(\d{1,3})\s+days?\b",
                "Relative limitation period specified in notice",
            ),
            (
                r"\b(\d{1,3})\s+दिनों\s+के\s+भीतर\b",
                "Hindi notice limitation timeframe",
            ),
            (
                r"\b(?:statutory\s+period\s+of|limitation\s+of)\s+(\d{1,3})\s+days?\b",
                "Statutory limitation period",
            ),
        ]

        for pat, basis in patterns:
            for match in re.finditer(pat, text, re.IGNORECASE):
                days = int(match.group(1))
                computed_date = ref_date + timedelta(days=days)
                iso_val = computed_date.strftime("%Y-%m-%d")

                start = max(0, match.start() - 25)
                end = min(len(text), match.end() + 25)
                snippet = text[start:end].strip().replace("\n", " ")

                urgency = "CRITICAL" if days <= 3 else ("HIGH" if days <= 7 else ("MEDIUM" if days <= 30 else "LOW"))

                results.append({
                    "label": f"Reply / Action Deadline ({days} Days)",
                    "value": iso_val,
                    "source_text": snippet,
                    "page_number": page_number,
                    "confidence": 0.88,
                    "assumptions": f"Calculated as {days} days from document receipt date ({ref_date.strftime('%Y-%m-%d')}).",
                    "requires_verification": True,
                    "urgency_level": urgency,
                    "statutory_basis": basis,
                })

        return results

    @classmethod
    def _find_explicit_dates(cls, text: str, page_number: int) -> list[dict[str, Any]]:
        results = []
        date_regex = re.compile(
            r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})\b|\b(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})\b"
        )

        for match in date_regex.finditer(text):
            parsed_dt = cls._parse_date_string(match.group(0))
            if parsed_dt:
                start = max(0, match.start() - 25)
                end = min(len(text), match.end() + 25)
                snippet = text[start:end].strip().replace("\n", " ")

                label = "Document Date / Mentioned Date"
                if re.search(r"notice|demand|dated|issued|cause|dated", snippet, re.IGNORECASE):
                    label = "Notice Issuance / Action Date"
                if re.search(r"appearance|hearing|peshi|adjourn|appear|court", snippet, re.IGNORECASE):
                    label = "Court Appearance Date"

                urgency = cls.compute_urgency(parsed_dt)

                results.append({
                    "label": label,
                    "value": parsed_dt.strftime("%Y-%m-%d"),
                    "source_text": snippet,
                    "page_number": page_number,
                    "confidence": 0.85,
                    "assumptions": "Explicit date parsed from document context.",
                    "requires_verification": False,
                    "urgency_level": urgency,
                    "statutory_basis": "Document Text Recital",
                })

        return results

    @classmethod
    def compute_urgency(cls, target_date: datetime, current_date: Optional[datetime] = None) -> str:
        """
        Determines urgency level based on days remaining.
        CRITICAL: <= 3 days or already past
        HIGH: <= 7 days
        MEDIUM: <= 30 days
        LOW: > 30 days
        """
        curr = current_date or datetime.now(timezone.utc)
        if target_date.tzinfo is None and curr.tzinfo is not None:
            curr = curr.replace(tzinfo=None)
        elif target_date.tzinfo is not None and curr.tzinfo is None:
            target_date = target_date.replace(tzinfo=None)

        delta = (target_date - curr).days
        if delta <= 3:
            return "CRITICAL"
        if delta <= 7:
            return "HIGH"
        if delta <= 30:
            return "MEDIUM"
        return "LOW"

    @classmethod
    def _parse_date_string(cls, date_str: str) -> Optional[datetime]:
        """Parses various Indian and ISO date formats into datetime object."""
        if not date_str:
            return None

        clean = date_str.strip().lower()
        clean = re.sub(r"(\d+)(?:st|nd|rd|th)", r"\1", clean)

        # 1. DD/MM/YYYY or DD-MM-YYYY
        dmy_match = re.match(r"^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$", clean)
        if dmy_match:
            try:
                day, month, year = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
                if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                    return datetime(year, month, day, 10, 0, 0)
            except Exception:
                pass

        # 2. YYYY-MM-DD
        ymd_match = re.match(r"^(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})$", clean)
        if ymd_match:
            try:
                year, month, day = int(ymd_match.group(1)), int(ymd_match.group(2)), int(ymd_match.group(3))
                if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                    return datetime(year, month, day, 10, 0, 0)
            except Exception:
                pass

        # 3. 24 October 2024 / 24 अक्टूबर 2024
        named_match = re.match(r"^(\d{1,2})[\s\/\-\.]([A-Za-z\u0900-\u097F]+)[\s\/\-\.](\d{4})$", clean)
        if named_match:
            try:
                day = int(named_match.group(1))
                month_name = named_match.group(2)
                year = int(named_match.group(3))
                month = MONTH_MAP.get(month_name)
                if month and 1 <= day <= 31 and 1900 <= year <= 2100:
                    return datetime(year, month, day, 10, 0, 0)
            except Exception:
                pass

        return None

    @classmethod
    def generate_ics_calendar(
        cls,
        deadlines: list[dict[str, Any]],
        document_title: str = "Legal Notice / Document Deadline",
        doc_id: str = "doc_1",
    ) -> str:
        """
        Generates standard RFC 5545 iCalendar (.ics) format file content.
        """
        now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//NyayaMitra//Legal Deadline Guardian//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{document_title} - Legal Deadlines",
        ]

        for idx, dl in enumerate(deadlines, start=1):
            val = dl.get("value", "")
            parsed_dt = cls._parse_date_string(val)
            if not parsed_dt:
                continue

            dtstart = parsed_dt.strftime("%Y%m%d")
            dtend = (parsed_dt + timedelta(days=1)).strftime("%Y%m%d")
            uid = f"nyayamitra-{doc_id}-{idx}-{dtstart}@nyayamitra.gov.in"
            summary = f"NyayaMitra: {dl.get('label', 'Legal Deadline')}"
            desc = (
                f"Legal deadline extracted by NyayaMitra.\\n\\n"
                f"Label: {dl.get('label')}\\n"
                f"Urgency: {dl.get('urgency_level', 'MEDIUM')}\\n"
                f"Statutory Basis: {dl.get('statutory_basis', 'N/A')}\\n"
                f"Context: {dl.get('source_text', 'N/A')}\\n"
            )

            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_utc}",
                f"DTSTART;VALUE=DATE:{dtstart}",
                f"DTEND;VALUE=DATE:{dtend}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{desc}",
                f"STATUS:CONFIRMED",
                "PRIORITY:1",
                "BEGIN:VALARM",
                "TRIGGER:-P1D",
                "ACTION:DISPLAY",
                f"DESCRIPTION:Reminder: Imminent Legal Deadline tomorrow - {dl.get('label')}",
                "END:VALARM",
                "BEGIN:VALARM",
                "TRIGGER:-P3D",
                "ACTION:DISPLAY",
                f"DESCRIPTION:Notice: Upcoming Legal Deadline in 3 days - {dl.get('label')}",
                "END:VALARM",
                "END:VEVENT",
            ])

        ics_lines.append("END:VCALENDAR")
        return "\r\n".join(ics_lines)
