from datetime import UTC, datetime
from uuid import UUID

from app.repositories.memory import MemoryRepository
from app.schemas import QuickReviewItem


class QuickReviewService:
    """Returns a small user-scoped queue of expressions due for explicit review."""

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    async def list_due(
        self, user_id: UUID, *, now: datetime | None = None, limit: int = 10
    ) -> list[QuickReviewItem]:
        if limit < 1 or limit > 50:
            raise ValueError("Quick Review limit must be between 1 and 50.")
        anchor = now or datetime.now(UTC)
        expressions = [
            item
            for item in await self.repository.list_expressions(user_id)
            if item.next_review_at is not None and item.next_review_at <= anchor
        ]
        expressions.sort(key=lambda item: (item.next_review_at, str(item.id)))
        return [
            QuickReviewItem(
                expression_id=item.id,
                text=item.text,
                meaning=item.meaning,
                status=item.status,
                next_review_at=item.next_review_at,
            )
            for item in expressions[:limit]
        ]
