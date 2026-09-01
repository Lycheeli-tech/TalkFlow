from dataclasses import dataclass
from typing import Literal

from app.curriculum.interview_bootcamp_v1 import (
    LANGUAGE_INVENTORY,
    QUESTION_INVENTORY,
    STORY_CATEGORIES,
    STRATEGY_INVENTORY,
)
from app.schemas import ConfirmedProfile, DailySessionPlan, LearnerAssessment

SessionLength = Literal[10, 20, 30, 60]


@dataclass(frozen=True)
class DailyPlanHistory:
    """The minimal persisted-plan history needed for deterministic selection."""

    day: int
    question_family: str
    new_language_target_ids: tuple[str, ...]
    retrieval_target_ids: tuple[str, ...]


@dataclass(frozen=True)
class DailyPlannerInput:
    profile: ConfirmedProfile
    assessment: LearnerAssessment | None
    current_day: int
    duration_minutes: SessionLength
    history: tuple[DailyPlanHistory, ...] = ()


def phase_for_day(day: int) -> str:
    if not 1 <= day <= 30:
        raise ValueError("current_day must be between 1 and 30")
    if day <= 10:
        return "BUILD"
    if day <= 20:
        return "TRANSFER"
    return "PERFORM"


def _steps_for_duration(duration_minutes: SessionLength) -> list[str]:
    if duration_minutes == 10:
        return ["RECALL", "RETRIEVE", "INTERVIEW", "RECAP"]
    if duration_minutes == 20:
        return ["RECALL", "LEARN", "RETRIEVE", "TRANSFER", "INTERVIEW", "RECAP"]
    return ["RECALL", "LEARN", "IMITATE", "RETRIEVE", "TRANSFER", "INTERVIEW", "RECAP"]


def _stable_index(value: str, size: int) -> int:
    return sum(ord(character) for character in value) % size


def _story_category(question_family: str) -> str:
    direct_categories = set(STORY_CATEGORIES)
    if question_family in direct_categories:
        return question_family
    if question_family == "PROJECT_EXPERIENCE":
        return "TECHNICAL_CHALLENGE"
    if question_family == "RELEVANT_EXPERIENCE":
        return "COMMUNICATION"
    if question_family == "SELF_INTRODUCTION":
        return "CAREER_TRANSITION"
    return "CAREER_TRANSITION"


class DailyPlanner:
    """Selects plan targets from bounded inventories without judging learner evidence."""

    def plan(self, planner_input: DailyPlannerInput) -> DailySessionPlan:
        phase = phase_for_day(planner_input.current_day)
        if planner_input.current_day == 1:
            return DailySessionPlan(
                day=1,
                phase=phase,
                duration_minutes=planner_input.duration_minutes,
                topic_family="CAREER_TRANSITION",
                question_family="CAREER_TRANSITION",
                strategy_id="strategy.career_transition",
                story_category="CAREER_TRANSITION",
                new_language_target_ids=[
                    "lang.transition_into",
                    "lang.rapidly_evolving",
                    "lang.naturally_curious",
                    "lang.transferable",
                ],
                retrieval_target_ids=[],
                steps=_steps_for_duration(planner_input.duration_minutes),
                scaffolding_level="HIGH",
            )

        question = self._select_question(planner_input, phase)
        return DailySessionPlan(
            day=planner_input.current_day,
            phase=phase,
            duration_minutes=planner_input.duration_minutes,
            topic_family=question.family,
            question_family=question.family,
            strategy_id=self._select_strategy_id(question.tags),
            story_category=_story_category(question.family),
            new_language_target_ids=self._select_new_language_ids(planner_input, question.tags),
            retrieval_target_ids=self._select_retrieval_ids(planner_input, phase),
            steps=_steps_for_duration(planner_input.duration_minutes),
            scaffolding_level={"BUILD": "HIGH", "TRANSFER": "MEDIUM", "PERFORM": "LOW"}[phase],
        )

    def _select_question(self, planner_input: DailyPlannerInput, phase: str):
        covered_counts = {
            item.family: sum(
                item.family == entry.question_family for entry in planner_input.history
            )
            for item in QUESTION_INVENTORY
        }
        last_family = planner_input.history[-1].question_family if planner_input.history else None
        eligible = [
            item
            for item in QUESTION_INVENTORY
            if phase in item.eligible_phases and item.family != last_family
        ]
        min_count = min(covered_counts[item.family] for item in eligible)
        candidates = [item for item in eligible if covered_counts[item.family] == min_count]
        seed = f"{planner_input.profile.target_role}:{planner_input.current_day}"
        return candidates[_stable_index(seed, len(candidates))]

    def _select_strategy_id(self, question_tags: list[str]) -> str:
        matching = [
            item for item in STRATEGY_INVENTORY if set(item.tags).intersection(question_tags)
        ]
        return (matching or STRATEGY_INVENTORY)[0].id

    def _select_new_language_ids(
        self, planner_input: DailyPlannerInput, question_tags: list[str]
    ) -> list[str]:
        introduced = {
            target_id
            for entry in planner_input.history
            for target_id in entry.new_language_target_ids
        }
        matching = [
            item
            for item in LANGUAGE_INVENTORY
            if set(item.tags).intersection(question_tags) and item.id not in introduced
        ]
        fallback = [item for item in LANGUAGE_INVENTORY if item.id not in introduced]
        target = (matching or fallback or LANGUAGE_INVENTORY)[0]
        return [target.id]

    def _select_retrieval_ids(self, planner_input: DailyPlannerInput, phase: str) -> list[str]:
        introduced_in_order = [
            target_id
            for entry in planner_input.history
            for target_id in entry.new_language_target_ids
        ]
        if not introduced_in_order:
            return []

        previous_retrievals = {
            target_id for entry in planner_input.history for target_id in entry.retrieval_target_ids
        }
        unseen_retrieval = [
            target_id for target_id in introduced_in_order if target_id not in previous_retrievals
        ]
        ordered = list(dict.fromkeys(unseen_retrieval + introduced_in_order))
        target_count = 1 if phase == "BUILD" else 2
        return ordered[:target_count]
