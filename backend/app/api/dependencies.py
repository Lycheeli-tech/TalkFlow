from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import JWTVerificationError, SupabaseTokenVerifier, TokenVerifier
from app.db.session import get_database_session
from app.repositories.users import SQLUserRepository, UserRepository
from app.schemas import AuthenticatedUser

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
