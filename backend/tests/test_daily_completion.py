from datetime import date
from uuid import uuid4

import pytest

from app.repositories.daily_sessions import InMemoryDailySessionRepository
from app.schemas import DailyLessonContent, DailySessionPlan


def _plan(day: int = 1) -> DailySessionPlan:
    return DailySessionPlan(
        day=day,
        phase="BUILD",
        duration_minutes=10,
        topic_family="CAREER_TRANSITION",
        question_family="CAREER_TRANSITION",
        strategy_id="strategy.career_transition",
        story_category="CAREER_TRANSITION",
        steps=["RECALL", "RECAP"],
        scaffolding_level="HIGH",
    )


@pytest.mark.asyncio
async def test_daily_completion_awards_once_and_advances_journey() -> None:
    user_id = uuid4()
    repository = InMemoryDailySessionRepository()
    session = await repository.get_or_create(
        user_id=user_id,
        plan=_plan(),
        content=DailyLessonContent(
            question_prompt="Tell me about yourself.",
            reference_answer="I am an interview candidate.",
        ),
    )

    completed = await repository.complete(
        user_id=user_id, session_id=session.session_id, completed_on=date(2026, 9, 2)
    )
    replay = await repository.complete(
        user_id=user_id, session_id=session.session_id, completed_on=date(2026, 9, 2)
    )

    assert completed.awarded_xp == 1
    assert completed.progress.current_streak == 1
    assert completed.progress.current_day == 2
    assert replay.awarded_xp == 0
    assert replay.progress.xp == 1


@pytest.mark.asyncio
async def test_daily_completion_cannot_cross_user_boundary() -> None:
    repository = InMemoryDailySessionRepository()
    owner_id = uuid4()
    session = await repository.get_or_create(
        user_id=owner_id,
        plan=_plan(),
        content=DailyLessonContent(
            question_prompt="Tell me about yourself.",
            reference_answer="I am an interview candidate.",
        ),
    )

    with pytest.raises(LookupError):
        await repository.complete(
            user_id=uuid4(), session_id=session.session_id, completed_on=date(2026, 9, 2)
        )
