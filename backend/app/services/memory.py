from uuid import UUID

from app.repositories.memory import MemoryRepository
from app.schemas import Expression, ExpressionAttempt, Story
from app.services.mastery import MasteryEngine, ReviewScheduler
from app.services.memory_gate import MemoryGate


class MemoryApplicationService:
    async def create_expression(self, expression: Expression) -> Expression:
        return await self.repository.save_expression(expression)

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository
        self.gate = MemoryGate()
        self.mastery = MasteryEngine()
        self.reviews = ReviewScheduler()

    async def record_expression_evidence(self, evidence: ExpressionAttempt) -> Expression:
        expression = await self.repository.get_expression(evidence.expression_id, evidence.user_id)
        if expression is None:
            raise LookupError("Expression was not found for this user.")
        history = tuple(await self.repository.list_evidence(expression.id, expression.user_id))
        await self.repository.add_evidence(evidence)
        updated = self.evaluate_expression_evidence(expression, evidence, history)
        return await self.repository.save_expression(updated)

    def evaluate_expression_evidence(
        self,
        expression: Expression,
        evidence: ExpressionAttempt,
        history: tuple[ExpressionAttempt, ...],
    ) -> Expression:
        """Apply the shared deterministic mastery/review policy without persisting."""
        updated = self.mastery.apply(expression, evidence, history)
        return updated.model_copy(
            update={
                "next_review_at": self.reviews.next_review_at(expression=updated, evidence=evidence)
            }
        )

    async def confirm_story(self, **proposal) -> Story:
        story = self.gate.confirm_story(**proposal)
        return await self.repository.save_story(story)

    async def list_expressions(self, user_id: UUID) -> list[Expression]:
        return await self.repository.list_expressions(user_id)
