from typing import Any


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
