from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import EscalationResource
from app.repositories.base import BaseRepository


class EscalationRepository(BaseRepository[EscalationResource]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(EscalationResource, session)

    async def get_by_jurisdiction(
        self,
        state: str,
        district: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> Sequence[EscalationResource]:
        stmt = select(EscalationResource).where(
            EscalationResource.state.ilike(state),
            EscalationResource.is_active.is_(True),
        )
        if district:
            stmt = stmt.where(EscalationResource.district.ilike(district))
        if resource_type:
            stmt = stmt.where(EscalationResource.resource_type == resource_type)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_national_helplines(self) -> Sequence[EscalationResource]:
        stmt = select(EscalationResource).where(
            EscalationResource.state == "National",
            EscalationResource.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
