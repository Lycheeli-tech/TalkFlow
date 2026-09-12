from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

AnswerLanguage = Literal["ENGLISH", "CHINESE"]
AnswerStatus = Literal["PROCESSING", "SAVED", "PROCESSING_FAILED", "DISCARDED"]
AudioRetentionStatus = Literal["RETAINED", "PENDING_CLEANUP", "EXPIRED", "CLEANUP_FAILED"]
FeedbackStatus = Literal["NOT_REQUESTED", "PENDING", "READY", "FAILED"]


class CourseAnswer(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    user_id: UUID
    catalog_version: str
    course_id: str
    question_id: str
    answer_language: AnswerLanguage
    status: AnswerStatus
    idempotency_key: str
    response_duration_ms: int | None = None
    audio_path: str | None = None
    audio_content_type: str | None = None
    audio_retention_status: AudioRetentionStatus = "RETAINED"
    audio_cleanup_pending: bool = False
    provider_error_code: str | None = None
    failure_expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    saved_at: datetime | None = None
    saved_sequence: int | None = None
    confirmed_at: datetime | None = None


class CourseTranscript(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    answer_id: UUID
    user_id: UUID
    source_language: AnswerLanguage
    transcript: str
    organized_english: str | None = None
    stt_provider: str
    stt_model: str | None = None
    organizer_prompt_version: str | None = None
    created_at: datetime
    updated_at: datetime


class CourseFeedback(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    answer_id: UUID
    user_id: UUID
    status: FeedbackStatus
    summary: str | None = None
    priority_changes: list[dict[str, object]] | None = None
    prompt_version: str
    provider_name: str | None = None
    model_name: str | None = None
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime


class CourseAnswerAggregate(BaseModel):
    model_config = ConfigDict(frozen=True)

    answer: CourseAnswer
    transcript: CourseTranscript | None = None
    feedback: CourseFeedback | None = None


class PendingAudioCleanup(BaseModel):
    model_config = ConfigDict(frozen=True)

    answer_id: UUID
    user_id: UUID
    audio_path: str
