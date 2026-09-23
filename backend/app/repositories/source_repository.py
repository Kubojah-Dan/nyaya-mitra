from datetime import datetime, timezone
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Source, SourceSnapshot
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository[Source]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Source, session)

    async def get_by_code(self, source_code: str) -> Optional[Source]:
        stmt = select(Source).where(Source.source_code == source_code)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_by_tier(self, tier: int) -> Sequence[Source]:
        stmt = select(Source).where(Source.tier == tier, Source.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def record_health_check(self, source_code: str, is_healthy: bool) -> Optional[Source]:
        source = await self.get_by_code(source_code)
        if not source:
            return None
        now = datetime.now(timezone.utc)
        source.last_checked_at = now
        if is_healthy:
            source.last_healthy_at = now
        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def add_snapshot(
        self,
        source_id: str,
        content_hash: str,
        version_label: str,
        raw_content_uri: Optional[str] = None,
        status: str = "SUCCESS",
        item_count: int = 0,
        error_message: Optional[str] = None,
    ) -> SourceSnapshot:
        snapshot = SourceSnapshot(
            source_id=source_id,
            content_hash=content_hash,
            version_label=version_label,
            raw_content_uri=raw_content_uri,
            status=status,
            item_count=item_count,
            error_message=error_message,
        )
        self.session.add(snapshot)
        await self.session.flush()
        await self.session.refresh(snapshot)
        return snapshot

    async def get_latest_snapshot(self, source_id: str) -> Optional[SourceSnapshot]:
        stmt = (
            select(SourceSnapshot)
            .where(SourceSnapshot.source_id == source_id)
            .order_by(SourceSnapshot.fetched_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
