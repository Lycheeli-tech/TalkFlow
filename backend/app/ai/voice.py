import json
from pathlib import Path

import httpx

from app.schemas import (
    AttemptAnalysis,
    CalibrationQuestion,
    CalibrationQuestionSet,
    ConfirmedProfile,
)


class VoiceProviderError(RuntimeError):
    pass


class OpenAISpeechToTextService:
    provider_name = "openai"

    def __init__(self, *, api_key: str, model: str) -> None:
        self._api_key, self._model = api_key, model

    async def transcribe(self, *, audio: bytes, content_type: str) -> str:
        async with httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=60,
        ) as client:
            response = await client.post(
                "/audio/transcriptions",
                data={"model": self._model},
                files={"file": ("recording.webm", audio, content_type)},
            )
        try:
            response.raise_for_status()
            transcript = response.json()["text"].strip()
        except (httpx.HTTPError, KeyError, ValueError) as error:
            raise VoiceProviderError("Speech transcription failed.") from error
        if not transcript:
            raise VoiceProviderError("Speech transcription returned no text.")
        return transcript


class OpenAITextToSpeechService:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._api_key, self._model = api_key, model

    async def synthesize(self, *, text: str, voice: str) -> bytes:
        async with httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=60,
        ) as client:
            response = await client.post(
                "/audio/speech",
                json={
                    "model": self._model,
                    "voice": voice if voice != "default" else "alloy",
                    "input": text,
                },
            )
        try:
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise VoiceProviderError("Question speech synthesis failed.") from error
        return response.content


class _StructuredResponsesAdapter:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._api_key, self._model = api_key, model

    async def generate(self, *, prompt: str, input_text: str, schema_type, schema_name: str):
        schema = schema_type.model_json_schema()
        payload = {
            "model": self._model,
            "store": False,
            "instructions": prompt,
            "input": input_text,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        async with httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=60,
        ) as client:
            response = await client.post("/responses", json=payload)
        try:
            response.raise_for_status()
            return schema_type.model_validate(json.loads(response.json()["output_text"]))
        except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValueError) as error:
            raise VoiceProviderError(f"{schema_name} generation failed.") from error


class OpenAICalibrationQuestionGenerator:
    version = "calibration_questions_v1"

    def __init__(self, *, api_key: str, model: str) -> None:
        self._adapter = _StructuredResponsesAdapter(api_key=api_key, model=model)

    async def generate(self, *, profile: ConfirmedProfile) -> list[CalibrationQuestion]:
        prompt = (Path(__file__).with_name("prompts") / "calibration_questions_v1.txt").read_text(
            encoding="utf-8"
        )
        result = await self._adapter.generate(
            prompt=prompt,
            input_text=profile.model_dump_json(),
            schema_type=CalibrationQuestionSet,
            schema_name="calibration_questions",
        )
        return result.questions


class OpenAIAnswerAnalyzer:
    version = "answer_analyzer_v1"

    def __init__(self, *, api_key: str, model: str) -> None:
        self._adapter = _StructuredResponsesAdapter(api_key=api_key, model=model)

    async def analyze(self, *, question: str, transcript: str) -> AttemptAnalysis:
        prompt = (Path(__file__).with_name("prompts") / "answer_analyzer_v1.txt").read_text(
            encoding="utf-8"
        )
        return await self._adapter.generate(
            prompt=prompt,
            input_text=f"Question: {question}\nTranscript: {transcript}",
            schema_type=AttemptAnalysis,
            schema_name="attempt_analysis",
        )
