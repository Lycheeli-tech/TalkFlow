from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.ai.interfaces import ProfileExtractor
from app.repositories.profiles import ProfileRepository, new_source_document
from app.schemas import CandidateProfile, ConfirmedProfile, SourceDocument
from app.storage.documents import DocumentStorage, FakeDocumentStorage


class ProfileService:
    def __init__(
        self,
        repository: ProfileRepository,
        extractor: ProfileExtractor,
        storage: DocumentStorage | None = None,
    ) -> None:
        self._repository = repository
        self._extractor = extractor
        self._storage = storage or FakeDocumentStorage()

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
        return await self._create_candidate(
            user_id=user_id,
            target_role=target_role,
            raw_text=cleaned_text,
            source_type="background_text",
            filename=None,
        )

    async def create_pdf_candidate(
        self,
        *,
        user_id: UUID,
        target_role: str,
        filename: str,
        raw_text: str,
        content: bytes,
    ) -> tuple[SourceDocument, CandidateProfile]:
        source_id = uuid4()
        storage_path = await self._storage.store_resume(
            user_id=user_id,
            document_id=source_id,
            filename=filename,
            content=content,
        )
        return await self._create_candidate(
            user_id=user_id,
            target_role=target_role,
            raw_text=raw_text,
            source_type="resume_pdf",
            filename=filename,
            source_id=source_id,
            storage_path=storage_path,
        )

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

    async def _create_candidate(
        self,
        *,
        user_id: UUID,
        target_role: str,
        raw_text: str,
        source_type: str,
        filename: str | None,
        source_id: UUID | None = None,
        storage_path: str | None = None,
    ) -> tuple[SourceDocument, CandidateProfile]:
        source = new_source_document(
            source_id=source_id or uuid4(),
            user_id=user_id,
            source_type=source_type,
            filename=filename,
            raw_text=raw_text,
            storage_path=storage_path,
        )
        await self._repository.create_source(source)
        candidate = await self._extractor.extract(raw_text=raw_text, target_role=target_role)
        source = await self._repository.save_candidate(
            source.id, user_id, candidate, self._extractor.version
        )
        return source, candidate
