from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.course_dependencies import get_course_support_service
from app.course.support_entities import (
    CourseExpressionMaterials,
    CourseHints,
    CourseReferenceAnswer,
    ExpressionMaterial,
)
from app.main import app
from app.schemas import AuthenticatedUser


class StubCourseSupportService:
    async def hints(self, **kwargs):
        del kwargs
        return CourseHints(
            static_answer_focus="fixed focus",
            keywords=["ownership"],
            phrases=["I took ownership"],
            sentence_frames=["I chose __ because __."],
            prompt_version="course_hints_v1",
            provider_name="fake",
        )

    async def expression_materials(self, **kwargs):
        del kwargs
        return CourseExpressionMaterials(
            materials=[ExpressionMaterial(kind="PHRASE", text="I took ownership")],
            prompt_version="course_expression_materials_v1",
            provider_name="fake",
        )

    async def reference_answer(self, **kwargs):
        del kwargs
        return CourseReferenceAnswer(
            answer="A generic reference answer.",
            prompt_version="course_reference_answer_v1",
            provider_name="fake",
        )


def configure(override_current_user):
    override_current_user(AuthenticatedUser(id=uuid4(), email="support@example.test"))
    app.dependency_overrides[get_course_support_service] = lambda: StubCourseSupportService()


def test_support_endpoints_require_authentication(client: TestClient) -> None:
    base = "/api/v1/courses/course-11/questions/course-11.core"
    assert client.post(f"{base}/hints").status_code == 401
    assert client.post(f"{base}/expression-materials").status_code == 401
    assert client.post(f"{base}/reference-answer").status_code == 401


def test_support_endpoints_return_separate_structured_contracts(
    client: TestClient, override_current_user
) -> None:
    configure(override_current_user)
    base = "/api/v1/courses/course-11/questions/course-11.core"
    hints = client.post(f"{base}/hints")
    materials = client.post(f"{base}/expression-materials")
    reference = client.post(f"{base}/reference-answer")

    assert hints.status_code == 200
    assert hints.json()["static_answer_focus"] == "fixed focus"
    assert materials.status_code == 200
    assert materials.json()["materials"][0]["kind"] == "PHRASE"
    assert reference.status_code == 200
    assert reference.json()["answer"] == "A generic reference answer."
