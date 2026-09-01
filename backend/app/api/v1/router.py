from fastapi import APIRouter

from app.api.v1 import calibration, daily, health, memory, profiles, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(calibration.router, prefix="/calibration", tags=["calibration"])
api_router.include_router(daily.router, prefix="/daily", tags=["daily"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
