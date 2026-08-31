from uuid import UUID

from app.repositories.users import UserRepository
from app.schemas import UserState


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def get_or_create_current_user(self, authenticated_user_id: UUID) -> UserState:
        return await self._repository.get_or_create(authenticated_user_id)
