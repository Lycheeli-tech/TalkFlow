from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.ai.fakes import FakeLLMService
from app.schemas import ConfirmedProfile, DailySessionPlan
from app.services.daily_lesson_content import DailyLessonContentService


def profile() -> ConfirmedProfile:
    now = datetime.now(UTC)
    return ConfirmedProfile(
        user_id=uuid4(),
        source_document_id=uuid4(),
        target_role="AI product manager",
        confirmed_at=now,
        updated_at=now,
    )


def plan() -> DailySessionPlan:
    return DailySessionPlan(
        day=2,
        phase="BUILD",
        duration_minutes=20,
        topic_family="WHY_AI",
        question_family="WHY_AI",
        strategy_id="strategy.career_transition",
        story_category="CAREER_TRANSITION",
        new_language_target_ids=["lang.naturally_curious"],
        retrieval_target_ids=["lang.transition_into"],
        steps=["RECALL", "LEARN", "RETRIEVE", "TRANSFER", "INTERVIEW", "RECAP"],
        scaffolding_level="HIGH",
    )


@pytest.mark.asyncio
async def test_generates_structured_content_through_provider_boundary() -> None:
    content = {
        "question_prompt": "Why are you interested in AI?",
        "reference_answer": "I am naturally curious about how AI can improve products.",
        "language_explanations": ["Use naturally curious about + noun/gerund."],
        "imitation_variants": ["I am naturally curious about AI."],
        "transfer_prompts": ["Apply the phrase to your target role."],
        "follow_up_questions": ["Can you give a concrete example?"],
    }
    llm = FakeLLMService(content)

    result = await DailyLessonContentService(llm=llm).generate(plan=plan(), profile=profile())

    assert result.version == "daily_lesson_content_v1"
    assert result.reference_answer.startswith("I am")


@pytest.mark.asyncio
async def test_rejects_provider_output_that_is_not_lesson_content() -> None:
    llm = FakeLLMService({"unexpected": "value"})

    with pytest.raises(ValueError):
        await DailyLessonContentService(llm=llm).generate(plan=plan(), profile=profile())
