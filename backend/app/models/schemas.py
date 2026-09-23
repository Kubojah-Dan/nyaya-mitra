from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- 1. User Session ---
class UserSessionBase(BaseSchema):
    locale: str = "en"
    disclaimer_accepted: bool = False


class UserSessionCreate(UserSessionBase):
    ip_hash: Optional[str] = None
    user_agent_hash: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class UserSessionResponse(UserSessionBase):
    id: str
    session_token: str
    disclaimer_accepted_at: Optional[datetime] = None
    expires_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- 2. Intake State ---
class IntakeStateBase(BaseSchema):
    current_stage: str = "INITIAL"
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    collected_facts: dict[str, Any] = Field(default_factory=dict)
    missing_facts: list[str] = Field(default_factory=list)
    user_clarifications: list[dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = 0.0
    is_urgent: bool = False
    urgency_reason: Optional[str] = None
    language: str = "en"


class IntakeStateCreate(IntakeStateBase):
    session_id: str


class IntakeStateUpdate(BaseSchema):
    current_stage: Optional[str] = None
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    collected_facts: Optional[dict[str, Any]] = None
    missing_facts: Optional[list[str]] = None
    user_clarifications: Optional[list[dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    is_urgent: Optional[bool] = None
    urgency_reason: Optional[str] = None
    language: Optional[str] = None


class IntakeStateResponse(IntakeStateBase):
    id: str
    session_id: str
    created_at: datetime
    updated_at: datetime


# --- 3. Domain Classification ---
class DomainClassificationCreate(BaseSchema):
    session_id: Optional[str] = None
    intake_id: Optional[str] = None
    primary_domain: str
    secondary_domain: Optional[str] = None
    confidence: float
    rationale: str
    detected_keywords: list[str] = Field(default_factory=list)


class DomainClassificationResponse(DomainClassificationCreate):
    id: str
    created_at: datetime


# --- 4. Source ---
class SourceBase(BaseSchema):
    source_code: str
    name: str
    tier: int = 1
    publisher: str
    source_url: str
    jurisdiction: str = "Union of India"
    is_active: bool = True
    update_cadence_days: int = 7


class SourceCreate(SourceBase):
    pass


class SourceResponse(SourceBase):
    id: str
    last_checked_at: Optional[datetime] = None
    last_healthy_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# --- 5. Source Snapshot ---
class SourceSnapshotCreate(BaseSchema):
    source_id: str
    content_hash: str
    version_label: str
    raw_content_uri: Optional[str] = None
    status: str = "SUCCESS"
    error_message: Optional[str] = None
    item_count: int = 0


class SourceSnapshotResponse(SourceSnapshotCreate):
    id: str
    fetched_at: datetime
    created_at: datetime


# --- 6. Legal Document ---
class LegalDocumentBase(BaseSchema):
    act_code: str
    act_name: str
    act_number: Optional[str] = None
    act_year: int
    jurisdiction: str = "Union of India"
    enacted_date: Optional[datetime] = None
    effective_from: Optional[datetime] = None
    status: str = "ACTIVE"
    repeals_or_replaces: Optional[str] = None


class LegalDocumentCreate(LegalDocumentBase):
    source_id: Optional[str] = None


class LegalDocumentResponse(LegalDocumentBase):
    id: str
    source_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# --- 7. Legal Section ---
class LegalSectionBase(BaseSchema):
    chapter: Optional[str] = None
    section_number: str
    title: str
    subsections: list[dict[str, Any]] = Field(default_factory=list)
    full_text: str
    plain_english: Optional[str] = None
    plain_hindi: Optional[str] = None
    penalties: Optional[str] = None
    is_cognizable: Optional[bool] = None
    is_bailable: Optional[bool] = None
    is_compoundable: Optional[bool] = None
    relevant_keywords: list[str] = Field(default_factory=list)


class LegalSectionCreate(LegalSectionBase):
    document_id: str


class LegalSectionResponse(LegalSectionBase):
    id: str
    document_id: str
    created_at: datetime
    updated_at: datetime


# --- 8. Citation ---
class CitationBase(BaseSchema):
    act_name: str
    section_number: str
    pinpoint: Optional[str] = None
    verified_status: str = "VERIFIED_TIER_1"
    statutory_quote: str
    official_url: str


class CitationCreate(CitationBase):
    section_id: Optional[str] = None


class CitationResponse(CitationBase):
    id: str
    section_id: Optional[str] = None
    last_verified_at: datetime
    created_at: datetime


# --- 9. Retrieval Chunk ---
class RetrievalChunkCreate(BaseSchema):
    section_id: str
    chunk_index: int = 0
    chunk_text: str
    token_count: int = 0
    embedding_ref: Optional[str] = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class RetrievalChunkResponse(RetrievalChunkCreate):
    id: str
    created_at: datetime


# --- 10. Uploaded Document ---
class UploadedDocumentCreate(BaseSchema):
    session_id: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    file_hash: str
    storage_path: str
    retention_deadline: datetime


class UploadedDocumentResponse(BaseSchema):
    id: str
    session_id: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    file_hash: str
    uploaded_at: datetime
    retention_deadline: datetime
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    redacted_content: Optional[str] = None
    created_at: datetime


# --- 11. OCR Result ---
class OCRResultCreate(BaseSchema):
    document_id: str
    text_extracted: str
    confidence_score: float = 0.0
    detected_language: str = "en"
    page_count: int = 1
    ocr_engine: str = "mock"


class OCRResultResponse(OCRResultCreate):
    id: str
    processed_at: datetime
    created_at: datetime


# --- 12. Extracted Deadline ---
class ExtractedDeadlineBase(BaseSchema):
    deadline_date: Optional[datetime] = None
    relative_days: Optional[int] = None
    trigger_event: str
    label: str
    statutory_basis: str
    urgency_level: str = "MEDIUM"
    is_firm: bool = True


class ExtractedDeadlineCreate(ExtractedDeadlineBase):
    session_id: Optional[str] = None
    document_id: Optional[str] = None


class ExtractedDeadlineResponse(ExtractedDeadlineBase):
    id: str
    session_id: Optional[str] = None
    document_id: Optional[str] = None
    created_at: datetime


# --- 13. Generated Document ---
class GeneratedDocumentCreate(BaseSchema):
    session_id: str
    document_type: str
    title: str
    slots_data: dict[str, Any] = Field(default_factory=dict)
    markdown_content: str
    pdf_path: Optional[str] = None
    disclaimer_text: str
    version: int = 1


class GeneratedDocumentResponse(GeneratedDocumentCreate):
    id: str
    created_at: datetime
    updated_at: datetime


# --- 14. Escalation Resource ---
class EscalationResourceBase(BaseSchema):
    resource_type: str
    name: str
    state: str
    district: Optional[str] = None
    address: str
    contact_number: str
    email: Optional[str] = None
    website_url: Optional[str] = None
    languages_supported: list[str] = Field(default_factory=list)
    is_active: bool = True


class EscalationResourceCreate(EscalationResourceBase):
    pass


class EscalationResourceResponse(EscalationResourceBase):
    id: str
    verified_at: datetime
    created_at: datetime


# --- 15. Evaluation Result ---
class EvaluationResultCreate(BaseSchema):
    eval_run_id: str
    suite_name: str
    test_case_id: str
    query_prompt: str
    domain: str
    passed: bool
    citation_accuracy: float = 1.0
    faithfulness_score: float = 1.0
    outdated_law_detected: bool = False
    latency_ms: int = 0
    details_json: dict[str, Any] = Field(default_factory=dict)


class EvaluationResultResponse(EvaluationResultCreate):
    id: str
    created_at: datetime


# --- RAG Contract Schemas ---
class CitationItem(BaseSchema):
    act_name: str
    section_number: str
    pinpoint: Optional[str] = None
    quote: str
    official_url: str
    is_current_law: bool = True
    replaces_outdated_law: Optional[str] = None


class DeadlineItem(BaseSchema):
    label: str
    deadline_date: Optional[str] = None
    relative_timeframe: Optional[str] = None
    trigger_event: str
    statutory_basis: str
    urgency_level: str = "MEDIUM"


class RAGResponseContract(BaseSchema):
    """The mandatory structured output contract for legal assistance."""
    summary: str
    rights: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    deadlines: list[DeadlineItem] = Field(default_factory=list)
    citations: list[CitationItem] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    escalation_needed: bool = False
    escalation_reason: Optional[str] = None
    disclaimer: str = (
        "NyayaMitra is an AI legal information assistant and not a law firm. "
        "This response is for informational purposes only and does not constitute legal advice."
    )
