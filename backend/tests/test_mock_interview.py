import pytest

from app.ai.fakes import FakeAnswerAnalyzer
from app.services.mock_interview import MockInterviewService


def test_mock_interview_prompt_uses_bounded_inventory() -> None:
    prompt = MockInterviewService(FakeAnswerAnalyzer()).prompt("q.project.1")

    assert prompt.question_id == "q.project.1"
    assert prompt.family == "PROJECT_EXPERIENCE"
    assert prompt.question == "Tell me about a project you are proud of."


@pytest.mark.asyncio
async def test_mock_interview_evaluates_complete_answer_once() -> None:
    result = await MockInterviewService(FakeAnswerAnalyzer()).evaluate(
        question_id="q.project.1", transcript="I led a project and learned from it."
    )

    assert result.prompt.question_id == "q.project.1"
    assert result.analysis.fluency
    assert result.analyzer_version == "answer_analyzer_fixture_v1"
