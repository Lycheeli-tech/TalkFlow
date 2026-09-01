from typing import Any, Protocol

from app.schemas import AttemptAnalysis, CalibrationQuestion, CandidateProfile, ConfirmedProfile


class LLMService(Protocol):
    async def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]: ...


class SpeechToTextService(Protocol):
    provider_name: str

    async def transcribe(self, *, audio: bytes, content_type: str) -> str: ...


class TextToSpeechService(Protocol):
    async def synthesize(self, *, text: str, voice: str) -> bytes: ...


class CalibrationQuestionGenerator(Protocol):
    version: str

    async def generate(self, *, profile: ConfirmedProfile) -> list[CalibrationQuestion]: ...


class AnswerAnalyzer(Protocol):
    version: str

    async def analyze(self, *, question: str, transcript: str) -> AttemptAnalysis: ...


class ProfileExtractor(Protocol):
    version: str

    async def extract(self, *, raw_text: str, target_role: str) -> CandidateProfile: ...
