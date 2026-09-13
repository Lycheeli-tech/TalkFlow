import os

import pytest

from app.core.config import get_settings
from app.course.support_entities import CourseContext
from app.course.support_provider import BailianCourseSupportProvider


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_AI_LIVE") != "1",
    reason="set RUN_COURSE_AI_LIVE=1 to call the configured Course AI provider",
)
@pytest.mark.asyncio
async def test_live_course_support_is_structured_and_source_bound() -> None:
    settings = get_settings()
    if not settings.bailian_api_key:
        pytest.skip("BAILIAN_API_KEY is not configured")
    provider = BailianCourseSupportProvider(
        api_key=settings.bailian_api_key,
        base_url=settings.bailian_compatible_base_url,
        model=settings.bailian_text_model,
    )
    transcript = "I led a synthetic migration and chose a phased rollout."
    context = CourseContext(
        catalog_version="course_catalog_v1",
        course_id="course-11",
        course_name="A Project You Are Proud Of",
        question_id="course-11.core",
        question="Tell me about a project you are proud of.",
        answer_focus=(
            "Project goal → personal responsibility → key decisions → process and result, "
            "emphasizing what you did."
        ),
        target_roles=[],
        supplemental_facts=[],
        resume_excerpts=[],
        memories=[],
        prior_answers=[],
        current_answer=None,
    )

    hints = await provider.hints(context)
    reference = await provider.reference_answer(context)
    grounded_reference = await provider.reference_answer(
        context.model_copy(
            update={
                "supplemental_facts": ["I led a synthetic migration and chose a phased rollout."]
            }
        )
    )
    feedback = await provider.feedback(context.model_copy(update={"current_answer": transcript}))

    assert hints.static_answer_focus == context.answer_focus
    assert "[" in reference.answer and "]" in reference.answer
    assert grounded_reference.answer
    assert 1 <= len(feedback.priority_changes) <= 3
    for change in feedback.priority_changes:
        assert " ".join(change.original_quote.casefold().split()) in " ".join(
            transcript.casefold().split()
        )
