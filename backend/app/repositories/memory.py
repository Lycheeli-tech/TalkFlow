from typing import Protocol
from uuid import UUID

from app.schemas import ErrorPattern, Expression, ExpressionAttempt, Story


class MemoryRepository(Protocol):
    async def save_expression(self, expression: Expression) -> Expression: ...
    async def add_evidence(self, evidence: ExpressionAttempt) -> ExpressionAttempt: ...
    async def save_error_pattern(self, pattern: ErrorPattern) -> ErrorPattern: ...
    async def save_story(self, story: Story) -> Story: ...


class InMemoryMemoryRepository:
    def __init__(self) -> None:
        self.expressions: dict[UUID, Expression] = {}
        self.evidence: dict[UUID, ExpressionAttempt] = {}
        self.error_patterns: dict[UUID, ErrorPattern] = {}
        self.stories: dict[UUID, Story] = {}

    async def save_expression(self, expression: Expression) -> Expression:
        self.expressions[expression.id] = expression
        return expression

    async def add_evidence(self, evidence: ExpressionAttempt) -> ExpressionAttempt:
        expression = self.expressions.get(evidence.expression_id)
        if expression is None or expression.user_id != evidence.user_id:
            raise PermissionError("Evidence must reference the user's expression.")
        self.evidence[evidence.id] = evidence
        return evidence

    async def save_error_pattern(self, pattern: ErrorPattern) -> ErrorPattern:
        self.error_patterns[pattern.id] = pattern
        return pattern

    async def save_story(self, story: Story) -> Story:
        if not story.confirmed_by_user:
            raise PermissionError("Only confirmed stories can be persisted.")
        self.stories[story.id] = story
        return story
