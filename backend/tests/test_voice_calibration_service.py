from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.ai.fakes import (
    FakeAnswerAnalyzer,
    FakeCalibrationQuestionGenerator,
    FakeSpeechToTextService,
    FakeTextToSpeechService,
)
from app.repositories.calibration import InMemoryCalibrationRepository
from app.repositories.profiles import InMemoryProfileRepository
from app.schemas import CandidateProfile
from app.services.calibration import CalibrationService
from app.storage.audio import FakeAudioStorage


async def confirmed_profiles():
    repository = InMemoryProfileRepository()
    user_id, source_id = uuid4(), uuid4()
    await repository.save_confirmed(
        user_id,
        source_id,
        CandidateProfile(
            target_role="Product Manager",
            work_experience=["launching a payments product"],
            projects=["checkout redesign"],
            career_transition="product leadership",
        ),
        datetime.now(UTC),
    )
    return repository, user_id


def service(repository, profiles, audio, stt=None, analyzer=None):
    return CalibrationService(
        repository=repository,
        profiles=profiles,
        questions=FakeCalibrationQuestionGenerator(),
        stt=stt or FakeSpeechToTextService("I led a detailed project and measured the result."),
        tts=FakeTextToSpeechService(),
        analyzer=analyzer or FakeAnswerAnalyzer(),
        audio=audio,
    )


@pytest.mark.asyncio
async def test_requires_confirmed_profile_and_fixed_question_order() -> None:
    repository = InMemoryCalibrationRepository()
    profiles = InMemoryProfileRepository()
    user_id = uuid4()
    calibration = service(repository, profiles, FakeAudioStorage())
    with pytest.raises(PermissionError):
        await calibration.start(user_id)

    profiles, user_id = await confirmed_profiles()
    calibration = service(repository, profiles, FakeAudioStorage())
    session = await calibration.start(user_id)
    assert [question.category for question in session.questions] == [
        "EXPERIENCE",
        "MOTIVATION",
        "PROJECT",
    ]
    assert "payments product" in session.questions[0].text


@pytest.mark.asyncio
async def test_three_turns_preserve_audio_and_create_provisional_assessment() -> None:
    profiles, user_id = await confirmed_profiles()
    repository, audio = InMemoryCalibrationRepository(), FakeAudioStorage()
    calibration = service(repository, profiles, audio)
    session = await calibration.start(user_id)

    attempts = []
    for category in ("EXPERIENCE", "MOTIVATION", "PROJECT"):
        attempts.append(
            await calibration.submit(
                user_id=user_id,
                session_id=session.id,
                category=category,
                audio=f"raw-{category}".encode(),
                content_type="audio/webm",
                duration_ms=12000,
            )
        )

    result_session, saved, assessment = await calibration.result(
        user_id=user_id, session_id=session.id
    )
    assert result_session.status == "COMPLETED"
    assert len(saved) == 3
    assert all(item.status == "ANALYZED" and item.transcript for item in saved)
    assert all(item.audio_path in audio.objects for item in attempts)
    assert assessment is not None
    assert assessment.assessment_version == "learner_assessment_v1"
    assert assessment.fluency == "FUNCTIONAL"


class FailingOnceAnalyzer(FakeAnswerAnalyzer):
    def __init__(self) -> None:
        self.calls = 0

    async def analyze(self, *, question: str, transcript: str):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("fixture analyzer outage")
        return await super().analyze(question=question, transcript=transcript)


@pytest.mark.asyncio
async def test_analysis_failure_keeps_audio_transcript_and_retries_same_attempt() -> None:
    profiles, user_id = await confirmed_profiles()
    repository, audio = InMemoryCalibrationRepository(), FakeAudioStorage()
    calibration = service(repository, profiles, audio, analyzer=FailingOnceAnalyzer())
    session = await calibration.start(user_id)
    failed = await calibration.submit(
        user_id=user_id,
        session_id=session.id,
        category="EXPERIENCE",
        audio=b"irreplaceable recording",
        content_type="audio/webm",
        duration_ms=5000,
    )
    assert failed.status == "ANALYSIS_FAILED"
    assert failed.transcript
    assert audio.objects[failed.audio_path] == b"irreplaceable recording"

    retried = await calibration.retry(user_id=user_id, attempt_id=failed.id)
    assert retried.id == failed.id
    assert retried.audio_path == failed.audio_path
    assert retried.status == "ANALYZED"
    assert len(repository.attempts) == 1


@pytest.mark.asyncio
async def test_attempts_are_user_scoped() -> None:
    profiles, user_id = await confirmed_profiles()
    repository = InMemoryCalibrationRepository()
    calibration = service(repository, profiles, FakeAudioStorage())
    session = await calibration.start(user_id)
    with pytest.raises(LookupError):
        await calibration.result(user_id=uuid4(), session_id=session.id)
