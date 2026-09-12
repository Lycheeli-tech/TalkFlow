from fastapi import APIRouter

from app.api.v1 import about_me, course_answers, courses, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(course_answers.router, prefix="/course-answers", tags=["course-answers"])
api_router.include_router(about_me.router, prefix="/about-me", tags=["about-me"])
