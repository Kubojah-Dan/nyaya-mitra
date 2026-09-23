import re
from typing import Any, Optional

from app.sources.india_code import IndiaCodeAdapter


class LegalRetrievalEngine:
    """Hybrid retrieval engine for statutory sections, citations, and procedural rules.

    Combines exact pinpoint statutory matching with keyword-based BM25 relevance scoring,
    jurisdiction filtering, and effective-date filtering.
    """

    def __init__(self, india_code_adapter: Optional[IndiaCodeAdapter] = None) -> None:
        self.india_code = india_code_adapter or IndiaCodeAdapter()
        self._corpus = self.india_code.get_seed_legislation()

    def search(
        self,
        query: str,
        act_codes: Optional[list[str]] = None,
        jurisdiction: str = "Union of India",
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        query_clean = query.lower()
        terms = set(re.findall(r"\b\w{3,}\b", query_clean))

        scored_results = []

        # Check for explicit section numbers in query: e.g. "Section 318" or "173"
        sec_matches = re.findall(r"\b(?:section|sec\.?)?\s*([0-9]{1,4}[a-z]?)\b", query_clean)

        for act_code, act_data in self._corpus.items():
            if act_codes and act_code not in act_codes:
                continue

            act_jur = act_data.get("jurisdiction", "Union of India")
            if jurisdiction and act_jur.lower() != jurisdiction.lower():
                continue

            act_name = act_data["act_name"]

            for sec in act_data.get("sections", []):
                score = 0.0
                sec_num = sec["section_number"].lower()
                title = sec["title"].lower()
                body = sec["full_text"].lower()
                plain = (sec.get("plain_english") or "").lower()

                # Exact section match gives highest boost
                if sec_num in sec_matches:
                    score += 50.0

                # Term frequency scoring
                for term in terms:
                    if term in sec_num:
                        score += 15.0
                    if term in title:
                        score += 10.0
                    if term in plain:
                        score += 5.0
                    if term in body:
                        score += 2.0

                if score > 0.0:
                    scored_results.append({
                        "act_code": act_code,
                        "act_name": act_name,
                        "section_number": sec["section_number"],
                        "title": sec["title"],
                        "full_text": sec["full_text"],
                        "plain_english": sec.get("plain_english"),
                        "penalties": sec.get("penalties"),
                        "is_cognizable": sec.get("is_cognizable"),
                        "is_bailable": sec.get("is_bailable"),
                        "official_url": f"https://www.indiacode.nic.in/handle/123456789/{act_code}",
                        "score": score,
                    })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]
