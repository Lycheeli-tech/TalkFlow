from collections.abc import AsyncIterator, Callable

import pytest
from fastapi.testclient import TestClient

from app.ai.interfaces import ProfileExtractor
from app.api.dependencies import (
    get_current_user,
    get_profile_extractor,
    get_profile_repository,
    get_user_repository,
)
from app.main import app
from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository
from app.schemas import AuthenticatedUser


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def override_current_user() -> Callable[[AuthenticatedUser], None]:
    def apply(user: AuthenticatedUser) -> None:
        app.dependency_overrides[get_current_user] = lambda: user

    return apply


@pytest.fixture
def override_user_repository() -> Callable[[UserRepository], None]:
    def apply(repository: UserRepository) -> None:
        async def override() -> AsyncIterator[UserRepository]:
            yield repository

        app.dependency_overrides[get_user_repository] = override

    return apply


@pytest.fixture
def override_profile_dependencies() -> Callable[[ProfileRepository, ProfileExtractor], None]:
    def apply(repository: ProfileRepository, extractor: ProfileExtractor) -> None:
        async def override_repository() -> AsyncIterator[ProfileRepository]:
            yield repository

        app.dependency_overrides[get_profile_repository] = override_repository
        app.dependency_overrides[get_profile_extractor] = lambda: extractor

    return apply
