from datetime import datetime, timezone
import pytest
from app.models.schemas import (
    CitationCreate,
    CitationItem,
    DeadlineItem,
    DomainClassificationCreate,
    EscalationResourceCreate,
    EvaluationResultCreate,
    ExtractedDeadlineCreate,
    GeneratedDocumentCreate,
    IntakeStateCreate,
    IntakeStateUpdate,
    LegalDocumentCreate,
    LegalSectionCreate,
    OCRResultCreate,
    RAGResponseContract,
    RetrievalChunkCreate,
    SourceCreate,
    SourceSnapshotCreate,
    UploadedDocumentCreate,
    UserSessionCreate,
)


def test_pydantic_schemas_validation():
    # 1. UserSessionCreate
    session_data = UserSessionCreate(locale="hi", ip_hash="abcdef123456")
    assert session_data.locale == "hi"
    assert session_data.ip_hash == "abcdef123456"

    # 2. IntakeStateCreate
    intake = IntakeStateCreate(
        session_id="dummy-session-id",
        collected_facts={"tenant_name": "Ramesh", "notice_date": "2026-09-01"},
        missing_facts=["rent_agreement_present"],
        confidence_score=0.85,
        is_urgent=True,
        urgency_reason="Notice demands vacation within 48 hours",
    )
    assert intake.session_id == "dummy-session-id"
    assert intake.is_urgent is True

    # 3. DomainClassificationCreate
    domain = DomainClassificationCreate(
        primary_domain="TENANCY",
        confidence=0.95,
        rationale="Dispute regarding eviction notice and rent arrears",
        detected_keywords=["eviction", "rent", "landlord"],
    )
    assert domain.primary_domain == "TENANCY"

    # 4. SourceCreate
    src = SourceCreate(
        source_code="INDIA_CODE",
        name="India Code Official Legislation Portal",
        tier=1,
        publisher="Legislative Department, Ministry of Law and Justice",
        source_url="https://www.indiacode.nic.in",
    )
    assert src.tier == 1

    # 5. LegalDocumentCreate
    doc = LegalDocumentCreate(
        act_code="BNS_2023",
        act_name="Bharatiya Nyaya Sanhita, 2023",
        act_year=2023,
        status="ACTIVE",
        repeals_or_replaces="IPC_1860",
    )
    assert doc.act_code == "BNS_2023"

    # 6. LegalSectionCreate
    sec = LegalSectionCreate(
        document_id="dummy-doc-id",
        section_number="318",
        title="Cheating",
        full_text="Whoever, by deceiving any person, fraudulently or dishonestly induces...",
        plain_english="Cheating involves intentionally deceiving someone to deliver property.",
        penalties="Imprisonment up to 3 years or fine or both; up to 7 years if aggravated.",
        is_cognizable=True,
        is_bailable=False,
    )
    assert sec.section_number == "318"

    # 7. RAG Response Contract Schema
    rag_response = RAGResponseContract(
        summary="Your landlord cannot evict you without due process of law.",
        rights=[
            "Right to reasonable notice before eviction",
            "Protection against arbitrary dispossession under tenancy laws",
        ],
        next_steps=[
            "Draft a formal reply denying illegal eviction claims",
            "Collect all rent receipts and bank transfer records",
        ],
        deadlines=[
            DeadlineItem(
                label="Reply to Landlord Notice",
                relative_timeframe="Within 15 days of notice receipt",
                trigger_event="Receipt of eviction notice",
                statutory_basis="Model Tenancy Act / Delhi Rent Control Act",
                urgency_level="HIGH",
            )
        ],
        citations=[
            CitationItem(
                act_name="Bharatiya Nagarik Suraksha Sanhita, 2023",
                section_number="173",
                quote="Every information relating to the commission of a cognizable offence...",
                official_url="https://www.indiacode.nic.in/handle/123456789/2202",
                is_current_law=True,
                replaces_outdated_law="CrPC Section 154",
            )
        ],
        uncertainties=["Whether there is a registered written tenancy agreement"],
        escalation_needed=False,
    )
    assert rag_response.escalation_needed is False
    assert len(rag_response.citations) == 1
    assert rag_response.citations[0].replaces_outdated_law == "CrPC Section 154"
    assert "AI legal information assistant" in rag_response.disclaimer
