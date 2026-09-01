from typing import Any

from app.schemas import CandidateProfile


class FakeLLMService:
    def __init__(self, response: dict[str, Any] | None = None) -> None:
        self._response = response or {"provider": "fake", "status": "ok"}

    async def generate_structured(
        self,
        *,
        prompt_name: str,
        prompt_version: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            **self._response,
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "input_data": input_data,
        }


class FakeSpeechToTextService:
    def __init__(self, transcript: str = "Fixture transcript") -> None:
        self._transcript = transcript

    async def transcribe(self, *, audio: bytes, content_type: str) -> str:
        del audio, content_type
        return self._transcript


class FakeTextToSpeechService:
    async def synthesize(self, *, text: str, voice: str) -> bytes:
        return f"fake-audio:{voice}:{text}".encode()


class FakeProfileExtractor:
    version = "profile_extractor_fixture_v1"

    def __init__(self, candidate: CandidateProfile | None = None) -> None:
        self._candidate = candidate

    async def extract(self, *, raw_text: str, target_role: str) -> CandidateProfile:
        if self._candidate is not None:
            return self._candidate.model_copy(update={"target_role": target_role})
        summary = " ".join(raw_text.split())[:240]
        return CandidateProfile(
            target_role=target_role,
            work_experience=[summary] if summary else [],
        )
