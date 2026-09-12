from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.course.catalog_v1 import CATALOG_VERSION, CourseDefinition, QuestionDefinition


class CourseQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: Literal["CORE", "FOLLOW_UP"]
    text: str

    @classmethod
    def from_definition(cls, question: QuestionDefinition) -> "CourseQuestion":
        return cls(id=question.id, kind=question.kind, text=question.text)


class CourseCatalogItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    order: int
    name_en: str
    name_zh_cn: str
    answer_focus_en: str
    answer_focus_zh_cn: str
    core_question: CourseQuestion
    follow_up_question: CourseQuestion | None

    @classmethod
    def from_definition(cls, course: CourseDefinition) -> "CourseCatalogItem":
        return cls(
            id=course.id,
            order=course.order,
            name_en=course.name_en,
            name_zh_cn=course.name_zh_cn,
            answer_focus_en=course.answer_focus_en,
            answer_focus_zh_cn=course.answer_focus_zh_cn,
            core_question=CourseQuestion.from_definition(course.core_question),
            follow_up_question=(
                CourseQuestion.from_definition(course.follow_up_question)
                if course.follow_up_question is not None
                else None
            ),
        )


class CourseCatalogResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: Literal["course_catalog_v1"] = CATALOG_VERSION
    courses: tuple[CourseCatalogItem, ...]
