import os

import pytest

from app.core.config import get_settings
from app.practice_v2.feedback_service import BailianPracticeFeedbackProvider
from app.practice_v2.selection import select_questions


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_AI_LIVE") != "1", reason="opt-in Bailian whole-feedback fixture"
)
@pytest.mark.asyncio
async def test_live_whole_interview_feedback_has_exact_source_quotes():
    settings = get_settings()
    provider = BailianPracticeFeedbackProvider(
        key=settings.bailian_api_key,
        base_url=settings.bailian_compatible_base_url,
        model=settings.bailian_text_model,
    )
    answers = [
        {"question_id": q.id, "question": q.text, "transcript": t}
        for q, t in zip(
            select_questions(3, seed=23),
            (
                "I tested an idea with my team and explained what I learned.",
                "I asked for feedback, listened carefully, and changed my approach.",
                "I would like to understand the team's priorities and how success is defined.",
            ),
            strict=True,
        )
    ]
    result = await provider.generate(answers)
    evidence = {a["question_id"]: a["transcript"] for a in answers}
    assert 0 <= result.score <= 100
    for item in (*result.strengths, *result.improvements):
        assert item.question_id in evidence and item.quote in evidence[item.question_id]
