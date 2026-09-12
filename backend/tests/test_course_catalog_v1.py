import hashlib
import json
from dataclasses import FrozenInstanceError

import pytest
from fastapi.testclient import TestClient

from app.course.catalog_v1 import CATALOG_VERSION, COURSE_CATALOG_V1

EXPECTED_CATALOG_SHA256 = "b4a24ce143d7cbe3379900445c00bae9de0243216eef3827bb5939d27a7320e6"


def catalog_payload() -> list[dict[str, object]]:
    return [
        {
            "id": course.id,
            "order": course.order,
            "name_en": course.name_en,
            "name_zh_cn": course.name_zh_cn,
            "answer_focus_en": course.answer_focus_en,
            "answer_focus_zh_cn": course.answer_focus_zh_cn,
            "questions": [
                {"id": question.id, "kind": question.kind, "text": question.text}
                for question in course.questions
            ],
        }
        for course in COURSE_CATALOG_V1
    ]


def test_catalog_has_stable_course_order_and_question_shape() -> None:
    assert CATALOG_VERSION == "course_catalog_v1"
    assert len(COURSE_CATALOG_V1) == 30
    assert [course.id for course in COURSE_CATALOG_V1] == [
        f"course-{order:02d}" for order in range(1, 31)
    ]
    assert [course.order for course in COURSE_CATALOG_V1] == list(range(1, 31))

    question_ids = [question.id for course in COURSE_CATALOG_V1 for question in course.questions]
    assert len(question_ids) == 59
    assert len(set(question_ids)) == 59
    for course in COURSE_CATALOG_V1[:29]:
        assert [question.id for question in course.questions] == [
            f"{course.id}.core",
            f"{course.id}.follow-up",
        ]
    assert [question.id for question in COURSE_CATALOG_V1[29].questions] == ["course-30.core"]
    assert COURSE_CATALOG_V1[29].follow_up_question is None


def test_catalog_static_content_is_complete_and_immutable() -> None:
    for course in COURSE_CATALOG_V1:
        assert course.name_en.strip()
        assert course.name_zh_cn.strip()
        assert course.answer_focus_en.strip()
        assert course.answer_focus_zh_cn.strip()
        for question in course.questions:
            assert question.text.strip()
            assert question.id.startswith(f"{course.id}.")

    with pytest.raises(FrozenInstanceError):
        COURSE_CATALOG_V1[0].name_en = "Model-generated replacement"  # type: ignore[misc]


def test_catalog_content_digest_prevents_silent_rewording_or_reordering() -> None:
    serialized = json.dumps(catalog_payload(), ensure_ascii=False, separators=(",", ":")).encode()
    assert hashlib.sha256(serialized).hexdigest() == EXPECTED_CATALOG_SHA256


def test_catalog_api_is_public_read_only_and_returns_the_same_static_content(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    assert response.json()["version"] == CATALOG_VERSION
    assert len(response.json()["courses"]) == 30

    course = client.get("/api/v1/courses/course-11")
    assert course.status_code == 200
    assert course.json()["core_question"]["text"] == "Tell me about a project you are proud of."
    assert course.json()["follow_up_question"]["id"] == "course-11.follow-up"

    assert client.get("/api/v1/courses/course-31").status_code == 404
    assert client.post("/api/v1/courses").status_code == 405
