from uuid import uuid4

import pytest

from app.ai.fakes import (
    FakeAnswerAnalyzer,
    FakeSpeechToTextService,
    FakeTextToSpeechService,
)
from app.repositories.calibration import InMemoryCalibrationRepository
from app.repositories.daily_sessions import InMemoryDailySessionRepository
from app.schemas import DailyLessonContent, DailySessionPlan
from app.services.daily_voice import DailyVoiceService
from app.storage.audio import FakeAudioStorage


class FailingOnceAnalyzer(FakeAnswerAnalyzer):
    def __init__(self) -> None:
        self.calls = 0

    async def analyze(self, *, question: str, transcript: str):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("intentional analysis failure")
        return await super().analyze(question=question, transcript=transcript)


async def build_service(*, analyzer=None):
    user_id = uuid4()
    sessions = InMemoryDailySessionRepository()
    session = await sessions.get_or_create(
        user_id=user_id,
        plan=DailySessionPlan(
            day=1,
            phase="BUILD",
            duration_minutes=20,
            topic_family="CAREER",
            question_family="MOTIVATION",
            strategy_id="STAR",
            story_category="TRANSITION",
            steps=["RECALL", "LEARN", "IMITATE", "RETRIEVE", "TRANSFER", "INTERVIEW", "RECAP"],
            scaffolding_level="HIGH",
        ),
        content=DailyLessonContent(
            question_prompt="Why are you moving into this field?",
            reference_answer="I am building on my transferable experience.",
            imitation_variants=["I am moving into this field because it fits my strengths."],
            transfer_prompts=["Explain the same motivation to a hiring manager."],
            follow_up_questions=["What evidence supports that choice?"],
        ),
    )
    attempts = InMemoryCalibrationRepository()
    audio = FakeAudioStorage()
    service = DailyVoiceService(
        sessions=sessions,
        attempts=attempts,
        stt=FakeSpeechToTextService("I am moving because my experience transfers well."),
        tts=FakeTextToSpeechService(),
        analyzer=analyzer or FakeAnswerAnalyzer(),
        audio=audio,
    )
    return user_id, session, sessions, attempts, audio, service


@pytest.mark.asyncio
async def test_daily_voice_attempt_persists_audio_transcript_and_analysis() -> None:
    user_id, session, _, attempts, audio, service = await build_service()

    attempt = await service.submit(
        user_id=user_id,
        session_id=session.session_id,
        step="RECALL",
        audio=b"real-browser-audio",
        content_type="audio/webm;codecs=opus",
        duration_ms=2100,
    )

    assert attempt.status == "ANALYZED"
    assert attempt.transcript == "I am moving because my experience transfers well."
    assert attempt.analysis is not None
    assert audio.objects[attempt.audio_path] == b"real-browser-audio"
    assert await attempts.get_attempt(attempt.id, user_id) == attempt


@pytest.mark.asyncio
async def test_analysis_failure_keeps_audio_and_retries_same_attempt() -> None:
    analyzer = FailingOnceAnalyzer()
    user_id, session, _, attempts, audio, service = await build_service(analyzer=analyzer)

    failed = await service.submit(
        user_id=user_id,
        session_id=session.session_id,
        step="RECALL",
        audio=b"preserved-audio",
        content_type="audio/webm",
        duration_ms=1800,
    )
    retried = await service.retry(user_id=user_id, attempt_id=failed.id)

    assert failed.status == "ANALYSIS_FAILED"
    assert failed.transcript is not None
    assert audio.objects[failed.audio_path] == b"preserved-audio"
    assert retried.id == failed.id
    assert retried.audio_path == failed.audio_path
    assert retried.status == "ANALYZED"
    assert len(await attempts.list_attempts(session.session_id, user_id)) == 1


@pytest.mark.asyncio
async def test_daily_voice_rejects_non_current_or_passive_steps() -> None:
    user_id, session, _, _, _, service = await build_service()

    with pytest.raises(ValueError, match="current voice step"):
        await service.submit(
            user_id=user_id,
            session_id=session.session_id,
            step="LEARN",
            audio=b"audio",
            content_type="audio/webm",
            duration_ms=None,
        )
