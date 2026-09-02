from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserRow
from app.schemas import UserPreferencesUpdate, UserState


class UserRepository(Protocol):
    async def get_or_create(self, user_id: UUID) -> UserState: ...

    async def update_preferences(
        self, user_id: UUID, preferences: UserPreferencesUpdate
    ) -> UserState: ...

    async def update_progress(self, user_id: UUID, progress: UserState) -> UserState: ...


class SQLUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, user_id: UUID) -> UserState:
        statement = (
            insert(UserRow).values(id=user_id).on_conflict_do_nothing(index_elements=[UserRow.id])
        )
        await self._session.execute(statement)
        row = await self._session.scalar(select(UserRow).where(UserRow.id == user_id))
        if row is None:
            raise RuntimeError("Unable to load the authenticated user state.")
        await self._session.commit()
        return UserState.model_validate(row)

    async def update_preferences(
        self, user_id: UUID, preferences: UserPreferencesUpdate
    ) -> UserState:
        await self.get_or_create(user_id)
        row = await self._session.scalar(select(UserRow).where(UserRow.id == user_id))
        if row is None:
            raise RuntimeError("Unable to load the authenticated user state.")
        for field, value in preferences.model_dump().items():
            setattr(row, field, value)
        await self._session.commit()
        await self._session.refresh(row)
        return UserState.model_validate(row)

    async def update_progress(self, user_id: UUID, progress: UserState) -> UserState:
        await self.get_or_create(user_id)
        row = await self._session.scalar(select(UserRow).where(UserRow.id == user_id))
        if row is None:
            raise RuntimeError("Unable to load the authenticated user state.")
        row.xp = progress.xp
        row.current_streak = progress.current_streak
        row.last_completed_date = progress.last_completed_date
        await self._session.commit()
        await self._session.refresh(row)
        return UserState.model_validate(row)
