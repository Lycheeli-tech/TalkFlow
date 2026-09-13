from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.about_me.repository import AboutMeRepository
from app.about_me.service import AboutMeService
from app.ai.interfaces import SpeechToTextService, TextToSpeechService
from app.api.about_me_dependencies import get_about_me_repository, get_about_me_service
from app.api.core_dependencies import get_course_stt_service, get_course_tts_service
from app.core.config import get_settings
from app.course.answer_service import CourseAnswerService
from app.course.chinese_organizer import (
    BailianChineseAnswerOrganizer,
    ChineseAnswerOrganizer,
    FakeChineseAnswerOrganizer,
)
from app.course.context import CourseContextBuilder
from app.course.repository import CourseAnswerRepository, SQLCourseAnswerRepository
from app.course.storage import (
    CourseAudioStorage,
    build_course_audio_storage,
)
from app.course.support_provider import (
    BailianCourseSupportProvider,
    CourseSupportProvider,
    FakeCourseSupportProvider,
)
from app.course.support_service import CourseSupportService
from app.db.session import get_database_session


async def get_course_answer_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[CourseAnswerRepository]:
    yield SQLCourseAnswerRepository(session)


@lru_cache
def get_course_audio_storage() -> CourseAudioStorage:
    return build_course_audio_storage()


@lru_cache
def get_course_support_provider() -> CourseSupportProvider:
    settings = get_settings()
    if settings.llm_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for Course AI support.")
        return BailianCourseSupportProvider(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_text_model,
        )
    return FakeCourseSupportProvider()


def get_course_support_service(
    repository: CourseAnswerRepository = Depends(get_course_answer_repository),
    about_me: AboutMeRepository = Depends(get_about_me_repository),
    provider: CourseSupportProvider = Depends(get_course_support_provider),
) -> CourseSupportService:
    return CourseSupportService(
        repository=repository,
        context_builder=CourseContextBuilder(about_me=about_me, answers=repository),
        provider=provider,
    )


@lru_cache
def get_chinese_answer_organizer() -> ChineseAnswerOrganizer:
    settings = get_settings()
    if settings.llm_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for Chinese organization.")
        return BailianChineseAnswerOrganizer(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_text_model,
        )
    return FakeChineseAnswerOrganizer()


def get_course_answer_service(
    repository: CourseAnswerRepository = Depends(get_course_answer_repository),
    stt: SpeechToTextService = Depends(get_course_stt_service),
    tts: TextToSpeechService = Depends(get_course_tts_service),
    audio: CourseAudioStorage = Depends(get_course_audio_storage),
    memory_capture: AboutMeService = Depends(get_about_me_service),
    feedback_generator: CourseSupportService = Depends(get_course_support_service),
    chinese_organizer: ChineseAnswerOrganizer = Depends(get_chinese_answer_organizer),
) -> CourseAnswerService:
    return CourseAnswerService(
        repository=repository,
        stt=stt,
        tts=tts,
        audio=audio,
        memory_capture=memory_capture,
        feedback_generator=feedback_generator,
        chinese_organizer=chinese_organizer,
    )
