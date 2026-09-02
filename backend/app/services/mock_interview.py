from app.ai.interfaces import AnswerAnalyzer
from app.curriculum.interview_bootcamp_v1 import QUESTION_INVENTORY
from app.schemas import AttemptAnalysis, MockInterviewPrompt, MockInterviewResult


class MockInterviewService:
    """Runs one complete-answer interview turn with no mid-answer correction."""

    def __init__(self, analyzer: AnswerAnalyzer) -> None:
        self.analyzer = analyzer

    def prompt(self, question_id: str | None = None) -> MockInterviewPrompt:
        item = next(
            (candidate for candidate in QUESTION_INVENTORY if candidate.id == question_id),
            QUESTION_INVENTORY[0],
        )
        return MockInterviewPrompt(question_id=item.id, family=item.family, question=item.content)

    async def evaluate(self, *, question_id: str, transcript: str) -> MockInterviewResult:
        prompt = self.prompt(question_id)
        analysis: AttemptAnalysis = await self.analyzer.analyze(
            question=prompt.question, transcript=transcript
        )
        return MockInterviewResult(
            prompt=prompt, analysis=analysis, analyzer_version=self.analyzer.version
        )
