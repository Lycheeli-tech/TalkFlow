from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProfileRow, SourceDocumentRow
from app.schemas import CandidateProfile, ConfirmedProfile, SourceDocument


class ProfileRepository(Protocol):
    async def create_source(self, source: SourceDocument) -> SourceDocument: ...

    async def get_source(self, source_id: UUID, user_id: UUID) -> SourceDocument | None: ...

    async def save_candidate(
        self,
        source_id: UUID,
        user_id: UUID,
        candidate: CandidateProfile,
        extractor_version: str,
    ) -> SourceDocument: ...

    async def save_confirmed(
        self,
        user_id: UUID,
        source_id: UUID,
        candidate: CandidateProfile,
        confirmed_at: datetime,
    ) -> ConfirmedProfile: ...

    async def get_confirmed(self, user_id: UUID) -> ConfirmedProfile | None: ...


class SQLProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_source(self, source: SourceDocument) -> SourceDocument:
        row = SourceDocumentRow(**source.model_dump())
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return SourceDocument.model_validate(row)

    async def get_source(self, source_id: UUID, user_id: UUID) -> SourceDocument | None:
        row = await self._session.scalar(
            select(SourceDocumentRow).where(
                SourceDocumentRow.id == source_id,
                SourceDocumentRow.user_id == user_id,
            )
        )
        return SourceDocument.model_validate(row) if row else None

    async def save_candidate(
        self,
        source_id: UUID,
        user_id: UUID,
        candidate: CandidateProfile,
        extractor_version: str,
    ) -> SourceDocument:
        row = await self._session.scalar(
            select(SourceDocumentRow).where(
                SourceDocumentRow.id == source_id,
                SourceDocumentRow.user_id == user_id,
            )
        )
        if row is None:
            raise LookupError("Source document was not found for this user.")
        row.candidate_profile = candidate.model_dump()
        row.extractor_version = extractor_version
        row.parse_status = "extracted"
        await self._session.commit()
        await self._session.refresh(row)
        return SourceDocument.model_validate(row)

    async def save_confirmed(
        self,
        user_id: UUID,
        source_id: UUID,
        candidate: CandidateProfile,
        confirmed_at: datetime,
    ) -> ConfirmedProfile:
        values = candidate.model_dump(exclude={"potential_story_candidates"})
        statement = insert(ProfileRow).values(
            user_id=user_id,
            source_document_id=source_id,
            confirmed_at=confirmed_at,
            updated_at=confirmed_at,
            **values,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[ProfileRow.user_id],
            set_={
                "source_document_id": source_id,
                "confirmed_at": confirmed_at,
                "updated_at": confirmed_at,
                **values,
            },
        )
        await self._session.execute(statement)
        await self._session.commit()
        profile = await self.get_confirmed(user_id)
        if profile is None:
            raise RuntimeError("Confirmed profile could not be loaded.")
        return profile

    async def get_confirmed(self, user_id: UUID) -> ConfirmedProfile | None:
        row = await self._session.scalar(select(ProfileRow).where(ProfileRow.user_id == user_id))
        return ConfirmedProfile.model_validate(row) if row else None


class InMemoryProfileRepository:
    def __init__(self) -> None:
        self.sources: dict[UUID, SourceDocument] = {}
        self.profiles: dict[UUID, ConfirmedProfile] = {}

    async def create_source(self, source: SourceDocument) -> SourceDocument:
        self.sources[source.id] = source
        return source

    async def get_source(self, source_id: UUID, user_id: UUID) -> SourceDocument | None:
        source = self.sources.get(source_id)
        return source if source and source.user_id == user_id else None

    async def save_candidate(
        self,
        source_id: UUID,
        user_id: UUID,
        candidate: CandidateProfile,
        extractor_version: str,
    ) -> SourceDocument:
        source = await self.get_source(source_id, user_id)
        if source is None:
            raise LookupError("Source document was not found for this user.")
        updated = source.model_copy(
            update={
                "candidate_profile": candidate.model_dump(),
                "extractor_version": extractor_version,
                "parse_status": "extracted",
            }
        )
        self.sources[source_id] = updated
        return updated

    async def save_confirmed(
        self,
        user_id: UUID,
        source_id: UUID,
        candidate: CandidateProfile,
        confirmed_at: datetime,
    ) -> ConfirmedProfile:
        profile = ConfirmedProfile(
            user_id=user_id,
            source_document_id=source_id,
            confirmed_at=confirmed_at,
            updated_at=confirmed_at,
            **candidate.model_dump(exclude={"potential_story_candidates"}),
        )
        self.profiles[user_id] = profile
        return profile

    async def get_confirmed(self, user_id: UUID) -> ConfirmedProfile | None:
        return self.profiles.get(user_id)


def new_source_document(
    *,
    source_id: UUID,
    user_id: UUID,
    source_type: str,
    filename: str | None,
    raw_text: str,
) -> SourceDocument:
    return SourceDocument(
        id=source_id,
        user_id=user_id,
        source_type=source_type,
        filename=filename,
        raw_text=raw_text,
        created_at=datetime.now(UTC),
    )
