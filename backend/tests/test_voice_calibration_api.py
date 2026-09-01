import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.ai.fakes import (
    FakeAnswerAnalyzer,
    FakeCalibrationQuestionGenerator,
    FakeSpeechToTextService,
    FakeTextToSpeechService,
)
from app.api.dependencies import (
    get_answer_analyzer,
    get_audio_storage,
    get_calibration_repository,
    get_profile_repository,
    get_question_generator,
    get_stt_service,
    get_tts_service,
)
from app.main import app
from app.repositories.calibration import InMemoryCalibrationRepository
from app.repositories.profiles import InMemoryProfileRepository
from app.schemas import AuthenticatedUser, CandidateProfile
from app.storage.audio import FakeAudioStorage


def configure(user: AuthenticatedUser, profiles: InMemoryProfileRepository) -> None:
    calibration = InMemoryCalibrationRepository()
    audio = FakeAudioStorage()
    app.dependency_overrides[get_profile_repository] = lambda: profiles
    app.dependency_overrides[get_calibration_repository] = lambda: calibration
    app.dependency_overrides[get_question_generator] = lambda: FakeCalibrationQuestionGenerator()
    app.dependency_overrides[get_stt_service] = lambda: FakeSpeechToTextService(
        "I led the project and clearly explained the measurable result."
    )
    app.dependency_overrides[get_tts_service] = lambda: FakeTextToSpeechService()
    app.dependency_overrides[get_answer_analyzer] = lambda: FakeAnswerAnalyzer()
    app.dependency_overrides[get_audio_storage] = lambda: audio


def test_calibration_api_fixture_golden_path(
    client: TestClient,
    override_current_user,
) -> None:
    user = AuthenticatedUser(id=uuid4(), email="learner@example.com")
    profiles = InMemoryProfileRepository()
    asyncio.run(
        profiles.save_confirmed(
            user.id,
            uuid4(),
            CandidateProfile(
                target_role="Product Manager",
                work_experience=["payments launch"],
                projects=["checkout redesign"],
                career_transition="product leadership",
            ),
            datetime.now(UTC),
        )
    )
    override_current_user(user)
    configure(user, profiles)

    started = client.post("/api/v1/calibration/sessions")
    assert started.status_code == 201
    session = started.json()
    assert [item["category"] for item in session["questions"]] == [
        "EXPERIENCE",
        "MOTIVATION",
        "PROJECT",
    ]

    tts = client.get(f"/api/v1/calibration/sessions/{session['id']}/questions/EXPERIENCE/tts")
    assert tts.status_code == 200
    assert tts.content.startswith(b"fake-audio")

    attempt_ids = []
    for category in ("EXPERIENCE", "MOTIVATION", "PROJECT"):
        response = client.post(
            f"/api/v1/calibration/sessions/{session['id']}/attempts",
            data={"category": category, "response_duration_ms": "9000"},
            files={"recording": ("answer.webm", f"raw-{category}".encode(), "audio/webm")},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ANALYZED"
        attempt_ids.append(response.json()["id"])

    result = client.get(f"/api/v1/calibration/sessions/{session['id']}")
    assert result.status_code == 200
    payload = result.json()
    assert payload["session"]["status"] == "COMPLETED"
    assert len(payload["attempts"]) == 3
    assert payload["assessment"]["assessment_version"] == "learner_assessment_v1"
    assert len(set(attempt_ids)) == 3


def test_calibration_api_requires_confirmed_profile(
    client: TestClient,
    override_current_user,
) -> None:
    user = AuthenticatedUser(id=uuid4())
    override_current_user(user)
    configure(user, InMemoryProfileRepository())
    response = client.post("/api/v1/calibration/sessions")
    assert response.status_code == 409
    assert "confirmed profile" in response.json()["detail"].lower()
