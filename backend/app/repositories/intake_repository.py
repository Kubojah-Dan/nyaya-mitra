from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import IntakeState
from app.repositories.base import BaseRepository


class IntakeRepository(BaseRepository[IntakeState]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(IntakeState, session)

    async def get_by_session_id(self, session_id: str) -> Optional[IntakeState]:
        stmt = (
            select(IntakeState)
            .where(IntakeState.session_id == session_id)
            .order_by(IntakeState.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_facts(
        self,
        intake_id: str,
        facts: dict[str, Any],
        missing_facts: Optional[list[str]] = None,
        confidence_score: Optional[float] = None,
        stage: Optional[str] = None,
    ) -> Optional[IntakeState]:
        intake = await self.get_by_id(intake_id)
        if not intake:
            return None

        current_facts = dict(intake.collected_facts or {})
        current_facts.update(facts)
        intake.collected_facts = current_facts

        if missing_facts is not None:
            intake.missing_facts = missing_facts
        if confidence_score is not None:
            intake.confidence_score = confidence_score
        if stage is not None:
            intake.current_stage = stage

        await self.session.flush()
        await self.session.refresh(intake)
        return intake

    async def flag_urgency(self, intake_id: str, reason: str) -> Optional[IntakeState]:
        intake = await self.get_by_id(intake_id)
        if intake:
            intake.is_urgent = True
            intake.urgency_reason = reason
            await self.session.flush()
            await self.session.refresh(intake)
        return intake
