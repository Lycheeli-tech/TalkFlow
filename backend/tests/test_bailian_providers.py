import json
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest

from app.ai.bailian import (
    BailianAnswerAnalyzer,
    BailianCalibrationQuestionGenerator,
    BailianLLMService,
    BailianProfileExtractor,
    BailianSpeechToTextService,
    BailianTextToSpeechService,
)
from app.schemas import ConfirmedProfile


@pytest.mark.asyncio
async def test_bailian_text_providers_use_configured_compatible_endpoint(monkeypatch) -> None:
    requests: list[httpx.Request] = []
    real_client = httpx.AsyncClient

    candidate = {
        "target_role": "Product Manager",
        "primary_goal": "english_interview",
        "education": [],
        "work_experience": ["Led a launch"],
        "projects": [],
        "skills": ["Communication"],
        "industries": [],
        "career_transition": None,
        "technical_keywords": [],
        "potential_story_candidates": ["Launch"],
    }
    questions = {
        "questions": [
            {"category": "EXPERIENCE", "text": "Tell me about the launch."},
            {"category": "MOTIVATION", "text": "Why this role?"},
            {"category": "PROJECT", "text": "Describe the project."},
        ]
    }
    analysis = {
        "fluency": "FUNCTIONAL",
        "naturalness": "FUNCTIONAL",
        "grammar": "FUNCTIONAL",
        "retrieval": "FUNCTIONAL",
        "structure": "FUNCTIONAL",
        "strengths": ["Clear answer"],
        "focus_areas": ["More detail"],
        "observed_patterns": [],
        "evidence": ["I led the launch."],
    }
    lesson = {
        "version": "daily_lesson_content_v1",
        "question_prompt": "Why this role?",
        "reference_answer": "I am motivated by customer problems.",
        "language_explanations": [],
        "imitation_variants": [],
        "transfer_prompts": [],
        "follow_up_questions": [],
    }
    outputs = iter((candidate, questions, analysis, lesson))

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(next(outputs))}}]},
        )

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    common = {
        "api_key": "test-key",
        "base_url": "https://workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/",
        "model": "qwen3.7-flash",
    }
    now = datetime.now(UTC)
    profile = ConfirmedProfile(
        user_id=uuid4(),
        source_document_id=uuid4(),
        target_role="Product Manager",
        work_experience=["Led a launch"],
        confirmed_at=now,
        updated_at=now,
    )

    extracted = await BailianProfileExtractor(**common).extract(
        raw_text="Led a launch", target_role="Product Manager"
    )
    generated = await BailianCalibrationQuestionGenerator(**common).generate(profile=profile)
    analyzed = await BailianAnswerAnalyzer(**common).analyze(
        question="Tell me about the launch.", transcript="I led the launch."
    )
    content = await BailianLLMService(**common).generate_structured(
        prompt_name="daily_lesson_content",
        prompt_version="daily_lesson_content_v1",
        input_data={"profile": {"target_role": "Product Manager"}},
    )

    assert extracted.target_role == "Product Manager"
    assert [item.category for item in generated] == ["EXPERIENCE", "MOTIVATION", "PROJECT"]
    assert analyzed.fluency == "FUNCTIONAL"
    assert content["version"] == "daily_lesson_content_v1"
    assert len(requests) == 4
    for request in requests:
        assert str(request.url) == (
            "https://workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions"
        )
        body = json.loads(request.content)
        assert body["model"] == "qwen3.7-flash"
        assert body["response_format"]["type"] == "json_schema"
        assert body["enable_thinking"] is False


@pytest.mark.asyncio
async def test_bailian_speech_providers_use_configured_endpoints(monkeypatch) -> None:
    requests: list[httpx.Request] = []
    real_client = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/chat/completions"):
            return httpx.Response(200, json={"choices": [{"message": {"content": "Hello"}}]})
        if request.url.path.endswith("/multimodal-generation/generation"):
            return httpx.Response(
                200, json={"output": {"audio": {"url": "https://audio.example/test.wav"}}}
            )
        return httpx.Response(200, content=b"RIFF-test-audio")

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    transcript = await BailianSpeechToTextService(
        api_key="test-key",
        base_url="https://workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
        model="qwen3-asr-flash",
    ).transcribe(audio=b"webm-audio", content_type="audio/webm")
    audio = await BailianTextToSpeechService(
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/api/v1",
        model="qwen3-tts-flash",
    ).synthesize(text="Tell me about your experience.", voice="default")

    assert transcript == "Hello"
    assert audio == b"RIFF-test-audio"
    asr_body = json.loads(requests[0].content)
    assert asr_body["messages"][0]["content"][0]["input_audio"]["data"].startswith(
        "data:audio/webm;base64,"
    )
    assert asr_body["asr_options"] == {"language": "en", "enable_itn": True}
    tts_body = json.loads(requests[1].content)
    assert tts_body["input"]["voice"] == "Cherry"
    assert tts_body["input"]["language_type"] == "English"
