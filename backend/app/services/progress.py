from uuid import UUID

from app.repositories.users import UserRepository
from app.schemas import ProgressState, RewardEvent, UserState
from app.services.rewards import RewardEngine


class ProgressService:
    """Applies deterministic rewards and persists only the user's progress fields."""

    def __init__(self, repository: UserRepository, rewards: RewardEngine | None = None) -> None:
        self.repository = repository
        self.rewards = rewards or RewardEngine()

    async def record_event(self, user_id: UUID, event: RewardEvent) -> UserState:
        current = await self.repository.get_or_create(user_id)
        state = ProgressState(
            xp=current.xp,
            current_streak=current.current_streak,
            last_completed_date=current.last_completed_date,
        )
        updated = self.rewards.apply(state, event)
        return await self.repository.update_progress(
            user_id,
            current.model_copy(
                update={
                    "xp": updated.xp,
                    "current_streak": updated.current_streak,
                    "last_completed_date": updated.last_completed_date,
                }
            ),
        )
