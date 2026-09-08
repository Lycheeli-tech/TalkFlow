from typing import Any, Protocol
from uuid import UUID

import jwt
from jwt import PyJWKClient

from app.core.config import Settings, get_settings
from app.schemas import AuthenticatedUser


class JWTVerificationError(Exception):
    """Raised when a Supabase access token cannot be trusted."""


class TokenVerifier(Protocol):
    def verify(self, token: str) -> AuthenticatedUser: ...


class SupabaseTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._jwks_client = (
            None if settings.supabase_jwt_secret else PyJWKClient(settings.supabase_jwks_url)
        )

    @classmethod
    def from_settings(cls) -> "SupabaseTokenVerifier":
        return cls(get_settings())

    def verify(self, token: str) -> AuthenticatedUser:
        try:
            key: Any
            algorithms: list[str]
            if self._settings.supabase_jwt_secret:
                key = self._settings.supabase_jwt_secret
                algorithms = ["HS256"]
            else:
                if self._jwks_client is None:
                    raise JWTVerificationError("Supabase JWKS is not configured.")
                key = self._jwks_client.get_signing_key_from_jwt(token).key
                algorithms = ["RS256", "ES256"]

            payload = jwt.decode(
                token,
                key=key,
                algorithms=algorithms,
                audience=self._settings.supabase_jwt_audience,
                issuer=f"{self._settings.supabase_url.rstrip('/')}/auth/v1",
                leeway=self._settings.supabase_jwt_leeway_seconds,
                options={"require": ["sub", "exp", "aud", "iss"]},
            )
            return AuthenticatedUser(
                id=UUID(payload["sub"]),
                email=payload.get("email"),
            )
        except (jwt.PyJWTError, ValueError, KeyError) as error:
            raise JWTVerificationError from error
