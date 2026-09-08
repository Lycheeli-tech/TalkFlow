from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.ai.fakes import FakeLLMService
from app.api.v1.daily import advance_daily_session, create_daily_session
from app.repositories.calibration import InMemoryCalibrationRepository
from app.repositories.daily_sessions import InMemoryDailySessionRepository
from app.repositories.profiles import InMemoryProfileRepository
from app.schemas import (
    AuthenticatedUser,
    ConfirmedProfile,
    DailyLessonContent,
    DailySessionPlan,
    UserState,
    VoiceAttempt,
)


class InMemoryUserRepository:
    def __init__(self, state: UserState) -> None:
        self.state = state

    async def get_or_create(self, user_id):
        assert user_id == self.state.id
        return self.state


def test_daily_api_is_registered() -> None:
    assert create_daily_session.__name__ == "create_daily_session"


@pytest.mark.asyncio
async def test_daily_api_reuses_the_persisted_in_progress_session() -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    profiles = InMemoryProfileRepository()
    profiles.profiles[user_id] = ConfirmedProfile(
        user_id=user_id,
        source_document_id=uuid4(),
        target_role="AI product manager",
        confirmed_at=now,
        updated_at=now,
    )
    repository = InMemoryDailySessionRepository()
    users = InMemoryUserRepository(UserState(id=user_id, current_day=2, current_phase="BUILD"))
    llm = FakeLLMService(
        {
            "question_prompt": "Tell me about your transition.",
            "reference_answer": "I am building on my transferable experience.",
        }
    )

    first = await create_daily_session(
        AuthenticatedUser(id=user_id), profiles, repository, llm, users
    )
    second = await create_daily_session(
        AuthenticatedUser(id=user_id), profiles, repository, llm, users
    )

    assert first == second
    assert len(repository.sessions) == 1
    assert first.plan.day == 2


@pytest.mark.asyncio
async def test_voice_step_cannot_advance_until_attempt_is_analyzed() -> None:
    user_id = uuid4()
    repository = InMemoryDailySessionRepository()
    attempts = InMemoryCalibrationRepository()
    session = await repository.get_or_create(
        user_id=user_id,
        plan=DailySessionPlan(
            day=1,
            phase="BUILD",
            duration_minutes=20,
            topic_family="CAREER",
            question_family="MOTIVATION",
            strategy_id="STAR",
            story_category="TRANSITION",
            steps=["RECALL", "LEARN", "RECAP"],
            scaffolding_level="HIGH",
        ),
        content=DailyLessonContent(
            question_prompt="Why this field?",
            reference_answer="It matches my transferable strengths.",
        ),
    )

    with pytest.raises(HTTPException) as blocked:
        await advance_daily_session(
            session.session_id,
            AuthenticatedUser(id=user_id),
            repository,
            attempts,
        )
    assert blocked.value.status_code == 409

    now = datetime.now(UTC)
    await attempts.save_attempt(
        VoiceAttempt(
            id=uuid4(),
            session_id=session.session_id,
            user_id=user_id,
            question="Why this field?",
            question_type="RECALL",
            audio_path="private/path",
            audio_content_type="audio/webm",
            transcript="It matches my strengths.",
            analysis={"retrieval": "FUNCTIONAL"},
            status="ANALYZED",
            created_at=now,
            updated_at=now,
        )
    )

    advanced = await advance_daily_session(
        session.session_id,
        AuthenticatedUser(id=user_id),
        repository,
        attempts,
    )
    assert advanced.plan.steps[advanced.current_step] == "LEARN"
