from datetime import datetime, timezone
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ExtractedDeadline, OCRResult, UploadedDocument
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[UploadedDocument]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(UploadedDocument, session)

    async def get_active_by_session(self, session_id: str) -> Sequence[UploadedDocument]:
        stmt = (
            select(UploadedDocument)
            .where(
                UploadedDocument.session_id == session_id,
                UploadedDocument.is_deleted.is_(False),
            )
            .order_by(UploadedDocument.uploaded_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def soft_delete(self, document_id: str) -> bool:
        doc = await self.get_by_id(document_id)
        if not doc:
            return False
        doc.is_deleted = True
        doc.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True

    async def purge_expired_documents(self) -> int:
        """Data minimization: Purge/mark expired files past their 24h retention deadline."""
        now = datetime.now(timezone.utc)
        stmt = select(UploadedDocument).where(
            UploadedDocument.retention_deadline < now,
            UploadedDocument.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        expired_docs = result.scalars().all()
        count = 0
        for doc in expired_docs:
            doc.is_deleted = True
            doc.deleted_at = now
            doc.redacted_content = "[PURGED_EXPIRED_RETENTION_DEADLINE]"
            count += 1
        await self.session.flush()
        return count

    async def record_ocr(
        self,
        document_id: str,
        text_extracted: str,
        confidence_score: float,
        detected_language: str = "en",
        page_count: int = 1,
        ocr_engine: str = "mock",
    ) -> OCRResult:
        ocr = OCRResult(
            document_id=document_id,
            text_extracted=text_extracted,
            confidence_score=confidence_score,
            detected_language=detected_language,
            page_count=page_count,
            ocr_engine=ocr_engine,
        )
        self.session.add(ocr)
        await self.session.flush()
        await self.session.refresh(ocr)
        return ocr

    async def add_deadline(
        self,
        trigger_event: str,
        label: str,
        statutory_basis: str,
        urgency_level: str = "MEDIUM",
        session_id: Optional[str] = None,
        document_id: Optional[str] = None,
        deadline_date: Optional[datetime] = None,
        relative_days: Optional[int] = None,
        is_firm: bool = True,
    ) -> ExtractedDeadline:
        deadline = ExtractedDeadline(
            trigger_event=trigger_event,
            label=label,
            statutory_basis=statutory_basis,
            urgency_level=urgency_level,
            session_id=session_id,
            document_id=document_id,
            deadline_date=deadline_date,
            relative_days=relative_days,
            is_firm=is_firm,
        )
        self.session.add(deadline)
        await self.session.flush()
        await self.session.refresh(deadline)
        return deadline
