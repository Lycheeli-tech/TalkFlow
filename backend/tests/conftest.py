from collections.abc import AsyncIterator, Callable

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app.ai.interfaces import ProfileExtractor
from app.api.dependencies import (
    get_current_user,
    get_profile_extractor,
    get_profile_repository,
    get_user_repository,
)
from app.api.v1 import calibration, daily, entry, journey, memory, practice, profiles, users
from app.main import app, create_app
from app.repositories.profiles import ProfileRepository
from app.repositories.users import UserRepository
from app.schemas import AuthenticatedUser

legacy_test_router = APIRouter()
legacy_test_router.include_router(users.router, prefix="/users", tags=["users"])
legacy_test_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
legacy_test_router.include_router(calibration.router, prefix="/calibration", tags=["calibration"])
legacy_test_router.include_router(daily.router, prefix="/daily", tags=["daily"])
legacy_test_router.include_router(memory.router, prefix="/memory", tags=["memory"])
legacy_test_router.include_router(practice.router, prefix="/practice", tags=["practice"])
legacy_test_router.include_router(journey.router, prefix="/journey", tags=["journey"])
legacy_test_router.include_router(entry.router, prefix="/entry", tags=["entry"])

legacy_test_app = create_app()
legacy_test_app.include_router(legacy_test_router, prefix="/api/v1")


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> AsyncIterator[None]:
    yield
    app.dependency_overrides.clear()
    legacy_test_app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def legacy_client() -> TestClient:
    """Explicit rollback runtime for historical Legacy API regression tests only."""
    with TestClient(legacy_test_app) as test_client:
        yield test_client


@pytest.fixture
def override_current_user() -> Callable[[AuthenticatedUser], None]:
    def apply(user: AuthenticatedUser) -> None:
        app.dependency_overrides[get_current_user] = lambda: user
        legacy_test_app.dependency_overrides[get_current_user] = lambda: user

    return apply


@pytest.fixture
def override_user_repository() -> Callable[[UserRepository], None]:
    def apply(repository: UserRepository) -> None:
        async def override() -> AsyncIterator[UserRepository]:
            yield repository

        app.dependency_overrides[get_user_repository] = override
        legacy_test_app.dependency_overrides[get_user_repository] = override

    return apply


@pytest.fixture
def override_profile_dependencies() -> Callable[[ProfileRepository, ProfileExtractor], None]:
    def apply(repository: ProfileRepository, extractor: ProfileExtractor) -> None:
        async def override_repository() -> AsyncIterator[ProfileRepository]:
            yield repository

        app.dependency_overrides[get_profile_repository] = override_repository
        app.dependency_overrides[get_profile_extractor] = lambda: extractor
        legacy_test_app.dependency_overrides[get_profile_repository] = override_repository
        legacy_test_app.dependency_overrides[get_profile_extractor] = lambda: extractor

    return apply
