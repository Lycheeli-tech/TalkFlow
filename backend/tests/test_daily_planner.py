from datetime import UTC, datetime
from uuid import uuid4

from app.schemas import ConfirmedProfile
from app.services.daily_planner import (
    DailyPlanHistory,
    DailyPlanner,
    DailyPlannerInput,
    phase_for_day,
)


def confirmed_profile() -> ConfirmedProfile:
    now = datetime.now(UTC)
    return ConfirmedProfile(
        user_id=uuid4(),
        source_document_id=uuid4(),
        target_role="AI product manager",
        confirmed_at=now,
        updated_at=now,
    )


def planner_input(day: int, history: tuple[DailyPlanHistory, ...] = ()) -> DailyPlannerInput:
    return DailyPlannerInput(
        profile=confirmed_profile(),
        assessment=None,
        current_day=day,
        duration_minutes=30,
        history=history,
    )


def test_day_one_is_the_fixed_career_transition_start() -> None:
    plan = DailyPlanner().plan(planner_input(1))

    assert plan.question_family == "CAREER_TRANSITION"
    assert plan.strategy_id == "strategy.career_transition"
    assert plan.new_language_target_ids == [
        "lang.transition_into",
        "lang.rapidly_evolving",
        "lang.naturally_curious",
        "lang.transferable",
    ]
    assert plan.retrieval_target_ids == []
    assert plan.steps == [
        "RECALL",
        "LEARN",
        "IMITATE",
        "RETRIEVE",
        "TRANSFER",
        "INTERVIEW",
        "RECAP",
    ]


def test_later_plan_retrieves_previously_introduced_language() -> None:
    history = (
        DailyPlanHistory(
            day=1,
            question_family="CAREER_TRANSITION",
            new_language_target_ids=("lang.transition_into", "lang.naturally_curious"),
            retrieval_target_ids=(),
        ),
    )

    plan = DailyPlanner().plan(planner_input(2, history))

    assert plan.question_family != "CAREER_TRANSITION"
    assert plan.retrieval_target_ids == ["lang.transition_into"]
    assert plan.new_language_target_ids != plan.retrieval_target_ids
    assert not hasattr(plan, "mastery_status")


def test_stage_boundaries_and_scaffolding_are_deterministic() -> None:
    planner = DailyPlanner()

    assert phase_for_day(10) == "BUILD"
    assert phase_for_day(11) == "TRANSFER"
    assert phase_for_day(21) == "PERFORM"
    assert planner.plan(planner_input(10)).scaffolding_level == "HIGH"
    assert planner.plan(planner_input(11)).scaffolding_level == "MEDIUM"
    assert planner.plan(planner_input(21)).scaffolding_level == "LOW"
