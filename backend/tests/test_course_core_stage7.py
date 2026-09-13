from pathlib import Path
from uuid import uuid4

import pytest

from app.about_me.entities import AboutMeSnapshot
from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.api.course_dependencies import get_course_answer_service, get_course_support_service
from app.core.auth import AuthenticatedUser
from app.course.answer_service import CourseAnswerService
from app.course.catalog_v1 import COURSE_CATALOG_V1
from app.course.chinese_organizer import FakeChineseAnswerOrganizer
from app.course.context import CourseContextBuilder
from app.course.repository import InMemoryCourseAnswerRepository
from app.course.storage import FakeCourseAudioStorage
from app.course.support_provider import BailianCourseSupportProvider, FakeCourseSupportProvider
from app.course.support_service import CourseSupportService
from app.main import app

QUESTIONS = [(course, question) for course in COURSE_CATALOG_V1 for question in course.questions]


class EmptyAboutMe:
    async def snapshot(self, user_id):
        return AboutMeSnapshot(supplemental_facts=[], target_roles=[], resumes=[], memories=[])


def configure(override_current_user):
    owner = uuid4()
    override_current_user(AuthenticatedUser(id=owner, email="catalog-rollout@example.test"))
    repository = InMemoryCourseAnswerRepository()
    support = CourseSupportService(
        repository=repository,
        context_builder=CourseContextBuilder(about_me=EmptyAboutMe(), answers=repository),
        provider=FakeCourseSupportProvider(),
    )
    service = CourseAnswerService(
        repository=repository,
        audio=FakeCourseAudioStorage(),
        stt=FakeSpeechToTextService("This is a synthetic recording for a contract test."),
        chinese_stt=FakeSpeechToTextService("我负责测试。"),
        tts=FakeTextToSpeechService(),
        chinese_organizer=FakeChineseAnswerOrganizer(),
        feedback_generator=support,
    )
    app.dependency_overrides[get_course_answer_service] = lambda: service
    app.dependency_overrides[get_course_support_service] = lambda: support
    return repository


@pytest.mark.parametrize("course,question", QUESTIONS, ids=[q.id for _, q in QUESTIONS])
def test_all_catalog_questions_share_tts_support_english_and_confirmed_chinese_engine(
    client, override_current_user, course, question
):
    repository = configure(override_current_user)
    base = f"/api/v1/courses/{course.id}/questions/{question.id}"
    tts = client.get(f"{base}/tts")
    assert tts.status_code == 200
    assert tts.content == f"fake-audio:default:{question.text}".encode()
    assert client.get(f"{base}/history").json()["count"] == 0
    hints = client.post(f"{base}/hints")
    assert hints.status_code == 200
    assert hints.json()["static_answer_focus"] == course.answer_focus_en
    assert client.post(f"{base}/expression-materials").status_code == 200
    reference = client.post(f"{base}/reference-answer")
    assert reference.status_code == 200 and question.text in reference.json()["answer"]
    assert repository.answers == {}  # On-demand generation does not create state.

    english = client.post(
        f"{base}/answers",
        data={"idempotency_key": f"{question.id}-english", "answer_language": "ENGLISH"},
        files={"recording": ("english.webm", b"english-test-audio", "audio/webm")},
    )
    assert english.status_code == 201
    saved = english.json()
    assert saved["status"] == "SAVED" and saved["question_id"] == question.id
    assert saved["course_id"] == course.id and saved["feedback"]["status"] == "READY"
    repeated = client.post(
        f"{base}/answers",
        data={"idempotency_key": f"{question.id}-english", "answer_language": "ENGLISH"},
        files={"recording": ("retry.webm", b"retry-test-audio", "audio/webm")},
    )
    assert repeated.json()["id"] == saved["id"]

    chinese = client.post(
        f"{base}/answers",
        data={"idempotency_key": f"{question.id}-chinese", "answer_language": "CHINESE"},
        files={"recording": ("chinese.webm", b"chinese-test-audio", "audio/webm")},
    )
    assert chinese.status_code == 201
    draft = chinese.json()
    assert draft["status"] == "AWAITING_CONFIRMATION" and draft["feedback"] is None
    assert client.get(f"{base}/history").json()["count"] == 1
    assert client.get(f"{base}/drafts").json()["answers"][0]["id"] == draft["id"]
    confirmed = client.post(f"/api/v1/course-answers/{draft['id']}/confirm")
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "SAVED"
    assert confirmed.json()["transcript"]["organized_english"] == "I was responsible for testing."
    assert confirmed.json()["feedback"]["status"] == "READY"
    assert client.get(f"{base}/history").json()["count"] == 2
    assert client.get(f"{base}/drafts").json()["answers"] == []
    if question.kind == "FOLLOW_UP":
        core = f"/api/v1/courses/{course.id}/questions/{course.id}.core/history"
        assert client.get(core).json()["count"] == 0  # No core-answer prerequisite or leakage.


def test_course_thirty_has_no_follow_up_and_cross_course_questions_are_rejected(
    client, override_current_user
):
    configure(override_current_user)
    course = client.get("/api/v1/courses/course-30").json()
    assert course["follow_up_question"] is None
    for question_id in ("course-30.follow-up", "course-29.core"):
        base = f"/api/v1/courses/course-30/questions/{question_id}"
        assert client.get(f"{base}/tts").status_code == 404
        assert client.get(f"{base}/history").status_code == 404
        assert client.post(f"{base}/hints").status_code == 404
        assert (
            client.post(
                f"{base}/answers",
                data={"idempotency_key": f"invalid-{question_id}"},
                files={"recording": ("answer.webm", b"test-audio", "audio/webm")},
            ).status_code
            == 404
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("course,question", QUESTIONS, ids=[q.id for _, q in QUESTIONS])
async def test_no_context_production_reference_is_question_bound_without_provider_or_profile_facts(
    course, question
):
    context = await CourseContextBuilder(
        about_me=EmptyAboutMe(), answers=InMemoryCourseAnswerRepository()
    ).build(user_id=uuid4(), course_id=course.id, question_id=question.id)
    # Invalid provider URL proves the empty-context fallback makes no network request.
    provider = BailianCourseSupportProvider(
        api_key="test", base_url="http://invalid.test", model="test"
    )
    reference = await provider.reference_answer(context)
    assert reference.provider_name == "deterministic-fallback"
    assert question.text in reference.answer and "[your direct response]" in reference.answer


def test_frontend_catalog_rollout_has_no_course_eleven_branch_and_resets_course_state():
    root = Path(__file__).resolve().parents[2]
    detail = (root / "frontend/components/course-core/course-detail.tsx").read_text(
        encoding="utf-8"
    )
    workspace = (root / "frontend/components/course-core/course-workspace.tsx").read_text(
        encoding="utf-8"
    )
    assert "ENGLISH_ANSWER_ENABLED_COURSE_IDS" not in detail
    assert "course?.id === courseId" in detail and "key={course.id}" in detail
    assert "cancelled" in detail
    assert "String(course.order).padStart" in workspace
    for path in (root / "backend/app/course", root / "frontend/components/course-core"):
        for file in path.rglob("*"):
            if file.suffix in {".py", ".ts", ".tsx"}:
                assert "course-11" not in file.read_text(encoding="utf-8"), file
