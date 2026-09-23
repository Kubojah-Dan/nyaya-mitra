"""
NyayaMitra Document Classifier & Metadata Extraction
Identifies legal document types and extracts parties, authorities,
case numbers, and statutory sections from legal texts.
"""

import re
from typing import Any


class DocumentClassifier:
    """Classifies document type and extracts legal entities and parties."""

    DOCUMENT_SIGNATURES = {
        "COURT_NOTICE": [
            r"in the court of",
            r"hon['’]?ble court",
            r"high court of",
            r"district court",
            r"civil court",
            r"notice to appear",
            r"court notice",
            r"case no[\.\s:]",
            r"crl[\.\s]m[\.\s]c",
            r"os no[\.\s:]",
            r"न्यायालय",
            r"अदालत",
            r"सम्मन",
            r"नोटिस",
        ],
        "SUMMONS": [
            r"summons to (?:appear|witness|accused|defendant)",
            r"writ of summons",
            r"hereby summoned to appear",
            r"summoned to attend",
            r"section \d+ crpc",
            r"section \d+ bnss",
            r"आदेश सम्मन",
        ],
        "FIR_COPY": [
            r"first information report",
            r"\bfir\b",
            r"police station",
            r"u/s\s+\d+",
            r"under section\s+\d+",
            r"cr\.no",
            r"प्रथम सूचना रिपोर्ट",
            r"थाना",
            r"प्राथमिकी",
        ],
        "RENT_AGREEMENT": [
            r"rent(?:al)? agreement",
            r"lease deed",
            r"tenancy agreement",
            r"landlord",
            r"tenant",
            r"lessor",
            r"lessee",
            r"monthly rent",
            r"security deposit",
            r"किरायानामा",
            r"मकान मालिक",
            r"किरायेदार",
        ],
        "LEGAL_NOTICE": [
            r"legal notice",
            r"advocate notice",
            r"statutory demand notice",
            r"under section 138",
            r"negotiable instruments act",
            r"my client instructions",
            r"called upon you to pay",
            r"विधिक नोटिस",
            r"वकील नोटिस",
        ],
        "CONSUMER_COMPLAINT": [
            r"consumer disputes redressal commission",
            r"consumer protection act",
            r"district consumer forum",
            r"deficiency in service",
            r"unfair trade practice",
            r"उपभोक्ता फोरम",
            r"उपभोक्ता संरक्षण",
        ],
        "RTI_RESPONSE": [
            r"right to information act",
            r"rti application",
            r"public information officer",
            r"central information commission",
            r"state information commission",
            r"सूचना का अधिकार",
            r"जन सूचना अधिकारी",
        ],
        "EMPLOYMENT_TERMINATION": [
            r"termination of employment",
            r"notice of termination",
            r"severance",
            r"show cause notice",
            r"disciplinary enquiry",
            r"relieving letter",
            r"सेवा समाप्ति",
        ],
    }

    @classmethod
    def classify_document(cls, text: str) -> dict[str, Any]:
        """
        Determines the document type and confidence score.
        """
        if not text or not text.strip():
            return {
                "document_type": "UNKNOWN",
                "confidence": 0.0,
                "matched_patterns": [],
                "description": "Empty or unrecognized document text.",
            }

        text_lower = text.lower()
        type_scores: dict[str, int] = {}
        matched_details: dict[str, list[str]] = {}

        for doc_type, patterns in cls.DOCUMENT_SIGNATURES.items():
            matches = []
            score = 0
            for pattern in patterns:
                found = re.findall(pattern, text_lower)
                if found:
                    score += len(found) * 2
                    matches.append(pattern)
            if score > 0:
                type_scores[doc_type] = score
                matched_details[doc_type] = matches

        if not type_scores:
            return {
                "document_type": "UNKNOWN",
                "confidence": 0.3,
                "matched_patterns": [],
                "description": "General or unclassified legal correspondence.",
            }

        best_type = max(type_scores, key=type_scores.get)
        raw_score = type_scores[best_type]
        confidence = min(0.98, max(0.55, 0.5 + (raw_score * 0.08)))

        descriptions = {
            "COURT_NOTICE": "Judicial notice or order from a District Court, High Court, or Tribunal.",
            "SUMMONS": "Formal court summons requiring appearance or deposition.",
            "FIR_COPY": "First Information Report registered with a Police Station.",
            "RENT_AGREEMENT": "Tenancy contract / lease deed between Landlord and Tenant.",
            "LEGAL_NOTICE": "Statutory advocate legal notice or demand notice.",
            "CONSUMER_COMPLAINT": "Consumer forum complaint or grievance notice.",
            "RTI_RESPONSE": "Official communication or order under the Right to Information Act.",
            "EMPLOYMENT_TERMINATION": "Employment contract termination or disciplinary show-cause notice.",
        }

        return {
            "document_type": best_type,
            "confidence": round(confidence, 2),
            "matched_patterns": matched_details.get(best_type, []),
            "description": descriptions.get(best_type, "Legal document"),
        }

    @classmethod
    def extract_metadata_and_parties(cls, text: str) -> dict[str, Any]:
        """
        Extracts non-sensitive parties, case identifiers, and legal sections line by line.
        """
        parties: dict[str, Any] = {
            "petitioner_or_complainant": None,
            "respondent_or_accused": None,
            "issuing_authority": None,
            "case_number": None,
            "fir_number": None,
            "police_station": None,
            "sections_cited": [],
        }

        # Case number patterns (e.g. Case No. OS 450/2024, Crl. M.C. 45/2023, CC No. 987)
        case_match = re.search(
            r"(?:case\s+no|crl\.?\s*(?:m\.?c\.?|a\.?|rev)|cc\s+no|os\s+no|wp\s+no|complaint\s+no)[.:\s]+([A-Za-z0-9\/\-_\s]+?(?:\s+of\s+\d{4}|\/\d{4}|\b))(?:\n|\r|\.|$)",
            text,
            re.IGNORECASE,
        )
        if case_match:
            parties["case_number"] = re.sub(r"\s+", " ", case_match.group(0)).strip()

        # FIR number patterns
        fir_match = re.search(
            r"(?:FIR\s+(?:No\.?|Number)|प्राथमिकी\s+संख्या)[.:\s]+([A-Za-z0-9\/\-_]+)",
            text,
            re.IGNORECASE,
        )
        if fir_match:
            parties["fir_number"] = fir_match.group(1).strip()

        # Police Station
        ps_match = re.search(
            r"(?:police\s+station|P\.?S\.?|थाना)[.:\s]+([A-Za-z\s]{2,40}?)(?:,|District|Dist\.|\n|\.)",
            text,
            re.IGNORECASE,
        )
        if ps_match:
            parties["police_station"] = ps_match.group(1).strip()

        # Versus pattern across lines or inline
        vs_multi = re.search(
            r"([A-Za-z\s\.]+?)(?:\s*\.\.\.|\s+Petitioner|\s+Complainant|\s+Plaintiff)?\s*(?:\n|\s)+(?:versus|vs\.?|v/s|बनाम)\s*(?:\n|\s)+([A-Za-z\s\.]+?)(?:\s*\.\.\.|\s+Respondent|\s+Accused|\s+Defendant)?(?:\n|\.|$)",
            text,
            re.IGNORECASE,
        )
        if vs_multi:
            p1 = vs_multi.group(1).strip()
            p2 = vs_multi.group(2).strip()
            # Clean trailing/leading noise, dots, and role labels
            p1 = re.sub(r"^(?:IN THE MATTER OF:?\s*|Case No[^\n]+\n)", "", p1, flags=re.IGNORECASE)
            p1 = re.sub(r"(?:\s*\.\.\.|\s+Petitioner|\s+Complainant|\s+Plaintiff|[\s\.]+)$", "", p1, flags=re.IGNORECASE).strip()
            p2 = re.sub(r"(?:\s*\.\.\.|\s+Respondent|\s+Accused|\s+Defendant|[\s\.]+)$", "", p2, flags=re.IGNORECASE).strip()
            if p1 and len(p1) > 2:
                parties["petitioner_or_complainant"] = p1
            if p2 and len(p2) > 2:
                parties["respondent_or_accused"] = p2

        # Issuing Authority / Court name
        court_match = re.search(
            r"(?:IN THE COURT OF|BEFORE THE|HON['’]?BLE)\s+([A-Za-z\s,\.\(\)]{3,60}?(?:COURT|TRIBUNAL|MAGISTRATE|JUDGE|COMMISSION))",
            text,
            re.IGNORECASE,
        )
        if court_match:
            parties["issuing_authority"] = court_match.group(0).strip()

        # Section citations mentioned
        sections_found = re.findall(
            r"(?:Section|Sec\.?|धारा|u/s)\s+(\d{1,4}[A-Za-z]?(?:\s*\(\w+\))?)\s+(?:of\s+the\s+)?([A-Za-z\s]{0,30}?(?:Act|Code|Sanstha|BNS|BNSS|BSA|IPC|CrPC))?",
            text,
            re.IGNORECASE,
        )
        unique_sections = []
        for sec, act in sections_found:
            clean_sec = sec.strip()
            clean_act = act.strip() if act else "Statutory Provision"
            formatted = f"Section {clean_sec} ({clean_act})"
            if formatted not in unique_sections:
                unique_sections.append(formatted)

        parties["sections_cited"] = unique_sections[:10]

        return parties
