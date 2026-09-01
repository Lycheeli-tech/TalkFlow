from typing import Any

from app.ai.interfaces import LLMService
from app.curriculum.interview_bootcamp_v1 import LANGUAGE_INVENTORY, QUESTION_INVENTORY
from app.schemas import ConfirmedProfile, DailyLessonContent, DailySessionPlan

PROMPT_NAME = "daily_lesson_content"
PROMPT_VERSION = "daily_lesson_content_v1"


class DailyLessonContentService:
    """Provider-backed wording layer; target selection remains deterministic in DailyPlanner."""

    def __init__(self, *, llm: LLMService) -> None:
        self._llm = llm

    async def generate(
        self, *, plan: DailySessionPlan, profile: ConfirmedProfile
    ) -> DailyLessonContent:
        question = next(
            (item.content for item in QUESTION_INVENTORY if item.family == plan.question_family),
            plan.question_family.replace("_", " ").title(),
        )
        language = [
            item.content for item in LANGUAGE_INVENTORY if item.id in plan.new_language_target_ids
        ]
        input_data: dict[str, Any] = {
            "profile": profile.model_dump(mode="json"),
            "plan": plan.model_dump(mode="json"),
            "question": question,
            "language_targets": language,
            "constraints": {
                "deterministic_targets": True,
                "confirmed_profile_only": True,
                "no_unconfirmed_facts": True,
            },
        }
        result = await self._llm.generate_structured(
            prompt_name=PROMPT_NAME,
            prompt_version=PROMPT_VERSION,
            input_data=input_data,
        )
        return DailyLessonContent.model_validate(result)
