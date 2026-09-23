import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import UserSession
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[UserSession]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(UserSession, session)

    async def create_anonymous_session(
        self,
        locale: str = "en",
        ip_hash: Optional[str] = None,
        user_agent_hash: Optional[str] = None,
        duration_hours: int = 24,
    ) -> UserSession:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        return await self.create(
            session_token=token,
            locale=locale,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
            expires_at=expires,
            is_active=True,
            disclaimer_accepted=False,
        )

    async def get_by_token(self, token: str) -> Optional[UserSession]:
        stmt = select(UserSession).where(
            UserSession.session_token == token,
            UserSession.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        user_session = result.scalars().first()
        if user_session:
            expires = user_session.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                user_session.is_active = False
                await self.session.flush()
                return None
        return user_session

    async def accept_disclaimer(self, session_id: str) -> Optional[UserSession]:
        user_session = await self.get_by_id(session_id)
        if user_session:
            user_session.disclaimer_accepted = True
            user_session.disclaimer_accepted_at = datetime.now(timezone.utc)
            await self.session.flush()
            await self.session.refresh(user_session)
        return user_session
