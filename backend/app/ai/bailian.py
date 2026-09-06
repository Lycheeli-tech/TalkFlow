import base64
import json
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from app.schemas import (
    AttemptAnalysis,
    CalibrationQuestion,
    CalibrationQuestionSet,
    CandidateProfile,
    ConfirmedProfile,
    DailyLessonContent,
)


class BailianProviderError(RuntimeError):
    pass


class _BailianClient:
    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def structured(
        self, *, instructions: str, input_text: str, schema_type: type[BaseModel], schema_name: str
    ) -> BaseModel:
        schema = schema_type.model_json_schema()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": schema},
            },
            "enable_thinking": False,
        }
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60,
        ) as client:
            response = await client.post("/chat/completions", json=payload)
        try:
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return schema_type.model_validate(json.loads(content))
        except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError, ValueError) as error:
            raise BailianProviderError(f"{schema_name} generation failed.") from error


class BailianLLMService:
    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._client = _BailianClient(api_key=api_key, base_url=base_url, model=model)

    async def generate_structured(
        self, *, prompt_name: str, prompt_version: str, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        if prompt_name != "daily_lesson_content" or prompt_version != "daily_lesson_content_v1":
            raise BailianProviderError("Unsupported versioned prompt.")
        instructions = (
            "Create personalized English interview lesson content from confirmed "
            "learner data only. "
            "Respect every deterministic target and constraint in the input. Do not invent learner "
            "facts. Return only the required structured JSON."
        )
        result = await self._client.structured(
            instructions=instructions,
            input_text=json.dumps(input_data, ensure_ascii=False, default=str),
            schema_type=DailyLessonContent,
            schema_name="daily_lesson_content",
        )
        return result.model_dump()


class BailianProfileExtractor:
    version = "profile_extractor_v1"

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._client = _BailianClient(api_key=api_key, base_url=base_url, model=model)

    async def extract(self, *, raw_text: str, target_role: str) -> CandidateProfile:
        instructions = (Path(__file__).with_name("prompts") / "profile_extractor_v1.txt").read_text(
            encoding="utf-8"
        )
        result = await self._client.structured(
            instructions=instructions,
            input_text=f"Target role: {target_role}\n\nSource text:\n{raw_text}",
            schema_type=CandidateProfile,
            schema_name="candidate_profile",
        )
        return CandidateProfile.model_validate(result)


class BailianCalibrationQuestionGenerator:
    version = "calibration_questions_v1"

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._client = _BailianClient(api_key=api_key, base_url=base_url, model=model)

    async def generate(self, *, profile: ConfirmedProfile) -> list[CalibrationQuestion]:
        instructions = (
            Path(__file__).with_name("prompts") / "calibration_questions_v1.txt"
        ).read_text(encoding="utf-8")
        result = await self._client.structured(
            instructions=instructions,
            input_text=profile.model_dump_json(),
            schema_type=CalibrationQuestionSet,
            schema_name="calibration_questions",
        )
        return CalibrationQuestionSet.model_validate(result).questions


class BailianAnswerAnalyzer:
    version = "answer_analyzer_v1"

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._client = _BailianClient(api_key=api_key, base_url=base_url, model=model)

    async def analyze(self, *, question: str, transcript: str) -> AttemptAnalysis:
        instructions = (Path(__file__).with_name("prompts") / "answer_analyzer_v1.txt").read_text(
            encoding="utf-8"
        )
        result = await self._client.structured(
            instructions=instructions,
            input_text=f"Question: {question}\nTranscript: {transcript}",
            schema_type=AttemptAnalysis,
            schema_name="attempt_analysis",
        )
        return AttemptAnalysis.model_validate(result)


class BailianSpeechToTextService:
    provider_name = "bailian"

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def transcribe(self, *, audio: bytes, content_type: str) -> str:
        data_uri = f"data:{content_type};base64,{base64.b64encode(audio).decode('ascii')}"
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "input_audio", "input_audio": {"data": data_uri}}],
                }
            ],
            "stream": False,
            "asr_options": {"language": "en", "enable_itn": True},
        }
        async with httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=60,
        ) as client:
            response = await client.post("/chat/completions", json=payload)
        try:
            response.raise_for_status()
            transcript = response.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            raise BailianProviderError("Speech transcription failed.") from error
        if not transcript:
            raise BailianProviderError("Speech transcription returned no text.")
        return transcript


class BailianTextToSpeechService:
    def __init__(
        self, *, api_key: str, base_url: str, model: str, default_voice: str = "Cherry"
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._default_voice = default_voice

    async def synthesize(self, *, text: str, voice: str) -> bytes:
        payload = {
            "model": self._model,
            "input": {
                "text": text,
                "voice": self._default_voice if voice == "default" else voice,
                "language_type": "English",
            },
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(
            base_url=self._base_url, headers=headers, timeout=60
        ) as client:
            response = await client.post(
                "/services/aigc/multimodal-generation/generation", json=payload
            )
            try:
                response.raise_for_status()
                audio_url = response.json()["output"]["audio"]["url"]
                audio_response = await client.get(audio_url)
                audio_response.raise_for_status()
            except (httpx.HTTPError, KeyError, ValueError) as error:
                raise BailianProviderError("Question speech synthesis failed.") from error
        if not audio_response.content:
            raise BailianProviderError("Question speech synthesis returned no audio.")
        return audio_response.content
