from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRow(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    interface_language: Mapped[str] = mapped_column(String(8), default="en")
    support_language: Mapped[str] = mapped_column(String(8), default="en")
    default_session_length: Mapped[int] = mapped_column(SmallInteger, default=20)
    coaching_style: Mapped[str] = mapped_column(String(16), default="supportive")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    target_role: Mapped[str | None] = mapped_column(String(160))
    primary_goal: Mapped[str] = mapped_column(String(32), default="english_interview")
    current_day: Mapped[int] = mapped_column(SmallInteger, default=1)
    current_phase: Mapped[str] = mapped_column(String(16), default="BUILD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SourceDocumentRow(Base):
    __tablename__ = "source_documents"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(32))
    filename: Mapped[str | None] = mapped_column(String(255))
    storage_path: Mapped[str | None] = mapped_column(String(512))
    raw_text: Mapped[str] = mapped_column(Text)
    parse_status: Mapped[str] = mapped_column(String(16), default="ready")
    candidate_profile: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    extractor_version: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProfileRow(Base):
    __tablename__ = "profiles"
    __table_args__ = {"schema": "public"}

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), primary_key=True
    )
    source_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.source_documents.id", ondelete="RESTRICT")
    )
    target_role: Mapped[str] = mapped_column(String(160))
    primary_goal: Mapped[str] = mapped_column(String(32), default="english_interview")
    education: Mapped[list[str]] = mapped_column(JSONB, default=list)
    work_experience: Mapped[list[str]] = mapped_column(JSONB, default=list)
    projects: Mapped[list[str]] = mapped_column(JSONB, default=list)
    skills: Mapped[list[str]] = mapped_column(JSONB, default=list)
    industries: Mapped[list[str]] = mapped_column(JSONB, default=list)
    career_transition: Mapped[str | None] = mapped_column(Text)
    technical_keywords: Mapped[list[str]] = mapped_column(JSONB, default=list)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SessionRow(Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), index=True
    )
    session_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(24), default="IN_PROGRESS")
    questions: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)
    day: Mapped[int | None] = mapped_column(SmallInteger)
    phase: Mapped[str | None] = mapped_column(String(16))
    duration_plan: Mapped[int | None] = mapped_column(SmallInteger)
    topic_family: Mapped[str | None] = mapped_column(String(64))
    scaffolding_level: Mapped[str | None] = mapped_column(String(24))
    session_plan: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AttemptRow(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("session_id", "question_type", name="uq_attempt_session_question_type"),
        {"schema": "public"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.sessions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(24))
    audio_path: Mapped[str] = mapped_column(String(512))
    audio_content_type: Mapped[str] = mapped_column(String(96))
    response_duration_ms: Mapped[int | None] = mapped_column(Integer)
    transcript: Mapped[str | None] = mapped_column(Text)
    analysis: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(24), default="AUDIO_SAVED")
    provider_error: Mapped[str | None] = mapped_column(Text)
    stt_provider: Mapped[str | None] = mapped_column(String(64))
    analyzer_version: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LearnerAssessmentRow(Base):
    __tablename__ = "learner_assessments"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.sessions.id", ondelete="RESTRICT"), unique=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), index=True
    )
    fluency: Mapped[str] = mapped_column(String(24))
    naturalness: Mapped[str] = mapped_column(String(24))
    grammar: Mapped[str] = mapped_column(String(24))
    retrieval: Mapped[str] = mapped_column(String(24))
    structure: Mapped[str] = mapped_column(String(24))
    strengths: Mapped[list[str]] = mapped_column(JSONB, default=list)
    primary_focus: Mapped[str] = mapped_column(Text)
    secondary_focus: Mapped[str | None] = mapped_column(Text)
    observed_patterns: Mapped[list[str]] = mapped_column(JSONB, default=list)
    assessment_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExpressionRow(Base):
    __tablename__ = "expressions"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    meaning: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(24))
    source_id: Mapped[UUID | None]
    status: Mapped[str] = mapped_column(String(24), default="NEW")
    successful_recall: Mapped[int] = mapped_column(Integer, default=0)
    failed_recall: Mapped[int] = mapped_column(Integer, default=0)
    transfer_success: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ExpressionAttemptRow(Base):
    __tablename__ = "expression_attempts"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    expression_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.expressions.id", ondelete="CASCADE"), index=True
    )
    attempt_id: Mapped[UUID] = mapped_column(ForeignKey("public.attempts.id", ondelete="CASCADE"))
    session_id: Mapped[UUID] = mapped_column(ForeignKey("public.sessions.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), index=True
    )
    context: Mapped[str] = mapped_column(Text)
    retrieval_type: Mapped[str] = mapped_column(String(24))
    hint_used: Mapped[bool] = mapped_column(Boolean, default=False)
    independent_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    usage_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    result: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ErrorPatternRow(Base):
    __tablename__ = "error_patterns"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), index=True
    )
    pattern_type: Mapped[str] = mapped_column(String(64))
    original_example: Mapped[str] = mapped_column(Text)
    preferred_expression: Mapped[str | None] = mapped_column(Text)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    successful_correction_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(24), default="CANDIDATE")
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StoryRow(Base):
    __tablename__ = "stories"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(24))
    source_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("public.source_documents.id", ondelete="RESTRICT")
    )
    source_attempt_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("public.attempts.id", ondelete="RESTRICT")
    )
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RetrievalOpportunityRow(Base):
    __tablename__ = "retrieval_opportunities"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.users.id", ondelete="CASCADE"), index=True
    )
    expression_id: Mapped[UUID] = mapped_column(
        ForeignKey("public.expressions.id", ondelete="CASCADE")
    )
    session_id: Mapped[UUID] = mapped_column(ForeignKey("public.sessions.id", ondelete="CASCADE"))
    retrieval_opportunity_id: Mapped[UUID | None]
    question_family: Mapped[str] = mapped_column(String(64))
    question_text: Mapped[str] = mapped_column(Text)
    retrieval_type: Mapped[str] = mapped_column(String(24), default="TRANSFER")
    status: Mapped[str] = mapped_column(String(24), default="CREATED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
