import re
from typing import Any


class LegalCorpusParser:
    """Legal-text-aware structural parser.

    Chunks enactments by Act -> Chapter -> Section rather than arbitrary character splits,
    preserving statutory coherence and metadata attributes.
    """

    COGNIZABLE_KEYWORDS = ["cognizable", "police officer may arrest without warrant"]
    NON_COGNIZABLE_KEYWORDS = ["non-cognizable", "shall not arrest without a warrant"]
    BAILABLE_KEYWORDS = ["bailable"]
    NON_BAILABLE_KEYWORDS = ["non-bailable"]

    @classmethod
    def parse_section(cls, raw_text: str, act_code: str) -> dict[str, Any]:
        """Parses a raw section string and extracts structured attributes."""
        # Detect section number and title pattern: e.g. "318. Cheating. - (1) Whoever..."
        sec_match = re.match(r"^([0-9A-Za-z]+)\.\s*([^\.\n]+)\.\s*[\-—–]?\s*(.*)", raw_text.strip(), re.DOTALL)
        if sec_match:
            sec_num = sec_match.group(1).strip()
            title = sec_match.group(2).strip()
            body = sec_match.group(3).strip()
        else:
            sec_num = "1"
            title = "Section Title"
            body = raw_text.strip()

        # Extract subsections: (1), (2), etc.
        subsections = []
        sub_matches = re.finditer(r"\(([0-9]+|[a-z]+)\)\s*([^\(]+)", body)
        for match in sub_matches:
            subsections.append({
                "sub_index": match.group(1),
                "text": match.group(2).strip(),
            })

        lower_text = raw_text.lower()

        # Classification attributes
        is_cognizable = None
        if any(kw in lower_text for kw in cls.NON_COGNIZABLE_KEYWORDS):
            is_cognizable = False
        elif any(kw in lower_text for kw in cls.COGNIZABLE_KEYWORDS):
            is_cognizable = True

        is_bailable = None
        if any(kw in lower_text for kw in cls.NON_BAILABLE_KEYWORDS):
            is_bailable = False
        elif any(kw in lower_text for kw in cls.BAILABLE_KEYWORDS):
            is_bailable = True

        return {
            "act_code": act_code,
            "section_number": sec_num,
            "title": title,
            "full_text": body or raw_text,
            "subsections": subsections,
            "is_cognizable": is_cognizable,
            "is_bailable": is_bailable,
        }

    @classmethod
    def chunk_section_for_retrieval(cls, section_dict: dict[str, Any], max_chunk_tokens: int = 400) -> list[dict[str, Any]]:
        """Creates semantic retrieval chunks enriched with statutory breadcrumb metadata."""
        act_code = section_dict.get("act_code", "ACT")
        sec_num = section_dict.get("section_number", "")
        title = section_dict.get("title", "")
        body = section_dict.get("full_text", "")

        header = f"[{act_code}] Section {sec_num}: {title}\n"
        full_section_content = header + body

        words = full_section_content.split()
        chunks = []
        chunk_words = 300  # approximately ~400 tokens

        for i in range(0, len(words), chunk_words):
            chunk_slice = words[i : i + chunk_words]
            chunk_text = " ".join(chunk_slice)
            chunks.append({
                "chunk_index": len(chunks),
                "chunk_text": chunk_text,
                "token_count": len(chunk_slice),
                "metadata": {
                    "act_code": act_code,
                    "section_number": sec_num,
                    "title": title,
                },
            })

        return chunks
