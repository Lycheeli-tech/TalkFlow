from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExpressionRow, RetrievalOpportunityRow, SessionRow
from app.schemas import RetrievalOpportunity


class RetrievalOpportunityRepository(Protocol):
    async def create(self, opportunity: RetrievalOpportunity) -> RetrievalOpportunity: ...
    async def get(self, opportunity_id: UUID, user_id: UUID) -> RetrievalOpportunity | None: ...
    async def consume(self, opportunity_id: UUID, user_id: UUID) -> RetrievalOpportunity: ...


class InMemoryRetrievalOpportunityRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, RetrievalOpportunity] = {}

    async def create(self, opportunity: RetrievalOpportunity) -> RetrievalOpportunity:
        self.items[opportunity.id] = opportunity
        return opportunity

    async def get(self, opportunity_id: UUID, user_id: UUID) -> RetrievalOpportunity | None:
        value = self.items.get(opportunity_id)
        return value if value and value.user_id == user_id else None

    async def consume(self, opportunity_id: UUID, user_id: UUID) -> RetrievalOpportunity:
        value = await self.get(opportunity_id, user_id)
        if value is None:
            raise LookupError("Retrieval opportunity was not found for this user.")
        if value.status != "CREATED":
            raise ValueError("Retrieval opportunity has already been consumed.")
        value = value.model_copy(update={"status": "CONSUMED", "consumed_at": datetime.now(UTC)})
        self.items[value.id] = value
        return value


class SQLRetrievalOpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, opportunity: RetrievalOpportunity) -> RetrievalOpportunity:
        expression = await self.session.scalar(
            select(ExpressionRow.id).where(
                ExpressionRow.id == opportunity.expression_id,
                ExpressionRow.user_id == opportunity.user_id,
            )
        )
        daily_session = await self.session.scalar(
            select(SessionRow.id).where(
                SessionRow.id == opportunity.session_id,
                SessionRow.user_id == opportunity.user_id,
                SessionRow.session_type == "DAILY",
                SessionRow.status == "IN_PROGRESS",
            )
        )
        if expression is None or daily_session is None:
            raise PermissionError("Opportunity requires user-owned Expression and Daily Session.")
        self.session.add(RetrievalOpportunityRow(**opportunity.model_dump()))
        await self.session.commit()
        return opportunity

    async def get(self, opportunity_id: UUID, user_id: UUID) -> RetrievalOpportunity | None:
        row = await self.session.scalar(
            select(RetrievalOpportunityRow).where(
                RetrievalOpportunityRow.id == opportunity_id,
                RetrievalOpportunityRow.user_id == user_id,
            )
        )
        return RetrievalOpportunity.model_validate(row) if row else None

    async def consume(self, opportunity_id: UUID, user_id: UUID) -> RetrievalOpportunity:
        result = await self.session.execute(
            update(RetrievalOpportunityRow)
            .where(
                RetrievalOpportunityRow.id == opportunity_id,
                RetrievalOpportunityRow.user_id == user_id,
                RetrievalOpportunityRow.status == "CREATED",
            )
            .values(status="CONSUMED", consumed_at=datetime.now(UTC))
        )
        if result.rowcount != 1:
            raise ValueError("Retrieval opportunity is missing or already consumed.")
        await self.session.commit()
        value = await self.get(opportunity_id, user_id)
        if value is None:
            raise LookupError("Consumed retrieval opportunity could not be loaded.")
        return value
