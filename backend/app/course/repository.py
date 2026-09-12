from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.course.entities import (
    CourseAnswer,
    CourseAnswerAggregate,
    CourseFeedback,
    CourseTranscript,
    PendingAudioCleanup,
)
from app.course.models import CourseAnswerRow, CourseFeedbackRow, CourseTranscriptRow


class CourseAnswerRepository(Protocol):
    async def get_by_idempotency(self, user_id: UUID, key: str) -> CourseAnswerAggregate | None: ...
    async def create(self, answer: CourseAnswer) -> CourseAnswerAggregate: ...
    async def attach_audio(
        self, answer: CourseAnswer, *, path: str, content_type: str
    ) -> CourseAnswerAggregate: ...
    async def get(self, user_id: UUID, answer_id: UUID) -> CourseAnswerAggregate | None: ...
    async def mark_failed(
        self, answer: CourseAnswer, *, error_code: str, expires_at: datetime
    ) -> CourseAnswerAggregate: ...
    async def save_transcript(
        self, answer: CourseAnswer, transcript: CourseTranscript
    ) -> tuple[CourseAnswerAggregate, list[PendingAudioCleanup]]: ...
    async def list_history(
        self, user_id: UUID, question_id: str
    ) -> list[CourseAnswerAggregate]: ...
    async def list_pending_audio_cleanup(
        self, *, now: datetime, limit: int
    ) -> list[PendingAudioCleanup]: ...
    async def mark_cleanup_complete(self, user_id: UUID, answer_id: UUID) -> None: ...
    async def mark_cleanup_failed(self, user_id: UUID, answer_id: UUID) -> None: ...


class SQLCourseAnswerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_idempotency(self, user_id: UUID, key: str) -> CourseAnswerAggregate | None:
        row = await self._session.scalar(
            select(CourseAnswerRow).where(
                CourseAnswerRow.user_id == user_id,
                CourseAnswerRow.idempotency_key == key,
            )
        )
        return await self._aggregate(row) if row else None

    async def create(self, answer: CourseAnswer) -> CourseAnswerAggregate:
        existing = await self.get_by_idempotency(answer.user_id, answer.idempotency_key)
        if existing:
            return existing
        row = CourseAnswerRow(**answer.model_dump())
        self._session.add(row)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            existing = await self.get_by_idempotency(answer.user_id, answer.idempotency_key)
            if existing:
                return existing
            raise
        await self._session.refresh(row)
        return CourseAnswerAggregate(answer=CourseAnswer.model_validate(row))

    async def attach_audio(
        self, answer: CourseAnswer, *, path: str, content_type: str
    ) -> CourseAnswerAggregate:
        row = await self._owned_row(answer.user_id, answer.id)
        if row.audio_path is None:
            row.audio_path = path
            row.audio_content_type = content_type
            row.updated_at = datetime.now(row.updated_at.tzinfo)
            await self._session.commit()
            await self._session.refresh(row)
        return await self._aggregate(row)

    async def get(self, user_id: UUID, answer_id: UUID) -> CourseAnswerAggregate | None:
        row = await self._session.scalar(
            select(CourseAnswerRow).where(
                CourseAnswerRow.id == answer_id, CourseAnswerRow.user_id == user_id
            )
        )
        return await self._aggregate(row) if row else None

    async def mark_failed(
        self, answer: CourseAnswer, *, error_code: str, expires_at: datetime
    ) -> CourseAnswerAggregate:
        row = await self._owned_row(answer.user_id, answer.id)
        row.status = "PROCESSING_FAILED"
        row.provider_error_code = error_code
        row.failure_expires_at = expires_at
        row.updated_at = datetime.now(expires_at.tzinfo)
        await self._session.commit()
        await self._session.refresh(row)
        return await self._aggregate(row)

    async def save_transcript(
        self, answer: CourseAnswer, transcript: CourseTranscript
    ) -> tuple[CourseAnswerAggregate, list[PendingAudioCleanup]]:
        row = await self._owned_row(answer.user_id, answer.id)
        existing_transcript = await self._session.get(CourseTranscriptRow, answer.id)
        if existing_transcript is None:
            self._session.add(CourseTranscriptRow(**transcript.model_dump()))
        now = transcript.updated_at
        row.status = "SAVED"
        row.provider_error_code = None
        row.failure_expires_at = None
        row.saved_at = now
        row.saved_sequence = await self._session.scalar(
            text("select nextval('public.course_answer_saved_sequence')")
        )
        row.updated_at = now
        await self._session.flush()

        previous_audio_rows = (
            await self._session.scalars(
                select(CourseAnswerRow)
                .where(
                    CourseAnswerRow.user_id == answer.user_id,
                    CourseAnswerRow.question_id == answer.question_id,
                    CourseAnswerRow.answer_language == answer.answer_language,
                    CourseAnswerRow.status == "SAVED",
                    CourseAnswerRow.audio_path.is_not(None),
                    CourseAnswerRow.id != answer.id,
                )
                .order_by(CourseAnswerRow.saved_sequence.desc())
                .with_for_update()
            )
        ).all()
        pending: list[PendingAudioCleanup] = []
        for expired in previous_audio_rows[1:]:
            if expired.audio_path is None:
                continue
            expired.audio_retention_status = "PENDING_CLEANUP"
            expired.audio_cleanup_pending = True
            pending.append(
                PendingAudioCleanup(
                    answer_id=expired.id,
                    user_id=expired.user_id,
                    audio_path=expired.audio_path,
                )
            )
        await self._session.commit()
        await self._session.refresh(row)
        return await self._aggregate(row), pending

    async def list_history(self, user_id: UUID, question_id: str) -> list[CourseAnswerAggregate]:
        rows = (
            await self._session.scalars(
                select(CourseAnswerRow)
                .where(
                    CourseAnswerRow.user_id == user_id,
                    CourseAnswerRow.question_id == question_id,
                    CourseAnswerRow.status == "SAVED",
                )
                .order_by(CourseAnswerRow.saved_sequence.desc())
            )
        ).all()
        return [await self._aggregate(row) for row in rows]

    async def list_pending_audio_cleanup(
        self, *, now: datetime, limit: int
    ) -> list[PendingAudioCleanup]:
        rows = (
            await self._session.scalars(
                select(CourseAnswerRow)
                .where(
                    (
                        (CourseAnswerRow.audio_cleanup_pending.is_(True))
                        | (
                            (CourseAnswerRow.status == "PROCESSING_FAILED")
                            & (CourseAnswerRow.failure_expires_at <= now)
                        )
                    ),
                    CourseAnswerRow.audio_path.is_not(None),
                )
                .order_by(CourseAnswerRow.failure_expires_at)
                .limit(limit)
            )
        ).all()
        return [
            PendingAudioCleanup(answer_id=row.id, user_id=row.user_id, audio_path=row.audio_path)
            for row in rows
            if row.audio_path is not None
        ]

    async def mark_cleanup_complete(self, user_id: UUID, answer_id: UUID) -> None:
        row = await self._owned_row(user_id, answer_id)
        row.audio_path = None
        row.audio_content_type = None
        row.audio_retention_status = "EXPIRED"
        row.audio_cleanup_pending = False
        row.updated_at = datetime.now(row.updated_at.tzinfo)
        await self._session.commit()

    async def mark_cleanup_failed(self, user_id: UUID, answer_id: UUID) -> None:
        row = await self._owned_row(user_id, answer_id)
        row.audio_retention_status = "CLEANUP_FAILED"
        row.audio_cleanup_pending = True
        row.updated_at = datetime.now(row.updated_at.tzinfo)
        await self._session.commit()

    async def _owned_row(self, user_id: UUID, answer_id: UUID) -> CourseAnswerRow:
        row = await self._session.scalar(
            select(CourseAnswerRow).where(
                CourseAnswerRow.id == answer_id, CourseAnswerRow.user_id == user_id
            )
        )
        if row is None:
            raise LookupError("Course Answer was not found.")
        return row

    async def _aggregate(self, answer: CourseAnswerRow) -> CourseAnswerAggregate:
        transcript = await self._session.get(CourseTranscriptRow, answer.id)
        feedback = await self._session.get(CourseFeedbackRow, answer.id)
        return CourseAnswerAggregate(
            answer=CourseAnswer.model_validate(answer),
            transcript=CourseTranscript.model_validate(transcript) if transcript else None,
            feedback=CourseFeedback.model_validate(feedback) if feedback else None,
        )


class InMemoryCourseAnswerRepository:
    def __init__(self) -> None:
        self.answers: dict[UUID, CourseAnswer] = {}
        self.transcripts: dict[UUID, CourseTranscript] = {}
        self.feedback: dict[UUID, CourseFeedback] = {}
        self._saved_sequence = 0

    async def get_by_idempotency(self, user_id: UUID, key: str) -> CourseAnswerAggregate | None:
        answer = next(
            (
                item
                for item in self.answers.values()
                if item.user_id == user_id and item.idempotency_key == key
            ),
            None,
        )
        return self._aggregate(answer) if answer else None

    async def create(self, answer: CourseAnswer) -> CourseAnswerAggregate:
        existing = await self.get_by_idempotency(answer.user_id, answer.idempotency_key)
        if existing:
            return existing
        self.answers[answer.id] = answer
        return self._aggregate(answer)

    async def attach_audio(
        self, answer: CourseAnswer, *, path: str, content_type: str
    ) -> CourseAnswerAggregate:
        current = await self.get(answer.user_id, answer.id)
        if current is None:
            raise LookupError("Course Answer was not found.")
        if current.answer.audio_path is None:
            self.answers[answer.id] = current.answer.model_copy(
                update={
                    "audio_path": path,
                    "audio_content_type": content_type,
                    "updated_at": datetime.now(current.answer.updated_at.tzinfo),
                }
            )
        return self._aggregate(self.answers[answer.id])

    async def get(self, user_id: UUID, answer_id: UUID) -> CourseAnswerAggregate | None:
        answer = self.answers.get(answer_id)
        return self._aggregate(answer) if answer and answer.user_id == user_id else None

    async def mark_failed(
        self, answer: CourseAnswer, *, error_code: str, expires_at: datetime
    ) -> CourseAnswerAggregate:
        current = await self.get(answer.user_id, answer.id)
        if current is None:
            raise LookupError("Course Answer was not found.")
        failed = current.answer.model_copy(
            update={
                "status": "PROCESSING_FAILED",
                "provider_error_code": error_code,
                "failure_expires_at": expires_at,
                "updated_at": datetime.now(expires_at.tzinfo),
            }
        )
        self.answers[answer.id] = failed
        return self._aggregate(failed)

    async def save_transcript(
        self, answer: CourseAnswer, transcript: CourseTranscript
    ) -> tuple[CourseAnswerAggregate, list[PendingAudioCleanup]]:
        current = await self.get(answer.user_id, answer.id)
        if current is None:
            raise LookupError("Course Answer was not found.")
        self._saved_sequence += 1
        saved = current.answer.model_copy(
            update={
                "status": "SAVED",
                "provider_error_code": None,
                "failure_expires_at": None,
                "saved_at": transcript.updated_at,
                "saved_sequence": self._saved_sequence,
                "updated_at": transcript.updated_at,
            }
        )
        self.answers[answer.id] = saved
        self.transcripts[answer.id] = transcript
        previous = sorted(
            (
                item
                for item in self.answers.values()
                if item.id != answer.id
                and item.user_id == answer.user_id
                and item.question_id == answer.question_id
                and item.answer_language == answer.answer_language
                and item.status == "SAVED"
                and item.audio_path is not None
            ),
            key=lambda item: item.saved_sequence or 0,
            reverse=True,
        )
        pending: list[PendingAudioCleanup] = []
        for expired in previous[1:]:
            if expired.audio_path is None:
                continue
            self.answers[expired.id] = expired.model_copy(
                update={"audio_retention_status": "PENDING_CLEANUP", "audio_cleanup_pending": True}
            )
            pending.append(
                PendingAudioCleanup(
                    answer_id=expired.id, user_id=expired.user_id, audio_path=expired.audio_path
                )
            )
        return self._aggregate(saved), pending

    async def list_history(self, user_id: UUID, question_id: str) -> list[CourseAnswerAggregate]:
        answers = sorted(
            (
                item
                for item in self.answers.values()
                if item.user_id == user_id
                and item.question_id == question_id
                and item.status == "SAVED"
            ),
            key=lambda item: item.saved_sequence or 0,
            reverse=True,
        )
        return [self._aggregate(answer) for answer in answers]

    async def list_pending_audio_cleanup(
        self, *, now: datetime, limit: int
    ) -> list[PendingAudioCleanup]:
        expired = sorted(
            (
                item
                for item in self.answers.values()
                if (
                    item.audio_cleanup_pending
                    or (
                        item.status == "PROCESSING_FAILED"
                        and item.failure_expires_at is not None
                        and item.failure_expires_at <= now
                    )
                )
                and item.audio_path is not None
            ),
            key=lambda item: item.failure_expires_at or now,
        )[:limit]
        return [
            PendingAudioCleanup(
                answer_id=item.id, user_id=item.user_id, audio_path=item.audio_path or ""
            )
            for item in expired
        ]

    async def mark_cleanup_complete(self, user_id: UUID, answer_id: UUID) -> None:
        aggregate = await self.get(user_id, answer_id)
        if aggregate is None:
            raise LookupError("Course Answer was not found.")
        self.answers[answer_id] = aggregate.answer.model_copy(
            update={
                "audio_path": None,
                "audio_content_type": None,
                "audio_retention_status": "EXPIRED",
                "audio_cleanup_pending": False,
            }
        )

    async def mark_cleanup_failed(self, user_id: UUID, answer_id: UUID) -> None:
        aggregate = await self.get(user_id, answer_id)
        if aggregate is None:
            raise LookupError("Course Answer was not found.")
        self.answers[answer_id] = aggregate.answer.model_copy(
            update={"audio_retention_status": "CLEANUP_FAILED", "audio_cleanup_pending": True}
        )

    def _aggregate(self, answer: CourseAnswer) -> CourseAnswerAggregate:
        return CourseAnswerAggregate(
            answer=answer,
            transcript=self.transcripts.get(answer.id),
            feedback=self.feedback.get(answer.id),
        )
