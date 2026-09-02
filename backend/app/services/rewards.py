from datetime import timedelta

from app.schemas import ProgressState, RewardEvent, RewardRules


class RewardEngine:
    """Deterministic, versioned XP and streak policy for completed practice events."""

    def __init__(self, rules: RewardRules | None = None) -> None:
        self.rules = rules or RewardRules()

    def apply(self, state: ProgressState, event: RewardEvent) -> ProgressState:
        points = {
            "PASSIVE_LEARN": self.rules.passive_learn_xp,
            "IMITATION": self.rules.imitation_xp,
            "RECALL": self.rules.recall_xp,
            "TRANSFER": self.rules.transfer_xp,
            "MASTERY": self.rules.mastery_xp,
        }[event.event_type]

        if state.last_completed_date == event.completed_on:
            streak = state.current_streak
        elif state.last_completed_date == event.completed_on - timedelta(days=1):
            streak = state.current_streak + 1
        else:
            streak = 1

        return state.model_copy(
            update={
                "xp": state.xp + points,
                "current_streak": streak,
                "last_completed_date": event.completed_on,
            }
        )
