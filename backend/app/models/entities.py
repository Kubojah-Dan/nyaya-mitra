from datetime import datetime, timezone
from typing import Any, Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserSession(Base):
    """Anonymous user session adhering to data minimization."""

    __tablename__ = "user_sessions"

    session_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    locale: Mapped[str] = mapped_column(String(10), default="en")
    disclaimer_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    disclaimer_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    intake_states: Mapped[list["IntakeState"]] = relationship("IntakeState", back_populates="session", cascade="all, delete-orphan")
    uploaded_documents: Mapped[list["UploadedDocument"]] = relationship("UploadedDocument", back_populates="session", cascade="all, delete-orphan")
    generated_documents: Mapped[list["GeneratedDocument"]] = relationship("GeneratedDocument", back_populates="session", cascade="all, delete-orphan")


class IntakeState(Base):
    """Multi-turn intake engine state."""

    __tablename__ = "intake_states"

    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_sessions.id", ondelete="CASCADE"), index=True)
    current_stage: Mapped[str] = mapped_column(String(32), default="INITIAL", index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    subdomain: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    collected_facts: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    missing_facts: Mapped[list[str]] = mapped_column(JSON, default=list)
    user_clarifications: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    urgency_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")

    session: Mapped["UserSession"] = relationship("UserSession", back_populates="intake_states")


class DomainClassification(Base):
    """Domain classification inference log."""

    __tablename__ = "domain_classifications"

    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    intake_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    primary_domain: Mapped[str] = mapped_column(String(64), index=True)
    secondary_domain: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    rationale: Mapped[str] = mapped_column(Text, default="")
    detected_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)


class Source(Base):
    """Official legal source registry."""

    __tablename__ = "sources"

    source_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    tier: Mapped[int] = mapped_column(Integer, default=1)  # 1=Authoritative Primary, 2=Official Secondary, 3=Trusted Secondary
    publisher: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str] = mapped_column(String(512))
    jurisdiction: Mapped[str] = mapped_column(String(128), default="Union of India")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    update_cadence_days: Mapped[int] = mapped_column(Integer, default=7)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_healthy_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    snapshots: Mapped[list["SourceSnapshot"]] = relationship("SourceSnapshot", back_populates="source", cascade="all, delete-orphan")
    documents: Mapped[list["LegalDocument"]] = relationship("LegalDocument", back_populates="source")


class SourceSnapshot(Base):
    """Versioned snapshot of an ingested official source."""

    __tablename__ = "source_snapshots"

    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)  # SHA-256
    version_label: Mapped[str] = mapped_column(String(64))
    raw_content_uri: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="SUCCESS")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    item_count: Mapped[int] = mapped_column(Integer, default=0)

    source: Mapped["Source"] = relationship("Source", back_populates="snapshots")


class LegalDocument(Base):
    """Statute, Act or Regulation document."""

    __tablename__ = "legal_documents"

    source_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    act_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    act_name: Mapped[str] = mapped_column(String(255), index=True)
    act_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    act_year: Mapped[int] = mapped_column(Integer, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(128), default="Union of India")
    enacted_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")  # ACTIVE, REPEALED, SUPERSEDED
    repeals_or_replaces: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="documents")
    sections: Mapped[list["LegalSection"]] = relationship("LegalSection", back_populates="document", cascade="all, delete-orphan")


class LegalSection(Base):
    """Section / Article within an enactment."""

    __tablename__ = "legal_sections"

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("legal_documents.id", ondelete="CASCADE"), index=True)
    chapter: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    section_number: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    subsections: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    full_text: Mapped[str] = mapped_column(Text)
    plain_english: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plain_hindi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    penalties: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_cognizable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_bailable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_compoundable: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    relevant_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)

    document: Mapped["LegalDocument"] = relationship("LegalDocument", back_populates="sections")
    retrieval_chunks: Mapped[list["RetrievalChunk"]] = relationship("RetrievalChunk", back_populates="section", cascade="all, delete-orphan")
    citations: Mapped[list["Citation"]] = relationship("Citation", back_populates="section", cascade="all, delete-orphan")


class Citation(Base):
    """Verified citation record matching statutory ground truth."""

    __tablename__ = "citations"

    section_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("legal_sections.id", ondelete="SET NULL"), nullable=True, index=True)
    act_name: Mapped[str] = mapped_column(String(255), index=True)
    section_number: Mapped[str] = mapped_column(String(32), index=True)
    pinpoint: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    verified_status: Mapped[str] = mapped_column(String(32), default="VERIFIED_TIER_1")  # VERIFIED_TIER_1, UNVERIFIED, OUTDATED_REPEALED
    statutory_quote: Mapped[str] = mapped_column(Text)
    official_url: Mapped[str] = mapped_column(String(512))
    last_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    section: Mapped[Optional["LegalSection"]] = relationship("LegalSection", back_populates="citations")


class RetrievalChunk(Base):
    """Text chunk indexed for hybrid retrieval and semantic matching."""

    __tablename__ = "retrieval_chunks"

    section_id: Mapped[str] = mapped_column(String(36), ForeignKey("legal_sections.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk_text: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding_ref: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    section: Mapped["LegalSection"] = relationship("LegalSection", back_populates="retrieval_chunks")


class UploadedDocument(Base):
    """Short-lived uploaded legal notice / order with strict 24h retention."""

    __tablename__ = "uploaded_documents"

    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_sessions.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(128))
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    file_hash: Mapped[str] = mapped_column(String(64), index=True)  # SHA-256
    storage_path: Mapped[str] = mapped_column(String(512))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    retention_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    redacted_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    session: Mapped["UserSession"] = relationship("UserSession", back_populates="uploaded_documents")
    ocr_results: Mapped[list["OCRResult"]] = relationship("OCRResult", back_populates="uploaded_document", cascade="all, delete-orphan")
    deadlines: Mapped[list["ExtractedDeadline"]] = relationship("ExtractedDeadline", back_populates="uploaded_document", cascade="all, delete-orphan")


class OCRResult(Base):
    """OCR output from uploaded notice."""

    __tablename__ = "ocr_results"

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("uploaded_documents.id", ondelete="CASCADE"), index=True)
    text_extracted: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    detected_language: Mapped[str] = mapped_column(String(10), default="en")
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    ocr_engine: Mapped[str] = mapped_column(String(64), default="mock")
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    uploaded_document: Mapped["UploadedDocument"] = relationship("UploadedDocument", back_populates="ocr_results")


class ExtractedDeadline(Base):
    """Extracted or calculated statutory/contractual deadline."""

    __tablename__ = "extracted_deadlines"

    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("uploaded_documents.id", ondelete="CASCADE"), nullable=True, index=True)
    deadline_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    relative_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    trigger_event: Mapped[str] = mapped_column(String(255))
    label: Mapped[str] = mapped_column(String(255))
    statutory_basis: Mapped[str] = mapped_column(String(512))
    urgency_level: Mapped[str] = mapped_column(String(32), default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW
    is_firm: Mapped[bool] = mapped_column(Boolean, default=True)

    uploaded_document: Mapped[Optional["UploadedDocument"]] = relationship("UploadedDocument", back_populates="deadlines")


class GeneratedDocument(Base):
    """Deterministic slot-filled output document (RTI, Consumer Complaint, Tenant Reply)."""

    __tablename__ = "generated_documents"

    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_sessions.id", ondelete="CASCADE"), index=True)
    document_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    slots_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    markdown_content: Mapped[str] = mapped_column(Text)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    disclaimer_text: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)

    session: Mapped["UserSession"] = relationship("UserSession", back_populates="generated_documents")


class EscalationResource(Base):
    """Official legal aid resources (NALSA, SLSA, DLSA, Tele-Law)."""

    __tablename__ = "escalation_resources"

    resource_type: Mapped[str] = mapped_column(String(32), index=True)  # NALSA, SLSA, DLSA, TALUK, TELE_LAW, CONSUMER_HELPLINE
    name: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(100), index=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    address: Mapped[str] = mapped_column(Text)
    contact_number: Mapped[str] = mapped_column(String(128))
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    languages_supported: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EvaluationResult(Base):
    """Audit log for automated evaluation test cases and quality benchmarking."""

    __tablename__ = "evaluation_results"

    eval_run_id: Mapped[str] = mapped_column(String(64), index=True)
    suite_name: Mapped[str] = mapped_column(String(64), index=True)
    test_case_id: Mapped[str] = mapped_column(String(64), index=True)
    query_prompt: Mapped[str] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(String(64), index=True)
    passed: Mapped[bool] = mapped_column(Boolean, index=True)
    citation_accuracy: Mapped[float] = mapped_column(Float, default=1.0)
    faithfulness_score: Mapped[float] = mapped_column(Float, default=1.0)
    outdated_law_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
