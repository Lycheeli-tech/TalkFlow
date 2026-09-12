from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.about_me.entities import (
    AboutMeSnapshot,
    MemoryCitation,
    MemoryDecision,
    MemoryItem,
    MemorySource,
    PendingDocumentCleanup,
    ResumeDocument,
    TargetRole,
)
from app.about_me.models import AboutMeProfileRow, MemoryItemRow, MemorySourceRow, TargetRoleRow

MEMORY_PROMPT_VERSION = "memory_decision_v1"


class AboutMeRepository(Protocol):
    async def snapshot(self, user_id: UUID) -> AboutMeSnapshot: ...
    async def update_facts(self, user_id: UUID, facts: list[str]) -> AboutMeSnapshot: ...
    async def add_target_role(self, user_id: UUID, role_name: str) -> TargetRole: ...
    async def delete_target_role(self, user_id: UUID, role_id: UUID) -> None: ...
    async def add_resume(
        self, *, user_id: UUID, document_id: UUID, filename: str, storage_path: str, raw_text: str
    ) -> ResumeDocument: ...
    async def delete_resume(
        self, user_id: UUID, document_id: UUID
    ) -> PendingDocumentCleanup | None: ...
    async def list_document_cleanup_jobs(self, limit: int) -> list[PendingDocumentCleanup]: ...
    async def mark_document_cleanup_complete(self, user_id: UUID, document_id: UUID) -> None: ...
    async def mark_document_cleanup_failed(self, user_id: UUID, document_id: UUID) -> None: ...
    async def delete_memory(self, user_id: UUID, memory_id: UUID) -> None: ...
    async def apply_memory_decision(
        self, user_id: UUID, decision: MemoryDecision
    ) -> MemoryItem | None: ...


class SQLAboutMeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def snapshot(self, user_id: UUID) -> AboutMeSnapshot:
        profile = await self._session.get(AboutMeProfileRow, user_id)
        roles = (
            await self._session.scalars(
                select(TargetRoleRow)
                .where(TargetRoleRow.user_id == user_id)
                .order_by(TargetRoleRow.created_at, TargetRoleRow.id)
            )
        ).all()
        resume_rows = (
            (
                await self._session.execute(
                    text(
                        "select id, user_id, filename, raw_text, parse_status, created_at "
                        "from public.source_documents "
                        "where user_id = :user_id and source_type = 'resume_pdf' "
                        "order by created_at desc, id"
                    ),
                    {"user_id": user_id},
                )
            )
            .mappings()
            .all()
        )
        return AboutMeSnapshot(
            supplemental_facts=list(profile.supplemental_facts) if profile else [],
            target_roles=[TargetRole.model_validate(row) for row in roles],
            resumes=[ResumeDocument.model_validate(dict(row)) for row in resume_rows],
            memories=await self._list_memories(user_id),
        )

    async def update_facts(self, user_id: UUID, facts: list[str]) -> AboutMeSnapshot:
        now = datetime.now(UTC)
        profile = await self._session.get(AboutMeProfileRow, user_id)
        previous = list(profile.supplemental_facts) if profile else []
        if profile is None:
            self._session.add(
                AboutMeProfileRow(
                    user_id=user_id, supplemental_facts=facts, created_at=now, updated_at=now
                )
            )
        else:
            profile.supplemental_facts = facts
            profile.updated_at = now
        for removed in set(previous) - set(facts):
            await self._session.execute(
                delete(MemorySourceRow).where(
                    MemorySourceRow.user_id == user_id,
                    MemorySourceRow.source_type == "USER_INPUT",
                    MemorySourceRow.source_id == user_id,
                    MemorySourceRow.source_excerpt == removed,
                )
            )
        await self._delete_orphan_memories(user_id)
        await self._session.commit()
        return await self.snapshot(user_id)

    async def add_target_role(self, user_id: UUID, role_name: str) -> TargetRole:
        row = TargetRoleRow(
            id=uuid4(), user_id=user_id, role_name=role_name, created_at=datetime.now(UTC)
        )
        self._session.add(row)
        try:
            await self._session.commit()
        except IntegrityError as error:
            await self._session.rollback()
            raise ValueError("That target role already exists.") from error
        await self._session.refresh(row)
        return TargetRole.model_validate(row)

    async def delete_target_role(self, user_id: UUID, role_id: UUID) -> None:
        row = await self._session.scalar(
            select(TargetRoleRow).where(
                TargetRoleRow.id == role_id, TargetRoleRow.user_id == user_id
            )
        )
        if row is None:
            raise LookupError("About Me item was not found.")
        await self._remove_source_links(user_id, "PROFILE", role_id)
        await self._session.delete(row)
        await self._delete_orphan_memories(user_id)
        await self._session.commit()

    async def add_resume(
        self, *, user_id: UUID, document_id: UUID, filename: str, storage_path: str, raw_text: str
    ) -> ResumeDocument:
        now = datetime.now(UTC)
        await self._session.execute(
            text(
                "insert into public.source_documents "
                "(id, user_id, source_type, filename, storage_path, raw_text, "
                "parse_status, created_at) values (:id, :user_id, 'resume_pdf', "
                ":filename, :storage_path, :raw_text, 'ready', :created_at)"
            ),
            {
                "id": document_id,
                "user_id": user_id,
                "filename": filename,
                "storage_path": storage_path,
                "raw_text": raw_text,
                "created_at": now,
            },
        )
        await self._session.commit()
        return ResumeDocument(
            id=document_id,
            user_id=user_id,
            filename=filename,
            raw_text=raw_text,
            parse_status="ready",
            created_at=now,
        )

    async def delete_resume(
        self, user_id: UUID, document_id: UUID
    ) -> PendingDocumentCleanup | None:
        row = (
            (
                await self._session.execute(
                    text(
                        "select storage_path from public.source_documents "
                        "where id = :id and user_id = :user_id "
                        "and source_type = 'resume_pdf' for update"
                    ),
                    {"id": document_id, "user_id": user_id},
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            raise LookupError("About Me item was not found.")
        pending = None
        if row["storage_path"]:
            pending = PendingDocumentCleanup(
                document_id=document_id,
                user_id=user_id,
                storage_path=row["storage_path"],
            )
            await self._session.execute(
                text(
                    "insert into public.document_cleanup_jobs "
                    "(document_id, user_id, storage_path) values (:id, :user_id, :path) "
                    "on conflict (document_id) do update set storage_path = excluded.storage_path"
                ),
                {"id": document_id, "user_id": user_id, "path": row["storage_path"]},
            )
        await self._remove_source_links(user_id, "SOURCE_DOCUMENT", document_id)
        await self._session.execute(
            text("delete from public.source_documents where id = :id and user_id = :user_id"),
            {"id": document_id, "user_id": user_id},
        )
        await self._delete_orphan_memories(user_id)
        await self._session.commit()
        return pending

    async def list_document_cleanup_jobs(self, limit: int) -> list[PendingDocumentCleanup]:
        rows = (
            (
                await self._session.execute(
                    text(
                        "select document_id, user_id, storage_path "
                        "from public.document_cleanup_jobs order by created_at limit :limit"
                    ),
                    {"limit": limit},
                )
            )
            .mappings()
            .all()
        )
        return [PendingDocumentCleanup(**dict(row)) for row in rows]

    async def mark_document_cleanup_complete(self, user_id: UUID, document_id: UUID) -> None:
        await self._session.execute(
            text(
                "delete from public.document_cleanup_jobs "
                "where document_id = :id and user_id = :user_id"
            ),
            {"id": document_id, "user_id": user_id},
        )
        await self._session.commit()

    async def mark_document_cleanup_failed(self, user_id: UUID, document_id: UUID) -> None:
        await self._session.execute(
            text(
                "update public.document_cleanup_jobs set attempts = attempts + 1, "
                "last_error_at = now() where document_id = :id and user_id = :user_id"
            ),
            {"id": document_id, "user_id": user_id},
        )
        await self._session.commit()

    async def delete_memory(self, user_id: UUID, memory_id: UUID) -> None:
        result = await self._session.execute(
            delete(MemoryItemRow).where(
                MemoryItemRow.id == memory_id, MemoryItemRow.user_id == user_id
            )
        )
        if result.rowcount == 0:
            await self._session.rollback()
            raise LookupError("About Me item was not found.")
        await self._session.commit()

    async def apply_memory_decision(
        self, user_id: UUID, decision: MemoryDecision
    ) -> MemoryItem | None:
        if decision.action == "IGNORE":
            return None
        content = (decision.candidate_content or "").strip()
        if not content or not decision.source_citations:
            raise ValueError("A persisted Memory requires content and at least one valid source.")
        targets = list(dict.fromkeys(decision.target_memory_ids))
        if decision.action == "CREATE" and targets:
            raise ValueError("CREATE cannot name an existing Memory target.")
        if decision.action == "UPDATE" and len(targets) != 1:
            raise ValueError("UPDATE requires exactly one Memory target.")
        if decision.action == "MERGE" and len(targets) < 2:
            raise ValueError("MERGE requires at least two Memory targets.")

        try:
            target_rows = (
                await self._session.scalars(
                    select(MemoryItemRow)
                    .where(MemoryItemRow.id.in_(targets), MemoryItemRow.user_id == user_id)
                    .with_for_update()
                )
            ).all()
            if len(target_rows) != len(targets):
                raise ValueError("A Memory target is missing or belongs to another user.")
            for citation in decision.source_citations:
                await self._validate_citation(user_id, citation)

            now = datetime.now(UTC)
            if decision.action == "CREATE":
                row = MemoryItemRow(
                    id=uuid4(),
                    user_id=user_id,
                    content=content,
                    normalized_content=_normalize(content),
                    extractor_prompt_version=MEMORY_PROMPT_VERSION,
                    created_at=now,
                    updated_at=now,
                )
                self._session.add(row)
                await self._session.flush()
            else:
                by_id = {row.id: row for row in target_rows}
                row = by_id[targets[0]]
                row.content = content
                row.normalized_content = _normalize(content)
                row.extractor_prompt_version = MEMORY_PROMPT_VERSION
                row.updated_at = now
                if decision.action == "MERGE":
                    for redundant_id in targets[1:]:
                        sources = (
                            await self._session.scalars(
                                select(MemorySourceRow).where(
                                    MemorySourceRow.memory_id == redundant_id,
                                    MemorySourceRow.user_id == user_id,
                                )
                            )
                        ).all()
                        for source in sources:
                            duplicate = await self._session.scalar(
                                select(MemorySourceRow.id).where(
                                    MemorySourceRow.memory_id == row.id,
                                    MemorySourceRow.source_type == source.source_type,
                                    MemorySourceRow.source_id == source.source_id,
                                    MemorySourceRow.source_excerpt == source.source_excerpt,
                                    MemorySourceRow.source_field_path == source.source_field_path,
                                )
                            )
                            if duplicate:
                                await self._session.delete(source)
                            else:
                                source.memory_id = row.id
                        await self._session.execute(
                            delete(MemoryItemRow).where(
                                MemoryItemRow.id == redundant_id,
                                MemoryItemRow.user_id == user_id,
                            )
                        )
            for citation in decision.source_citations:
                existing_source = await self._session.scalar(
                    select(MemorySourceRow.id).where(
                        MemorySourceRow.memory_id == row.id,
                        MemorySourceRow.source_type == citation.source_type,
                        MemorySourceRow.source_id == citation.source_id,
                        MemorySourceRow.source_excerpt == citation.source_excerpt,
                        MemorySourceRow.source_field_path == citation.source_field_path,
                    )
                )
                if not existing_source:
                    self._session.add(
                        MemorySourceRow(
                            id=uuid4(),
                            memory_id=row.id,
                            user_id=user_id,
                            source_type=citation.source_type,
                            source_id=citation.source_id,
                            source_excerpt=citation.source_excerpt,
                            source_field_path=citation.source_field_path,
                            created_at=now,
                        )
                    )
            await self._session.commit()
            return await self._get_memory(user_id, row.id)
        except Exception:
            await self._session.rollback()
            raise

    async def _validate_citation(self, user_id: UUID, citation: MemoryCitation) -> None:
        excerpt = citation.source_excerpt.strip()
        if citation.source_type == "SOURCE_DOCUMENT":
            source_text = await self._session.scalar(
                text(
                    "select raw_text from public.source_documents "
                    "where id = :id and user_id = :user_id"
                ),
                {"id": citation.source_id, "user_id": user_id},
            )
        elif citation.source_type == "COURSE_ANSWER":
            if citation.source_field_path not in {None, "transcript"}:
                raise ValueError("A Memory citation field path is invalid.")
            source_text = await self._session.scalar(
                text(
                    "select t.transcript from public.course_transcripts t "
                    "join public.course_answers a on a.id = t.answer_id and a.user_id = t.user_id "
                    "where a.id = :id and a.user_id = :user_id and a.status = 'SAVED'"
                ),
                {"id": citation.source_id, "user_id": user_id},
            )
        elif citation.source_type == "PROFILE":
            if citation.source_field_path != "target_roles":
                raise ValueError("A Memory citation field path is invalid.")
            source_text = await self._session.scalar(
                select(TargetRoleRow.role_name).where(
                    TargetRoleRow.id == citation.source_id, TargetRoleRow.user_id == user_id
                )
            )
        else:
            if citation.source_id != user_id or citation.source_field_path != "supplemental_facts":
                source_text = None
            else:
                profile = await self._session.get(AboutMeProfileRow, user_id)
                source_text = "\n".join(profile.supplemental_facts) if profile else None
        if not source_text or excerpt.casefold() not in source_text.casefold():
            raise ValueError("A Memory citation does not match an owned source.")

    async def _list_memories(self, user_id: UUID) -> list[MemoryItem]:
        rows = (
            await self._session.scalars(
                select(MemoryItemRow)
                .where(MemoryItemRow.user_id == user_id)
                .order_by(MemoryItemRow.updated_at.desc(), MemoryItemRow.id)
            )
        ).all()
        return [await self._memory_from_row(row) for row in rows]

    async def _get_memory(self, user_id: UUID, memory_id: UUID) -> MemoryItem:
        row = await self._session.scalar(
            select(MemoryItemRow).where(
                MemoryItemRow.id == memory_id, MemoryItemRow.user_id == user_id
            )
        )
        if row is None:
            raise LookupError("About Me item was not found.")
        return await self._memory_from_row(row)

    async def _memory_from_row(self, row: MemoryItemRow) -> MemoryItem:
        sources = (
            await self._session.scalars(
                select(MemorySourceRow)
                .where(MemorySourceRow.memory_id == row.id, MemorySourceRow.user_id == row.user_id)
                .order_by(MemorySourceRow.created_at, MemorySourceRow.id)
            )
        ).all()
        return MemoryItem(
            **MemoryItem.model_validate(row).model_dump(exclude={"sources"}),
            sources=[MemorySource.model_validate(source) for source in sources],
        )

    async def _remove_source_links(self, user_id: UUID, source_type: str, source_id: UUID) -> None:
        await self._session.execute(
            delete(MemorySourceRow).where(
                MemorySourceRow.user_id == user_id,
                MemorySourceRow.source_type == source_type,
                MemorySourceRow.source_id == source_id,
            )
        )

    async def _delete_orphan_memories(self, user_id: UUID) -> None:
        await self._session.execute(
            text(
                "delete from public.memory_items m where m.user_id = :user_id "
                "and not exists (select 1 from public.memory_sources s where s.memory_id = m.id)"
            ),
            {"user_id": user_id},
        )


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())
