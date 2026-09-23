"""
NyayaMitra Document Understanding & Deadline Guardian Router
Provides REST endpoints for document upload, OCR analysis,
deadline guardian tracking, user corrections, and iCalendar export.
"""

from datetime import datetime, timezone
import uuid
from typing import Any, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from app.services.deadline_guardian import DeadlineGuardian
from app.services.document_classifier import DocumentClassifier
from app.services.ocr_service import DocumentSecurityValidator, OCRService

router = APIRouter(prefix="/documents", tags=["documents"])

# In-memory document session cache
_DOCUMENT_STORE: dict[str, dict[str, Any]] = {}


class DeadlineItemSchema(BaseModel):
    label: str
    value: str
    source_text: str
    page_number: int = 1
    confidence: float = 0.9
    assumptions: str = ""
    requires_verification: bool = False
    urgency_level: str = "MEDIUM"
    statutory_basis: str = ""


class AnalyzeDocumentTextRequest(BaseModel):
    raw_text: str
    document_title: Optional[str] = "Uploaded Legal Document"
    session_id: Optional[str] = None
    reference_date: Optional[str] = None


class DocumentAnalysisResponse(BaseModel):
    document_id: str
    session_id: Optional[str] = None
    filename: str
    detected_language: str
    document_type: str
    document_description: str
    classification_confidence: float
    parties: dict[str, Any]
    deadlines: list[DeadlineItemSchema]
    plain_summary: str
    rights_and_next_steps: list[str]
    redacted_preview: str
    pii_redacted_count: int
    page_count: int
    ocr_engine: str
    sha256_hash: str
    processed_at: str


class UpdateDeadlinesRequest(BaseModel):
    deadlines: list[DeadlineItemSchema]


@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document_upload(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    document_title: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
):
    """
    Accepts file upload (PDF, PNG, JPG, TXT) or raw text for complete legal analysis:
    OCR, language detection, document classification, party extraction, and deadline guardian.
    """
    doc_id = str(uuid.uuid4())
    filename = "document.txt"
    file_bytes = b""
    mime_type = "text/plain"

    if file is not None:
        filename = file.filename or "uploaded_document"
        mime_type = file.content_type or "application/octet-stream"
        file_bytes = await file.read()
        try:
            val_result = DocumentSecurityValidator.validate_file(
                file_bytes, filename=filename, declared_mime=mime_type
            )
            mime_type = val_result["mime_type"]
            file_hash = val_result["sha256_hash"]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif raw_text:
        filename = (document_title or "raw_text_input") + ".txt"
        file_bytes = raw_text.encode("utf-8")
        val_result = DocumentSecurityValidator.validate_file(
            file_bytes, filename=filename, declared_mime="text/plain"
        )
        file_hash = val_result["sha256_hash"]
        mime_type = "text/plain"
    else:
        raise HTTPException(
            status_code=400, detail="Either 'file' or 'raw_text' must be provided."
        )

    # 1. OCR / Text Extraction
    extraction = OCRService.extract_text(file_bytes, mime_type, filename=filename)
    extracted_text = extraction["text"]
    detected_lang = extraction["detected_language"]
    ocr_engine = extraction["engine"]
    page_count = extraction["page_count"]

    # 2. PII Redaction
    redacted_text, redactions = OCRService.redact_pii(extracted_text)

    # 3. Document Classification & Parties
    classification = DocumentClassifier.classify_document(extracted_text)
    parties_meta = DocumentClassifier.extract_metadata_and_parties(extracted_text)

    # 4. Deadline Extraction
    extracted_deadlines = DeadlineGuardian.extract_deadlines(
        extracted_text, page_count=page_count
    )

    # 5. Plain Language Summary & Rights/Next Steps
    doc_type = classification["document_type"]
    plain_summary, next_steps = _generate_plain_summary(
        doc_type, parties_meta, extracted_deadlines, detected_lang
    )

    now_iso = datetime.now(timezone.utc).isoformat()

    stored_data = {
        "document_id": doc_id,
        "session_id": session_id,
        "filename": filename,
        "detected_language": detected_lang,
        "document_type": doc_type,
        "document_description": classification["description"],
        "classification_confidence": classification["confidence"],
        "parties": parties_meta,
        "deadlines": extracted_deadlines,
        "plain_summary": plain_summary,
        "rights_and_next_steps": next_steps,
        "redacted_preview": redacted_text[:500] + ("..." if len(redacted_text) > 500 else ""),
        "pii_redacted_count": len(redactions),
        "page_count": page_count,
        "ocr_engine": ocr_engine,
        "sha256_hash": file_hash,
        "processed_at": now_iso,
    }

    _DOCUMENT_STORE[doc_id] = stored_data

    return DocumentAnalysisResponse(**stored_data)


@router.post("/analyze-text", response_model=DocumentAnalysisResponse)
async def analyze_document_json(request: AnalyzeDocumentTextRequest):
    """JSON body alternative for text-based document analysis."""
    return await analyze_document_upload(
        file=None,
        raw_text=request.raw_text,
        document_title=request.document_title,
        session_id=request.session_id,
    )


@router.get("/{doc_id}", response_model=DocumentAnalysisResponse)
async def get_document_analysis(doc_id: str):
    """Retrieves existing document analysis by document ID."""
    if doc_id not in _DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentAnalysisResponse(**_DOCUMENT_STORE[doc_id])


@router.patch("/{doc_id}/deadlines")
async def update_document_deadlines(doc_id: str, payload: UpdateDeadlinesRequest):
    """Allows user to correct, add, or confirm extracted deadlines."""
    if doc_id not in _DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail="Document not found.")

    _DOCUMENT_STORE[doc_id]["deadlines"] = [d.model_dump() for d in payload.deadlines]
    return {
        "status": "SUCCESS",
        "document_id": doc_id,
        "deadlines_count": len(payload.deadlines),
        "message": "Deadlines updated and confirmed successfully.",
    }


@router.get("/{doc_id}/calendar")
async def download_calendar_ics(doc_id: str):
    """Generates and downloads standard RFC 5545 .ics iCalendar file for confirmed deadlines."""
    if doc_id not in _DOCUMENT_STORE:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc_data = _DOCUMENT_STORE[doc_id]
    deadlines = doc_data.get("deadlines", [])
    if not deadlines:
        raise HTTPException(
            status_code=400, detail="No deadlines found for this document to export."
        )

    ics_content = DeadlineGuardian.generate_ics_calendar(
        deadlines=deadlines,
        document_title=doc_data.get("filename", "Legal Document"),
        doc_id=doc_id,
    )

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=nyayamitra-deadlines-{doc_id[:8]}.ics"
        },
    )


def _generate_plain_summary(
    doc_type: str,
    parties: dict[str, Any],
    deadlines: list[dict[str, Any]],
    lang: str = "en",
) -> tuple[str, list[str]]:
    """Generates plain language summary and actionable next steps."""
    case_no = parties.get("case_number") or "Not Specified"
    authority = parties.get("issuing_authority") or "Legal Authority / Forum"
    petitioner = parties.get("petitioner_or_complainant") or "Claimant"
    respondent = parties.get("respondent_or_accused") or "Opposite Party"

    dl_summary = f"{len(deadlines)} key deadline(s) identified." if deadlines else "No explicit dates detected."

    if lang == "hi":
        summary = (
            f"यह दस्तावेज़ '{doc_type}' श्रेणी का है। "
            f"जारीकर्ता प्राधिकरण: {authority}। "
            f"पक्षकार: {petitioner} बनाम {respondent} (केस नं: {case_no})। "
            f"{dl_summary}"
        )
        steps = [
            "सभी उल्लिखित तारीखों और समय-सीमाओं की पुष्टि करें।",
            "दस्तावेज़ की मूल प्रति सुरक्षित रखें।",
            "यदि यह सम्मन या कोर्ट नोटिस है, तो निर्धारित तारीख पर उपस्थित हों या वकील से परामर्श लें।",
            "निःशुल्क कानूनी सलाह के लिए अपने ज़िला कानूनी सेवा प्राधिकरण (DLSA) से संपर्क करें।",
        ]
    else:
        summary = (
            f"This is a {doc_type.replace('_', ' ').title()} issued by {authority}. "
            f"Parties involved: {petitioner} vs. {respondent} (Ref: {case_no}). "
            f"{dl_summary}"
        )
        steps = [
            "Review and confirm all extracted dates and statutory deadlines in the calendar tab.",
            "Retain all original envelopes and proof of delivery/service timestamps.",
            "If this is a Court Notice or Summons, avoid non-appearance as ex-parte orders may be passed.",
            "Draft a formal reply or seek assistance from your District Legal Services Authority (DLSA).",
        ]

    return summary, steps
