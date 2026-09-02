from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

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
        self, *, user_id: UUID, session_id: UUID, completed_at: datetime | None = None
    ) -> DailySessionCompletion: ...

    async def advance(self, *, user_id: UUID, session_id: UUID) -> DailySessionResponse: ...


class SQLDailySessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(
        self, *, user_id: UUID, plan: DailySessionPlan, content: DailyLessonContent
    ) -> DailySessionResponse:
        user = await self._session.scalar(select(UserRow).where(UserRow.id == user_id))
        if user is not None and user.program_completed_at is not None:
            raise ValueError("The 30-day Bootcamp is complete.")
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
        self, *, user_id: UUID, session_id: UUID, completed_at: datetime | None = None
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
        if not row.completion_ready:
            raise ValueError("Daily session has not reached the recap step.")
        if user.program_completed_at is not None:
            return DailySessionCompletion(
                session_id=row.id, awarded_xp=0, progress=UserState.model_validate(user)
            )
        instant = completed_at or datetime.now(UTC)
        try:
            completed_on = instant.astimezone(ZoneInfo(user.timezone)).date()
        except Exception:
            completed_on = instant.astimezone(UTC).date()

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
        if row.day == 30:
            user.program_completed_at = instant
        row.status = "COMPLETED"
        row.completed_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(user)
        return DailySessionCompletion(
            session_id=row.id,
            awarded_xp=awarded_xp,
            progress=UserState.model_validate(user),
        )

    async def advance(self, *, user_id: UUID, session_id: UUID) -> DailySessionResponse:
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
        payload = row.session_plan or {}
        plan = DailySessionPlan.model_validate(payload["plan"])
        if row.status != "COMPLETED":
            row.current_step = min(row.current_step + 1, len(plan.steps) - 1)
            row.completion_ready = row.current_step == len(plan.steps) - 1
            await self._session.commit()
        return DailySessionResponse(
            session_id=row.id,
            status=row.status,
            current_step=row.current_step,
            completion_ready=row.completion_ready,
            plan=plan,
            content=DailyLessonContent.model_validate(payload["content"]),
        )


class InMemoryDailySessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[tuple[UUID, int], DailySessionResponse] = {}
        self.progress: dict[UUID, UserState] = {}

    async def get_or_create(
        self, *, user_id: UUID, plan: DailySessionPlan, content: DailyLessonContent
    ) -> DailySessionResponse:
        key = (user_id, plan.day)
        if self.progress.get(user_id, UserState(id=user_id)).program_completed_at is not None:
            raise ValueError("The 30-day Bootcamp is complete.")
        if key not in self.sessions:
            self.sessions[key] = DailySessionResponse(
                session_id=uuid4(), plan=plan, content=content
            )
        return self.sessions[key]

    async def complete(
        self, *, user_id: UUID, session_id: UUID, completed_at: datetime | None = None
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
        if not match.completion_ready:
            raise ValueError("Daily session has not reached the recap step.")
        instant = completed_at or datetime.now(UTC)
        try:
            completed_on = instant.astimezone(ZoneInfo(state.timezone)).date()
        except Exception:
            completed_on = instant.astimezone(UTC).date()
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
                "program_completed_at": instant if match.plan.day == 30 else None,
            }
        )
        self.progress[user_id] = progress
        self.sessions[(user_id, match.plan.day)] = match.model_copy(update={"status": "COMPLETED"})
        return DailySessionCompletion(
            session_id=session_id,
            awarded_xp=updated.xp - state.xp,
            progress=progress,
        )

    async def advance(self, *, user_id: UUID, session_id: UUID) -> DailySessionResponse:
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
        if match.status == "COMPLETED":
            return match
        current = min(match.current_step + 1, len(match.plan.steps) - 1)
        updated = match.model_copy(
            update={
                "current_step": current,
                "completion_ready": current == len(match.plan.steps) - 1,
            }
        )
        self.sessions[(user_id, match.plan.day)] = updated
        return updated
