from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.fakes import (
    FakeAnswerAnalyzer,
    FakeCalibrationQuestionGenerator,
    FakeProfileExtractor,
    FakeSpeechToTextService,
    FakeTextToSpeechService,
)
from app.ai.interfaces import (
    AnswerAnalyzer,
    CalibrationQuestionGenerator,
    ProfileExtractor,
    SpeechToTextService,
    TextToSpeechService,
)
from app.ai.profile_extractor import OpenAIProfileExtractor
from app.ai.voice import (
    OpenAIAnswerAnalyzer,
    OpenAICalibrationQuestionGenerator,
    OpenAISpeechToTextService,
    OpenAITextToSpeechService,
)
from app.core.config import get_settings
from app.core.security import JWTVerificationError, SupabaseTokenVerifier, TokenVerifier
from app.db.session import get_database_session
from app.repositories.calibration import CalibrationRepository, SQLCalibrationRepository
from app.repositories.profiles import ProfileRepository, SQLProfileRepository
from app.repositories.users import SQLUserRepository, UserRepository
from app.schemas import AuthenticatedUser
from app.storage.audio import AudioStorage, FakeAudioStorage, SupabaseAudioStorage
from app.storage.documents import DocumentStorage, FakeDocumentStorage, SupabaseDocumentStorage

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_token_verifier() -> TokenVerifier:
    return SupabaseTokenVerifier.from_settings()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer token is required.",
        )

    try:
        return verifier.verify(credentials.credentials)
    except JWTVerificationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The access token is invalid or expired.",
        ) from error


async def get_user_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[UserRepository]:
    yield SQLUserRepository(session)


async def get_profile_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[ProfileRepository]:
    yield SQLProfileRepository(session)


async def get_calibration_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[CalibrationRepository]:
    yield SQLCalibrationRepository(session)


@lru_cache
def get_question_generator() -> CalibrationQuestionGenerator:
    settings = get_settings()
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for calibration questions.")
        return OpenAICalibrationQuestionGenerator(
            api_key=settings.openai_api_key, model=settings.openai_calibration_model
        )
    return FakeCalibrationQuestionGenerator()


@lru_cache
def get_stt_service() -> SpeechToTextService:
    settings = get_settings()
    if settings.stt_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for STT.")
        return OpenAISpeechToTextService(
            api_key=settings.openai_api_key, model=settings.openai_stt_model
        )
    return FakeSpeechToTextService()


@lru_cache
def get_tts_service() -> TextToSpeechService:
    settings = get_settings()
    if settings.tts_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for TTS.")
        return OpenAITextToSpeechService(
            api_key=settings.openai_api_key, model=settings.openai_tts_model
        )
    return FakeTextToSpeechService()


@lru_cache
def get_answer_analyzer() -> AnswerAnalyzer:
    settings = get_settings()
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for answer analysis.")
        return OpenAIAnswerAnalyzer(
            api_key=settings.openai_api_key, model=settings.openai_calibration_model
        )
    return FakeAnswerAnalyzer()


@lru_cache
def get_audio_storage() -> AudioStorage:
    settings = get_settings()
    if settings.audio_storage_provider == "supabase":
        if not settings.supabase_service_role_key:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required for audio storage.")
        return SupabaseAudioStorage(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
        )
    return FakeAudioStorage()


@lru_cache
def get_profile_extractor() -> ProfileExtractor:
    settings = get_settings()
    if settings.profile_extractor_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI profile extractor.")
        return OpenAIProfileExtractor(
            api_key=settings.openai_api_key,
            model=settings.openai_profile_model,
        )
    return FakeProfileExtractor()


@lru_cache
def get_document_storage() -> DocumentStorage:
    settings = get_settings()
    if settings.document_storage_provider == "supabase":
        if not settings.supabase_service_role_key:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required for document storage.")
        return SupabaseDocumentStorage(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
        )
    return FakeDocumentStorage()
