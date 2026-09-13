import json
from pathlib import Path
from typing import Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.practice_v2.schemas import GeneratedFeedback

PROMPT_VERSION = "practice_feedback_v1"


class EvidenceDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str
    observation: str = Field(min_length=1, max_length=1500)


class FeedbackDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=1, max_length=2000)
    strengths: list[EvidenceDraft] = Field(min_length=1, max_length=3)
    improvements: list[EvidenceDraft] = Field(min_length=1, max_length=3)
    score: int = Field(ge=0, le=100)


def quote_sources(answers):
    sources = {}
    for index, answer in enumerate(answers):
        transcript = answer["transcript"]
        for offset in range(0, len(transcript), 500):
            quote = transcript[offset : offset + 500]
            if quote.strip():
                sources[f"a{index}-s{offset}"] = {
                    "question_id": answer["question_id"],
                    "quote": quote,
                }
    if not sources:
        raise RuntimeError("No answer evidence is available.")
    return sources


class PracticeFeedbackProvider(Protocol):
    provider_name: str
    model_name: str | None

    async def generate(self, answers: list[dict]) -> GeneratedFeedback: ...


class FakePracticeFeedbackProvider:
    provider_name = "fake"
    model_name = "fixture"

    async def generate(self, answers):
        evidence = {
            "question_id": answers[0]["question_id"],
            "quote": answers[0]["transcript"][:200],
        }
        return GeneratedFeedback(
            summary="You completed a useful round of speaking practice.",
            strengths=[{**evidence, "observation": "You gave a direct response."}],
            improvements=[
                {**evidence, "observation": "Make your main point clear in the opening sentence."}
            ],
            score=95,
        )


class BailianPracticeFeedbackProvider:
    provider_name = "bailian"

    def __init__(self, *, key: str, base_url: str, model: str):
        self.key, self.base_url, self.model_name = key, base_url, model

    async def generate(self, answers):
        prompt = (Path(__file__).parents[1] / "ai/prompts/practice_feedback_v1.txt").read_text(
            encoding="utf-8"
        )
        sources = quote_sources(answers)
        schema = FeedbackDraft.model_json_schema()
        schema["$defs"]["EvidenceDraft"]["properties"]["evidence_id"]["enum"] = list(sources)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.key}"},
                json={
                    "model": self.model_name,
                    "enable_thinking": False,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {
                            "role": "user",
                            "content": json.dumps(
                                {
                                    "answers": answers,
                                    "source_quotes": sources,
                                    "output_contract": schema,
                                },
                                ensure_ascii=False,
                            ),
                        },
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": PROMPT_VERSION,
                            "strict": True,
                            "schema": schema,
                        },
                    },
                },
            )
        try:
            response.raise_for_status()
            draft = FeedbackDraft.model_validate_json(
                response.json()["choices"][0]["message"]["content"]
            )
            return GeneratedFeedback(
                summary=draft.summary,
                score=draft.score,
                strengths=[
                    {**sources[item.evidence_id], "observation": item.observation}
                    for item in draft.strengths
                ],
                improvements=[
                    {**sources[item.evidence_id], "observation": item.observation}
                    for item in draft.improvements
                ],
            )
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            status = response.status_code
            raise RuntimeError(
                f"Practice feedback generation failed ({status}/{type(error).__name__})."
            ) from error
