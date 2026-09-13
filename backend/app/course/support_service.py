from datetime import UTC, datetime
from uuid import UUID

from app.course.context import CourseContextBuilder, _resolve_question
from app.course.entities import CourseAnswerAggregate, CourseFeedback
from app.course.repository import CourseAnswerRepository
from app.course.support_entities import (
    CourseExpressionMaterials,
    CourseHints,
    CourseReferenceAnswer,
)
from app.course.support_provider import FEEDBACK_PROMPT_VERSION, CourseSupportProvider


class CourseFeedbackGenerator:
    async def generate_for_answer(
        self, *, user_id: UUID, answer_id: UUID
    ) -> CourseAnswerAggregate: ...


class CourseSupportService:
    def __init__(
        self,
        *,
        repository: CourseAnswerRepository,
        context_builder: CourseContextBuilder,
        provider: CourseSupportProvider,
    ) -> None:
        self._repository = repository
        self._context_builder = context_builder
        self._provider = provider

    async def hints(self, *, user_id: UUID, course_id: str, question_id: str) -> CourseHints:
        self._require_available(course_id, question_id)
        context = await self._context_builder.build(
            user_id=user_id, course_id=course_id, question_id=question_id
        )
        result = await self._provider.hints(context)
        # Static product copy always comes from Catalog, never from the model.
        return result.model_copy(update={"static_answer_focus": context.answer_focus})

    async def expression_materials(
        self, *, user_id: UUID, course_id: str, question_id: str
    ) -> CourseExpressionMaterials:
        self._require_available(course_id, question_id)
        context = await self._context_builder.build(
            user_id=user_id, course_id=course_id, question_id=question_id
        )
        result = await self._provider.expression_materials(context)
        evidence = _context_evidence(context)
        for item in result.materials:
            if item.kind == "FACT_BASED_SENTENCE" and (
                not item.source_excerpt
                or not any(
                    item.source_excerpt.casefold() in source.casefold() for source in evidence
                )
            ):
                raise ValueError("A fact-based expression requires an exact verified excerpt.")
        return result

    async def reference_answer(
        self, *, user_id: UUID, course_id: str, question_id: str
    ) -> CourseReferenceAnswer:
        self._require_available(course_id, question_id)
        context = await self._context_builder.build(
            user_id=user_id, course_id=course_id, question_id=question_id
        )
        return await self._provider.reference_answer(context)

    async def generate_for_answer(self, *, user_id: UUID, answer_id: UUID) -> CourseAnswerAggregate:
        aggregate = await self._repository.get(user_id, answer_id)
        if aggregate is None:
            raise LookupError("Course Answer was not found.")
        if aggregate.answer.status != "SAVED" or aggregate.transcript is None:
            raise ValueError("Feedback requires a saved Course Answer.")
        answer = aggregate.answer
        self._require_available(answer.course_id, answer.question_id)
        now = datetime.now(UTC)
        await self._repository.save_feedback(
            CourseFeedback(
                answer_id=answer.id,
                user_id=user_id,
                status="PENDING",
                prompt_version=FEEDBACK_PROMPT_VERSION,
                provider_name=self._provider.provider_name,
                model_name=self._provider.model_name,
                created_at=aggregate.feedback.created_at if aggregate.feedback else now,
                updated_at=now,
            )
        )
        try:
            context = await self._context_builder.build(
                user_id=user_id,
                course_id=answer.course_id,
                question_id=answer.question_id,
                current_answer=aggregate.transcript.transcript,
            )
            generated = await self._provider.feedback(context)
            _validate_feedback(aggregate.transcript.transcript, generated)
            feedback = CourseFeedback(
                answer_id=answer.id,
                user_id=user_id,
                status="READY",
                summary=generated.summary,
                priority_changes=[item.model_dump() for item in generated.priority_changes],
                prompt_version=FEEDBACK_PROMPT_VERSION,
                provider_name=self._provider.provider_name,
                model_name=self._provider.model_name,
                created_at=aggregate.feedback.created_at if aggregate.feedback else now,
                updated_at=datetime.now(UTC),
            )
        except Exception:
            feedback = CourseFeedback(
                answer_id=answer.id,
                user_id=user_id,
                status="FAILED",
                prompt_version=FEEDBACK_PROMPT_VERSION,
                provider_name=self._provider.provider_name,
                model_name=self._provider.model_name,
                error_code="FEEDBACK_GENERATION_FAILED",
                created_at=aggregate.feedback.created_at if aggregate.feedback else now,
                updated_at=datetime.now(UTC),
            )
        return await self._repository.save_feedback(feedback)

    @staticmethod
    def _require_available(course_id: str, question_id: str) -> None:
        _resolve_question(course_id, question_id)


def _validate_feedback(transcript: str, generated) -> None:
    import re

    normalized = " ".join(transcript.casefold().split())
    for change in generated.priority_changes:
        quote = " ".join(change.original_quote.casefold().split())
        if not quote or quote not in normalized:
            raise ValueError("Feedback cited text outside the current Answer.")
    output_text = " ".join(
        [
            generated.summary,
            *(item.suggestion for item in generated.priority_changes),
        ]
    )
    unsupported_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", output_text)) - set(
        re.findall(r"\d+(?:\.\d+)?%?", transcript)
    )
    if unsupported_numbers:
        raise ValueError("Feedback introduced a number outside the current Answer.")


def _context_evidence(context) -> list[str]:
    return [
        *context.target_roles,
        *context.supplemental_facts,
        *context.resume_excerpts,
        *context.memories,
        *context.prior_answers,
    ]
