from typing import Optional, Sequence
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import Citation, LegalDocument, LegalSection, RetrievalChunk
from app.repositories.base import BaseRepository


class LegalCorpusRepository(BaseRepository[LegalDocument]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(LegalDocument, session)

    async def get_by_act_code(self, act_code: str) -> Optional[LegalDocument]:
        stmt = (
            select(LegalDocument)
            .where(LegalDocument.act_code == act_code)
            .options(selectinload(LegalDocument.sections))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_section(self, act_code: str, section_number: str) -> Optional[LegalSection]:
        stmt = (
            select(LegalSection)
            .join(LegalDocument, LegalSection.document_id == LegalDocument.id)
            .where(
                LegalDocument.act_code == act_code,
                LegalSection.section_number == section_number,
            )
            .options(selectinload(LegalSection.document), selectinload(LegalSection.citations))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def search_sections(
        self,
        query_text: str,
        act_codes: Optional[list[str]] = None,
        limit: int = 10,
    ) -> Sequence[LegalSection]:
        stmt = select(LegalSection).join(LegalDocument, LegalSection.document_id == LegalDocument.id)

        if act_codes:
            stmt = stmt.where(LegalDocument.act_code.in_(act_codes))

        search_filter = or_(
            LegalSection.title.ilike(f"%{query_text}%"),
            LegalSection.full_text.ilike(f"%{query_text}%"),
            LegalSection.plain_english.ilike(f"%{query_text}%"),
        )
        stmt = stmt.where(search_filter).options(selectinload(LegalSection.document)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_section(
        self,
        document_id: str,
        section_number: str,
        title: str,
        full_text: str,
        chapter: Optional[str] = None,
        plain_english: Optional[str] = None,
        plain_hindi: Optional[str] = None,
        penalties: Optional[str] = None,
        is_cognizable: Optional[bool] = None,
        is_bailable: Optional[bool] = None,
        is_compoundable: Optional[bool] = None,
    ) -> LegalSection:
        section = LegalSection(
            document_id=document_id,
            section_number=section_number,
            title=title,
            full_text=full_text,
            chapter=chapter,
            plain_english=plain_english,
            plain_hindi=plain_hindi,
            penalties=penalties,
            is_cognizable=is_cognizable,
            is_bailable=is_bailable,
            is_compoundable=is_compoundable,
        )
        self.session.add(section)
        await self.session.flush()
        await self.session.refresh(section)
        return section

    async def add_citation(
        self,
        section_id: Optional[str],
        act_name: str,
        section_number: str,
        statutory_quote: str,
        official_url: str,
        pinpoint: Optional[str] = None,
        verified_status: str = "VERIFIED_TIER_1",
    ) -> Citation:
        citation = Citation(
            section_id=section_id,
            act_name=act_name,
            section_number=section_number,
            pinpoint=pinpoint,
            statutory_quote=statutory_quote,
            official_url=official_url,
            verified_status=verified_status,
        )
        self.session.add(citation)
        await self.session.flush()
        await self.session.refresh(citation)
        return citation
