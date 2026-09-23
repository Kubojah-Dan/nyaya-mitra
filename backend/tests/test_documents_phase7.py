"""
Comprehensive Test Suite for Phase 7:
OCR, Deadline Guardian & Document Understanding
"""

from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app
from app.services.deadline_guardian import DeadlineGuardian
from app.services.document_classifier import DocumentClassifier
from app.services.ocr_service import DocumentSecurityValidator, OCRService


# ==========================================
# 1. Document Security & Validation Tests
# ==========================================

def test_document_security_valid_text():
    content = b"This is a valid legal document text."
    result = DocumentSecurityValidator.validate_file(content, "notice.txt", "text/plain")
    assert result["valid"] is True
    assert result["mime_type"] == "text/plain"
    assert "sha256_hash" in result


def test_document_security_valid_pdf_magic_bytes():
    content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    result = DocumentSecurityValidator.validate_file(content, "summons.pdf", "application/pdf")
    assert result["valid"] is True
    assert result["mime_type"] == "application/pdf"


def test_document_security_size_limit_exceeded():
    large_content = b"A" * (11 * 1024 * 1024)  # 11 MB
    with pytest.raises(ValueError, match="exceeds maximum allowable limit"):
        DocumentSecurityValidator.validate_file(large_content, "huge.txt", "text/plain")


def test_document_security_empty_file():
    with pytest.raises(ValueError, match="empty"):
        DocumentSecurityValidator.validate_file(b"", "empty.txt", "text/plain")


def test_document_security_invalid_mime():
    content = b"MZ\x90\x00\x03\x00\x00\x00"
    with pytest.raises(ValueError, match="Unsupported file format"):
        DocumentSecurityValidator.validate_file(content, "malware.exe", "application/x-msdownload")


def test_document_security_magic_bytes_mismatch():
    fake_pdf = b"Plain text trying to pass as PDF"
    with pytest.raises(ValueError, match="File content signature mismatch"):
        DocumentSecurityValidator.validate_file(fake_pdf, "fake.pdf", "application/pdf")


def test_document_security_malware_screening():
    malicious = b"%PDF-1.4\n<script>alert('xss')</script>\ntrailer"
    with pytest.raises(ValueError, match="Security screening failed"):
        DocumentSecurityValidator.validate_file(malicious, "attack.pdf", "application/pdf")


# ==========================================
# 2. OCR & Text Extraction Tests
# ==========================================

def test_ocr_plain_text_extraction():
    content = "IN THE COURT OF THE DISTRICT JUDGE, SAKET, NEW DELHI".encode("utf-8")
    result = OCRService.extract_text(content, "text/plain")
    assert "DISTRICT JUDGE" in result["text"]
    assert result["detected_language"] == "en"
    assert result["confidence"] == 1.0


def test_ocr_hindi_detection():
    hindi_text = "न्यायालय मुख्य न्यायिक मजिस्ट्रेट, जयपुर। अभियुक्त को 24 अक्टूबर 2024 को पेश होने का सम्मन जारी किया जाता है।"
    lang = OCRService.detect_language(hindi_text)
    assert lang == "hi"


def test_ocr_hinglish_detection():
    hinglish_text = "police thaney mein FIR darj karwai hai. kripya nyay dilwayein aur peshi tarikh batayein."
    lang = OCRService.detect_language(hinglish_text)
    assert lang == "hi"


def test_pii_redaction():
    text = (
        "Complainant Aadhaar No: 5432 1234 8765, PAN: ABCDE1234F, "
        "Phone: +919876543210 filed a complaint."
    )
    redacted, items = OCRService.redact_pii(text)
    assert "5432 1234 8765" not in redacted
    assert "XXXX-XXXX-8765" in redacted
    assert "ABCDE1234F" not in redacted
    assert "9876543210" not in redacted
    assert len(items) >= 3


# ==========================================
# 3. Document Classifier Tests
# ==========================================

def test_classify_court_notice():
    doc = """
    IN THE COURT OF THE PRINCIPAL DISTRICT AND SESSIONS JUDGE, BENGALURU
    Case No. OS 450/2024
    Ramesh Kumar ... Petitioner
    versus
    Suresh Patel ... Respondent
    Notice to appear before this Hon'ble Court on 15-11-2024.
    """
    res = DocumentClassifier.classify_document(doc)
    assert res["document_type"] == "COURT_NOTICE"
    assert res["confidence"] >= 0.5

    meta = DocumentClassifier.extract_metadata_and_parties(doc)
    assert meta["petitioner_or_complainant"] == "Ramesh Kumar"
    assert meta["respondent_or_accused"] == "Suresh Patel"
    assert "450/2024" in (meta["case_number"] or "")


def test_classify_fir_copy():
    doc = """
    FIRST INFORMATION REPORT (Under Section 154 Cr.P.C.)
    FIR No. 120/2024
    Police Station: Cyber Crime Cell, Bengaluru
    Sections cited: Section 420 IPC, Section 66D IT Act
    """
    res = DocumentClassifier.classify_document(doc)
    assert res["document_type"] == "FIR_COPY"

    meta = DocumentClassifier.extract_metadata_and_parties(doc)
    assert meta["fir_number"] == "120/2024"
    assert "Cyber Crime Cell" in (meta["police_station"] or "")


def test_classify_rent_agreement():
    doc = """
    RENTAL LEASE AGREEMENT
    This Tenancy Agreement is made between Landlord Shri Amit Verma and Tenant Smt. Neha Singh.
    Monthly rent of Rs. 25,000/- with security deposit of Rs. 1,00,000/-.
    """
    res = DocumentClassifier.classify_document(doc)
    assert res["document_type"] == "RENT_AGREEMENT"


def test_classify_cheque_bounce_notice():
    doc = """
    STATUTORY LEGAL NOTICE UNDER SECTION 138 NEGOTIABLE INSTRUMENTS ACT
    My client instructions: You are hereby called upon to pay Rs. 1,50,000 within 15 days of receipt.
    """
    res = DocumentClassifier.classify_document(doc)
    assert res["document_type"] == "LEGAL_NOTICE"


# ==========================================
# 4. Deadline Guardian Tests
# ==========================================

def test_deadline_hearing_date_extraction():
    doc = "The accused is directed to appear before this Court on 24-10-2025 at 10:30 AM."
    deadlines = DeadlineGuardian.extract_deadlines(doc)
    assert len(deadlines) >= 1
    d = deadlines[0]
    assert d["value"] == "2025-10-24"
    assert "Court Appearance" in d["label"]
    assert "source_text" in d
    assert "2025" in d["source_text"]


def test_deadline_hindi_date_extraction():
    doc = "अदालत में तारीख पेशी 24 अक्टूबर 2025 नियत की गई है।"
    deadlines = DeadlineGuardian.extract_deadlines(doc)
    assert len(deadlines) >= 1
    assert deadlines[0]["value"] == "2025-10-24"


def test_deadline_relative_period_calculation():
    ref_date = datetime(2025, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
    doc = "You are called upon to make payment within 15 days of receipt of this notice."
    deadlines = DeadlineGuardian.extract_deadlines(doc, reference_date=ref_date)
    assert len(deadlines) >= 1
    rel_dl = [d for d in deadlines if "15 Days" in d["label"]][0]
    assert rel_dl["value"] == "2025-05-16"
    assert rel_dl["requires_verification"] is True


def test_deadline_urgency_levels():
    curr = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert DeadlineGuardian.compute_urgency(datetime(2025, 6, 2, 10, 0, 0), curr) == "CRITICAL"
    assert DeadlineGuardian.compute_urgency(datetime(2025, 6, 6, 10, 0, 0), curr) == "HIGH"
    assert DeadlineGuardian.compute_urgency(datetime(2025, 6, 20, 10, 0, 0), curr) == "MEDIUM"
    assert DeadlineGuardian.compute_urgency(datetime(2025, 8, 1, 10, 0, 0), curr) == "LOW"


def test_calendar_ics_generation():
    deadlines = [
        {
            "label": "Court Appearance Date",
            "value": "2025-10-24",
            "source_text": "Appear on 24-10-2025",
            "page_number": 1,
            "urgency_level": "CRITICAL",
            "statutory_basis": "Summons Order",
        }
    ]
    ics = DeadlineGuardian.generate_ics_calendar(deadlines, "Court Summons", "doc-test-1")
    assert "BEGIN:VCALENDAR" in ics
    assert "BEGIN:VEVENT" in ics
    assert "DTSTART;VALUE=DATE:20251024" in ics
    assert "BEGIN:VALARM" in ics
    assert "END:VCALENDAR" in ics


# ==========================================
# 5. Documents API End-to-End Tests
# ==========================================

@pytest.mark.asyncio
async def test_api_analyze_text():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "raw_text": (
                "IN THE COURT OF CHIEF JUDICIAL MAGISTRATE, DELHI\n"
                "Case No. CC 543/2024\n"
                "Anand Kumar ... Complainant vs Rajesh Sharma ... Accused\n"
                "Summons to appear before this court on 20-11-2025.\n"
                "Aadhaar 1234 5678 9012"
            ),
            "document_title": "Court Summons Notice",
        }
        resp = await client.post("/api/v1/documents/analyze-text", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_type"] in ["COURT_NOTICE", "SUMMONS"]
        assert data["parties"]["petitioner_or_complainant"] == "Anand Kumar"
        assert data["parties"]["respondent_or_accused"] == "Rajesh Sharma"
        assert len(data["deadlines"]) >= 1
        assert data["pii_redacted_count"] >= 1
        doc_id = data["document_id"]

        # Test GET document
        get_resp = await client.get(f"/api/v1/documents/{doc_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["document_id"] == doc_id

        # Test PATCH deadlines (correction mode)
        patch_payload = {
            "deadlines": [
                {
                    "label": "Confirmed Appearance Date",
                    "value": "2025-11-20",
                    "source_text": "Summons date confirmed",
                    "page_number": 1,
                    "confidence": 1.0,
                    "assumptions": "Confirmed by user",
                    "requires_verification": False,
                    "urgency_level": "HIGH",
                    "statutory_basis": "Court Summons Order",
                }
            ]
        }
        patch_resp = await client.patch(f"/api/v1/documents/{doc_id}/deadlines", json=patch_payload)
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "SUCCESS"

        # Test GET calendar .ics
        cal_resp = await client.get(f"/api/v1/documents/{doc_id}/calendar")
        assert cal_resp.status_code == 200
        assert cal_resp.headers["content-type"].startswith("text/calendar")
        assert "BEGIN:VCALENDAR" in cal_resp.text
        assert "20251120" in cal_resp.text


@pytest.mark.asyncio
async def test_api_analyze_upload_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        file_content = b"FIRST INFORMATION REPORT FIR No 99/2024 Police Station Connaught Place"
        files = {"file": ("fir.txt", file_content, "text/plain")}
        resp = await client.post("/api/v1/documents/analyze", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["document_type"] == "FIR_COPY"
        assert data["parties"]["fir_number"] == "99/2024"
