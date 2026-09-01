import json

import httpx

from app.ai.profile_extractor import OpenAIProfileExtractor


async def test_openai_profile_extractor_uses_versioned_strict_schema() -> None:
    captured: dict[str, object] = {}
    candidate = {
        "target_role": "Product Manager",
        "primary_goal": "english_interview",
        "education": [],
        "work_experience": ["Led a product launch"],
        "projects": [],
        "skills": ["Communication"],
        "industries": [],
        "career_transition": None,
        "technical_keywords": [],
        "potential_story_candidates": ["Product launch"],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"output_text": json.dumps(candidate)})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.openai.com/v1",
    ) as client:
        extractor = OpenAIProfileExtractor(
            api_key="test-key",
            model="gpt-5.6-luna",
            client=client,
        )
        result = await extractor.extract(
            raw_text="Led a product launch.", target_role="Product Manager"
        )

    assert result.work_experience == ["Led a product launch"]
    assert captured["store"] is False
    assert captured["model"] == "gpt-5.6-luna"
    text_format = captured["text"]["format"]
    assert text_format["type"] == "json_schema"
    assert text_format["strict"] is True
    assert set(text_format["schema"]["required"]) == set(text_format["schema"]["properties"])
