from datetime import UTC, date, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SessionRow, UserRow
from app.schemas import (
    DailyLessonContent,
    DailySessionCompletion,
    DailySessionPlan,
    DailySessionResponse,
    ProgressState,
    RewardEvent,
    UserState,
)
from app.services.daily_planner import phase_for_day
from app.services.rewards import RewardEngine


class DailySessionRepository(Protocol):
    async def get_or_create(
        self, *, user_id: UUID, plan: DailySessionPlan, content: DailyLessonContent
    ) -> DailySessionResponse: ...

    async def complete(
        self, *, user_id: UUID, session_id: UUID, completed_on: date
    ) -> DailySessionCompletion: ...


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
            session_id=row.id,
            status=row.status,
            plan=DailySessionPlan.model_validate(payload["plan"]),
            content=DailyLessonContent.model_validate(payload["content"]),
        )

    async def complete(
        self, *, user_id: UUID, session_id: UUID, completed_on: date
    ) -> DailySessionCompletion:
        row = await self._session.scalar(
            select(SessionRow)
            .where(
                SessionRow.id == session_id,
                SessionRow.user_id == user_id,
                SessionRow.session_type == "DAILY",
            )
            .with_for_update()
        )
        if row is None:
            raise LookupError("Daily session not found.")

        user = await self._session.scalar(
            select(UserRow).where(UserRow.id == user_id).with_for_update()
        )
        if user is None:
            raise RuntimeError("Unable to load the authenticated user state.")

        if row.status == "COMPLETED":
            return DailySessionCompletion(
                session_id=row.id,
                awarded_xp=0,
                progress=UserState.model_validate(user),
            )

        updated = RewardEngine().apply(
            ProgressState(
                xp=user.xp,
                current_streak=user.current_streak,
                last_completed_date=user.last_completed_date,
            ),
            RewardEvent(event_type="PASSIVE_LEARN", completed_on=completed_on),
        )
        awarded_xp = updated.xp - user.xp
        user.xp = updated.xp
        user.current_streak = updated.current_streak
        user.last_completed_date = updated.last_completed_date
        user.current_day = min((row.day or user.current_day) + 1, 30)
        user.current_phase = phase_for_day(user.current_day)
        row.status = "COMPLETED"
        row.completed_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(user)
        return DailySessionCompletion(
            session_id=row.id,
            awarded_xp=awarded_xp,
            progress=UserState.model_validate(user),
        )


class InMemoryDailySessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[tuple[UUID, int], DailySessionResponse] = {}
        self.progress: dict[UUID, UserState] = {}

    async def get_or_create(
        self, *, user_id: UUID, plan: DailySessionPlan, content: DailyLessonContent
    ) -> DailySessionResponse:
        key = (user_id, plan.day)
        if key not in self.sessions:
            self.sessions[key] = DailySessionResponse(
                session_id=uuid4(), plan=plan, content=content
            )
        return self.sessions[key]

    async def complete(
        self, *, user_id: UUID, session_id: UUID, completed_on: date
    ) -> DailySessionCompletion:
        match = next(
            (
                item
                for (owner, _), item in self.sessions.items()
                if owner == user_id and item.session_id == session_id
            ),
            None,
        )
        if match is None:
            raise LookupError("Daily session not found.")
        state = self.progress.setdefault(user_id, UserState(id=user_id))
        if match.status == "COMPLETED":
            return DailySessionCompletion(session_id=session_id, awarded_xp=0, progress=state)
        updated = RewardEngine().apply(
            ProgressState(
                xp=state.xp,
                current_streak=state.current_streak,
                last_completed_date=state.last_completed_date,
            ),
            RewardEvent(event_type="PASSIVE_LEARN", completed_on=completed_on),
        )
        progress = state.model_copy(
            update={
                "xp": updated.xp,
                "current_streak": updated.current_streak,
                "last_completed_date": updated.last_completed_date,
                "current_day": min(match.plan.day + 1, 30),
                "current_phase": phase_for_day(min(match.plan.day + 1, 30)),
            }
        )
        self.progress[user_id] = progress
        self.sessions[(user_id, match.plan.day)] = match.model_copy(update={"status": "COMPLETED"})
        return DailySessionCompletion(
            session_id=session_id,
            awarded_xp=updated.xp - state.xp,
            progress=progress,
        )
