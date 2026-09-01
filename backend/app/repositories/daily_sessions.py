from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SessionRow
from app.schemas import DailyLessonContent, DailySessionPlan, DailySessionResponse


class DailySessionRepository(Protocol):
    async def get_or_create(
        self, *, user_id: UUID, plan: DailySessionPlan, content: DailyLessonContent
    ) -> DailySessionResponse: ...


class SQLDailySessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(
        self, *, user_id: UUID, plan: DailySessionPlan, content: DailyLessonContent
    ) -> DailySessionResponse:
        row = await self._session.scalar(
            select(SessionRow)
            .where(
                SessionRow.user_id == user_id,
                SessionRow.session_type == "DAILY",
                SessionRow.day == plan.day,
                SessionRow.status == "IN_PROGRESS",
            )
            .order_by(SessionRow.started_at.desc())
        )
        if row is None:
            row = SessionRow(
                id=uuid4(),
                user_id=user_id,
                session_type="DAILY",
                status="IN_PROGRESS",
                questions=[],
                day=plan.day,
                phase=plan.phase,
                duration_plan=plan.duration_minutes,
                topic_family=plan.topic_family,
                scaffolding_level=plan.scaffolding_level,
                session_plan={
                    "plan": plan.model_dump(mode="json"),
                    "content": content.model_dump(),
                },
            )
            self._session.add(row)
            await self._session.commit()
        payload = row.session_plan or {}
        return DailySessionResponse(
            plan=DailySessionPlan.model_validate(payload["plan"]),
            content=DailyLessonContent.model_validate(payload["content"]),
        )


class InMemoryDailySessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[tuple[UUID, int], DailySessionResponse] = {}

    async def get_or_create(
        self, *, user_id: UUID, plan: DailySessionPlan, content: DailyLessonContent
    ) -> DailySessionResponse:
        key = (user_id, plan.day)
        if key not in self.sessions:
            self.sessions[key] = DailySessionResponse(plan=plan, content=content)
        return self.sessions[key]
