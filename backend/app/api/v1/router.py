from fastapi import APIRouter

from app.api.v1 import calibration, health, profiles, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(calibration.router, prefix="/calibration", tags=["calibration"])
