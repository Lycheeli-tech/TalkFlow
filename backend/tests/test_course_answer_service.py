from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.course.answer_service import FAILED_AUDIO_TTL, CourseAnswerService
from app.course.entities import CourseAnswer
from app.course.repository import InMemoryCourseAnswerRepository
from app.course.storage import FakeCourseAudioStorage


class FailingOnceSTT(FakeSpeechToTextService):
    def __init__(self) -> None:
        super().__init__("Recovered transcript")
        self.calls = 0

    async def transcribe(self, *, audio: bytes, content_type: str) -> str:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("intentional STT failure")
        return await super().transcribe(audio=audio, content_type=content_type)


class AlwaysFailingSTT(FakeSpeechToTextService):
    async def transcribe(self, *, audio: bytes, content_type: str) -> str:
        del audio, content_type
        raise RuntimeError("intentional STT failure")


def build_service(*, stt=None):
    repository = InMemoryCourseAnswerRepository()
    audio = FakeCourseAudioStorage()
    service = CourseAnswerService(
        repository=repository,
        stt=stt or FakeSpeechToTextService("I led the delivery and validated the result."),
        tts=FakeTextToSpeechService(),
        audio=audio,
    )
    return repository, audio, service


@pytest.mark.asyncio
async def test_english_answer_saves_audio_final_transcript_and_question_history() -> None:
    user_id = uuid4()
    repository, audio, service = build_service()

    saved = await service.submit_english(
        user_id=user_id,
        course_id="course-11",
        question_id="course-11.core",
        idempotency_key="answer-request-1",
        audio=b"spoken-answer",
        content_type="audio/webm",
        duration_ms=2400,
    )

    assert saved.answer.status == "SAVED"
    assert saved.answer.response_duration_ms == 2400
    assert saved.transcript is not None
    assert saved.transcript.transcript == "I led the delivery and validated the result."
    assert saved.answer.audio_path in audio.objects
    assert await repository.list_history(user_id, "course-11.core") == [saved]


@pytest.mark.asyncio
async def test_idempotent_submit_does_not_create_or_store_a_second_attempt() -> None:
    user_id = uuid4()
    repository, audio, service = build_service()
    request = dict(
        user_id=user_id,
        course_id="course-11",
        question_id="course-11.core",
        idempotency_key="same-answer-request",
        content_type="audio/webm",
        duration_ms=1500,
    )

    first = await service.submit_english(audio=b"first", **request)
    replay = await service.submit_english(audio=b"must-not-store", **request)

    assert replay.answer.id == first.answer.id
    assert len(repository.answers) == 1
    assert len(audio.objects) == 1
    assert next(iter(audio.objects.values())) == b"first"

    with pytest.raises(ValueError, match="belongs to another"):
        await service.submit_english(
            audio=b"wrong-target",
            **{**request, "question_id": "course-11.follow-up"},
        )


@pytest.mark.asyncio
async def test_stt_failure_keeps_same_attempt_and_audio_for_three_day_retry() -> None:
    user_id = uuid4()
    repository, audio, service = build_service(stt=FailingOnceSTT())

    failed = await service.submit_english(
        user_id=user_id,
        course_id="course-11",
        question_id="course-11.follow-up",
        idempotency_key="recoverable-answer",
        audio=b"preserved",
        content_type="audio/webm",
        duration_ms=2100,
    )

    assert FAILED_AUDIO_TTL == timedelta(days=3)
    assert failed.answer.status == "PROCESSING_FAILED"
    assert failed.answer.provider_error_code == "STT_FAILED"
    assert failed.answer.failure_expires_at is not None
    assert (
        timedelta(days=2, hours=23)
        < (failed.answer.failure_expires_at - datetime.now(UTC))
        <= timedelta(days=3)
    )
    assert failed.answer.audio_path in audio.objects
    assert await repository.list_history(user_id, "course-11.follow-up") == []

    recovered = await service.retry(user_id=user_id, answer_id=failed.answer.id)
    assert recovered.answer.id == failed.answer.id
    assert recovered.answer.status == "SAVED"
    assert recovered.transcript is not None
    assert len(repository.answers) == 1


@pytest.mark.asyncio
async def test_retry_recovers_processing_answer_after_audio_was_attached() -> None:
    user_id = uuid4()
    repository, audio, service = build_service()
    now = datetime.now(UTC)
    processing = CourseAnswer(
        id=uuid4(),
        user_id=user_id,
        catalog_version="course_catalog_v1",
        course_id="course-11",
        question_id="course-11.core",
        answer_language="ENGLISH",
        status="PROCESSING",
        idempotency_key="interrupted-processing",
        response_duration_ms=1800,
        created_at=now,
        updated_at=now,
    )
    await repository.create(processing)
    path = await audio.store(
        user_id=user_id,
        answer_id=processing.id,
        content=b"preserved-after-interruption",
        content_type="audio/webm",
    )
    await repository.attach_audio(processing, path=path, content_type="audio/webm")

    recovered = await service.retry(user_id=user_id, answer_id=processing.id)

    assert recovered.answer.status == "SAVED"
    assert recovered.transcript is not None


@pytest.mark.asyncio
async def test_third_saved_answer_expires_only_oldest_audio_and_keeps_text_history() -> None:
    user_id = uuid4()
    repository, audio, service = build_service()

    answers = []
    for index in range(3):
        answers.append(
            await service.submit_english(
                user_id=user_id,
                course_id="course-11",
                question_id="course-11.core",
                idempotency_key=f"retention-{index}",
                audio=f"audio-{index}".encode(),
                content_type="audio/webm",
                duration_ms=1000 + index,
            )
        )

    history = await service.history(
        user_id=user_id, course_id="course-11", question_id="course-11.core"
    )
    assert len(history) == 3
    oldest = await repository.get(user_id, answers[0].answer.id)
    assert oldest is not None
    assert oldest.answer.audio_path is None
    assert oldest.answer.audio_retention_status == "EXPIRED"
    assert oldest.transcript is not None
    assert len(audio.objects) == 2


@pytest.mark.asyncio
async def test_failed_audio_expires_after_three_days_and_cannot_be_retried() -> None:
    user_id = uuid4()
    repository, audio, service = build_service(stt=AlwaysFailingSTT("unused"))
    failed = await service.submit_english(
        user_id=user_id,
        course_id="course-11",
        question_id="course-11.core",
        idempotency_key="expired-failure",
        audio=b"failed-audio",
        content_type="audio/webm",
        duration_ms=1200,
    )
    repository.answers[failed.answer.id] = failed.answer.model_copy(
        update={"failure_expires_at": datetime.now(UTC) - timedelta(seconds=1)}
    )

    with pytest.raises(ValueError, match="expired"):
        await service.retry(user_id=user_id, answer_id=failed.answer.id)

    expired = await repository.get(user_id, failed.answer.id)
    assert expired is not None
    assert expired.answer.audio_path is None
    assert expired.answer.audio_retention_status == "EXPIRED"
    assert audio.objects == {}


@pytest.mark.asyncio
async def test_audio_cleanup_failure_does_not_undo_saved_answer_or_transcript() -> None:
    user_id = uuid4()
    repository, audio, service = build_service()
    audio.fail_deletes = True

    answers = []
    for index in range(3):
        answers.append(
            await service.submit_english(
                user_id=user_id,
                course_id="course-11",
                question_id="course-11.core",
                idempotency_key=f"cleanup-failure-{index}",
                audio=f"audio-{index}".encode(),
                content_type="audio/webm",
                duration_ms=1000,
            )
        )

    oldest = await repository.get(user_id, answers[0].answer.id)
    assert oldest is not None
    assert oldest.answer.status == "SAVED"
    assert oldest.answer.audio_retention_status == "CLEANUP_FAILED"
    assert oldest.answer.audio_cleanup_pending is True
    assert oldest.transcript is not None

    audio.fail_deletes = False
    assert await service.cleanup_expired_failed_audio() == 1
    cleaned = await repository.get(user_id, answers[0].answer.id)
    assert cleaned is not None
    assert cleaned.answer.audio_retention_status == "EXPIRED"
    assert cleaned.answer.audio_path is None
    assert cleaned.transcript is not None


@pytest.mark.asyncio
async def test_answer_delete_is_final_while_failed_audio_cleanup_remains_retryable() -> None:
    user_id = uuid4()
    repository, audio, service = build_service()
    saved = await service.submit_english(
        user_id=user_id,
        course_id="course-11",
        question_id="course-11.core",
        idempotency_key="delete-cleanup-failure",
        audio=b"delete-me",
        content_type="audio/webm",
        duration_ms=900,
    )
    audio.fail_deletes = True
    await service.delete(user_id=user_id, answer_id=saved.answer.id)
    assert await repository.get(user_id, saved.answer.id) is None
    assert saved.answer.id in repository.cleanup_jobs

    audio.fail_deletes = False
    assert await service.cleanup_expired_failed_audio() == 1
    assert repository.cleanup_jobs == {}
    assert audio.objects == {}


@pytest.mark.asyncio
async def test_user_ownership_and_catalog_boundaries_are_enforced() -> None:
    owner_id, other_user_id = uuid4(), uuid4()
    _, _, service = build_service()
    saved = await service.submit_english(
        user_id=owner_id,
        course_id="course-11",
        question_id="course-11.core",
        idempotency_key="owner-answer",
        audio=b"owned",
        content_type="audio/webm",
        duration_ms=900,
    )

    with pytest.raises(LookupError):
        await service.get(user_id=other_user_id, answer_id=saved.answer.id)
    with pytest.raises(LookupError):
        await service.submit_english(
            user_id=owner_id,
            course_id="course-30",
            question_id="course-30.follow-up",
            idempotency_key="outside-catalog",
            audio=b"audio",
            content_type="audio/webm",
            duration_ms=900,
        )


@pytest.mark.asyncio
async def test_tts_uses_exact_catalog_question_text() -> None:
    _, _, service = build_service()
    audio = await service.synthesize_question(
        course_id="course-11", question_id="course-11.follow-up"
    )
    assert audio == b"fake-audio:default:What was specifically your contribution?"
