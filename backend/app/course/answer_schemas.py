from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.course.entities import (
    AnswerLanguage,
    AnswerStatus,
    AudioRetentionStatus,
    CourseAnswerAggregate,
    FeedbackStatus,
)


class CourseTranscriptView(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_language: AnswerLanguage
    transcript: str
    organized_english: str | None
    stt_provider: str
    stt_model: str | None
    created_at: datetime


class CourseFeedbackView(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: FeedbackStatus
    summary: str | None
    priority_changes: list[dict[str, object]] | None


class CourseAnswerView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    catalog_version: str
    course_id: str
    question_id: str
    answer_language: AnswerLanguage
    status: AnswerStatus
    response_duration_ms: int | None
    audio_available: bool
    audio_retention_status: AudioRetentionStatus
    provider_error_code: str | None
    failure_expires_at: datetime | None
    created_at: datetime
    saved_at: datetime | None
    transcript: CourseTranscriptView | None
    feedback: CourseFeedbackView | None

    @classmethod
    def from_aggregate(cls, aggregate: CourseAnswerAggregate) -> "CourseAnswerView":
        answer = aggregate.answer
        return cls(
            id=answer.id,
            catalog_version=answer.catalog_version,
            course_id=answer.course_id,
            question_id=answer.question_id,
            answer_language=answer.answer_language,
            status=answer.status,
            response_duration_ms=answer.response_duration_ms,
            audio_available=answer.audio_path is not None,
            audio_retention_status=answer.audio_retention_status,
            provider_error_code=answer.provider_error_code,
            failure_expires_at=answer.failure_expires_at,
            created_at=answer.created_at,
            saved_at=answer.saved_at,
            transcript=(
                CourseTranscriptView(
                    source_language=aggregate.transcript.source_language,
                    transcript=aggregate.transcript.transcript,
                    organized_english=aggregate.transcript.organized_english,
                    stt_provider=aggregate.transcript.stt_provider,
                    stt_model=aggregate.transcript.stt_model,
                    created_at=aggregate.transcript.created_at,
                )
                if aggregate.transcript
                else None
            ),
            feedback=(
                CourseFeedbackView(
                    status=aggregate.feedback.status,
                    summary=aggregate.feedback.summary,
                    priority_changes=aggregate.feedback.priority_changes,
                )
                if aggregate.feedback
                else None
            ),
        )


class CourseHistoryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    course_id: str
    question_id: str
    count: int
    answers: tuple[CourseAnswerView, ...]
