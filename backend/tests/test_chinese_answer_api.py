from uuid import uuid4

from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.api.course_dependencies import get_course_answer_service
from app.core.auth import AuthenticatedUser
from app.course.answer_service import CourseAnswerService
from app.course.chinese_organizer import FakeChineseAnswerOrganizer
from app.course.repository import InMemoryCourseAnswerRepository
from app.course.storage import FakeCourseAudioStorage
from app.main import app


def test_chinese_draft_api_confirmation_recovery_discard_and_ownership(
    client, override_current_user
):
    owner = AuthenticatedUser(id=uuid4(), email="p6@example.test")
    override_current_user(owner)
    service = CourseAnswerService(
        repository=InMemoryCourseAnswerRepository(),
        stt=FakeSpeechToTextService("我负责测试。"),
        tts=FakeTextToSpeechService(),
        audio=FakeCourseAudioStorage(),
        chinese_organizer=FakeChineseAnswerOrganizer(),
    )
    app.dependency_overrides[get_course_answer_service] = lambda: service
    path = "/api/v1/courses/course-11/questions/course-11.core"
    response = client.post(
        path + "/answers",
        data={"answer_language": "CHINESE", "idempotency_key": "p6-api-request"},
        files={"recording": ("answer.webm", b"audio", "audio/webm")},
    )
    assert response.status_code == 201
    draft = response.json()
    answer_path = f"/api/v1/course-answers/{draft['id']}"
    assert draft["status"] == "AWAITING_CONFIRMATION"
    assert "audio_path" not in draft and draft["transcript"]["organized_english"]
    assert client.get(path + "/history").json()["count"] == 0
    assert client.get(path + "/drafts").json()["answers"][0]["id"] == draft["id"]
    assert client.get(answer_path).json()["status"] == "AWAITING_CONFIRMATION"
    assert client.get(answer_path + "/audio").status_code == 404
    other = AuthenticatedUser(id=uuid4(), email="other@example.test")
    override_current_user(other)
    assert client.get(path + "/drafts").json()["count"] == 0
    assert client.post(answer_path + "/confirm").status_code == 404
    assert client.delete(answer_path + "/draft").status_code == 204
    override_current_user(owner)
    assert client.post(answer_path + "/confirm").json()["status"] == "SAVED"
    assert client.post(answer_path + "/confirm").json()["status"] == "SAVED"
    assert client.get(path + "/history").json()["count"] == 1
    assert client.get(path + "/drafts").json()["count"] == 0
    assert client.delete(answer_path + "/draft").status_code == 409
    assert client.delete(answer_path).status_code == 204
    response = client.post(
        path + "/answers",
        data={"answer_language": "CHINESE", "idempotency_key": "p6-api-discard"},
        files={"recording": ("answer.webm", b"audio", "audio/webm")},
    )
    discard = f"/api/v1/course-answers/{response.json()['id']}/draft"
    assert client.delete(discard).status_code == 204
    assert client.delete(discard).status_code == 204
    assert client.get(path + "/drafts").json()["count"] == 0


def test_new_draft_endpoints_require_authentication(client):
    base = "/api/v1/course-answers/00000000-0000-0000-0000-000000000001"
    assert client.post(base + "/confirm").status_code == 401
    assert client.delete(base + "/draft").status_code == 401
    assert (
        client.get("/api/v1/courses/course-11/questions/course-11.core/drafts").status_code == 401
    )
