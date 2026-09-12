from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CourseAnswerRow(Base):
    __tablename__ = "course_answers"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_course_answer_idempotency"),
        UniqueConstraint("id", "user_id", name="uq_course_answer_owner"),
        {"schema": "public"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column()
    catalog_version: Mapped[str] = mapped_column(String(64))
    course_id: Mapped[str] = mapped_column(String(32))
    question_id: Mapped[str] = mapped_column(String(64))
    answer_language: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(24))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    response_duration_ms: Mapped[int | None] = mapped_column(Integer)
    audio_path: Mapped[str | None] = mapped_column(String(512))
    audio_content_type: Mapped[str | None] = mapped_column(String(96))
    audio_retention_status: Mapped[str] = mapped_column(String(24))
    audio_cleanup_pending: Mapped[bool] = mapped_column(Boolean)
    provider_error_code: Mapped[str | None] = mapped_column(String(96))
    failure_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    saved_sequence: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CourseTranscriptRow(Base):
    __tablename__ = "course_transcripts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["answer_id", "user_id"],
            ["public.course_answers.id", "public.course_answers.user_id"],
            name="course_transcripts_answer_owner_fk",
            ondelete="CASCADE",
        ),
        {"schema": "public"},
    )

    answer_id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column()
    source_language: Mapped[str] = mapped_column(String(16))
    transcript: Mapped[str] = mapped_column(Text)
    organized_english: Mapped[str | None] = mapped_column(Text)
    stt_provider: Mapped[str] = mapped_column(String(64))
    stt_model: Mapped[str | None] = mapped_column(String(64))
    organizer_prompt_version: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CourseFeedbackRow(Base):
    __tablename__ = "course_feedback"
    __table_args__ = (
        ForeignKeyConstraint(
            ["answer_id", "user_id"],
            ["public.course_answers.id", "public.course_answers.user_id"],
            name="course_feedback_answer_owner_fk",
            ondelete="CASCADE",
        ),
        {"schema": "public"},
    )

    answer_id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column()
    status: Mapped[str] = mapped_column(String(24))
    summary: Mapped[str | None] = mapped_column(Text)
    priority_changes: Mapped[list[dict[str, object]] | None] = mapped_column(JSONB)
    prompt_version: Mapped[str] = mapped_column(String(64))
    provider_name: Mapped[str | None] = mapped_column(String(64))
    model_name: Mapped[str | None] = mapped_column(String(64))
    error_code: Mapped[str | None] = mapped_column(String(96))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
