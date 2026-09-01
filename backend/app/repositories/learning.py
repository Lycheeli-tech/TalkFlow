from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.learning import Expression, ExpressionAttemptEvidence


class LearningRepository(Protocol):
    async def save_expression(self, expression: Expression) -> None: ...

    async def get_expression(self, expression_id: UUID, user_id: UUID) -> Expression | None: ...

    async def list_due_expressions(self, user_id: UUID, due_at: datetime) -> list[Expression]: ...

    async def add_evidence(self, evidence: ExpressionAttemptEvidence) -> None: ...

    async def list_evidence(
        self, expression_id: UUID, user_id: UUID
    ) -> list[ExpressionAttemptEvidence]: ...


class InMemoryLearningRepository:
    """Fixture repository that preserves state across service calls and sessions."""

    def __init__(self) -> None:
        self._expressions: dict[UUID, Expression] = {}
        self._evidence: list[ExpressionAttemptEvidence] = []

    async def save_expression(self, expression: Expression) -> None:
        self._expressions[expression.id] = expression

    async def get_expression(self, expression_id: UUID, user_id: UUID) -> Expression | None:
        expression = self._expressions.get(expression_id)
        if expression is None or expression.user_id != user_id:
            return None
        return expression

    async def list_due_expressions(self, user_id: UUID, due_at: datetime) -> list[Expression]:
        return [
            expression
            for expression in self._expressions.values()
            if expression.user_id == user_id
            and expression.next_review_at is not None
            and expression.next_review_at <= due_at
        ]

    async def add_evidence(self, evidence: ExpressionAttemptEvidence) -> None:
        self._evidence.append(evidence)

    async def list_evidence(
        self, expression_id: UUID, user_id: UUID
    ) -> list[ExpressionAttemptEvidence]:
        return [
            evidence
            for evidence in self._evidence
            if evidence.expression_id == expression_id and evidence.user_id == user_id
        ]
