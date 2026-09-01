from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.ai.interfaces import ProfileExtractor
from app.repositories.profiles import ProfileRepository, new_source_document
from app.schemas import CandidateProfile, ConfirmedProfile, SourceDocument


class ProfileService:
    def __init__(self, repository: ProfileRepository, extractor: ProfileExtractor) -> None:
        self._repository = repository
        self._extractor = extractor

    async def create_text_candidate(
        self,
        *,
        user_id: UUID,
        target_role: str,
        raw_text: str,
    ) -> tuple[SourceDocument, CandidateProfile]:
        cleaned_text = raw_text.strip()
        if not cleaned_text:
            raise ValueError("Background text cannot be empty.")
        source = new_source_document(
            source_id=uuid4(),
            user_id=user_id,
            source_type="background_text",
            filename=None,
            raw_text=cleaned_text,
        )
        await self._repository.create_source(source)
        candidate = await self._extractor.extract(raw_text=cleaned_text, target_role=target_role)
        source = await self._repository.save_candidate(
            source.id,
            user_id,
            candidate,
            self._extractor.version,
        )
        return source, candidate

    async def confirm_candidate(
        self,
        *,
        user_id: UUID,
        source_id: UUID,
        edited_candidate: CandidateProfile,
    ) -> ConfirmedProfile:
        source = await self._repository.get_source(source_id, user_id)
        if source is None or source.candidate_profile is None:
            raise LookupError("An extracted candidate profile is required before confirmation.")
        return await self._repository.save_confirmed(
            user_id,
            source_id,
            edited_candidate,
            datetime.now(UTC),
        )

    async def get_confirmed(self, user_id: UUID) -> ConfirmedProfile | None:
        return await self._repository.get_confirmed(user_id)
