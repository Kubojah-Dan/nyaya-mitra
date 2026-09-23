import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.entities import (
    Citation,
    DomainClassification,
    EscalationResource,
    EvaluationResult,
    ExtractedDeadline,
    GeneratedDocument,
    IntakeState,
    LegalDocument,
    LegalSection,
    OCRResult,
    RetrievalChunk,
    Source,
    SourceSnapshot,
    UploadedDocument,
    UserSession,
)

# In-memory test SQLite engine
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_database_all_15_tables_created(test_engine):
    """Verify that all 15 tables are mapped and created in the database schema."""
    async with test_engine.connect() as conn:
        table_names = await conn.run_sync(lambda sync_conn: Base.metadata.tables.keys())
        expected_tables = {
            "user_sessions",
            "intake_states",
            "domain_classifications",
            "sources",
            "source_snapshots",
            "legal_documents",
            "legal_sections",
            "citations",
            "retrieval_chunks",
            "uploaded_documents",
            "ocr_results",
            "extracted_deadlines",
            "generated_documents",
            "escalation_resources",
            "evaluation_results",
        }
        for table in expected_tables:
            assert table in table_names, f"Missing table in metadata: {table}"
