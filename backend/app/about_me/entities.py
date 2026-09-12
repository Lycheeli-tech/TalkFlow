from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MemoryAction = Literal["CREATE", "UPDATE", "MERGE", "IGNORE"]
MemorySourceType = Literal["PROFILE", "SOURCE_DOCUMENT", "USER_INPUT", "COURSE_ANSWER"]


class TargetRole(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    user_id: UUID
    role_name: str
    created_at: datetime


class ResumeDocument(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    user_id: UUID
    filename: str
    raw_text: str
    parse_status: str
    created_at: datetime


class MemorySource(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    memory_id: UUID
    user_id: UUID
    source_type: MemorySourceType
    source_id: UUID
    source_excerpt: str
    source_field_path: str | None = None
    created_at: datetime


class MemoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    user_id: UUID
    content: str
    normalized_content: str
    extractor_prompt_version: str
    created_at: datetime
    updated_at: datetime
    sources: list[MemorySource] = Field(default_factory=list)


class MemoryCitation(BaseModel):
    source_type: MemorySourceType
    source_id: UUID
    source_excerpt: str = Field(min_length=1, max_length=2000)
    source_field_path: str | None = None

    @field_validator("source_excerpt")
    @classmethod
    def trim_excerpt(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A Memory citation excerpt cannot be empty.")
        return value


class MemoryDecision(BaseModel):
    action: MemoryAction
    candidate_content: str | None = Field(max_length=4000)
    target_memory_ids: list[UUID] = Field(max_length=20)
    source_citations: list[MemoryCitation] = Field(max_length=20)


class AboutMeSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    supplemental_facts: list[str]
    target_roles: list[TargetRole]
    resumes: list[ResumeDocument]
    memories: list[MemoryItem]


class PendingDocumentCleanup(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_id: UUID
    user_id: UUID
    storage_path: str
