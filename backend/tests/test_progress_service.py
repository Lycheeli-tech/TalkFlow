from datetime import date
from uuid import uuid4

import pytest

from app.schemas import RewardEvent, UserState
from app.services.progress import ProgressService


class FakeUsers:
    def __init__(self) -> None:
        self.state = UserState(id=uuid4())

    async def get_or_create(self, user_id):
        return self.state

    async def update_progress(self, user_id, progress):
        self.state = progress
        return progress


@pytest.mark.asyncio
async def test_progress_service_persists_rewarded_user_state() -> None:
    users = FakeUsers()
    result = await ProgressService(users).record_event(
        users.state.id,
        RewardEvent(event_type="TRANSFER", completed_on=date(2026, 9, 3)),
    )

    assert result.xp == 10
    assert result.current_streak == 1
    assert users.state.last_completed_date == date(2026, 9, 3)
