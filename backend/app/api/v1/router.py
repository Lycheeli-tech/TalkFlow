from fastapi import APIRouter

from app.api.v1 import calibration, daily, entry, health, journey, memory, practice, profiles, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(calibration.router, prefix="/calibration", tags=["calibration"])
api_router.include_router(daily.router, prefix="/daily", tags=["daily"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(practice.router, prefix="/practice", tags=["practice"])
api_router.include_router(journey.router, prefix="/journey", tags=["journey"])
api_router.include_router(entry.router, prefix="/entry", tags=["entry"])
