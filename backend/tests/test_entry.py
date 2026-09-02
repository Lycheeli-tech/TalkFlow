from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.repositories.calibration import InMemoryCalibrationRepository
from app.repositories.profiles import InMemoryProfileRepository
from app.schemas import AuthenticatedUser, CalibrationSession, ConfirmedProfile, UserState


def test_entry_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/entry")
    assert response.status_code == 401


class FakeUsers:
    def __init__(self, state: UserState) -> None:
        self.state = state

    async def get_or_create(self, user_id):
        return self.state


@pytest.mark.asyncio
async def test_entry_routes_profile_and_calibration_states() -> None:
    from app.api.v1.entry import get_application_entry

    user_id = uuid4()
    users = FakeUsers(UserState(id=user_id, interface_language="zh-CN"))
    profiles = InMemoryProfileRepository()
    calibration = InMemoryCalibrationRepository()
    current = AuthenticatedUser(id=user_id)

    assert (
        await get_application_entry(current, users, profiles, calibration)
    ).stage == "ONBOARDING"
    now = datetime.now(UTC)
    profiles.profiles[user_id] = ConfirmedProfile(
        user_id=user_id,
        source_document_id=uuid4(),
        target_role="PM",
        confirmed_at=now,
        updated_at=now,
    )
    assert (
        await get_application_entry(current, users, profiles, calibration)
    ).stage == "CALIBRATION"
    calibration.sessions[uuid4()] = CalibrationSession(
        id=uuid4(),
        user_id=user_id,
        questions=[],
        started_at=now,
        status="COMPLETED",
        completed_at=now,
    )
    assert (await get_application_entry(current, users, profiles, calibration)).stage == "TODAY"
