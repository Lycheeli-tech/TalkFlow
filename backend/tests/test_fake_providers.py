import pytest

from app.ai.fakes import FakeLLMService, FakeSpeechToTextService, FakeTextToSpeechService


@pytest.mark.asyncio
async def test_fake_providers_are_deterministic() -> None:
    llm = FakeLLMService({"candidate": "fixture"})
    stt = FakeSpeechToTextService("fixture transcript")
    tts = FakeTextToSpeechService()

    llm_response = await llm.generate_structured(
        prompt_name="foundation_fixture",
        prompt_version="v1",
        input_data={"user_id": "fixture-user"},
    )

    assert llm_response["candidate"] == "fixture"
    assert llm_response["prompt_version"] == "v1"
    assert await stt.transcribe(audio=b"audio", content_type="audio/webm") == "fixture transcript"
    assert await tts.synthesize(text="Hello", voice="fixture") == b"fake-audio:fixture:Hello"
