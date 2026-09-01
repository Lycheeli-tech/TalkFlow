from typing import Any, Protocol

from app.schemas import CandidateProfile


class LLMService(Protocol):
    async def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]: ...


class SpeechToTextService(Protocol):
    async def transcribe(self, *, audio: bytes, content_type: str) -> str: ...


class TextToSpeechService(Protocol):
    async def synthesize(self, *, text: str, voice: str) -> bytes: ...


class ProfileExtractor(Protocol):
    version: str

    async def extract(self, *, raw_text: str, target_role: str) -> CandidateProfile: ...
