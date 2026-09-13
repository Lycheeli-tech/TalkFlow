import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.about_me.cleanup import run_about_me_document_cleanup_loop, stop_about_me_document_cleanup
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.course.cleanup import run_course_audio_cleanup_loop, stop_course_audio_cleanup
from app.practice_v2.cleanup import run_practice_cleanup_loop, stop_practice_cleanup


@asynccontextmanager
async def lifespan(_: FastAPI):
    cleanup_task = asyncio.create_task(run_course_audio_cleanup_loop())
    document_cleanup_task = asyncio.create_task(run_about_me_document_cleanup_loop())
    practice_cleanup_task = asyncio.create_task(run_practice_cleanup_loop())
    try:
        yield
    finally:
        await stop_course_audio_cleanup(cleanup_task)
        await stop_about_me_document_cleanup(document_cleanup_task)
        await stop_practice_cleanup(practice_cleanup_task)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="FluentLoop API",
        version=__version__,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
