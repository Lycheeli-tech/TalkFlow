import json

import httpx
import pytest

from app.course.support_entities import CourseContext
from app.course.support_provider import BailianCourseSupportProvider


def context():
    return CourseContext(
        catalog_version="course_catalog_v1",
        course_id="course-01",
        course_name="Introduce Yourself",
        question_id="course-01.core",
        question="Tell me about yourself.",
        answer_focus="Relevant background",
        target_roles=[],
        supplemental_facts=["我负责数据分析。"],
        resume_excerpts=[],
        memories=[],
        prior_answers=[],
        current_answer=None,
    )


VALID = {
    "segments": [
        {
            "kind": "SOURCE_GROUNDED",
            "text": "I am responsible for data analysis.",
            "source_id": "source-1",
        }
    ]
}


def mock_provider(monkeypatch, outputs, *, status=200):
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        output = outputs[min(len(requests) - 1, len(outputs) - 1)]
        return httpx.Response(
            status, json={"choices": [{"message": {"content": json.dumps(output)}}]}
        )

    client_class = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: client_class(**kwargs, transport=httpx.MockTransport(handle)),
    )
    return BailianCourseSupportProvider(
        api_key="fixture", base_url="https://fixture.test", model="fixture"
    ), requests


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid",
    [
        {"segments": [{"kind": "GENERIC_TEMPLATE", "text": "", "source_id": None}]},
        {
            "segments": [
                {
                    "kind": "SOURCE_GROUNDED",
                    "text": "I analyze data.",
                    "source_id": "unknown-source",
                }
            ]
        },
        {
            "segments": [
                {
                    "kind": "SOURCE_GROUNDED",
                    "text": "I improved results by 50%.",
                    "source_id": "source-1",
                }
            ]
        },
        {
            "segments": [
                {
                    "kind": "GENERIC_TEMPLATE",
                    "text": "invented fact",
                    "source_id": "source-1",
                }
            ]
        },
    ],
)
async def test_initial_reference_retries_invalid_content_without_relaxing_checks(
    monkeypatch, invalid
):
    provider, requests = mock_provider(monkeypatch, [invalid, VALID])
    result = await provider.reference_answer(context())
    assert result.answer == "I am responsible for data analysis."
    assert result.prompt_version == "course_reference_answer_v2"
    assert len(requests) == 2
    assert "previous draft failed" in requests[1]["messages"][0]["content"]
    assert requests[0]["messages"][1] == requests[1]["messages"][1]


@pytest.mark.asyncio
async def test_invalid_evidence_still_fails_after_one_retry(monkeypatch):
    invalid = {
        "segments": [
            {
                "kind": "SOURCE_GROUNDED",
                "text": "I led a company.",
                "source_id": "unknown-source",
            }
        ]
    }
    provider, requests = mock_provider(monkeypatch, [invalid])
    with pytest.raises(ValueError, match="verified source ID"):
        await provider.reference_answer(context())
    assert len(requests) == 2


@pytest.mark.asyncio
async def test_provider_outage_is_not_retried(monkeypatch):
    provider, requests = mock_provider(monkeypatch, [VALID], status=503)
    with pytest.raises(RuntimeError, match="generation failed"):
        await provider.reference_answer(context())
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_valid_first_draft_needs_no_retry(monkeypatch):
    provider, requests = mock_provider(monkeypatch, [VALID])
    assert (await provider.reference_answer(context())).answer == VALID["segments"][0]["text"]
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_numbers_from_another_source_cannot_support_selected_source(monkeypatch):
    draft = {
        "segments": [
            {"kind": "SOURCE_GROUNDED", "text": "I analyzed 50 projects.", "source_id": "source-1"}
        ]
    }
    provider, requests = mock_provider(monkeypatch, [draft])
    learner_context = context().model_copy(update={"resume_excerpts": ["50 projects"]})
    with pytest.raises(ValueError, match="unsupported number"):
        await provider.reference_answer(learner_context)
    assert len(requests) == 2
    supplied = json.loads(requests[0]["messages"][1]["content"])["reference_sources"]
    assert supplied == {"source-1": "我负责数据分析。", "source-2": "50 projects"}
