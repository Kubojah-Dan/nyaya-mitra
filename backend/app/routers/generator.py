"""
NyayaMitra Controlled Document Generator ("Mera Document") Router
Provides REST endpoints for listing templates, slot validation,
deterministic document generation, and multi-format downloads.
"""

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.services.document_generator import DocumentGeneratorService

router = APIRouter(prefix="/generator", tags=["generator"])

# In-memory store for generated documents
_GENERATED_STORE: dict[str, dict[str, Any]] = {}


class ValidateSlotsRequest(BaseModel):
    template_id: str
    slots: dict[str, Any] = Field(default_factory=dict)


class GenerateDocumentRequest(BaseModel):
    template_id: str
    slots: dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None


class GenerateDocumentResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    session_id: Optional[str] = None
    template_id: Optional[str] = None
    title: Optional[str] = None
    statutory_basis: Optional[str] = None
    markdown_content: Optional[str] = None
    disclaimer: Optional[str] = None
    slots_used: Optional[dict[str, Any]] = None
    version: Optional[str] = None
    sha256_hash: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None
    missing_fields: Optional[list[dict[str, Any]]] = None


@router.get("/templates")
async def list_templates():
    """Returns all available legal document templates and their slot requirements."""
    templates = DocumentGeneratorService.list_templates()
    return {"templates": templates, "count": len(templates)}


@router.get("/templates/{template_id}")
async def get_template_spec(template_id: str):
    """Returns detailed specification and fields for a single template."""
    tmpl = DocumentGeneratorService.get_template(template_id.upper())
    if not tmpl:
        raise HTTPException(
            status_code=404, detail=f"Template '{template_id}' not found."
        )
    return tmpl


@router.post("/validate")
async def validate_template_slots(payload: ValidateSlotsRequest):
    """Validates user-submitted slots against a template schema."""
    result = DocumentGeneratorService.validate_slots(
        template_id=payload.template_id.upper(), slots_data=payload.slots
    )
    if "error" in result and not result.get("valid"):
        if "Unknown template" in result.get("error", ""):
            raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/generate", response_model=GenerateDocumentResponse)
async def generate_legal_document(payload: GenerateDocumentRequest):
    """
    Deterministically fills slots into approved Indian legal templates,
    validates completeness, and attaches mandatory statutory disclaimers.
    """
    result = DocumentGeneratorService.generate_document(
        template_id=payload.template_id.upper(),
        slots_data=payload.slots,
        session_id=payload.session_id,
    )

    if not result.get("success"):
        return GenerateDocumentResponse(**result)

    doc_id = result["document_id"]
    _GENERATED_STORE[doc_id] = result
    return GenerateDocumentResponse(**result)


@router.get("/documents/{doc_id}", response_model=GenerateDocumentResponse)
async def get_generated_document(doc_id: str):
    """Retrieves a previously generated legal document by ID."""
    if doc_id not in _GENERATED_STORE:
        raise HTTPException(status_code=404, detail="Generated document not found.")
    return GenerateDocumentResponse(**_GENERATED_STORE[doc_id])


@router.get("/download/{doc_id}")
async def download_generated_document(
    doc_id: str,
    format: str = Query(
        "md", enum=["md", "txt", "html"], description="Download format"
    ),
):
    """Downloads the generated legal draft as Markdown, Plain Text, or HTML."""
    if doc_id not in _GENERATED_STORE:
        raise HTTPException(status_code=404, detail="Generated document not found.")

    doc = _GENERATED_STORE[doc_id]
    md_content = doc.get("markdown_content", "")
    tmpl_id = doc.get("template_id", "document").lower()

    if format == "txt":
        # Plain text without markdown symbols
        txt_content = md_content.replace("#", "").replace("**", "").replace("*", "")
        return Response(
            content=txt_content,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={tmpl_id}-{doc_id[:8]}.txt"
            },
        )
    elif format == "html":
        # Clean HTML wrapper
        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{doc.get('title', 'NyayaMitra Legal Draft')}</title>
<style>
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; color: #222; }}
h1, h2, h3 {{ color: #1a365d; }}
hr {{ border: 0; border-top: 1px solid #ccc; margin: 20px 0; }}
blockquote {{ border-left: 4px solid #3182ce; padding-left: 15px; color: #4a5568; margin: 20px 0; background: #ebf8ff; padding: 10px; }}
pre {{ white-space: pre-wrap; }}
</style>
</head>
<body>
<pre>{md_content}</pre>
</body>
</html>"""
        return Response(
            content=html_content,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={tmpl_id}-{doc_id[:8]}.html"
            },
        )
    else:  # md
        return Response(
            content=md_content,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={tmpl_id}-{doc_id[:8]}.md"
            },
        )
