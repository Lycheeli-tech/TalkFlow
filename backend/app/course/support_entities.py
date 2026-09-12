from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    catalog_version: str
    course_id: str
    course_name: str
    question_id: str
    question: str
    answer_focus: str
    target_roles: list[str] = Field(max_length=3)
    supplemental_facts: list[str] = Field(max_length=6)
    resume_excerpts: list[str] = Field(max_length=3)
    memories: list[str] = Field(max_length=6)
    prior_answers: list[str] = Field(max_length=3)
    current_answer: str | None = None


class CourseHints(BaseModel):
    static_answer_focus: str
    keywords: list[str] = Field(min_length=1, max_length=6)
    phrases: list[str] = Field(min_length=1, max_length=6)
    sentence_frames: list[str] = Field(min_length=1, max_length=4)
    personalization_note: str | None = Field(default=None, max_length=240)
    prompt_version: str
    provider_name: str
    model_name: str | None = None


class ExpressionMaterial(BaseModel):
    kind: Literal["PHRASE", "SENTENCE_FRAME", "NATURAL_EXPRESSION", "FACT_BASED_SENTENCE"]
    text: str = Field(min_length=1, max_length=500)
    source_excerpt: str | None = Field(default=None, max_length=1000)


class CourseExpressionMaterials(BaseModel):
    materials: list[ExpressionMaterial] = Field(min_length=1, max_length=8)
    personalization_note: str | None = Field(default=None, max_length=240)
    prompt_version: str
    provider_name: str
    model_name: str | None = None


class CourseReferenceAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)
    personalization_note: str | None = Field(default=None, max_length=240)
    prompt_version: str
    provider_name: str
    model_name: str | None = None


class ReferenceAnswerSegment(BaseModel):
    kind: Literal["GENERIC_TEMPLATE", "SOURCE_GROUNDED"]
    text: str = Field(min_length=1, max_length=1200)
    source_excerpt: str | None = Field(default=None, max_length=1200)


class ReferenceAnswerDraft(BaseModel):
    segments: list[ReferenceAnswerSegment] = Field(min_length=1, max_length=8)


class FeedbackChange(BaseModel):
    original_quote: str = Field(min_length=1, max_length=1000)
    suggestion: str = Field(min_length=1, max_length=1000)


class GeneratedCourseFeedback(BaseModel):
    summary: str = Field(min_length=1, max_length=1000)
    priority_changes: list[FeedbackChange] = Field(min_length=1, max_length=3)

    @field_validator("priority_changes")
    @classmethod
    def require_unique_quotes(cls, value: list[FeedbackChange]) -> list[FeedbackChange]:
        if len({item.original_quote.casefold() for item in value}) != len(value):
            raise ValueError("Feedback changes must cite distinct user quotes.")
        return value
