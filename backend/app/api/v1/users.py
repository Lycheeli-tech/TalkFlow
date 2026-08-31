from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_user_repository
from app.repositories.users import UserRepository
from app.schemas import AuthenticatedUser, UserState
from app.services.users import UserService

router = APIRouter()


@router.get("/me", response_model=UserState)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: UserRepository = Depends(get_user_repository),
) -> UserState:
    return await UserService(repository).get_or_create_current_user(current_user.id)
