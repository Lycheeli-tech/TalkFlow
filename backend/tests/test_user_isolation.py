from collections.abc import Callable
from uuid import UUID

from fastapi.testclient import TestClient

from app.repositories.users import UserRepository
from app.schemas import AuthenticatedUser, UserPreferencesUpdate, UserState


class InMemoryUserRepository:
    def __init__(self, users: dict[UUID, UserState]) -> None:
        self._users = users

    async def get_or_create(self, user_id: UUID) -> UserState:
        return self._users.setdefault(user_id, UserState(id=user_id))

    async def update_preferences(
        self, user_id: UUID, preferences: UserPreferencesUpdate
    ) -> UserState:
        current = await self.get_or_create(user_id)
        updated = current.model_copy(update=preferences.model_dump())
        self._users[user_id] = updated
        return updated


def test_users_me_is_scoped_to_authenticated_user(
    legacy_client: TestClient,
    override_current_user: Callable[[AuthenticatedUser], None],
    override_user_repository: Callable[[UserRepository], None],
) -> None:
    first_user = UserState(
        id=UUID("11111111-1111-4111-8111-111111111111"),
        interface_language="zh-CN",
    )
    second_user = UserState(
        id=UUID("22222222-2222-4222-8222-222222222222"),
        interface_language="en",
    )
    repository = InMemoryUserRepository(
        {
            first_user.id: first_user,
            second_user.id: second_user,
        }
    )
    override_current_user(AuthenticatedUser(id=first_user.id))
    override_user_repository(repository)

    response = legacy_client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(first_user.id)
    assert response.json()["interface_language"] == "zh-CN"
    assert str(second_user.id) not in response.text


def test_user_can_update_only_their_own_onboarding_preferences(
    legacy_client: TestClient,
    override_current_user: Callable[[AuthenticatedUser], None],
    override_user_repository: Callable[[UserRepository], None],
) -> None:
    first_user = UserState(id=UUID("11111111-1111-4111-8111-111111111111"))
    second_user = UserState(id=UUID("22222222-2222-4222-8222-222222222222"))
    repository = InMemoryUserRepository({first_user.id: first_user, second_user.id: second_user})
    override_current_user(AuthenticatedUser(id=first_user.id))
    override_user_repository(repository)

    response = legacy_client.patch(
        "/api/v1/users/me",
        json={
            "interface_language": "zh-CN",
            "support_language": "zh-CN",
            "default_session_length": 30,
            "target_role": "Product Manager",
        },
    )

    assert response.status_code == 200
    assert response.json()["target_role"] == "Product Manager"
    assert repository._users[second_user.id] == second_user
