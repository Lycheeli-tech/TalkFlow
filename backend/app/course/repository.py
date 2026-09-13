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
    async def save_draft(
        self, answer: CourseAnswer, transcript: CourseTranscript
    ) -> CourseAnswerAggregate: ...
    async def list_drafts(self, user_id: UUID, question_id: str) -> list[CourseAnswerAggregate]: ...
    async def list_history(
        self, user_id: UUID, question_id: str
    ) -> list[CourseAnswerAggregate]: ...
    async def save_feedback(self, feedback: CourseFeedback) -> CourseAnswerAggregate: ...
    async def list_pending_audio_cleanup(
        self, *, now: datetime, limit: int
    ) -> list[PendingAudioCleanup]: ...
    async def mark_cleanup_complete(self, user_id: UUID, answer_id: UUID) -> None: ...
    async def mark_cleanup_failed(self, user_id: UUID, answer_id: UUID) -> None: ...
    async def delete(
        self, user_id: UUID, answer_id: UUID, *, draft_only: bool = False
    ) -> PendingAudioCleanup | None: ...


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
        if row.status in {"SAVED", "AWAITING_CONFIRMATION"}:
            return await self._aggregate(row)
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
        if row.status == "SAVED":
            return await self._aggregate(row), []
        # Serialize retention decisions for the entire owner/question/language group.
        await self._session.execute(
            text("select pg_advisory_xact_lock(hashtextextended(:group_key, 0))"),
            {"group_key": f"{answer.user_id}:{answer.question_id}:{answer.answer_language}"},
        )
        if answer.answer_language == "CHINESE":
            if row.status != "AWAITING_CONFIRMATION" or not transcript.organized_english:
                raise ValueError("Chinese Draft is not ready for confirmation.")
            row.confirmed_at = transcript.updated_at
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

    async def save_draft(
        self, answer: CourseAnswer, transcript: CourseTranscript
    ) -> CourseAnswerAggregate:
        row = await self._owned_row(answer.user_id, answer.id)
        if row.status in {"SAVED", "AWAITING_CONFIRMATION"}:
            return await self._aggregate(row)
        existing = await self._session.get(CourseTranscriptRow, answer.id)
        if existing is None:
            self._session.add(CourseTranscriptRow(**transcript.model_dump()))
        else:
            if existing.transcript != transcript.transcript:
                raise ValueError("Chinese Transcript is immutable.")
            existing.organized_english = transcript.organized_english
            existing.organizer_prompt_version = transcript.organizer_prompt_version
            existing.organizer_provider = transcript.organizer_provider
            existing.organizer_model = transcript.organizer_model
            existing.fidelity_prompt_version = transcript.fidelity_prompt_version
            existing.updated_at = transcript.updated_at
        row.status = "AWAITING_CONFIRMATION" if transcript.organized_english else "PROCESSING"
        row.provider_error_code = None
        row.failure_expires_at = None
        row.updated_at = transcript.updated_at
        await self._session.commit()
        await self._session.refresh(row)
        return await self._aggregate(row)

    async def list_drafts(self, user_id: UUID, question_id: str) -> list[CourseAnswerAggregate]:
        rows = (
            await self._session.scalars(
                select(CourseAnswerRow)
                .where(
                    CourseAnswerRow.user_id == user_id,
                    CourseAnswerRow.question_id == question_id,
                    CourseAnswerRow.answer_language == "CHINESE",
                    CourseAnswerRow.status.in_(
                        ["PROCESSING", "PROCESSING_FAILED", "AWAITING_CONFIRMATION"]
                    ),
                )
                .order_by(CourseAnswerRow.created_at.desc())
            )
        ).all()
        return [await self._aggregate(row) for row in rows]

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

    async def save_feedback(self, feedback: CourseFeedback) -> CourseAnswerAggregate:
        answer = await self._owned_row(feedback.user_id, feedback.answer_id)
        row = await self._session.get(CourseFeedbackRow, feedback.answer_id)
        values = feedback.model_dump(exclude={"answer_id", "user_id", "created_at"})
        if row is None:
            row = CourseFeedbackRow(**feedback.model_dump())
            self._session.add(row)
        else:
            for key, value in values.items():
                setattr(row, key, value)
        await self._session.commit()
        await self._session.refresh(answer)
        return await self._aggregate(answer)

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
        pending = [
            PendingAudioCleanup(answer_id=row.id, user_id=row.user_id, audio_path=row.audio_path)
            for row in rows
            if row.audio_path is not None
        ]
        remaining = max(0, limit - len(pending))
        if remaining:
            jobs = (
                (
                    await self._session.execute(
                        text(
                            "select answer_id, user_id, audio_path "
                            "from public.course_audio_cleanup_jobs "
                            "order by created_at limit :limit"
                        ),
                        {"limit": remaining},
                    )
                )
                .mappings()
                .all()
            )
            pending.extend(PendingAudioCleanup(**dict(job)) for job in jobs)
        return pending

    async def mark_cleanup_complete(self, user_id: UUID, answer_id: UUID) -> None:
        deleted = await self._session.execute(
            text(
                "delete from public.course_audio_cleanup_jobs "
                "where answer_id = :answer_id and user_id = :user_id"
            ),
            {"answer_id": answer_id, "user_id": user_id},
        )
        if deleted.rowcount:
            await self._session.commit()
            return
        row = await self._owned_row(user_id, answer_id)
        row.audio_path = None
        row.audio_content_type = None
        row.audio_retention_status = "EXPIRED"
        row.audio_cleanup_pending = False
        row.updated_at = datetime.now(row.updated_at.tzinfo)
        await self._session.commit()

    async def mark_cleanup_failed(self, user_id: UUID, answer_id: UUID) -> None:
        updated = await self._session.execute(
            text(
                "update public.course_audio_cleanup_jobs "
                "set attempts = attempts + 1, last_error_at = now() "
                "where answer_id = :answer_id and user_id = :user_id"
            ),
            {"answer_id": answer_id, "user_id": user_id},
        )
        if updated.rowcount:
            await self._session.commit()
            return
        row = await self._owned_row(user_id, answer_id)
        row.audio_retention_status = "CLEANUP_FAILED"
        row.audio_cleanup_pending = True
        row.updated_at = datetime.now(row.updated_at.tzinfo)
        await self._session.commit()

    async def delete(
        self, user_id: UUID, answer_id: UUID, *, draft_only: bool = False
    ) -> PendingAudioCleanup | None:
        row = await self._session.scalar(
            select(CourseAnswerRow)
            .where(CourseAnswerRow.id == answer_id, CourseAnswerRow.user_id == user_id)
            .with_for_update()
        )
        if row is None:
            raise LookupError("Course Answer was not found.")
        if draft_only and (row.answer_language != "CHINESE" or row.status == "SAVED"):
            raise ValueError("A saved Answer cannot be discarded as a Draft.")
        pending = None
        if row.audio_path:
            pending = PendingAudioCleanup(
                answer_id=row.id, user_id=row.user_id, audio_path=row.audio_path
            )
            await self._session.execute(
                text(
                    "insert into public.course_audio_cleanup_jobs "
                    "(answer_id, user_id, audio_path) values (:answer_id, :user_id, :audio_path) "
                    "on conflict (answer_id) do update set audio_path = excluded.audio_path"
                ),
                {
                    "answer_id": row.id,
                    "user_id": row.user_id,
                    "audio_path": row.audio_path,
                },
            )
        await self._session.execute(
            text(
                "delete from public.memory_sources where user_id = :user_id "
                "and source_type = 'COURSE_ANSWER' and source_id = :answer_id"
            ),
            {"user_id": user_id, "answer_id": answer_id},
        )
        await self._session.execute(
            text(
                "delete from public.memory_items m where m.user_id = :user_id "
                "and not exists (select 1 from public.memory_sources s where s.memory_id = m.id)"
            ),
            {"user_id": user_id},
        )
        await self._session.delete(row)
        await self._session.commit()
        return pending

    async def _owned_row(self, user_id: UUID, answer_id: UUID) -> CourseAnswerRow:
        row = await self._session.scalar(
            select(CourseAnswerRow)
            .where(CourseAnswerRow.id == answer_id, CourseAnswerRow.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
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
        self.cleanup_jobs: dict[UUID, PendingAudioCleanup] = {}

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
        if current.answer.status in {"SAVED", "AWAITING_CONFIRMATION"}:
            return current
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
        if current.answer.status == "SAVED":
            return current, []
        if answer.answer_language == "CHINESE" and (
            current.answer.status != "AWAITING_CONFIRMATION" or not transcript.organized_english
        ):
            raise ValueError("Chinese Draft is not ready for confirmation.")
        self._saved_sequence += 1
        saved = current.answer.model_copy(
            update={
                "status": "SAVED",
                "provider_error_code": None,
                "failure_expires_at": None,
                "saved_at": transcript.updated_at,
                "saved_sequence": self._saved_sequence,
                "confirmed_at": transcript.updated_at
                if answer.answer_language == "CHINESE"
                else None,
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

    async def save_draft(
        self, answer: CourseAnswer, transcript: CourseTranscript
    ) -> CourseAnswerAggregate:
        current = await self.get(answer.user_id, answer.id)
        if current is None:
            raise LookupError("Course Answer was not found.")
        if current.answer.status in {"SAVED", "AWAITING_CONFIRMATION"}:
            return current
        existing = self.transcripts.get(answer.id)
        if existing and existing.transcript != transcript.transcript:
            raise ValueError("Chinese Transcript is immutable.")
        self.transcripts[answer.id] = transcript
        self.answers[answer.id] = current.answer.model_copy(
            update={
                "status": "AWAITING_CONFIRMATION" if transcript.organized_english else "PROCESSING",
                "provider_error_code": None,
                "failure_expires_at": None,
                "updated_at": transcript.updated_at,
            }
        )
        return self._aggregate(self.answers[answer.id])

    async def list_drafts(self, user_id: UUID, question_id: str) -> list[CourseAnswerAggregate]:
        return [
            self._aggregate(item)
            for item in sorted(
                self.answers.values(), key=lambda item: item.created_at, reverse=True
            )
            if item.user_id == user_id
            and item.question_id == question_id
            and item.answer_language == "CHINESE"
            and item.status in {"PROCESSING", "PROCESSING_FAILED", "AWAITING_CONFIRMATION"}
        ]

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

    async def save_feedback(self, feedback: CourseFeedback) -> CourseAnswerAggregate:
        aggregate = await self.get(feedback.user_id, feedback.answer_id)
        if aggregate is None:
            raise LookupError("Course Answer was not found.")
        self.feedback[feedback.answer_id] = feedback
        return self._aggregate(aggregate.answer)

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
        pending = [
            PendingAudioCleanup(
                answer_id=item.id, user_id=item.user_id, audio_path=item.audio_path or ""
            )
            for item in expired
        ]
        return (pending + list(self.cleanup_jobs.values()))[:limit]

    async def mark_cleanup_complete(self, user_id: UUID, answer_id: UUID) -> None:
        if answer_id in self.cleanup_jobs:
            self.cleanup_jobs.pop(answer_id)
            return
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
        if answer_id in self.cleanup_jobs:
            return
        aggregate = await self.get(user_id, answer_id)
        if aggregate is None:
            raise LookupError("Course Answer was not found.")
        self.answers[answer_id] = aggregate.answer.model_copy(
            update={"audio_retention_status": "CLEANUP_FAILED", "audio_cleanup_pending": True}
        )

    async def delete(
        self, user_id: UUID, answer_id: UUID, *, draft_only: bool = False
    ) -> PendingAudioCleanup | None:
        aggregate = await self.get(user_id, answer_id)
        if aggregate is None:
            raise LookupError("Course Answer was not found.")
        answer = aggregate.answer
        if draft_only and (answer.answer_language != "CHINESE" or answer.status == "SAVED"):
            raise ValueError("A saved Answer cannot be discarded as a Draft.")
        pending = None
        if answer.audio_path:
            pending = PendingAudioCleanup(
                answer_id=answer.id, user_id=answer.user_id, audio_path=answer.audio_path
            )
            self.cleanup_jobs[answer.id] = pending
        self.answers.pop(answer_id, None)
        self.transcripts.pop(answer_id, None)
        self.feedback.pop(answer_id, None)
        return pending

    def _aggregate(self, answer: CourseAnswer) -> CourseAnswerAggregate:
        return CourseAnswerAggregate(
            answer=answer,
            transcript=self.transcripts.get(answer.id),
            feedback=self.feedback.get(answer.id),
        )
