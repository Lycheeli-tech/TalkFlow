from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.ai.interfaces import LLMService
from app.api.dependencies import (
    get_current_user,
    get_daily_session_repository,
    get_llm_service,
    get_profile_repository,
    get_user_repository,
)
from app.repositories.daily_sessions import DailySessionRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository
from app.schemas import AuthenticatedUser, DailySessionCompletion, DailySessionResponse
from app.services.daily_lesson_content import DailyLessonContentService
from app.services.daily_planner import DailyPlanner, DailyPlannerInput

router = APIRouter()


@router.post("/sessions", response_model=DailySessionResponse)
async def create_daily_session(
    current_user: AuthenticatedUser = Depends(get_current_user),
    profiles: ProfileRepository = Depends(get_profile_repository),
    repository: DailySessionRepository = Depends(get_daily_session_repository),
    llm: LLMService = Depends(get_llm_service),
    users: UserRepository = Depends(get_user_repository),
) -> DailySessionResponse:
    profile = await profiles.get_confirmed(current_user.id)
    if profile is None:
        raise HTTPException(status_code=409, detail="A confirmed profile is required first.")
    user = await users.get_or_create(current_user.id)
    if user.program_completed_at is not None:
        raise HTTPException(status_code=409, detail="The 30-day Bootcamp is complete.")
    plan = DailyPlanner().plan(
        DailyPlannerInput(
            profile=profile,
            assessment=None,
            current_day=user.current_day,
            duration_minutes=user.default_session_length,
        )
    )
    content = await DailyLessonContentService(llm=llm).generate(plan=plan, profile=profile)
    return await repository.get_or_create(user_id=current_user.id, plan=plan, content=content)


@router.post("/sessions/{session_id}/complete", response_model=DailySessionCompletion)
async def complete_daily_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: DailySessionRepository = Depends(get_daily_session_repository),
) -> DailySessionCompletion:
    try:
        return await repository.complete(user_id=current_user.id, session_id=session_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Daily session not found.") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/sessions/{session_id}/advance", response_model=DailySessionResponse)
async def advance_daily_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: DailySessionRepository = Depends(get_daily_session_repository),
) -> DailySessionResponse:
    try:
        return await repository.advance(user_id=current_user.id, session_id=session_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Daily session not found.") from error
