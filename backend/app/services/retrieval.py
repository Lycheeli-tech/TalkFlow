from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.repositories.memory import MemoryRepository
from app.repositories.retrieval import RetrievalOpportunityRepository
from app.schemas import RetrievalOpportunity


class RetrievalService:
    def __init__(
        self, memory: MemoryRepository, opportunities: RetrievalOpportunityRepository
    ) -> None:
        self.memory, self.opportunities = memory, opportunities

    async def create_due_opportunity(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        question_family: str,
        question_text: str,
        now: datetime | None = None,
    ) -> RetrievalOpportunity | None:
        anchor = now or datetime.now(UTC)
        due = sorted(
            (
                item
                for item in await self.memory.list_expressions(user_id)
                if item.status != "MASTERED"
                and item.next_review_at
                and item.next_review_at <= anchor
            ),
            key=lambda item: (item.next_review_at, str(item.id)),
        )
        if not due:
            return None
        target = due[0]
        normalized_question = question_text.casefold()
        if (
            target.text.casefold() in normalized_question
            or "earlier practice" in normalized_question
            or "previously learned" in normalized_question
        ):
            raise ValueError("Interviewer question leaks or meta-hints the hidden target.")
        return await self.opportunities.create(
            RetrievalOpportunity(
                id=uuid4(),
                user_id=user_id,
                expression_id=target.id,
                session_id=session_id,
                question_family=question_family,
                question_text=question_text,
                created_at=anchor,
            )
        )
