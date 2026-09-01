from fastapi import APIRouter, Depends, HTTPException

from app.ai.interfaces import LLMService
from app.api.dependencies import get_current_user, get_llm_service, get_profile_repository
from app.repositories.profiles import ProfileRepository
from app.schemas import AuthenticatedUser, DailySessionResponse
from app.services.daily_lesson_content import DailyLessonContentService
from app.services.daily_planner import DailyPlanner, DailyPlannerInput

router = APIRouter()


@router.post("/sessions", response_model=DailySessionResponse)
async def create_daily_session(
    current_user: AuthenticatedUser = Depends(get_current_user),
    profiles: ProfileRepository = Depends(get_profile_repository),
    llm: LLMService = Depends(get_llm_service),
) -> DailySessionResponse:
    profile = await profiles.get_confirmed(current_user.id)
    if profile is None:
        raise HTTPException(status_code=409, detail="A confirmed profile is required first.")
    plan = DailyPlanner().plan(
        DailyPlannerInput(
            profile=profile,
            assessment=None,
            current_day=1,
            duration_minutes=20,
        )
    )
    content = await DailyLessonContentService(llm=llm).generate(plan=plan, profile=profile)
    return DailySessionResponse(plan=plan, content=content)
