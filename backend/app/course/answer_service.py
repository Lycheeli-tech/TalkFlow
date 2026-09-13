from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.ai.interfaces import SpeechToTextService, TextToSpeechService
from app.course.catalog_v1 import CATALOG_VERSION, COURSES_BY_ID, QuestionDefinition
from app.course.chinese_organizer import (
    FIDELITY_PROMPT_VERSION,
    ORGANIZER_PROMPT_VERSION,
    ChineseAnswerOrganizer,
    validate_organized_draft,
)
from app.course.cleanup import cleanup_course_audio_batch
from app.course.entities import CourseAnswer, CourseAnswerAggregate, CourseTranscript
from app.course.repository import CourseAnswerRepository
from app.course.storage import CourseAudioStorage


class CourseAnswerMemoryCapture:
    async def capture_course_answer(
        self, *, user_id: UUID, answer_id: UUID, transcript: str
    ) -> None: ...


class CourseAnswerFeedbackGenerator:
    async def generate_for_answer(
        self, *, user_id: UUID, answer_id: UUID
    ) -> CourseAnswerAggregate: ...


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
        feedback_generator: CourseAnswerFeedbackGenerator | None = None,
        chinese_organizer: ChineseAnswerOrganizer | None = None,
        chinese_stt: SpeechToTextService | None = None,
    ) -> None:
        self._repository = repository
        self._stt = stt
        self._tts = tts
        self._audio = audio
        self._memory_capture = memory_capture
        self._feedback_generator = feedback_generator
        self._chinese_organizer = chinese_organizer
        self._chinese_stt = chinese_stt or stt

    async def synthesize_question(
        self, *, course_id: str, question_id: str, voice: str = "default"
    ) -> bytes:
        question = self._question(course_id, question_id)
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
        return await self._submit(
            user_id=user_id,
            course_id=course_id,
            question_id=question_id,
            idempotency_key=idempotency_key,
            audio=audio,
            content_type=content_type,
            duration_ms=duration_ms,
            language="ENGLISH",
        )

    async def submit_chinese(
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
        if self._chinese_organizer is None:
            raise PermissionError("Chinese answering is not enabled.")
        return await self._submit(
            user_id=user_id,
            course_id=course_id,
            question_id=question_id,
            idempotency_key=idempotency_key,
            audio=audio,
            content_type=content_type,
            duration_ms=duration_ms,
            language="CHINESE",
        )

    async def _submit(
        self,
        *,
        user_id: UUID,
        course_id: str,
        question_id: str,
        idempotency_key: str,
        audio: bytes,
        content_type: str,
        duration_ms: int | None,
        language,
    ) -> CourseAnswerAggregate:
        await self.cleanup_expired_failed_audio()
        self._question(course_id, question_id)
        existing = await self._repository.get_by_idempotency(user_id, idempotency_key)
        if existing:
            self._validate_idempotent_target(existing, course_id, question_id, language)
            return existing

        now = datetime.now(UTC)
        answer = CourseAnswer(
            id=uuid4(),
            user_id=user_id,
            catalog_version=CATALOG_VERSION,
            course_id=course_id,
            question_id=question_id,
            answer_language=language,
            status="PROCESSING",
            idempotency_key=idempotency_key,
            response_duration_ms=duration_ms,
            created_at=now,
            updated_at=now,
        )
        reserved = await self._repository.create(answer)
        if reserved.answer.id != answer.id:
            self._validate_idempotent_target(reserved, course_id, question_id, language)
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
        if answer.status in {"SAVED", "AWAITING_CONFIRMATION"}:
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

    async def drafts(
        self, *, user_id: UUID, course_id: str, question_id: str
    ) -> list[CourseAnswerAggregate]:
        self._question(course_id, question_id)
        return await self._repository.list_drafts(user_id, question_id)

    async def confirm(self, *, user_id: UUID, answer_id: UUID) -> CourseAnswerAggregate:
        aggregate = await self.get(user_id=user_id, answer_id=answer_id)
        if aggregate.answer.answer_language != "CHINESE":
            raise ValueError("Only Chinese Drafts require confirmation.")
        if aggregate.answer.status == "SAVED":
            return aggregate
        if aggregate.answer.status != "AWAITING_CONFIRMATION" or not aggregate.transcript:
            raise ValueError("Chinese Draft is not ready for confirmation.")
        transcript = aggregate.transcript.model_copy(update={"updated_at": datetime.now(UTC)})
        saved, pending = await self._repository.save_transcript(aggregate.answer, transcript)
        return await self._after_save(saved, pending)

    async def discard_draft(self, *, user_id: UUID, answer_id: UUID) -> None:
        if await self._repository.get(user_id, answer_id) is None:
            return
        pending = await self._repository.delete(user_id, answer_id, draft_only=True)
        if pending is not None:
            await self._cleanup_one(pending.user_id, pending.answer_id, pending.audio_path)

    async def history(
        self, *, user_id: UUID, course_id: str, question_id: str
    ) -> list[CourseAnswerAggregate]:
        await self.cleanup_expired_failed_audio()
        self._question(course_id, question_id)
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
        current = await self.get(user_id=answer.user_id, answer_id=answer.id)
        if current.answer.status in {"SAVED", "AWAITING_CONFIRMATION"}:
            return current
        if answer.answer_language == "CHINESE" and current.transcript is not None:
            return await self._organize(current)
        try:
            recognizer = self._chinese_stt if answer.answer_language == "CHINESE" else self._stt
            transcript_text = await recognizer.transcribe(
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
            source_language=answer.answer_language,
            transcript=transcript_text,
            stt_provider=recognizer.provider_name,
            created_at=now,
            updated_at=now,
        )
        if answer.answer_language == "CHINESE":
            draft = await self._repository.save_draft(answer, transcript)
            return await self._organize(draft)
        aggregate, pending_cleanup = await self._repository.save_transcript(answer, transcript)
        return await self._after_save(aggregate, pending_cleanup)

    async def _organize(self, aggregate: CourseAnswerAggregate) -> CourseAnswerAggregate:
        if self._chinese_organizer is None or aggregate.transcript is None:
            return await self._fail(aggregate.answer, "ORGANIZER_UNAVAILABLE")
        try:
            draft = await self._chinese_organizer.organize(aggregate.transcript.transcript)
            english = validate_organized_draft(aggregate.transcript.transcript, draft)
            if not await self._chinese_organizer.verify(aggregate.transcript.transcript, draft):
                raise ValueError("Chinese organization failed fidelity validation.")
        except Exception:
            return await self._fail(aggregate.answer, "CHINESE_ORGANIZER_FAILED")
        transcript = aggregate.transcript.model_copy(
            update={
                "organized_english": english,
                "organizer_prompt_version": ORGANIZER_PROMPT_VERSION,
                "organizer_provider": self._chinese_organizer.provider_name,
                "organizer_model": self._chinese_organizer.model_name,
                "fidelity_prompt_version": FIDELITY_PROMPT_VERSION,
                "updated_at": datetime.now(UTC),
            }
        )
        return await self._repository.save_draft(aggregate.answer, transcript)

    async def _after_save(
        self, aggregate: CourseAnswerAggregate, pending_cleanup
    ) -> CourseAnswerAggregate:
        answer = aggregate.answer
        transcript_text = aggregate.transcript.transcript if aggregate.transcript else ""
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
        if self._feedback_generator is not None:
            try:
                aggregate = await self._feedback_generator.generate_for_answer(
                    user_id=answer.user_id, answer_id=answer.id
                )
            except Exception:
                # Feedback is optional and can never roll back a safely saved Answer.
                pass
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
    def _validate_idempotent_target(
        aggregate: CourseAnswerAggregate, course_id: str, question_id: str, language="ENGLISH"
    ) -> None:
        answer = aggregate.answer
        if (
            answer.course_id != course_id
            or answer.question_id != question_id
            or answer.answer_language != language
        ):
            raise ValueError("The idempotency key belongs to another Course Question.")
