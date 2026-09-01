import json
from pathlib import Path

import httpx

from app.schemas import CandidateProfile


class ProfileExtractionError(RuntimeError):
    pass


class OpenAIProfileExtractor:
    version = "profile_extractor_v1"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._client = client

    async def extract(self, *, raw_text: str, target_role: str) -> CandidateProfile:
        prompt_path = Path(__file__).with_name("prompts") / "profile_extractor_v1.txt"
        instructions = prompt_path.read_text(encoding="utf-8")
        schema = CandidateProfile.model_json_schema()
        schema["required"] = list(schema["properties"])
        schema["additionalProperties"] = False
        payload = {
            "model": self._model,
            "store": False,
            "reasoning": {"effort": "low"},
            "instructions": instructions,
            "input": f"Target role: {target_role}\n\nSource text:\n{raw_text}",
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "candidate_profile",
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=45,
        )
        try:
            response = await client.post("/responses", json=payload)
            response.raise_for_status()
            output_text = response.json().get("output_text")
            if not output_text:
                raise ProfileExtractionError("Profile extractor returned no structured output.")
            return CandidateProfile.model_validate(json.loads(output_text))
        except (httpx.HTTPError, json.JSONDecodeError, ValueError) as error:
            raise ProfileExtractionError("Profile extraction failed.") from error
        finally:
            if owns_client:
                await client.aclose()
