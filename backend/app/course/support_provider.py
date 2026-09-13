import json
import re
from pathlib import Path
from typing import Protocol, TypeVar

import httpx
from pydantic import BaseModel

from app.course.support_entities import (
    CourseContext,
    CourseExpressionMaterials,
    CourseHints,
    CourseReferenceAnswer,
    GeneratedCourseFeedback,
    ReferenceAnswerDraft,
)

HINTS_PROMPT_VERSION = "course_hints_v1"
MATERIALS_PROMPT_VERSION = "course_expression_materials_v1"
REFERENCE_PROMPT_VERSION = "course_reference_answer_v1"
FEEDBACK_PROMPT_VERSION = "course_feedback_v1"


class CourseSupportProvider(Protocol):
    provider_name: str
    model_name: str | None

    async def hints(self, context: CourseContext) -> CourseHints: ...
    async def expression_materials(self, context: CourseContext) -> CourseExpressionMaterials: ...
    async def reference_answer(self, context: CourseContext) -> CourseReferenceAnswer: ...
    async def feedback(self, context: CourseContext) -> GeneratedCourseFeedback: ...


class FakeCourseSupportProvider:
    provider_name = "fake"
    model_name = "fixture"

    async def hints(self, context: CourseContext) -> CourseHints:
        return CourseHints(
            static_answer_focus=context.answer_focus,
            keywords=["responsibility", "decision", "result"],
            phrases=["I was responsible for", "The key decision I made was"],
            sentence_frames=["The goal was __, and my role was __."],
            personalization_note=_personalization_note(context),
            prompt_version=HINTS_PROMPT_VERSION,
            provider_name=self.provider_name,
            model_name=self.model_name,
        )

    async def expression_materials(self, context: CourseContext) -> CourseExpressionMaterials:
        from app.course.support_entities import ExpressionMaterial

        return CourseExpressionMaterials(
            materials=[
                ExpressionMaterial(kind="PHRASE", text="I took ownership of ..."),
                ExpressionMaterial(
                    kind="SENTENCE_FRAME", text="One decision I made was __ because __."
                ),
                ExpressionMaterial(
                    kind="NATURAL_EXPRESSION", text="What I am most proud of is ..."
                ),
            ],
            personalization_note=_personalization_note(context),
            prompt_version=MATERIALS_PROMPT_VERSION,
            provider_name=self.provider_name,
            model_name=self.model_name,
        )

    async def reference_answer(self, context: CourseContext) -> CourseReferenceAnswer:
        return CourseReferenceAnswer(
            answer=_safe_generic_reference(context),
            personalization_note=_personalization_note(context),
            prompt_version=REFERENCE_PROMPT_VERSION,
            provider_name=self.provider_name,
            model_name=self.model_name,
        )

    async def feedback(self, context: CourseContext) -> GeneratedCourseFeedback:
        from app.course.support_entities import FeedbackChange

        answer = context.current_answer or ""
        quote = answer[:240].strip() or "The saved answer"
        return GeneratedCourseFeedback(
            summary=(
                "Your answer communicates the main idea; make your personal contribution clearer."
            ),
            priority_changes=[
                FeedbackChange(
                    original_quote=quote,
                    suggestion=(
                        "State one concrete action you personally took and why you chose it."
                    ),
                )
            ],
        )


SchemaT = TypeVar("SchemaT", bound=BaseModel)


class BailianCourseSupportProvider:
    provider_name = "bailian"

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self.model_name = model

    async def hints(self, context: CourseContext) -> CourseHints:
        result = await self._generate(HINTS_PROMPT_VERSION, context, CourseHints)
        return result.model_copy(
            update={
                "static_answer_focus": context.answer_focus,
                "prompt_version": HINTS_PROMPT_VERSION,
                "provider_name": self.provider_name,
                "model_name": self.model_name,
            }
        )

    async def expression_materials(self, context: CourseContext) -> CourseExpressionMaterials:
        result = await self._generate(MATERIALS_PROMPT_VERSION, context, CourseExpressionMaterials)
        return result.model_copy(
            update={
                "prompt_version": MATERIALS_PROMPT_VERSION,
                "provider_name": self.provider_name,
                "model_name": self.model_name,
            }
        )

    async def reference_answer(self, context: CourseContext) -> CourseReferenceAnswer:
        evidence = _context_evidence(context)
        if not evidence:
            return CourseReferenceAnswer(
                answer=_safe_generic_reference(context),
                personalization_note=_personalization_note(context),
                prompt_version=REFERENCE_PROMPT_VERSION,
                provider_name="deterministic-fallback",
                model_name=None,
            )
        draft = await self._generate(REFERENCE_PROMPT_VERSION, context, ReferenceAnswerDraft)
        answer_segments: list[str] = []
        for segment in draft.segments:
            if segment.kind == "GENERIC_TEMPLATE":
                if segment.source_excerpt is not None:
                    raise RuntimeError("A generic reference segment cannot cite learner data.")
                answer_segments.append(_safe_generic_reference(context))
            elif not segment.source_excerpt or not any(
                segment.source_excerpt.casefold() in item.casefold() for item in evidence
            ):
                raise RuntimeError(
                    "A grounded reference segment requires an exact verified excerpt."
                )
            else:
                unsupported_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", segment.text)) - set(
                    re.findall(r"\d+(?:\.\d+)?%?", " ".join(evidence))
                )
                if unsupported_numbers:
                    raise RuntimeError(
                        "A grounded reference segment contains an unsupported number."
                    )
                answer_segments.append(segment.text.strip())
        return CourseReferenceAnswer(
            answer=" ".join(dict.fromkeys(answer_segments)),
            personalization_note=_personalization_note(context),
            prompt_version=REFERENCE_PROMPT_VERSION,
            provider_name=self.provider_name,
            model_name=self.model_name,
        )

    async def feedback(self, context: CourseContext) -> GeneratedCourseFeedback:
        return await self._generate(FEEDBACK_PROMPT_VERSION, context, GeneratedCourseFeedback)

    async def _generate(
        self, prompt_version: str, context: CourseContext, schema_type: type[SchemaT]
    ) -> SchemaT:
        instructions = (
            Path(__file__).parents[1] / "ai" / "prompts" / f"{prompt_version}.txt"
        ).read_text(encoding="utf-8")
        schema = schema_type.model_json_schema()
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"context": context.model_dump(), "output_contract": schema},
                        ensure_ascii=False,
                        default=str,
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": prompt_version,
                    "strict": True,
                    "schema": schema,
                },
            },
            "enable_thinking": False,
        }
        async with httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=60,
        ) as client:
            response = await client.post("/chat/completions", json=payload)
        try:
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return schema_type.model_validate(json.loads(content))
        except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError) as error:
            raise RuntimeError(f"{prompt_version} generation failed.") from error


def _personalization_note(context: CourseContext) -> str:
    if any(
        (
            context.target_roles,
            context.supplemental_facts,
            context.resume_excerpts,
            context.memories,
            context.prior_answers,
        )
    ):
        return "Uses the available verified profile context."
    return "Add About Me details for more personalized help."


def _context_evidence(context: CourseContext) -> list[str]:
    return [
        *context.target_roles,
        *context.supplemental_facts,
        *context.resume_excerpts,
        *context.memories,
        *context.prior_answers,
    ]


def _safe_generic_reference(context: CourseContext) -> str:
    return (
        f'To answer "{context.question}", replace the placeholders with your own true details: '
        "[your direct response]. [relevant context or reasoning]. "
        "[supporting facts, if available]."
    )
