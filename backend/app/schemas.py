from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedUser(BaseModel):
    id: UUID
    email: str | None = None


class UserState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interface_language: Literal["en", "zh-CN"] = "en"
    support_language: Literal["en", "zh-CN"] = "en"
    default_session_length: Literal[10, 20, 30, 60] = 20
    coaching_style: Literal["supportive", "professional", "strict"] = "supportive"
    timezone: str = "UTC"
    target_role: str | None = None
    primary_goal: Literal["english_interview"] = "english_interview"


class UserPreferencesUpdate(BaseModel):
    interface_language: Literal["en", "zh-CN"]
    support_language: Literal["en", "zh-CN"]
    default_session_length: Literal[10, 20, 30, 60]
    target_role: str = Field(min_length=1, max_length=160)


class CandidateProfile(BaseModel):
    target_role: str = Field(min_length=1, max_length=160)
    primary_goal: Literal["english_interview"] = "english_interview"
    education: list[str] = Field(default_factory=list)
    work_experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    career_transition: str | None = None
    technical_keywords: list[str] = Field(default_factory=list)
    potential_story_candidates: list[str] = Field(default_factory=list)


class SourceDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    source_type: Literal["resume_pdf", "background_text"]
    filename: str | None = None
    raw_text: str
    parse_status: Literal["ready", "extracted", "failed"] = "ready"
    candidate_profile: dict[str, object] | None = None
    extractor_version: str | None = None
    created_at: datetime


class TextProfileImport(BaseModel):
    target_role: str = Field(min_length=1, max_length=160)
    raw_text: str = Field(min_length=1, max_length=100_000)


class CandidateExtractionResponse(BaseModel):
    source_id: UUID
    extractor_version: str
    candidate: CandidateProfile


class ProfileConfirmationRequest(BaseModel):
    source_id: UUID
    candidate: CandidateProfile


class ConfirmedProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    source_document_id: UUID
    target_role: str
    primary_goal: Literal["english_interview"] = "english_interview"
    education: list[str] = Field(default_factory=list)
    work_experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    career_transition: str | None = None
    technical_keywords: list[str] = Field(default_factory=list)
    confirmed_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["fluentloop-api"] = "fluentloop-api"
    version: str
