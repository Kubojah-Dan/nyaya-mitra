"""
NyayaMitra Document Comparison Router
Provides high-performance REST endpoints to compare legal documents, agreements,
court notices, and amendments. Integrates structural alignment, deterministic diffing,
and GenAI semantic synthesis (Tier 3 REASONING).

Endpoints:
- POST /api/v1/documents/compare (JSON or Multipart file upload)

Complexity:
- Time: O(N * M) for section sequence alignment, where N, M are clause counts (typically < 100).
- Space: O(N + M) memory footprint; temporary upload streams validated up to 10MB per file.
"""

import logging
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.compare_service import (
    CompareService,
    DocumentCompareRequest,
    DocumentCompareResponse,
)
from app.services.ocr_service import DocumentSecurityValidator, OCRService

logger = logging.getLogger("nyayamitra.router.compare")

router = APIRouter(prefix="/documents", tags=["compare"])


@router.post("/compare", response_model=DocumentCompareResponse)
async def compare_legal_documents(
    file_a: Optional[UploadFile] = File(None),
    file_b: Optional[UploadFile] = File(None),
    document_a: Optional[str] = Form(None),
    document_b: Optional[str] = Form(None),
    title_a: Optional[str] = Form("Original Document (A)"),
    title_b: Optional[str] = Form("Revised Document (B)"),
    language: Optional[str] = Form("en"),
    session_id: Optional[str] = Form(None),
):
    """
    Compares two legal documents (uploaded files or raw text strings) and produces
    structured section-level deltas, additions, removals, modifications, citations, and plain-language summary.
    """
    text_a = ""
    text_b = ""
    resolved_title_a = title_a or "Document A"
    resolved_title_b = title_b or "Document B"

    # Extract Document A
    if file_a is not None:
        filename_a = file_a.filename or "doc_a.txt"
        mime_a = file_a.content_type or "application/octet-stream"
        bytes_a = await file_a.read()
        try:
            val_a = DocumentSecurityValidator.validate_file(bytes_a, filename=filename_a, declared_mime=mime_a)
            text_a = OCRService.extract_text(bytes_a, val_a["mime_type"], filename=filename_a)["text"]
            resolved_title_a = filename_a
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid file A: {str(e)}") from e
    elif document_a:
        text_a = document_a
    else:
        raise HTTPException(status_code=400, detail="Document A (file_a or document_a) is required.")

    # Extract Document B
    if file_b is not None:
        filename_b = file_b.filename or "doc_b.txt"
        mime_b = file_b.content_type or "application/octet-stream"
        bytes_b = await file_b.read()
        try:
            val_b = DocumentSecurityValidator.validate_file(bytes_b, filename=filename_b, declared_mime=mime_b)
            text_b = OCRService.extract_text(bytes_b, val_b["mime_type"], filename=filename_b)["text"]
            resolved_title_b = filename_b
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid file B: {str(e)}") from e
    elif document_b:
        text_b = document_b
    else:
        raise HTTPException(status_code=400, detail="Document B (file_b or document_b) is required.")

    req = DocumentCompareRequest(
        document_a=text_a,
        document_b=text_b,
        title_a=resolved_title_a,
        title_b=resolved_title_b,
        language=language or "en",
        session_id=session_id,
    )

    try:
        return CompareService.compare(req)
    except Exception as exc:
        logger.error(f"Error executing document compare: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process document comparison.") from exc


@router.post("/compare-json", response_model=DocumentCompareResponse)
async def compare_legal_documents_json(request: DocumentCompareRequest):
    """
    JSON alternative for pure text-based legal document comparison.
    """
    if not request.document_a.strip() or not request.document_b.strip():
        raise HTTPException(status_code=400, detail="Both document_a and document_b must be non-empty.")

    try:
        return CompareService.compare(request)
    except Exception as exc:
        logger.error(f"Error executing document compare json: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process document comparison.") from exc
