from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_calibration_repository,
    get_current_user,
    get_profile_repository,
    get_user_repository,
)
from app.repositories.calibration import CalibrationRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository
from app.schemas import ApplicationEntry, AuthenticatedUser

router = APIRouter()


@router.get("", response_model=ApplicationEntry)
async def get_application_entry(
    current_user: AuthenticatedUser = Depends(get_current_user),
    users: UserRepository = Depends(get_user_repository),
    profiles: ProfileRepository = Depends(get_profile_repository),
    calibration: CalibrationRepository = Depends(get_calibration_repository),
) -> ApplicationEntry:
    user = await users.get_or_create(current_user.id)
    profile = await profiles.get_confirmed(current_user.id)
    if profile is None:
        return ApplicationEntry(
            stage="ONBOARDING",
            interface_language=user.interface_language,
            target_role=user.target_role,
        )
    session = await calibration.get_latest_session(current_user.id)
    return ApplicationEntry(
        stage="TODAY" if session and session.status == "COMPLETED" else "CALIBRATION",
        interface_language=user.interface_language,
        target_role=user.target_role,
    )
