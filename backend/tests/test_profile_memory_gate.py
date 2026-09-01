from uuid import UUID

import pytest

from app.ai.fakes import FakeProfileExtractor
from app.repositories.profiles import InMemoryProfileRepository
from app.schemas import CandidateProfile
from app.services.profiles import ProfileService

USER_ID = UUID("10000000-0000-0000-0000-000000000001")
OTHER_USER_ID = UUID("10000000-0000-0000-0000-000000000002")


@pytest.fixture
def candidate() -> CandidateProfile:
    return CandidateProfile(
        target_role="Product Manager",
        work_experience=["Led a cross-functional product launch."],
        projects=["Interview practice platform"],
        skills=["Product strategy", "Stakeholder communication"],
        industries=["Education technology"],
        career_transition="Moving from engineering into product management.",
        technical_keywords=["Python", "SQL"],
        potential_story_candidates=["The product launch may become a STAR story."],
    )


async def test_candidate_is_not_durable_truth_until_user_confirms(
    candidate: CandidateProfile,
) -> None:
    repository = InMemoryProfileRepository()
    service = ProfileService(repository, FakeProfileExtractor(candidate))

    source, extracted = await service.create_text_candidate(
        user_id=USER_ID,
        target_role="Product Manager",
        raw_text="Engineering background and a cross-functional product launch.",
    )

    assert extracted == candidate
    assert source.parse_status == "extracted"
    assert await service.get_confirmed(USER_ID) is None

    edited = extracted.model_copy(update={"skills": [*extracted.skills, "User research"]})
    confirmed = await service.confirm_candidate(
        user_id=USER_ID,
        source_id=source.id,
        edited_candidate=edited,
    )

    assert confirmed.skills[-1] == "User research"
    assert not hasattr(confirmed, "potential_story_candidates")
    assert confirmed.source_document_id == source.id
    assert await service.get_confirmed(USER_ID) == confirmed


async def test_source_and_confirmation_are_user_scoped(candidate: CandidateProfile) -> None:
    repository = InMemoryProfileRepository()
    service = ProfileService(repository, FakeProfileExtractor(candidate))
    source, extracted = await service.create_text_candidate(
        user_id=USER_ID,
        target_role="Product Manager",
        raw_text="Private resume content.",
    )

    with pytest.raises(LookupError):
        await service.confirm_candidate(
            user_id=OTHER_USER_ID,
            source_id=source.id,
            edited_candidate=extracted,
        )

    assert await service.get_confirmed(OTHER_USER_ID) is None


async def test_pdf_source_keeps_private_storage_provenance(candidate: CandidateProfile) -> None:
    repository = InMemoryProfileRepository()
    service = ProfileService(repository, FakeProfileExtractor(candidate))

    source, _ = await service.create_pdf_candidate(
        user_id=USER_ID,
        target_role="Product Manager",
        filename="resume.pdf",
        raw_text="Extracted resume text.",
        content=b"%PDF fixture",
    )

    assert source.source_type == "resume_pdf"
    assert source.storage_path == f"{USER_ID}/{source.id}/resume.pdf"


async def test_extraction_failure_preserves_source_document() -> None:
    class FailingExtractor:
        version = "failing_fixture_v1"

        async def extract(self, *, raw_text: str, target_role: str) -> CandidateProfile:
            del raw_text, target_role
            raise RuntimeError("provider unavailable")

    repository = InMemoryProfileRepository()
    service = ProfileService(repository, FailingExtractor())

    with pytest.raises(RuntimeError, match="provider unavailable"):
        await service.create_text_candidate(
            user_id=USER_ID,
            target_role="Product Manager",
            raw_text="This source must survive extraction failure.",
        )

    [source] = repository.sources.values()
    assert source.raw_text == "This source must survive extraction failure."
    assert source.parse_status == "ready"
    assert await service.get_confirmed(USER_ID) is None
