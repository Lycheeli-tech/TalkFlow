import json

import httpx
import pytest

from app.practice_v2.feedback_service import BailianPracticeFeedbackProvider


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", [False, True])
async def test_provider_resolves_only_supplied_transcript_ids(monkeypatch, invalid):
    def handler(request):
        payload = json.loads(request.content)
        context = json.loads(payload["messages"][1]["content"])
        supplied = context["source_quotes"]
        source = next(iter(supplied)) if not invalid else "fabricated-question-quote"
        evidence = {"evidence_id": source, "observation": "Make the main point easier to follow."}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "You gave a useful answer.",
                                    "score": 95,
                                    "strengths": [evidence],
                                    "improvements": [evidence],
                                }
                            )
                        }
                    }
                ]
            },
        )

    original = httpx.AsyncClient
    monkeypatch.setattr(
        "app.practice_v2.feedback_service.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    provider = BailianPracticeFeedbackProvider(
        key="fixture", base_url="https://fixture.test", model="fixture"
    )
    answers = [
        {
            "question_id": "course-11.core",
            "question": "Tell me about a project you are proud of.",
            "transcript": "I tested an idea with my team.",
        }
    ]
    if invalid:
        with pytest.raises(RuntimeError):
            await provider.generate(answers)
    else:
        generated = await provider.generate(answers)
        assert generated.strengths[0].quote == answers[0]["transcript"]
        assert generated.strengths[0].question_id == answers[0]["question_id"]
