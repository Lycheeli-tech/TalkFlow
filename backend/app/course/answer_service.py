from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.ai.interfaces import SpeechToTextService, TextToSpeechService
from app.course.catalog_v1 import CATALOG_VERSION, COURSES_BY_ID, QuestionDefinition
from app.course.cleanup import cleanup_course_audio_batch
from app.course.entities import CourseAnswer, CourseAnswerAggregate, CourseTranscript
from app.course.repository import CourseAnswerRepository
from app.course.rollout import english_answer_is_enabled
from app.course.storage import CourseAudioStorage


class CourseAnswerMemoryCapture:
    async def capture_course_answer(
        self, *, user_id: UUID, answer_id: UUID, transcript: str
    ) -> None: ...


FAILED_AUDIO_TTL = timedelta(days=3)


class CourseAnswerService:
    def __init__(
        self,
        *,
        repository: CourseAnswerRepository,
        stt: SpeechToTextService,
        tts: TextToSpeechService,
        audio: CourseAudioStorage,
        memory_capture: CourseAnswerMemoryCapture | None = None,
    ) -> None:
        self._repository = repository
        self._stt = stt
        self._tts = tts
        self._audio = audio
        self._memory_capture = memory_capture

    async def synthesize_question(
        self, *, course_id: str, question_id: str, voice: str = "default"
    ) -> bytes:
        question = self._question(course_id, question_id)
        self._require_rollout(course_id)
        return await self._tts.synthesize(text=question.text, voice=voice)

    async def submit_english(
        self,
        *,
        user_id: UUID,
        course_id: str,
        question_id: str,
        idempotency_key: str,
        audio: bytes,
        content_type: str,
        duration_ms: int | None,
    ) -> CourseAnswerAggregate:
        await self.cleanup_expired_failed_audio()
        self._question(course_id, question_id)
        self._require_rollout(course_id)
        existing = await self._repository.get_by_idempotency(user_id, idempotency_key)
        if existing:
            self._validate_idempotent_target(existing, course_id, question_id)
            return existing

        now = datetime.now(UTC)
        answer = CourseAnswer(
            id=uuid4(),
            user_id=user_id,
            catalog_version=CATALOG_VERSION,
            course_id=course_id,
            question_id=question_id,
            answer_language="ENGLISH",
            status="PROCESSING",
            idempotency_key=idempotency_key,
            response_duration_ms=duration_ms,
            created_at=now,
            updated_at=now,
        )
        reserved = await self._repository.create(answer)
        if reserved.answer.id != answer.id:
            self._validate_idempotent_target(reserved, course_id, question_id)
            return reserved
        try:
            audio_path = await self._audio.store(
                user_id=user_id,
                answer_id=answer.id,
                content=audio,
                content_type=content_type,
            )
        except Exception:
            return await self._fail(answer, "AUDIO_STORAGE_FAILED")
        try:
            attached = await self._repository.attach_audio(
                answer, path=audio_path, content_type=content_type
            )
        except Exception:
            try:
                await self._audio.delete(path=audio_path)
            except Exception:
                pass
            return await self._fail(answer, "AUDIO_METADATA_FAILED")
        return await self._process(attached.answer, audio)

    async def retry(self, *, user_id: UUID, answer_id: UUID) -> CourseAnswerAggregate:
        aggregate = await self._repository.get(user_id, answer_id)
        if aggregate is None:
            raise LookupError("Course Answer was not found.")
        answer = aggregate.answer
        if answer.status == "SAVED":
            return aggregate
        if answer.status not in {"PROCESSING", "PROCESSING_FAILED"} or answer.audio_path is None:
            raise ValueError("This Course Answer cannot be retried.")
        if (
            answer.status == "PROCESSING_FAILED"
            and answer.failure_expires_at is not None
            and answer.failure_expires_at <= datetime.now(UTC)
        ):
            await self._cleanup_one(answer.user_id, answer.id, answer.audio_path)
            raise ValueError("This failed Course Answer audio has expired.")
        try:
            audio = await self._audio.load(path=answer.audio_path)
        except Exception:
            return await self._fail(answer, "AUDIO_READ_FAILED")
        return await self._process(answer, audio)

    async def get(self, *, user_id: UUID, answer_id: UUID) -> CourseAnswerAggregate:
        aggregate = await self._repository.get(user_id, answer_id)
        if aggregate is None:
            raise LookupError("Course Answer was not found.")
        return aggregate

    async def history(
        self, *, user_id: UUID, course_id: str, question_id: str
    ) -> list[CourseAnswerAggregate]:
        await self.cleanup_expired_failed_audio()
        self._question(course_id, question_id)
        self._require_rollout(course_id)
        return await self._repository.list_history(user_id, question_id)

    async def audio_for(self, *, user_id: UUID, answer_id: UUID) -> tuple[bytes, str]:
        aggregate = await self.get(user_id=user_id, answer_id=answer_id)
        answer = aggregate.answer
        if answer.status != "SAVED" or answer.audio_path is None:
            raise LookupError("Course Answer audio is not available.")
        return await self._audio.load(path=answer.audio_path), (
            answer.audio_content_type or "application/octet-stream"
        )

    async def delete(self, *, user_id: UUID, answer_id: UUID) -> None:
        pending = await self._repository.delete(user_id, answer_id)
        if pending is not None:
            await self._cleanup_one(pending.user_id, pending.answer_id, pending.audio_path)

    async def cleanup_expired_failed_audio(self, *, limit: int = 50) -> int:
        return await cleanup_course_audio_batch(
            repository=self._repository,
            audio=self._audio,
            now=datetime.now(UTC),
            limit=limit,
        )

    async def _process(self, answer: CourseAnswer, audio: bytes) -> CourseAnswerAggregate:
        try:
            transcript_text = await self._stt.transcribe(
                audio=audio, content_type=answer.audio_content_type or "application/octet-stream"
            )
        except Exception:
            return await self._fail(answer, "STT_FAILED")
        transcript_text = transcript_text.strip()
        if not transcript_text:
            return await self._fail(answer, "STT_EMPTY")
        now = datetime.now(UTC)
        transcript = CourseTranscript(
            answer_id=answer.id,
            user_id=answer.user_id,
            source_language="ENGLISH",
            transcript=transcript_text,
            stt_provider=self._stt.provider_name,
            created_at=now,
            updated_at=now,
        )
        aggregate, pending_cleanup = await self._repository.save_transcript(answer, transcript)
        if self._memory_capture is not None:
            try:
                await self._memory_capture.capture_course_answer(
                    user_id=answer.user_id,
                    answer_id=answer.id,
                    transcript=transcript_text,
                )
            except Exception:
                # A saved Answer is never rolled back or hidden by optional AI Memory extraction.
                pass
        for pending in pending_cleanup:
            await self._cleanup_one(pending.user_id, pending.answer_id, pending.audio_path)
        return aggregate

    async def _cleanup_one(self, user_id: UUID, answer_id: UUID, path: str) -> bool:
        try:
            await self._audio.delete(path=path)
        except Exception:
            await self._repository.mark_cleanup_failed(user_id, answer_id)
            return False
        await self._repository.mark_cleanup_complete(user_id, answer_id)
        return True

    async def _fail(self, answer: CourseAnswer, error_code: str) -> CourseAnswerAggregate:
        now = datetime.now(UTC)
        return await self._repository.mark_failed(
            answer, error_code=error_code, expires_at=now + FAILED_AUDIO_TTL
        )

    @staticmethod
    def _question(course_id: str, question_id: str) -> QuestionDefinition:
        course = COURSES_BY_ID.get(course_id)
        if course is None:
            raise LookupError("Course was not found.")
        question = next((item for item in course.questions if item.id == question_id), None)
        if question is None:
            raise LookupError("Question was not found in this Course.")
        return question

    @staticmethod
    def _require_rollout(course_id: str) -> None:
        if not english_answer_is_enabled(course_id):
            raise PermissionError("English answering is not enabled for this Course yet.")

    @staticmethod
    def _validate_idempotent_target(
        aggregate: CourseAnswerAggregate, course_id: str, question_id: str
    ) -> None:
        answer = aggregate.answer
        if answer.course_id != course_id or answer.question_id != question_id:
            raise ValueError("The idempotency key belongs to another Course Question.")
