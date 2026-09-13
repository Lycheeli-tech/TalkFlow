import json
import re
from pathlib import Path
from typing import Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field

ORGANIZER_PROMPT_VERSION = "chinese_answer_organizer_v1"
ORGANIZER_INSTRUCTIONS = (
    Path(__file__).resolve().parents[1] / "ai" / "prompts" / f"{ORGANIZER_PROMPT_VERSION}.txt"
).read_text(encoding="utf-8")
FIDELITY_PROMPT_VERSION = "chinese_answer_fidelity_v1"
FIDELITY_INSTRUCTIONS = (
    Path(__file__).resolve().parents[1] / "ai" / "prompts" / f"{FIDELITY_PROMPT_VERSION}.txt"
).read_text(encoding="utf-8")


class FidelityVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    faithful: bool


class OrganizedSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_excerpt: str = Field(min_length=1, max_length=5000)
    english: str = Field(min_length=1, max_length=5000)


class OrganizedDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    segments: list[OrganizedSegment] = Field(min_length=1, max_length=20)


class ChineseAnswerOrganizer(Protocol):
    provider_name: str
    model_name: str | None

    async def organize(self, transcript: str) -> OrganizedDraft: ...
    async def verify(self, transcript: str, draft: OrganizedDraft) -> bool: ...


def validate_organized_draft(transcript: str, draft: OrganizedDraft) -> str:
    # Exact Chinese citations are required for every English segment; never accept profile context.
    for segment in draft.segments:
        if segment.source_excerpt not in transcript:
            raise ValueError("Organizer returned an unverifiable source excerpt.")
        source_numbers = set(re.findall(r"\d+(?:\.\d+)?", segment.source_excerpt))
        output_numbers = set(re.findall(r"\d+(?:\.\d+)?", segment.english))
        if not output_numbers.issubset(source_numbers):
            raise ValueError("Organizer introduced unsupported numbers.")
    return " ".join(segment.english.strip() for segment in draft.segments)


class FakeChineseAnswerOrganizer:
    provider_name = "fake"
    model_name = "fixture"

    async def verify(self, transcript: str, draft: OrganizedDraft) -> bool:
        return transcript == "我负责测试。" and all(
            segment.source_excerpt == transcript
            and segment.english == "I was responsible for testing."
            for segment in draft.segments
        )

    async def organize(self, transcript: str) -> OrganizedDraft:
        # Translate only a fixed fixture; fake mode never invents arbitrary learner facts.
        if transcript != "我负责测试。":
            raise ValueError("No Chinese organizer fixture for this transcript.")
        return OrganizedDraft(
            segments=[
                OrganizedSegment(
                    source_excerpt=transcript, english="I was responsible for testing."
                )
            ]
        )


class BailianChineseAnswerOrganizer:
    provider_name = "bailian"

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self.model_name = model

    async def organize(self, transcript: str) -> OrganizedDraft:
        return OrganizedDraft.model_validate_json(
            await self._generate(
                ORGANIZER_PROMPT_VERSION,
                ORGANIZER_INSTRUCTIONS,
                {"transcript": transcript},
                OrganizedDraft.model_json_schema(),
            )
        )

    async def verify(self, transcript: str, draft: OrganizedDraft) -> bool:
        content = await self._generate(
            FIDELITY_PROMPT_VERSION,
            FIDELITY_INSTRUCTIONS,
            {"transcript": transcript, "draft": draft.model_dump()},
            FidelityVerdict.model_json_schema(),
        )
        return FidelityVerdict.model_validate_json(content).faithful

    async def _generate(self, version: str, instructions: str, data: dict, schema: dict) -> str:
        async with httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=60,
        ) as client:
            response = await client.post(
                "/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": instructions},
                        {
                            "role": "user",
                            "content": json.dumps(data, ensure_ascii=False),
                        },
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": version,
                            "strict": True,
                            "schema": schema,
                        },
                    },
                    "enable_thinking": False,
                },
            )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
