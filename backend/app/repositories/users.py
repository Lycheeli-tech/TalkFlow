from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserRow
from app.schemas import UserState


class UserRepository(Protocol):
    async def get_or_create(self, user_id: UUID) -> UserState: ...


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
