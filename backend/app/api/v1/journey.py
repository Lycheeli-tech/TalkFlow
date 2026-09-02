from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_user_repository
from app.repositories.users import UserRepository
from app.schemas import AuthenticatedUser, JourneyResponse
from app.services.journey import JourneyService
from app.services.users import UserService

router = APIRouter()


@router.get("", response_model=JourneyResponse)
async def get_journey(
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: UserRepository = Depends(get_user_repository),
) -> JourneyResponse:
    state = await UserService(repository).get_or_create_current_user(current_user.id)
    return JourneyService().build(state)
