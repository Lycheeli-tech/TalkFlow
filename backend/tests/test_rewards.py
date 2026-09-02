from datetime import date

from app.schemas import ProgressState, RewardEvent, RewardRules
from app.services.rewards import RewardEngine


def test_reward_engine_uses_versioned_weights_and_consecutive_streaks() -> None:
    engine = RewardEngine(RewardRules())
    state = ProgressState()

    state = engine.apply(
        state, RewardEvent(event_type="PASSIVE_LEARN", completed_on=date(2026, 9, 1))
    )
    assert state.xp == 1
    assert state.current_streak == 1

    state = engine.apply(state, RewardEvent(event_type="TRANSFER", completed_on=date(2026, 9, 2)))
    assert state.xp == 11
    assert state.current_streak == 2


def test_same_day_reward_is_xp_eligible_but_does_not_increment_streak() -> None:
    engine = RewardEngine()
    state = ProgressState(xp=5, current_streak=2, last_completed_date=date(2026, 9, 2))

    updated = engine.apply(state, RewardEvent(event_type="RECALL", completed_on=date(2026, 9, 2)))

    assert updated.xp == 10
    assert updated.current_streak == 2


def test_gap_resets_streak_without_reducing_xp() -> None:
    state = ProgressState(xp=10, current_streak=4, last_completed_date=date(2026, 9, 2))

    updated = RewardEngine().apply(
        state, RewardEvent(event_type="MASTERY", completed_on=date(2026, 9, 5))
    )

    assert updated.xp == 30
    assert updated.current_streak == 1
