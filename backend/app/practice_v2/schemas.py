from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Attempt(BaseModel):
    id: UUID
    question_id: str
    idempotency_key: str
    status: Literal["PROCESSING", "FAILED", "SAVED"] = "PROCESSING"
    audio_path: str
    audio_stored: bool = False
    content_type: str
    duration_ms: int
    transcript: str | None = None
    stt_provider: str | None = None
    stt_model: str | None = None
    error_code: str | None = None
    retries: int = 0
    updated_at: datetime


class Run(BaseModel):
    id: UUID
    user_id: UUID
    idempotency_key: str
    question_ids: list[str]
    current_position: int = 0
    status: Literal["ACTIVE", "PAUSED", "GENERATING"] = "ACTIVE"
    answers: list[Attempt] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    revision: int = 0
    feedback_retries: int = 0
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

    def latest(self, question_id: str) -> Attempt | None:
        return next(
            (answer for answer in reversed(self.answers) if answer.question_id == question_id), None
        )


class CreateRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_count: Literal[3, 5]
    idempotency_key: str = Field(min_length=8, max_length=128)


class PositionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    position: int = Field(ge=0, le=4)
    paused: bool = False
    skip_current: bool = False


class FeedbackEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str
    quote: str = Field(min_length=1, max_length=1500)
    observation: str = Field(min_length=1, max_length=1500)


class GeneratedFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=1, max_length=2000)
    strengths: list[FeedbackEvidence] = Field(min_length=1, max_length=3)
    improvements: list[FeedbackEvidence] = Field(min_length=1, max_length=3)
    score: int = Field(ge=0, le=100)


class Feedback(GeneratedFeedback):
    prompt_version: str
    provider_name: str
    model_name: str | None
