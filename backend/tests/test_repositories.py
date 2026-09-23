from datetime import datetime, timedelta, timezone
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.repositories import (
    DocumentRepository,
    EscalationRepository,
    IntakeRepository,
    LegalCorpusRepository,
    SessionRepository,
    SourceRepository,
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(TEST_DB_URL, echo=False, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as sess:
        yield sess
        await sess.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_session_lifecycle_and_disclaimer(session: AsyncSession):
    repo = SessionRepository(session)
    user_session = await repo.create_anonymous_session(locale="en", ip_hash="hash_123")
    assert user_session.id is not None
    assert user_session.disclaimer_accepted is False

    # Accept disclaimer
    updated = await repo.accept_disclaimer(user_session.id)
    assert updated is not None
    assert updated.disclaimer_accepted is True
    assert updated.disclaimer_accepted_at is not None

    # Lookup by token
    fetched = await repo.get_by_token(user_session.session_token)
    assert fetched is not None
    assert fetched.id == user_session.id


@pytest.mark.asyncio
async def test_intake_facts_and_urgency(session: AsyncSession):
    sess_repo = SessionRepository(session)
    user_sess = await sess_repo.create_anonymous_session()

    intake_repo = IntakeRepository(session)
    intake = await intake_repo.create(
        session_id=user_sess.id,
        current_stage="INITIAL",
        domain="CONSUMER",
        collected_facts={"product": "Mobile Phone", "defect": "Battery exploding"},
    )
    assert intake.domain == "CONSUMER"

    # Update facts and mark urgent
    updated = await intake_repo.update_facts(
        intake_id=intake.id,
        facts={"purchase_date": "2026-08-10"},
        stage="FACTS_GATHERING",
        confidence_score=0.9,
    )
    assert updated is not None
    assert updated.collected_facts["product"] == "Mobile Phone"
    assert updated.collected_facts["purchase_date"] == "2026-08-10"
    assert updated.current_stage == "FACTS_GATHERING"

    urgent_intake = await intake_repo.flag_urgency(intake.id, "Physical safety hazard reported")
    assert urgent_intake is not None
    assert urgent_intake.is_urgent is True
    assert urgent_intake.urgency_reason == "Physical safety hazard reported"


@pytest.mark.asyncio
async def test_legal_corpus_and_citations(session: AsyncSession):
    corpus_repo = LegalCorpusRepository(session)
    doc = await corpus_repo.create(
        act_code="BNS_2023",
        act_name="Bharatiya Nyaya Sanhita, 2023",
        act_year=2023,
        status="ACTIVE",
        repeals_or_replaces="IPC_1860",
    )
    assert doc.id is not None

    section = await corpus_repo.add_section(
        document_id=doc.id,
        section_number="318",
        title="Cheating",
        full_text="Whoever, by deceiving any person...",
        plain_english="Deceiving someone to dishonestly obtain property.",
        penalties="Imprisonment up to 3 years or fine or both.",
        is_cognizable=True,
    )
    assert section.id is not None

    # Retrieve section
    retrieved = await corpus_repo.get_section("BNS_2023", "318")
    assert retrieved is not None
    assert retrieved.title == "Cheating"

    # Add citation
    citation = await corpus_repo.add_citation(
        section_id=section.id,
        act_name="Bharatiya Nyaya Sanhita, 2023",
        section_number="318",
        statutory_quote="Whoever, by deceiving any person...",
        official_url="https://www.indiacode.nic.in/handle/123456789/2201",
    )
    assert citation.id is not None
    assert citation.verified_status == "VERIFIED_TIER_1"


@pytest.mark.asyncio
async def test_privacy_retention_purging(session: AsyncSession):
    sess_repo = SessionRepository(session)
    user_sess = await sess_repo.create_anonymous_session()

    doc_repo = DocumentRepository(session)
    # Create an expired document (uploaded 25 hours ago, retention deadline in past)
    past_time = datetime.now(timezone.utc) - timedelta(hours=25)
    expired_deadline = datetime.now(timezone.utc) - timedelta(hours=1)

    expired_doc = await doc_repo.create(
        session_id=user_sess.id,
        original_filename="eviction_notice.pdf",
        mime_type="application/pdf",
        file_size_bytes=1024,
        file_hash="sha256_dummy_hash",
        storage_path="/uploads/notice.pdf",
        uploaded_at=past_time,
        retention_deadline=expired_deadline,
        is_deleted=False,
    )

    # Purge expired documents
    purged_count = await doc_repo.purge_expired_documents()
    assert purged_count == 1

    # Verify doc is soft-deleted and content redacted
    fetched = await doc_repo.get_by_id(expired_doc.id)
    assert fetched is not None
    assert fetched.is_deleted is True
    assert fetched.redacted_content == "[PURGED_EXPIRED_RETENTION_DEADLINE]"


@pytest.mark.asyncio
async def test_escalation_resources_lookup(session: AsyncSession):
    repo = EscalationRepository(session)
    await repo.create(
        resource_type="SLSA",
        name="Delhi State Legal Services Authority",
        state="Delhi",
        district="Central",
        address="Patiala House Courts Complex, New Delhi",
        contact_number="011-23384781",
        email="dslsa-phc@nic.in",
        website_url="https://dslsa.org",
        languages_supported=["Hindi", "English"],
    )
    await repo.create(
        resource_type="NALSA",
        name="NALSA National Legal Aid Helpline",
        state="National",
        address="Jamnagar House, Shahjahan Road, New Delhi",
        contact_number="15100",
        website_url="https://nalsa.gov.in",
        languages_supported=["Hindi", "English", "Regional"],
    )

    delhi_resources = await repo.get_by_jurisdiction(state="Delhi")
    assert len(delhi_resources) == 1
    assert delhi_resources[0].name == "Delhi State Legal Services Authority"

    national = await repo.get_national_helplines()
    assert len(national) == 1
    assert national[0].contact_number == "15100"
