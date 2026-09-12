from uuid import UUID

from app.about_me.repository import AboutMeRepository
from app.course.catalog_v1 import CATALOG_VERSION, COURSES_BY_ID, QuestionDefinition
from app.course.repository import CourseAnswerRepository
from app.course.support_entities import CourseContext

CONTEXT_EVIDENCE_CHAR_LIMIT = 10_000


class CourseContextBuilder:
    def __init__(
        self,
        *,
        about_me: AboutMeRepository,
        answers: CourseAnswerRepository,
    ) -> None:
        self._about_me = about_me
        self._answers = answers

    async def build(
        self,
        *,
        user_id: UUID,
        course_id: str,
        question_id: str,
        current_answer: str | None = None,
    ) -> CourseContext:
        course, question = _resolve_question(course_id, question_id)
        snapshot = await self._about_me.snapshot(user_id)
        history = await self._answers.list_history(user_id, question_id)
        prior_answer_candidates = [
            item.transcript.transcript
            for item in history
            if item.transcript is not None and item.transcript.transcript != current_answer
        ]
        remaining = CONTEXT_EVIDENCE_CHAR_LIMIT

        def take(values: list[str], *, count: int, item_limit: int) -> list[str]:
            nonlocal remaining
            selected: list[str] = []
            for value in values[:count]:
                if remaining <= 0:
                    break
                cleaned = " ".join(value.split())[: min(item_limit, remaining)]
                if not cleaned:
                    continue
                selected.append(cleaned)
                remaining -= len(cleaned)
            return selected

        target_roles = take(
            [item.role_name for item in snapshot.target_roles], count=3, item_limit=160
        )
        supplemental_facts = take(snapshot.supplemental_facts, count=6, item_limit=600)
        memories = take([item.content for item in snapshot.memories], count=6, item_limit=700)
        resume_excerpts = take(
            [item.raw_text for item in snapshot.resumes], count=3, item_limit=1200
        )
        prior_answers = take(prior_answer_candidates, count=3, item_limit=1000)
        return CourseContext(
            catalog_version=CATALOG_VERSION,
            course_id=course.id,
            course_name=course.name_en,
            question_id=question.id,
            question=question.text,
            answer_focus=course.answer_focus_en,
            target_roles=target_roles,
            supplemental_facts=supplemental_facts,
            resume_excerpts=resume_excerpts,
            memories=memories,
            prior_answers=prior_answers,
            current_answer=current_answer[:5000] if current_answer else None,
        )


def _resolve_question(course_id: str, question_id: str):
    course = COURSES_BY_ID.get(course_id)
    if course is None:
        raise LookupError("Course was not found.")
    question: QuestionDefinition | None = next(
        (item for item in course.questions if item.id == question_id), None
    )
    if question is None:
        raise LookupError("Question was not found in this Course.")
    return course, question
