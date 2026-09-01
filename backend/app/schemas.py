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
    storage_path: str | None = None
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


CalibrationQuestionType = Literal["EXPERIENCE", "MOTIVATION", "PROJECT"]
AttemptStatus = Literal["AUDIO_SAVED", "STT_FAILED", "TRANSCRIBED", "ANALYSIS_FAILED", "ANALYZED"]
AssessmentLevel = Literal["NEEDS_WORK", "DEVELOPING", "FUNCTIONAL", "STRONG"]
LearningPhase = Literal["BUILD", "TRANSFER", "PERFORM"]
DailyStep = Literal["RECALL", "LEARN", "IMITATE", "RETRIEVE", "TRANSFER", "INTERVIEW", "RECAP"]
ExpressionStatus = Literal["NEW", "LEARNING", "RECALLED", "TRANSFERRED", "MASTERED"]
RetrievalType = Literal["LEARNING", "RECALL", "TRANSFER"]
EvidenceResult = Literal["SUCCESS", "FAILURE"]
ErrorPatternStatus = Literal["CANDIDATE", "ACTIVE", "IMPROVING", "RESOLVED"]


class CalibrationQuestion(BaseModel):
    category: CalibrationQuestionType
    text: str = Field(min_length=1, max_length=1000)


class CalibrationQuestionSet(BaseModel):
    questions: list[CalibrationQuestion]


class CalibrationSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    session_type: Literal["CALIBRATION"] = "CALIBRATION"
    status: Literal["IN_PROGRESS", "COMPLETED"] = "IN_PROGRESS"
    questions: list[CalibrationQuestion]
    started_at: datetime
    completed_at: datetime | None = None


class VoiceAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    user_id: UUID
    question: str
    question_type: CalibrationQuestionType
    audio_path: str
    audio_content_type: str
    response_duration_ms: int | None = None
    transcript: str | None = None
    analysis: dict[str, object] | None = None
    status: AttemptStatus = "AUDIO_SAVED"
    provider_error: str | None = None
    stt_provider: str | None = None
    analyzer_version: str | None = None
    created_at: datetime
    updated_at: datetime


class AttemptAnalysis(BaseModel):
    fluency: AssessmentLevel
    naturalness: AssessmentLevel
    grammar: AssessmentLevel
    retrieval: AssessmentLevel
    structure: AssessmentLevel
    strengths: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    observed_patterns: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class LearnerAssessment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    user_id: UUID
    fluency: AssessmentLevel
    naturalness: AssessmentLevel
    grammar: AssessmentLevel
    retrieval: AssessmentLevel
    structure: AssessmentLevel
    strengths: list[str] = Field(default_factory=list)
    primary_focus: str
    secondary_focus: str | None = None
    observed_patterns: list[str] = Field(default_factory=list)
    assessment_version: str
    created_at: datetime


class CalibrationResult(BaseModel):
    session: CalibrationSession
    attempts: list[VoiceAttempt]
    assessment: LearnerAssessment | None = None


class InventoryItem(BaseModel):
    id: str
    item_type: Literal["QUESTION", "LANGUAGE", "STRATEGY"]
    family: str
    content: str
    tags: list[str] = Field(default_factory=list)
    eligible_phases: list[LearningPhase] = Field(
        default_factory=lambda: ["BUILD", "TRANSFER", "PERFORM"]
    )


class DailySessionPlan(BaseModel):
    version: Literal["daily_session_plan_v1"] = "daily_session_plan_v1"
    day: int = Field(ge=1, le=30)
    phase: LearningPhase
    duration_minutes: Literal[10, 20, 30, 60]
    topic_family: str
    question_family: str
    strategy_id: str
    story_category: str
    new_language_target_ids: list[str] = Field(default_factory=list)
    retrieval_target_ids: list[str] = Field(default_factory=list)
    steps: list[DailyStep]
    scaffolding_level: Literal["HIGH", "MEDIUM", "LOW"]


class DailyLessonContent(BaseModel):
    version: Literal["daily_lesson_content_v1"] = "daily_lesson_content_v1"
    question_prompt: str = Field(min_length=1, max_length=1000)
    reference_answer: str = Field(min_length=1, max_length=4000)
    language_explanations: list[str] = Field(default_factory=list)
    imitation_variants: list[str] = Field(default_factory=list)
    transfer_prompts: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class DailySessionResponse(BaseModel):
    plan: DailySessionPlan
    content: DailyLessonContent


class MasteryRules(BaseModel):
    version: Literal["mastery_rules_v1"] = "mastery_rules_v1"
    recall_successes_required: int = Field(default=3, ge=1)
    transfer_successes_required: int = Field(default=2, ge=1)
    sessions_required: int = Field(default=3, ge=1)
    review_intervals_days: list[int] = Field(default_factory=lambda: [1, 3, 7, 14])


class ErrorPatternRules(BaseModel):
    version: Literal["error_pattern_rules_v1"] = "error_pattern_rules_v1"
    active_occurrences_required: int = Field(default=2, ge=2)
    resolved_corrections_required: int = Field(default=2, ge=1)


class Expression(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    text: str = Field(min_length=1, max_length=500)
    meaning: str = Field(min_length=1, max_length=1000)
    source_type: Literal["CURRICULUM", "ATTEMPT", "USER"]
    source_id: UUID | None = None
    status: ExpressionStatus = "NEW"
    successful_recall: int = Field(default=0, ge=0)
    failed_recall: int = Field(default=0, ge=0)
    transfer_success: int = Field(default=0, ge=0)
    next_review_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ExpressionAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    expression_id: UUID
    attempt_id: UUID
    session_id: UUID
    user_id: UUID
    context: str = Field(min_length=1, max_length=2000)
    retrieval_type: RetrievalType
    hint_used: bool = False
    independent_evidence: bool = False
    usage_correct: bool = False
    result: EvidenceResult
    created_at: datetime


class ErrorPattern(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    pattern_type: str
    original_example: str
    preferred_expression: str | None = None
    occurrence_count: int = Field(default=1, ge=1)
    successful_correction_count: int = Field(default=0, ge=0)
    status: ErrorPatternStatus = "CANDIDATE"
    first_seen: datetime
    last_seen: datetime


class Story(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    content: str
    source_type: Literal["DOCUMENT", "ATTEMPT", "USER"] = "USER"
    source_document_id: UUID | None = None
    source_attempt_id: UUID | None = None
    confirmed_by_user: Literal[True]
    created_at: datetime
    updated_at: datetime


class RetrievalOpportunity(BaseModel):
    expression_id: UUID
    prompt_context: str = Field(min_length=1, max_length=2000)
    retrieval_type: Literal["RECALL", "TRANSFER"] = "TRANSFER"
    due_at: datetime


class HiddenTransferOpportunity(BaseModel):
    expression_id: UUID
    session_id: UUID
    interviewer_prompt: str = Field(min_length=1, max_length=2000)
    retrieval_type: Literal["TRANSFER"] = "TRANSFER"


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["fluentloop-api"] = "fluentloop-api"
    version: str
