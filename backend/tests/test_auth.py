from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import JWTVerificationError, SupabaseTokenVerifier


def test_users_me_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_supabase_hs256_token_is_verified() -> None:
    user_id = uuid4()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_jwt_secret="test-secret-that-is-never-used-outside-tests",
    )
    token = jwt.encode(
        {
            "sub": str(user_id),
            "email": "learner@example.com",
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )

    user = SupabaseTokenVerifier(settings).verify(token)

    assert user.id == user_id
    assert user.email == "learner@example.com"


def test_expired_token_is_rejected() -> None:
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_jwt_secret="test-secret-that-is-never-used-outside-tests",
    )
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )

    with pytest.raises(JWTVerificationError):
        SupabaseTokenVerifier(settings).verify(token)
