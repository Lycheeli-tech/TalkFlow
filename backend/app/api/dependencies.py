from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.bailian import (
    BailianAnswerAnalyzer,
    BailianCalibrationQuestionGenerator,
    BailianLLMService,
    BailianProfileExtractor,
    BailianSpeechToTextService,
    BailianTextToSpeechService,
)
from app.ai.fakes import (
    FakeAnswerAnalyzer,
    FakeCalibrationQuestionGenerator,
    FakeLLMService,
    FakeProfileExtractor,
    FakeSpeechToTextService,
    FakeTextToSpeechService,
)
from app.ai.interfaces import (
    AnswerAnalyzer,
    CalibrationQuestionGenerator,
    LLMService,
    ProfileExtractor,
    SpeechToTextService,
    TextToSpeechService,
)
from app.core.config import get_settings
from app.core.security import JWTVerificationError, SupabaseTokenVerifier, TokenVerifier
from app.db.session import get_database_session
from app.repositories.calibration import (
    CalibrationRepository,
    SQLCalibrationRepository,
    VoiceAttemptRepository,
)
from app.repositories.daily_sessions import DailySessionRepository, SQLDailySessionRepository
from app.repositories.memory import MemoryRepository, SQLMemoryRepository
from app.repositories.profiles import ProfileRepository, SQLProfileRepository
from app.repositories.retrieval import (
    RetrievalOpportunityRepository,
    SQLRetrievalOpportunityRepository,
)
from app.repositories.users import SQLUserRepository, UserRepository
from app.schemas import AuthenticatedUser
from app.services.cross_session_uow import SQLCrossSessionUnitOfWork
from app.services.mock_interview import MockInterviewService
from app.services.verification import VerificationService
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


async def get_voice_attempt_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[VoiceAttemptRepository]:
    yield SQLCalibrationRepository(session)


async def get_daily_session_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[DailySessionRepository]:
    yield SQLDailySessionRepository(session)


async def get_memory_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[MemoryRepository]:
    yield SQLMemoryRepository(session)


async def get_retrieval_opportunity_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[RetrievalOpportunityRepository]:
    yield SQLRetrievalOpportunityRepository(session)


def get_verification_service(
    session: AsyncSession = Depends(get_database_session),
) -> VerificationService:
    return VerificationService(SQLCrossSessionUnitOfWork(session))


@lru_cache
def get_question_generator() -> CalibrationQuestionGenerator:
    settings = get_settings()
    if settings.llm_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for calibration questions.")
        return BailianCalibrationQuestionGenerator(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_text_model,
        )
    return FakeCalibrationQuestionGenerator()


@lru_cache
def get_llm_service() -> LLMService:
    settings = get_settings()
    if settings.llm_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for lesson content.")
        return BailianLLMService(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_text_model,
        )
    return FakeLLMService(
        {
            "question_prompt": "Tell me about your transition.",
            "reference_answer": "I am building on my transferable experience.",
            "language_explanations": [],
            "imitation_variants": [],
            "transfer_prompts": [],
            "follow_up_questions": [],
        }
    )


@lru_cache
def get_stt_service() -> SpeechToTextService:
    settings = get_settings()
    if settings.stt_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for STT.")
        return BailianSpeechToTextService(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_stt_model,
        )
    return FakeSpeechToTextService()


@lru_cache
def get_tts_service() -> TextToSpeechService:
    settings = get_settings()
    if settings.tts_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for TTS.")
        return BailianTextToSpeechService(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_dashscope_base_url,
            model=settings.bailian_tts_model,
            default_voice=settings.bailian_tts_voice,
        )
    return FakeTextToSpeechService()


@lru_cache
def get_answer_analyzer() -> AnswerAnalyzer:
    settings = get_settings()
    if settings.llm_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for answer analysis.")
        return BailianAnswerAnalyzer(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_text_model,
        )
    return FakeAnswerAnalyzer()


def get_mock_interview_service(
    analyzer: AnswerAnalyzer = Depends(get_answer_analyzer),
) -> MockInterviewService:
    return MockInterviewService(analyzer)


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
    if settings.profile_extractor_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for the profile extractor.")
        return BailianProfileExtractor(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_text_model,
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
