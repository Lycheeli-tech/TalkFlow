from app.curriculum.interview_bootcamp_v1 import (
    LANGUAGE_INVENTORY,
    QUESTION_INVENTORY,
    STORY_CATEGORIES,
    STRATEGY_INVENTORY,
)
from app.schemas import DailySessionPlan


def test_mvp_inventories_are_bounded_and_cover_core_interview_families() -> None:
    families = {item.family for item in QUESTION_INVENTORY}
    assert {"SELF_INTRODUCTION", "CAREER_TRANSITION", "WHY_AI", "PROJECT_EXPERIENCE"} <= families
    assert len(QUESTION_INVENTORY) < 30
    assert {item.item_type for item in LANGUAGE_INVENTORY} == {"LANGUAGE"}
    assert {item.item_type for item in STRATEGY_INVENTORY} == {"STRATEGY"}
    assert "CAREER_TRANSITION" in STORY_CATEGORIES


def test_daily_session_plan_records_retrieval_without_mastery_state() -> None:
    plan = DailySessionPlan(
        day=2,
        phase="BUILD",
        duration_minutes=20,
        topic_family="WHY_AI",
        question_family="WHY_AI",
        strategy_id="strategy.career_transition",
        story_category="CAREER_TRANSITION",
        new_language_target_ids=["lang.naturally_curious"],
        retrieval_target_ids=["lang.transition_into"],
        steps=["RECALL", "LEARN", "IMITATE", "RETRIEVE", "INTERVIEW", "RECAP"],
        scaffolding_level="HIGH",
    )
    assert plan.retrieval_target_ids == ["lang.transition_into"]
    assert "status" not in plan.model_dump()
