from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.fakes import FakeProfileExtractor
from app.ai.interfaces import ProfileExtractor
from app.ai.profile_extractor import OpenAIProfileExtractor
from app.core.config import get_settings
from app.core.security import JWTVerificationError, SupabaseTokenVerifier, TokenVerifier
from app.db.session import get_database_session
from app.repositories.profiles import ProfileRepository, SQLProfileRepository
from app.repositories.users import SQLUserRepository, UserRepository
from app.schemas import AuthenticatedUser
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
