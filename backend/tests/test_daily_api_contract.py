from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.ai.fakes import FakeLLMService
from app.api.v1.daily import create_daily_session
from app.repositories.daily_sessions import InMemoryDailySessionRepository
from app.repositories.profiles import InMemoryProfileRepository
from app.schemas import AuthenticatedUser, ConfirmedProfile, UserState


class InMemoryUserRepository:
    def __init__(self, state: UserState) -> None:
        self.state = state

    async def get_or_create(self, user_id):
        assert user_id == self.state.id
        return self.state


def test_daily_api_is_registered() -> None:
    assert create_daily_session.__name__ == "create_daily_session"


@pytest.mark.asyncio
async def test_daily_api_reuses_the_persisted_in_progress_session() -> None:
    user_id = uuid4()
    now = datetime.now(UTC)
    profiles = InMemoryProfileRepository()
    profiles.profiles[user_id] = ConfirmedProfile(
        user_id=user_id,
        source_document_id=uuid4(),
        target_role="AI product manager",
        confirmed_at=now,
        updated_at=now,
    )
    repository = InMemoryDailySessionRepository()
    users = InMemoryUserRepository(UserState(id=user_id, current_day=2, current_phase="BUILD"))
    llm = FakeLLMService(
        {
            "question_prompt": "Tell me about your transition.",
            "reference_answer": "I am building on my transferable experience.",
        }
    )

    first = await create_daily_session(
        AuthenticatedUser(id=user_id), profiles, repository, llm, users
    )
    second = await create_daily_session(
        AuthenticatedUser(id=user_id), profiles, repository, llm, users
    )

    assert first == second
    assert len(repository.sessions) == 1
    assert first.plan.day == 2
