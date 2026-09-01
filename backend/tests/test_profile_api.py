from collections.abc import Callable
from uuid import UUID

from fastapi.testclient import TestClient

from app.ai.fakes import FakeProfileExtractor
from app.ai.interfaces import ProfileExtractor
from app.repositories.profiles import InMemoryProfileRepository, ProfileRepository
from app.schemas import AuthenticatedUser, CandidateProfile

USER = AuthenticatedUser(id=UUID("11111111-1111-4111-8111-111111111111"))


def configure_profile_api(
    *,
    override_current_user: Callable[[AuthenticatedUser], None],
    override_profile_dependencies: Callable[[ProfileRepository, ProfileExtractor], None],
) -> None:
    override_current_user(USER)
    override_profile_dependencies(
        InMemoryProfileRepository(),
        FakeProfileExtractor(
            CandidateProfile(
                target_role="Product Manager",
                skills=["Communication"],
                potential_story_candidates=["Possible story, awaiting confirmation"],
            )
        ),
    )


def test_text_import_review_and_confirmation_flow(
    client: TestClient,
    override_current_user: Callable[[AuthenticatedUser], None],
    override_profile_dependencies: Callable[[ProfileRepository, ProfileExtractor], None],
) -> None:
    configure_profile_api(
        override_current_user=override_current_user,
        override_profile_dependencies=override_profile_dependencies,
    )
    imported = client.post(
        "/api/v1/profiles/sources/text",
        json={
            "target_role": "Product Manager",
            "raw_text": "I led a cross-functional launch.",
        },
    )

    assert imported.status_code == 201
    payload = imported.json()
    assert payload["candidate"]["potential_story_candidates"]
    assert client.get("/api/v1/profiles/me").status_code == 404

    payload["candidate"]["skills"].append("User research")
    confirmed = client.post(
        "/api/v1/profiles/confirm",
        json={"source_id": payload["source_id"], "candidate": payload["candidate"]},
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["skills"] == ["Communication", "User research"]
    assert "potential_story_candidates" not in confirmed.json()
    assert client.get("/api/v1/profiles/me").json() == confirmed.json()


def test_pdf_upload_rejects_non_pdf_content(
    client: TestClient,
    override_current_user: Callable[[AuthenticatedUser], None],
    override_profile_dependencies: Callable[[ProfileRepository, ProfileExtractor], None],
) -> None:
    configure_profile_api(
        override_current_user=override_current_user,
        override_profile_dependencies=override_profile_dependencies,
    )
    response = client.post(
        "/api/v1/profiles/sources/pdf",
        data={"target_role": "Product Manager"},
        files={"resume": ("resume.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Uploaded file is not a valid PDF."
