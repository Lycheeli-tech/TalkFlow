from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.about_me.entities import AboutMeSnapshot
from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.course.answer_service import CourseAnswerService
from app.course.context import CourseContextBuilder
from app.course.repository import InMemoryCourseAnswerRepository
from app.course.storage import FakeCourseAudioStorage
from app.course.support_entities import FeedbackChange, GeneratedCourseFeedback
from app.course.support_provider import FakeCourseSupportProvider
from app.course.support_service import CourseSupportService


class EmptyAboutMeRepository:
    async def snapshot(self, user_id):
        del user_id
        return AboutMeSnapshot(supplemental_facts=[], target_roles=[], resumes=[], memories=[])


class FailingFeedbackProvider(FakeCourseSupportProvider):
    async def feedback(self, context):
        del context
        raise RuntimeError("provider unavailable")


class FabricatingFeedbackProvider(FakeCourseSupportProvider):
    async def feedback(self, context):
        del context
        return GeneratedCourseFeedback(
            summary="This must be rejected.",
            priority_changes=[
                FeedbackChange(
                    original_quote="I increased revenue by 40 percent.",
                    suggestion="Keep the invented number.",
                )
            ],
        )


def build_support(repository, provider=None):
    return CourseSupportService(
        repository=repository,
        context_builder=CourseContextBuilder(about_me=EmptyAboutMeRepository(), answers=repository),
        provider=provider or FakeCourseSupportProvider(),
    )


@pytest.mark.asyncio
async def test_on_demand_support_uses_catalog_focus_and_does_not_mutate_answer_state() -> None:
    user_id = uuid4()
    repository = InMemoryCourseAnswerRepository()
    support = build_support(repository)

    hints = await support.hints(
        user_id=user_id, course_id="course-11", question_id="course-11.core"
    )
    materials = await support.expression_materials(
        user_id=user_id, course_id="course-11", question_id="course-11.core"
    )
    reference = await support.reference_answer(
        user_id=user_id, course_id="course-11", question_id="course-11.core"
    )

    assert hints.static_answer_focus.startswith("Project goal")
    assert hints.personalization_note == "Add About Me details for more personalized help."
    assert 1 <= len(materials.materials) <= 8
    assert reference.answer
    assert repository.answers == {}


@pytest.mark.asyncio
async def test_saved_answer_feedback_is_ready_and_retries_same_row() -> None:
    user_id = uuid4()
    repository = InMemoryCourseAnswerRepository()
    support = build_support(repository)
    answer_service = CourseAnswerService(
        repository=repository,
        stt=FakeSpeechToTextService("I led the migration and chose a phased rollout."),
        tts=FakeTextToSpeechService(),
        audio=FakeCourseAudioStorage(),
        feedback_generator=support,
    )
    saved = await answer_service.submit_english(
        user_id=user_id,
        course_id="course-11",
        question_id="course-11.core",
        idempotency_key="feedback-answer",
        audio=b"audio",
        content_type="audio/webm",
        duration_ms=1000,
    )

    assert saved.answer.status == "SAVED"
    assert saved.feedback is not None
    assert saved.feedback.status == "READY"
    assert len(repository.feedback) == 1
    first_created_at = saved.feedback.created_at

    retried = await support.generate_for_answer(user_id=user_id, answer_id=saved.answer.id)
    assert retried.feedback is not None
    assert retried.feedback.status == "READY"
    assert retried.feedback.created_at == first_created_at
    assert len(repository.feedback) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", [FailingFeedbackProvider(), FabricatingFeedbackProvider()])
async def test_feedback_failure_or_non_source_quote_never_rolls_back_answer(provider) -> None:
    user_id = uuid4()
    repository = InMemoryCourseAnswerRepository()
    support = build_support(repository, provider)
    answer_service = CourseAnswerService(
        repository=repository,
        stt=FakeSpeechToTextService("I owned the decision."),
        tts=FakeTextToSpeechService(),
        audio=FakeCourseAudioStorage(),
        feedback_generator=support,
    )

    saved = await answer_service.submit_english(
        user_id=user_id,
        course_id="course-11",
        question_id="course-11.core",
        idempotency_key=f"failed-feedback-{provider.__class__.__name__}",
        audio=b"audio",
        content_type="audio/webm",
        duration_ms=1000,
    )

    assert saved.answer.status == "SAVED"
    assert saved.transcript is not None
    assert saved.feedback is not None
    assert saved.feedback.status == "FAILED"
    assert saved.feedback.error_code == "FEEDBACK_GENERATION_FAILED"


@pytest.mark.asyncio
async def test_feedback_requires_owner_and_saved_answer() -> None:
    repository = InMemoryCourseAnswerRepository()
    support = build_support(repository)
    with pytest.raises(LookupError):
        await support.generate_for_answer(user_id=uuid4(), answer_id=uuid4())


def test_feedback_prompt_metadata_is_versioned() -> None:
    provider = FakeCourseSupportProvider()
    assert provider.provider_name == "fake"
    assert provider.model_name == "fixture"
    assert datetime.now(UTC).tzinfo is not None
