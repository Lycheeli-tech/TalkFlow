from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.interfaces import SpeechToTextService, TextToSpeechService
from app.api.core_dependencies import get_course_stt_service, get_course_tts_service
from app.course.answer_service import CourseAnswerService
from app.course.repository import CourseAnswerRepository, SQLCourseAnswerRepository
from app.course.storage import (
    CourseAudioStorage,
    build_course_audio_storage,
)
from app.db.session import get_database_session


async def get_course_answer_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[CourseAnswerRepository]:
    yield SQLCourseAnswerRepository(session)


@lru_cache
def get_course_audio_storage() -> CourseAudioStorage:
    return build_course_audio_storage()


def get_course_answer_service(
    repository: CourseAnswerRepository = Depends(get_course_answer_repository),
    stt: SpeechToTextService = Depends(get_course_stt_service),
    tts: TextToSpeechService = Depends(get_course_tts_service),
    audio: CourseAudioStorage = Depends(get_course_audio_storage),
) -> CourseAnswerService:
    return CourseAnswerService(repository=repository, stt=stt, tts=tts, audio=audio)
