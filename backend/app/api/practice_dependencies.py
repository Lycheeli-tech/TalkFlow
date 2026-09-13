from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core_dependencies import get_course_stt_service, get_course_tts_service
from app.core.config import get_settings
from app.db.session import get_database_session
from app.practice_v2.answer_service import PracticeService
from app.practice_v2.feedback_service import (
    BailianPracticeFeedbackProvider,
    FakePracticeFeedbackProvider,
)
from app.practice_v2.repository import SQLPracticeRepository
from app.practice_v2.storage import PracticeAudioStorage


@lru_cache
def get_practice_audio():
    return PracticeAudioStorage()


@lru_cache
def get_practice_feedback():
    settings = get_settings()
    if settings.llm_provider == "bailian":
        return BailianPracticeFeedbackProvider(
            key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_text_model,
        )
    return FakePracticeFeedbackProvider()


def get_practice_service(
    session: AsyncSession = Depends(get_database_session),
    audio=Depends(get_practice_audio),
    stt=Depends(get_course_stt_service),
    tts=Depends(get_course_tts_service),
    feedback=Depends(get_practice_feedback),
):
    return PracticeService(
        repository=SQLPracticeRepository(session), audio=audio, stt=stt, tts=tts, feedback=feedback
    )
