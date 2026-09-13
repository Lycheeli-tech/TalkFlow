from uuid import uuid4

from fastapi.testclient import TestClient

from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.api.course_dependencies import get_course_answer_service
from app.course.answer_service import CourseAnswerService
from app.course.repository import InMemoryCourseAnswerRepository
from app.course.storage import FakeCourseAudioStorage
from app.main import app
from app.schemas import AuthenticatedUser


def configure_course_service(client: TestClient, override_current_user):
    user = AuthenticatedUser(id=uuid4(), email="course@example.test")
    override_current_user(user)
    repository = InMemoryCourseAnswerRepository()
    audio = FakeCourseAudioStorage()
    service = CourseAnswerService(
        repository=repository,
        stt=FakeSpeechToTextService("I owned the key technical decision."),
        tts=FakeTextToSpeechService(),
        audio=audio,
    )
    app.dependency_overrides[get_course_answer_service] = lambda: service
    return user, repository, audio


def test_course_answer_api_requires_authentication(client: TestClient) -> None:
    assert (
        client.get("/api/v1/course-answers/00000000-0000-0000-0000-000000000001").status_code == 401
    )
    assert (
        client.get("/api/v1/courses/course-11/questions/course-11.core/history").status_code == 401
    )


def test_submit_history_detail_audio_and_retry_contracts(
    client: TestClient, override_current_user
) -> None:
    _, _, audio = configure_course_service(client, override_current_user)
    response = client.post(
        "/api/v1/courses/course-11/questions/course-11.core/answers",
        data={"idempotency_key": "api-answer-1", "response_duration_ms": "2200"},
        files={"recording": ("answer.webm", b"audio", "audio/webm")},
    )
    assert response.status_code == 201
    payload = response.json()
    answer_id = payload["id"]
    assert payload["status"] == "SAVED"
    assert payload["transcript"]["transcript"] == "I owned the key technical decision."
    assert "audio_path" not in payload

    history = client.get("/api/v1/courses/course-11/questions/course-11.core/history")
    assert history.status_code == 200
    assert history.json()["count"] == 1
    assert history.json()["answers"][0]["id"] == answer_id

    detail = client.get(f"/api/v1/course-answers/{answer_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == answer_id
    assert client.get(f"/api/v1/course-answers/{answer_id}/audio").content == b"audio"

    replay = client.post(
        "/api/v1/courses/course-11/questions/course-11.core/answers",
        data={"idempotency_key": "api-answer-1", "response_duration_ms": "9999"},
        files={"recording": ("answer.webm", b"duplicate", "audio/webm")},
    )
    assert replay.status_code == 201
    assert replay.json()["id"] == answer_id
    assert client.post(f"/api/v1/course-answers/{answer_id}/retry").json()["id"] == answer_id

    deleted = client.delete(f"/api/v1/course-answers/{answer_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/course-answers/{answer_id}").status_code == 404
    assert audio.objects == {}


def test_course_answer_api_validates_media_question_and_catalog(
    client: TestClient, override_current_user
) -> None:
    configure_course_service(client, override_current_user)
    invalid_media = client.post(
        "/api/v1/courses/course-11/questions/course-11.core/answers",
        data={"idempotency_key": "invalid-media"},
        files={"recording": ("answer.txt", b"text", "text/plain")},
    )
    assert invalid_media.status_code == 415

    wrong_question = client.post(
        "/api/v1/courses/course-11/questions/course-10.core/answers",
        data={"idempotency_key": "wrong-question"},
        files={"recording": ("answer.webm", b"audio", "audio/webm")},
    )
    assert wrong_question.status_code == 404

    outside_catalog = client.post(
        "/api/v1/courses/course-31/questions/course-31.core/answers",
        data={"idempotency_key": "outside-catalog"},
        files={"recording": ("answer.webm", b"audio", "audio/webm")},
    )
    assert outside_catalog.status_code == 404


def test_question_tts_is_authenticated_and_exact(client: TestClient, override_current_user) -> None:
    configure_course_service(client, override_current_user)
    response = client.get("/api/v1/courses/course-11/questions/course-11.follow-up/tts")
    assert response.status_code == 200
    assert response.content == b"fake-audio:default:What was specifically your contribution?"
    assert (
        client.get("/api/v1/courses/course-30/questions/course-30.follow-up/tts").status_code == 404
    )
