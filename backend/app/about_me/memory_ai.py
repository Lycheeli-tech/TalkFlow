import json
from pathlib import Path
from typing import Protocol
from uuid import UUID

import httpx

from app.about_me.entities import MemoryDecision, MemoryItem, MemorySourceType


class MemoryDecisionProposer(Protocol):
    version: str

    async def propose(
        self,
        *,
        source_type: MemorySourceType,
        source_id: UUID,
        source_content: str,
        source_field_path: str | None,
        existing_memories: list[MemoryItem],
    ) -> MemoryDecision: ...


class IgnoreMemoryDecisionProposer:
    version = "memory_decision_v1"

    async def propose(
        self,
        *,
        source_type: MemorySourceType,
        source_id: UUID,
        source_content: str,
        source_field_path: str | None,
        existing_memories: list[MemoryItem],
    ) -> MemoryDecision:
        del source_type, source_id, source_content, source_field_path, existing_memories
        return MemoryDecision(
            action="IGNORE", candidate_content=None, target_memory_ids=[], source_citations=[]
        )


class BailianMemoryDecisionProposer:
    version = "memory_decision_v1"

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def propose(
        self,
        *,
        source_type: MemorySourceType,
        source_id: UUID,
        source_content: str,
        source_field_path: str | None,
        existing_memories: list[MemoryItem],
    ) -> MemoryDecision:
        instructions = (
            Path(__file__).parents[1] / "ai" / "prompts" / "memory_decision_v1.txt"
        ).read_text(encoding="utf-8")
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "source": {
                                "type": source_type,
                                "id": str(source_id),
                                "field_path": source_field_path,
                                "content": source_content[:20000],
                            },
                            "existing_memories": [
                                {"id": str(item.id), "content": item.content}
                                for item in existing_memories
                            ],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "memory_decision",
                    "strict": True,
                    "schema": MemoryDecision.model_json_schema(),
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
            return MemoryDecision.model_validate(json.loads(content))
        except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError) as error:
            raise RuntimeError("AI Memory decision generation failed.") from error
