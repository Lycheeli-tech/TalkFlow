from datetime import UTC, datetime
from uuid import UUID

from app.repositories.memory import MemoryRepository
from app.schemas import RetrievalOpportunity


class RetrievalService:
    """Deterministically selects due expressions without exposing target text."""

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    async def due_opportunities(
        self, *, user_id: UUID, now: datetime | None = None, limit: int = 3
    ) -> list[RetrievalOpportunity]:
        anchor = now or datetime.now(UTC)
        expressions = await self.repository.list_expressions(user_id)
        due = sorted(
            (
                expression
                for expression in expressions
                if expression.user_id == user_id
                and expression.status != "MASTERED"
                and expression.next_review_at is not None
                and expression.next_review_at <= anchor
            ),
            key=lambda expression: (expression.next_review_at, str(expression.id)),
        )
        return [
            RetrievalOpportunity(
                expression_id=expression.id,
                prompt_context=(
                    "Answer a new interview question using a useful phrase from earlier practice."
                ),
                retrieval_type="TRANSFER",
                due_at=expression.next_review_at,
            )
            for expression in due[: max(0, limit)]
        ]
