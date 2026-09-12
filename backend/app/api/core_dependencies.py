from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.ai.bailian import BailianSpeechToTextService, BailianTextToSpeechService
from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.ai.interfaces import SpeechToTextService, TextToSpeechService
from app.core.auth import AuthenticatedUser
from app.core.config import get_settings
from app.core.security import JWTVerificationError, SupabaseTokenVerifier, TokenVerifier

course_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_course_token_verifier() -> TokenVerifier:
    return SupabaseTokenVerifier.from_settings()


def get_course_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(course_bearer_scheme),
    verifier: TokenVerifier = Depends(get_course_token_verifier),
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


@lru_cache
def get_course_stt_service() -> SpeechToTextService:
    settings = get_settings()
    if settings.stt_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for Course Answer STT.")
        return BailianSpeechToTextService(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_stt_model,
        )
    return FakeSpeechToTextService()


@lru_cache
def get_course_tts_service() -> TextToSpeechService:
    settings = get_settings()
    if settings.tts_provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for Course Question TTS.")
        return BailianTextToSpeechService(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_dashscope_base_url,
            model=settings.bailian_tts_model,
            default_voice=settings.bailian_tts_voice,
        )
    return FakeTextToSpeechService()
