from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AttemptRow, LearnerAssessmentRow, SessionRow
from app.schemas import CalibrationSession, LearnerAssessment, VoiceAttempt


class CalibrationRepository(Protocol):
    async def create_session(self, session: CalibrationSession) -> CalibrationSession: ...
    async def get_session(self, session_id: UUID, user_id: UUID) -> CalibrationSession | None: ...
    async def save_attempt(self, attempt: VoiceAttempt) -> VoiceAttempt: ...
    async def get_attempt(self, attempt_id: UUID, user_id: UUID) -> VoiceAttempt | None: ...
    async def list_attempts(self, session_id: UUID, user_id: UUID) -> list[VoiceAttempt]: ...
    async def update_attempt(self, attempt: VoiceAttempt) -> VoiceAttempt: ...
    async def save_assessment(self, assessment: LearnerAssessment) -> LearnerAssessment: ...
    async def get_assessment(self, session_id: UUID, user_id: UUID) -> LearnerAssessment | None: ...
    async def complete_session(self, session_id: UUID, user_id: UUID) -> None: ...


class SQLCalibrationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(self, session: CalibrationSession) -> CalibrationSession:
        row = SessionRow(**session.model_dump(mode="json"))
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return CalibrationSession.model_validate(row)

    async def get_session(self, session_id: UUID, user_id: UUID) -> CalibrationSession | None:
        row = await self._session.scalar(
            select(SessionRow).where(SessionRow.id == session_id, SessionRow.user_id == user_id)
        )
        return CalibrationSession.model_validate(row) if row else None

    async def save_attempt(self, attempt: VoiceAttempt) -> VoiceAttempt:
        row = AttemptRow(**attempt.model_dump())
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return VoiceAttempt.model_validate(row)

    async def get_attempt(self, attempt_id: UUID, user_id: UUID) -> VoiceAttempt | None:
        row = await self._session.scalar(
            select(AttemptRow).where(AttemptRow.id == attempt_id, AttemptRow.user_id == user_id)
        )
        return VoiceAttempt.model_validate(row) if row else None

    async def list_attempts(self, session_id: UUID, user_id: UUID) -> list[VoiceAttempt]:
        rows = (
            await self._session.scalars(
                select(AttemptRow)
                .where(AttemptRow.session_id == session_id, AttemptRow.user_id == user_id)
                .order_by(AttemptRow.created_at)
            )
        ).all()
        return [VoiceAttempt.model_validate(row) for row in rows]

    async def update_attempt(self, attempt: VoiceAttempt) -> VoiceAttempt:
        row = await self._session.scalar(
            select(AttemptRow).where(
                AttemptRow.id == attempt.id, AttemptRow.user_id == attempt.user_id
            )
        )
        if row is None:
            raise LookupError("Attempt was not found for this user.")
        for name, value in attempt.model_dump(
            exclude={"id", "session_id", "user_id", "created_at"}
        ).items():
            setattr(row, name, value)
        await self._session.commit()
        await self._session.refresh(row)
        return VoiceAttempt.model_validate(row)

    async def save_assessment(self, assessment: LearnerAssessment) -> LearnerAssessment:
        row = LearnerAssessmentRow(**assessment.model_dump())
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return LearnerAssessment.model_validate(row)

    async def get_assessment(self, session_id: UUID, user_id: UUID) -> LearnerAssessment | None:
        row = await self._session.scalar(
            select(LearnerAssessmentRow).where(
                LearnerAssessmentRow.session_id == session_id,
                LearnerAssessmentRow.user_id == user_id,
            )
        )
        return LearnerAssessment.model_validate(row) if row else None

    async def complete_session(self, session_id: UUID, user_id: UUID) -> None:
        row = await self._session.scalar(
            select(SessionRow).where(SessionRow.id == session_id, SessionRow.user_id == user_id)
        )
        if row is None:
            raise LookupError("Calibration session was not found for this user.")
        row.status = "COMPLETED"
        row.completed_at = datetime.now(UTC)
        await self._session.commit()


class InMemoryCalibrationRepository:
    def __init__(self) -> None:
        self.sessions: dict[UUID, CalibrationSession] = {}
        self.attempts: dict[UUID, VoiceAttempt] = {}
        self.assessments: dict[UUID, LearnerAssessment] = {}

    async def create_session(self, session: CalibrationSession) -> CalibrationSession:
        self.sessions[session.id] = session
        return session

    async def get_session(self, session_id: UUID, user_id: UUID) -> CalibrationSession | None:
        value = self.sessions.get(session_id)
        return value if value and value.user_id == user_id else None

    async def save_attempt(self, attempt: VoiceAttempt) -> VoiceAttempt:
        existing = next(
            (
                item
                for item in self.attempts.values()
                if item.session_id == attempt.session_id
                and item.question_type == attempt.question_type
            ),
            None,
        )
        if existing:
            return existing
        self.attempts[attempt.id] = attempt
        return attempt

    async def get_attempt(self, attempt_id: UUID, user_id: UUID) -> VoiceAttempt | None:
        value = self.attempts.get(attempt_id)
        return value if value and value.user_id == user_id else None

    async def list_attempts(self, session_id: UUID, user_id: UUID) -> list[VoiceAttempt]:
        return [
            item
            for item in self.attempts.values()
            if item.session_id == session_id and item.user_id == user_id
        ]

    async def update_attempt(self, attempt: VoiceAttempt) -> VoiceAttempt:
        if await self.get_attempt(attempt.id, attempt.user_id) is None:
            raise LookupError("Attempt was not found for this user.")
        self.attempts[attempt.id] = attempt
        return attempt

    async def save_assessment(self, assessment: LearnerAssessment) -> LearnerAssessment:
        existing = self.assessments.get(assessment.session_id)
        if existing:
            return existing
        self.assessments[assessment.session_id] = assessment
        return assessment

    async def get_assessment(self, session_id: UUID, user_id: UUID) -> LearnerAssessment | None:
        value = self.assessments.get(session_id)
        return value if value and value.user_id == user_id else None

    async def complete_session(self, session_id: UUID, user_id: UUID) -> None:
        session = await self.get_session(session_id, user_id)
        if session is None:
            raise LookupError("Calibration session was not found for this user.")
        self.sessions[session_id] = session.model_copy(
            update={"status": "COMPLETED", "completed_at": datetime.now(UTC)}
        )
