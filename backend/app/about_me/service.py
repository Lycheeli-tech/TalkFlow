from uuid import UUID, uuid4

from app.about_me.entities import AboutMeSnapshot, MemorySourceType, ResumeDocument, TargetRole
from app.about_me.memory_ai import MemoryDecisionProposer
from app.about_me.repository import AboutMeRepository
from app.services.documents import PdfResumeParser
from app.storage.documents import DocumentStorage


class AboutMeService:
    def __init__(
        self,
        *,
        repository: AboutMeRepository,
        storage: DocumentStorage,
        parser: PdfResumeParser,
        memory: MemoryDecisionProposer,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._parser = parser
        self._memory = memory

    async def get(self, user_id: UUID) -> AboutMeSnapshot:
        return await self._repository.snapshot(user_id)

    async def update_facts(self, user_id: UUID, facts: list[str]) -> AboutMeSnapshot:
        cleaned = _clean_list(facts, max_items=50, max_length=1000)
        await self._repository.update_facts(user_id, cleaned)
        for fact in cleaned:
            await self._propose(
                user_id=user_id,
                source_type="USER_INPUT",
                source_id=user_id,
                content=fact,
                field_path="supplemental_facts",
            )
        return await self._repository.snapshot(user_id)

    async def add_target_role(self, user_id: UUID, role_name: str) -> TargetRole:
        role_name = " ".join(role_name.split())
        if not role_name or len(role_name) > 160:
            raise ValueError("Target role must be between 1 and 160 characters.")
        role = await self._repository.add_target_role(user_id, role_name)
        await self._propose(
            user_id=user_id,
            source_type="PROFILE",
            source_id=role.id,
            content=role.role_name,
            field_path="target_roles",
        )
        return role

    async def delete_target_role(self, user_id: UUID, role_id: UUID) -> None:
        await self._repository.delete_target_role(user_id, role_id)

    async def add_resume(
        self,
        *,
        user_id: UUID,
        filename: str | None,
        content_type: str | None,
        content: bytes,
    ) -> ResumeDocument:
        safe_filename = filename or "resume.pdf"
        raw_text = self._parser.parse(
            content=content, content_type=content_type, filename=safe_filename
        )
        document_id = uuid4()
        path = await self._storage.store_resume(
            user_id=user_id,
            document_id=document_id,
            filename=safe_filename,
            content=content,
        )
        try:
            document = await self._repository.add_resume(
                user_id=user_id,
                document_id=document_id,
                filename=safe_filename,
                storage_path=path,
                raw_text=raw_text,
            )
        except Exception:
            await self._storage.delete(path=path)
            raise
        await self._propose(
            user_id=user_id,
            source_type="SOURCE_DOCUMENT",
            source_id=document.id,
            content=document.raw_text,
            field_path=None,
        )
        return document

    async def delete_resume(self, user_id: UUID, document_id: UUID) -> None:
        pending = await self._repository.delete_resume(user_id, document_id)
        if pending:
            try:
                await self._storage.delete(path=pending.storage_path)
            except Exception:
                await self._repository.mark_document_cleanup_failed(user_id, document_id)
            else:
                await self._repository.mark_document_cleanup_complete(user_id, document_id)

    async def delete_memory(self, user_id: UUID, memory_id: UUID) -> None:
        await self._repository.delete_memory(user_id, memory_id)

    async def capture_course_answer(
        self, *, user_id: UUID, answer_id: UUID, transcript: str
    ) -> None:
        await self._propose(
            user_id=user_id,
            source_type="COURSE_ANSWER",
            source_id=answer_id,
            content=transcript,
            field_path="transcript",
        )

    async def _propose(
        self,
        *,
        user_id: UUID,
        source_type: MemorySourceType,
        source_id: UUID,
        content: str,
        field_path: str | None,
    ) -> None:
        snapshot = await self._repository.snapshot(user_id)
        try:
            decision = await self._memory.propose(
                source_type=source_type,
                source_id=source_id,
                source_content=content,
                source_field_path=field_path,
                existing_memories=snapshot.memories,
            )
            for citation in decision.source_citations:
                if (
                    citation.source_type != source_type
                    or citation.source_id != source_id
                    or citation.source_field_path != field_path
                    or citation.source_excerpt.casefold() not in content.casefold()
                ):
                    raise ValueError("AI Memory cited a source outside the supplied candidate.")
            await self._repository.apply_memory_decision(user_id, decision)
        except Exception:
            # Source persistence is authoritative and never rolled back by optional AI extraction.
            return


def _clean_list(values: list[str], *, max_items: int, max_length: int) -> list[str]:
    cleaned = list(dict.fromkeys(" ".join(value.split()) for value in values if value.strip()))
    if len(cleaned) > max_items or any(len(value) > max_length for value in cleaned):
        raise ValueError("Supplemental facts exceed the supported size.")
    return cleaned
