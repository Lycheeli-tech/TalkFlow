from uuid import uuid4

import pytest

from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.course.answer_service import CourseAnswerService
from app.course.chinese_organizer import (
    FakeChineseAnswerOrganizer,
    OrganizedDraft,
    OrganizedSegment,
    validate_organized_draft,
)
from app.course.repository import InMemoryCourseAnswerRepository
from app.course.storage import FakeCourseAudioStorage


class CountingSTT(FakeSpeechToTextService):
    def __init__(self):
        super().__init__("我负责测试。")
        self.calls = 0

    async def transcribe(self, *, audio, content_type):
        self.calls += 1
        return await super().transcribe(audio=audio, content_type=content_type)


class FailingOnceOrganizer(FakeChineseAnswerOrganizer):
    def __init__(self):
        self.calls = 0

    async def organize(self, transcript):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("fixture failure")
        return await super().organize(transcript)


class Capture:
    def __init__(self):
        self.calls = []

    async def capture_course_answer(self, **kwargs):
        self.calls.append(kwargs)


def build(organizer=None):
    repo, audio, stt, capture = (
        InMemoryCourseAnswerRepository(),
        FakeCourseAudioStorage(),
        CountingSTT(),
        Capture(),
    )
    service = CourseAnswerService(
        repository=repo,
        audio=audio,
        stt=stt,
        tts=FakeTextToSpeechService(),
        memory_capture=capture,
        chinese_organizer=organizer or FakeChineseAnswerOrganizer(),
    )
    return repo, audio, stt, capture, service


async def submit(service, owner, key="chinese-request-1", **overrides):
    request = dict(
        user_id=owner,
        course_id="course-11",
        question_id="course-11.core",
        idempotency_key=key,
        audio=b"chinese-audio",
        content_type="audio/webm",
        duration_ms=2000,
    )
    request.update(overrides)
    return await service.submit_chinese(**request)


@pytest.mark.asyncio
async def test_pending_draft_survives_service_reconstruction_but_never_enters_history_or_memory():
    repo, audio, stt, capture, service = build()
    owner = uuid4()
    draft = await submit(service, owner)
    assert draft.answer.status == "AWAITING_CONFIRMATION"
    assert draft.answer.saved_at is None and draft.answer.confirmed_at is None
    assert draft.transcript.transcript == "我负责测试。"
    assert draft.transcript.organized_english == "I was responsible for testing."
    assert capture.calls == [] and await repo.list_history(owner, "course-11.core") == []
    assert (await submit(service, owner)).answer.id == draft.answer.id
    assert stt.calls == 1 and len(audio.objects) == 1
    rebuilt = CourseAnswerService(
        repository=repo,
        audio=audio,
        stt=stt,
        tts=FakeTextToSpeechService(),
        chinese_organizer=FakeChineseAnswerOrganizer(),
    )
    assert (
        await rebuilt.drafts(user_id=owner, course_id="course-11", question_id="course-11.core")
    )[0] == draft
    with pytest.raises(LookupError):
        await rebuilt.confirm(user_id=uuid4(), answer_id=draft.answer.id)
    saved = await service.confirm(user_id=owner, answer_id=draft.answer.id)
    assert saved.answer.status == "SAVED" and saved.answer.confirmed_at is not None
    assert len(capture.calls) == 1
    assert await service.confirm(user_id=owner, answer_id=draft.answer.id) == saved
    assert len(capture.calls) == 1
    with pytest.raises(ValueError):
        await service.discard_draft(user_id=owner, answer_id=draft.answer.id)


@pytest.mark.asyncio
async def test_organizer_retry_reuses_immutable_chinese_transcript_and_audio():
    repo, audio, stt, capture, service = build(FailingOnceOrganizer())
    owner = uuid4()
    failed = await submit(service, owner)
    assert failed.answer.status == "PROCESSING_FAILED"
    assert failed.transcript.transcript == "我负责测试。"
    assert failed.answer.failure_expires_at is not None
    recovered = await service.retry(user_id=owner, answer_id=failed.answer.id)
    assert recovered.answer.status == "AWAITING_CONFIRMATION"
    assert recovered.answer.id == failed.answer.id and stt.calls == 1
    assert len(audio.objects) == 1 and capture.calls == []


@pytest.mark.asyncio
async def test_discard_is_idempotent_and_cleanup_failure_is_durable():
    repo, audio, _, capture, service = build()
    owner = uuid4()
    draft = await submit(service, owner)
    await service.discard_draft(user_id=uuid4(), answer_id=draft.answer.id)
    assert await repo.get(owner, draft.answer.id) is not None
    await service.discard_draft(user_id=owner, answer_id=draft.answer.id)
    await service.discard_draft(user_id=owner, answer_id=draft.answer.id)
    assert not repo.answers and not repo.transcripts and not audio.objects and not capture.calls
    second = await submit(service, owner, key="discard-with-cleanup-failure")
    audio.fail_deletes = True
    await service.discard_draft(user_id=owner, answer_id=second.answer.id)
    assert not repo.answers and not repo.transcripts and repo.cleanup_jobs
    audio.fail_deletes = False
    assert await service.cleanup_expired_failed_audio() == 1
    assert not repo.cleanup_jobs and not audio.objects


class EmbellishingOrganizer(FakeChineseAnswerOrganizer):
    async def organize(self, transcript):
        return OrganizedDraft(
            segments=[
                OrganizedSegment(source_excerpt=transcript, english="I led the entire project.")
            ]
        )


@pytest.mark.asyncio
async def test_fidelity_rejection_preserves_source_without_promoting_fabricated_responsibility():
    repo, _, _, capture, service = build(EmbellishingOrganizer())
    owner = uuid4()
    failed = await submit(service, owner)
    assert failed.answer.status == "PROCESSING_FAILED"
    assert failed.transcript.transcript == "我负责测试。"
    assert failed.transcript.organized_english is None
    assert capture.calls == [] and await repo.list_history(owner, "course-11.core") == []
    with pytest.raises(ValueError):
        await service.confirm(user_id=owner, answer_id=failed.answer.id)


@pytest.mark.asyncio
async def test_newest_two_only_counts_confirmed_chinese_and_language_groups_stay_independent():
    repo, audio, _, _, service = build()
    owner = uuid4()
    saved = []
    for number in range(3):
        draft = await submit(service, owner, key=f"chinese-request-{number}")
        saved.append(await service.confirm(user_id=owner, answer_id=draft.answer.id))
    pending = await submit(service, owner, key="pending-fourth")
    assert len(audio.objects) == 3  # two confirmed + one pending
    assert (await repo.get(owner, saved[0].answer.id)).answer.audio_path is None
    assert len(await repo.list_history(owner, "course-11.core")) == 3
    assert pending.answer.status == "AWAITING_CONFIRMATION"
    assert (await repo.get(owner, saved[0].answer.id)).transcript.organized_english is not None
    with pytest.raises(ValueError):
        await service.submit_english(
            user_id=owner,
            course_id="course-11",
            question_id="course-11.core",
            idempotency_key="pending-fourth",
            audio=b"other",
            content_type="audio/webm",
            duration_ms=100,
        )
    with pytest.raises(PermissionError):
        await submit(
            service,
            owner,
            key="blocked-other-course",
            course_id="course-12",
            question_id="course-12.core",
        )


@pytest.mark.parametrize(
    "source,excerpt,english",
    [
        ("我负责测试。", "我管理团队。", "I managed the team."),
        ("我负责测试。", "我负责测试。", "I improved revenue by 50%."),
    ],
)
def test_unverifiable_translation_sources_and_numbers_are_rejected(source, excerpt, english):
    with pytest.raises(ValueError):
        validate_organized_draft(
            source,
            OrganizedDraft(segments=[OrganizedSegment(source_excerpt=excerpt, english=english)]),
        )
