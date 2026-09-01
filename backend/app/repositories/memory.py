from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AttemptRow,
    ErrorPatternRow,
    ExpressionAttemptRow,
    ExpressionRow,
    SessionRow,
    SourceDocumentRow,
    StoryRow,
)
from app.schemas import ErrorPattern, Expression, ExpressionAttempt, Story, TrustedTransferAnalysis


class MemoryRepository(Protocol):
    async def get_expression(self, expression_id: UUID, user_id: UUID) -> Expression | None: ...
    async def list_expressions(self, user_id: UUID) -> list[Expression]: ...
    async def list_evidence(
        self, expression_id: UUID, user_id: UUID
    ) -> list[ExpressionAttempt]: ...
    async def save_expression(self, expression: Expression) -> Expression: ...
    async def add_evidence(self, evidence: ExpressionAttempt) -> ExpressionAttempt: ...
    async def save_error_pattern(self, pattern: ErrorPattern) -> ErrorPattern: ...
    async def save_story(self, story: Story) -> Story: ...


class InMemoryMemoryRepository:
    def __init__(self, *, strict_provenance: bool = False) -> None:
        self.strict_provenance = strict_provenance
        self.expressions: dict[UUID, Expression] = {}
        self.evidence: dict[UUID, ExpressionAttempt] = {}
        self.error_patterns: dict[UUID, ErrorPattern] = {}
        self.stories: dict[UUID, Story] = {}
        self.sessions: dict[UUID, UUID] = {}
        self.session_states: dict[UUID, tuple[str, str]] = {}
        self.attempts: dict[UUID, tuple[UUID, UUID]] = {}
        self.attempt_analyses: dict[UUID, TrustedTransferAnalysis] = {}
        self.attempt_questions: dict[UUID, str] = {}

    def register_session(
        self,
        session_id: UUID,
        user_id: UUID,
        *,
        session_type: str = "DAILY",
        status: str = "IN_PROGRESS",
    ) -> None:
        self.sessions[session_id] = user_id
        self.session_states[session_id] = (session_type, status)

    def register_attempt(
        self,
        attempt_id: UUID,
        session_id: UUID,
        user_id: UUID,
        analysis: TrustedTransferAnalysis | None = None,
        question: str | None = None,
    ) -> None:
        self.attempts[attempt_id] = (session_id, user_id)
        if analysis is not None:
            self.attempt_analyses[attempt_id] = analysis
        if question is not None:
            self.attempt_questions[attempt_id] = question

    async def save_expression(self, expression: Expression) -> Expression:
        self.expressions[expression.id] = expression
        return expression

    async def get_expression(self, expression_id: UUID, user_id: UUID) -> Expression | None:
        value = self.expressions.get(expression_id)
        return value if value and value.user_id == user_id else None

    async def list_expressions(self, user_id: UUID) -> list[Expression]:
        return [item for item in self.expressions.values() if item.user_id == user_id]

    async def list_evidence(self, expression_id: UUID, user_id: UUID) -> list[ExpressionAttempt]:
        return [
            item
            for item in self.evidence.values()
            if item.expression_id == expression_id and item.user_id == user_id
        ]

    async def add_evidence(self, evidence: ExpressionAttempt) -> ExpressionAttempt:
        expression = self.expressions.get(evidence.expression_id)
        if expression is None or expression.user_id != evidence.user_id:
            raise PermissionError("Evidence must reference the user's expression.")
        if self.strict_provenance and (
            self.sessions.get(evidence.session_id) != evidence.user_id
            or self.attempts.get(evidence.attempt_id) != (evidence.session_id, evidence.user_id)
        ):
            raise PermissionError("Evidence requires an existing user-owned Attempt and Session.")
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


class SQLMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_expression(self, expression: Expression) -> Expression:
        row = await self._session.get(ExpressionRow, expression.id)
        if row and row.user_id != expression.user_id:
            raise PermissionError("Expression belongs to another user.")
        if row is None:
            row = ExpressionRow(**expression.model_dump())
            self._session.add(row)
        else:
            for name, value in expression.model_dump(
                exclude={"id", "user_id", "created_at"}
            ).items():
                setattr(row, name, value)
        await self._session.commit()
        return expression

    async def get_expression(self, expression_id: UUID, user_id: UUID) -> Expression | None:
        row = await self._session.scalar(
            select(ExpressionRow).where(
                ExpressionRow.id == expression_id, ExpressionRow.user_id == user_id
            )
        )
        return Expression.model_validate(row) if row else None

    async def list_expressions(self, user_id: UUID) -> list[Expression]:
        rows = (
            await self._session.scalars(
                select(ExpressionRow)
                .where(ExpressionRow.user_id == user_id)
                .order_by(ExpressionRow.created_at)
            )
        ).all()
        return [Expression.model_validate(row) for row in rows]

    async def list_evidence(self, expression_id: UUID, user_id: UUID) -> list[ExpressionAttempt]:
        rows = (
            await self._session.scalars(
                select(ExpressionAttemptRow)
                .where(
                    ExpressionAttemptRow.expression_id == expression_id,
                    ExpressionAttemptRow.user_id == user_id,
                )
                .order_by(ExpressionAttemptRow.created_at)
            )
        ).all()
        return [ExpressionAttempt.model_validate(row) for row in rows]

    async def add_evidence(self, evidence: ExpressionAttempt) -> ExpressionAttempt:
        expression = await self.get_expression(evidence.expression_id, evidence.user_id)
        attempt = await self._session.scalar(
            select(AttemptRow).where(
                AttemptRow.id == evidence.attempt_id, AttemptRow.user_id == evidence.user_id
            )
        )
        session = await self._session.scalar(
            select(SessionRow).where(
                SessionRow.id == evidence.session_id, SessionRow.user_id == evidence.user_id
            )
        )
        if (
            expression is None
            or attempt is None
            or session is None
            or attempt.session_id != session.id
        ):
            raise PermissionError(
                "Evidence provenance must reference user-owned expression, attempt, and session."
            )
        self._session.add(ExpressionAttemptRow(**evidence.model_dump()))
        await self._session.commit()
        return evidence

    async def save_error_pattern(self, pattern: ErrorPattern) -> ErrorPattern:
        row = await self._session.get(ErrorPatternRow, pattern.id)
        if row and row.user_id != pattern.user_id:
            raise PermissionError("Error pattern belongs to another user.")
        if row is None:
            self._session.add(ErrorPatternRow(**pattern.model_dump()))
        else:
            for name, value in pattern.model_dump(exclude={"id", "user_id", "first_seen"}).items():
                setattr(row, name, value)
        await self._session.commit()
        return pattern

    async def save_story(self, story: Story) -> Story:
        if not story.confirmed_by_user:
            raise PermissionError("Only confirmed stories can be persisted.")
        if story.source_type == "DOCUMENT":
            source = await self._session.scalar(
                select(SourceDocumentRow).where(
                    SourceDocumentRow.id == story.source_document_id,
                    SourceDocumentRow.user_id == story.user_id,
                )
            )
            if source is None:
                raise PermissionError("Story document provenance must belong to the user.")
        if story.source_type == "ATTEMPT":
            source = await self._session.scalar(
                select(AttemptRow).where(
                    AttemptRow.id == story.source_attempt_id,
                    AttemptRow.user_id == story.user_id,
                )
            )
            if source is None:
                raise PermissionError("Story attempt provenance must belong to the user.")
        self._session.add(StoryRow(**story.model_dump()))
        await self._session.commit()
        return story
