from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.about_me.entities import (
    AboutMeSnapshot,
    MemoryItem,
    MemorySource,
    ResumeDocument,
    TargetRole,
)


class TargetRoleView(BaseModel):
    id: UUID
    role_name: str
    created_at: datetime

    @classmethod
    def from_role(cls, role: TargetRole) -> "TargetRoleView":
        return cls(id=role.id, role_name=role.role_name, created_at=role.created_at)


class MemorySourceView(BaseModel):
    id: UUID
    source_type: str
    source_excerpt: str
    source_field_path: str | None

    @classmethod
    def from_source(cls, source: MemorySource) -> "MemorySourceView":
        return cls(
            id=source.id,
            source_type=source.source_type,
            source_excerpt=source.source_excerpt,
            source_field_path=source.source_field_path,
        )


class MemoryView(BaseModel):
    id: UUID
    content: str
    updated_at: datetime
    sources: list[MemorySourceView]

    @classmethod
    def from_memory(cls, memory: MemoryItem) -> "MemoryView":
        return cls(
            id=memory.id,
            content=memory.content,
            updated_at=memory.updated_at,
            sources=[MemorySourceView.from_source(source) for source in memory.sources],
        )


class ResumeView(BaseModel):
    id: UUID
    filename: str
    parse_status: str
    created_at: datetime

    @classmethod
    def from_document(cls, document: ResumeDocument) -> "ResumeView":
        return cls(
            id=document.id,
            filename=document.filename,
            parse_status=document.parse_status,
            created_at=document.created_at,
        )


class AboutMeView(BaseModel):
    supplemental_facts: list[str]
    target_roles: list[TargetRoleView]
    resumes: list[ResumeView]
    memories: list[MemoryView]

    @classmethod
    def from_snapshot(cls, snapshot: AboutMeSnapshot) -> "AboutMeView":
        return cls(
            supplemental_facts=snapshot.supplemental_facts,
            target_roles=[TargetRoleView.from_role(item) for item in snapshot.target_roles],
            resumes=[ResumeView.from_document(item) for item in snapshot.resumes],
            memories=[MemoryView.from_memory(item) for item in snapshot.memories],
        )


class AboutMePatch(BaseModel):
    supplemental_facts: list[str] = Field(max_length=50)


class TargetRoleCreate(BaseModel):
    role_name: str = Field(min_length=1, max_length=160)


class DeleteResult(BaseModel):
    deleted_id: UUID
