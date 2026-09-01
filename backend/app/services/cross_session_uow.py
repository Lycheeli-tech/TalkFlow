from copy import deepcopy
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AttemptRow,
    ExpressionAttemptRow,
    ExpressionRow,
    RetrievalOpportunityRow,
    SessionRow,
)
from app.repositories.memory import InMemoryMemoryRepository, SQLMemoryRepository
from app.repositories.retrieval import InMemoryRetrievalOpportunityRepository
from app.schemas import Expression, ExpressionAttempt, RetrievalResult, TrustedTransferAnalysis
from app.services.memory import MemoryApplicationService


class CrossSessionUnitOfWork(Protocol):
    async def resolve(
        self, *, user_id: UUID, opportunity_id: UUID, attempt_id: UUID
    ) -> RetrievalResult: ...


def _evidence(
    *,
    expression: Expression,
    opportunity_id: UUID,
    attempt_id: UUID,
    session_id: UUID,
    context: str,
    analysis: TrustedTransferAnalysis,
) -> ExpressionAttempt:
    success = analysis.target_used and analysis.usage_correct
    return ExpressionAttempt(
        id=uuid4(),
        expression_id=expression.id,
        attempt_id=attempt_id,
        session_id=session_id,
        retrieval_opportunity_id=opportunity_id,
        user_id=expression.user_id,
        context=context,
        retrieval_type="TRANSFER",
        hint_used=analysis.direct_hint_used,
        independent_evidence=success and not analysis.direct_hint_used,
        usage_correct=analysis.usage_correct,
        result="SUCCESS" if success else "FAILURE",
        created_at=datetime.now(UTC),
    )


class InMemoryCrossSessionUnitOfWork:
    def __init__(
        self,
        memory: InMemoryMemoryRepository,
        opportunities: InMemoryRetrievalOpportunityRepository,
    ) -> None:
        self.memory, self.opportunities = memory, opportunities
        self.memory_service = MemoryApplicationService(memory)

    async def resolve(
        self,
        *,
        user_id: UUID,
        opportunity_id: UUID,
        attempt_id: UUID,
        fail_at: str | None = None,
    ) -> RetrievalResult:
        opportunity = await self.opportunities.get(opportunity_id, user_id)
        if opportunity is None:
            raise PermissionError("Opportunity was not found for this user.")
        expression = await self.memory.get_expression(opportunity.expression_id, user_id)
        analysis = self.memory.attempt_analyses.get(attempt_id)
        if (
            expression is None
            or self.memory.sessions.get(opportunity.session_id) != user_id
            or self.memory.session_states.get(opportunity.session_id) != ("DAILY", "IN_PROGRESS")
            or self.memory.attempts.get(attempt_id) != (opportunity.session_id, user_id)
            or analysis is None
            or self.memory.attempt_questions.get(attempt_id) != opportunity.question_text
        ):
            raise PermissionError(
                "Attempt, Session, Expression, and Opportunity ownership must match."
            )
        if opportunity.status == "CONSUMED":
            return RetrievalResult(
                opportunity_id=opportunity.id,
                recorded=False,
                expression_status=expression.status,
                next_review_at=expression.next_review_at,
            )
        if opportunity.status != "CREATED":
            raise ValueError("Retrieval opportunity is not consumable.")
        snapshot = deepcopy(
            (self.memory.expressions, self.memory.evidence, self.opportunities.items)
        )
        try:
            evidence = _evidence(
                expression=expression,
                opportunity_id=opportunity.id,
                attempt_id=attempt_id,
                session_id=opportunity.session_id,
                context=opportunity.question_text,
                analysis=analysis,
            )
            history = tuple(await self.memory.list_evidence(expression.id, user_id))
            await self.memory.add_evidence(evidence)
            if fail_at == "after_evidence":
                raise RuntimeError("simulated failure")
            updated = self.memory_service.evaluate_expression_evidence(
                expression, evidence, history
            )
            if fail_at == "expression":
                raise RuntimeError("simulated failure")
            await self.memory.save_expression(updated)
            await self.opportunities.consume(opportunity.id, user_id)
            return RetrievalResult(
                opportunity_id=opportunity.id,
                recorded=True,
                expression_status=updated.status,
                next_review_at=updated.next_review_at,
            )
        except Exception:
            self.memory.expressions, self.memory.evidence, self.opportunities.items = snapshot
            raise


class SQLCrossSessionUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.memory_service = MemoryApplicationService(SQLMemoryRepository(session))

    async def resolve(
        self, *, user_id: UUID, opportunity_id: UUID, attempt_id: UUID
    ) -> RetrievalResult:
        try:
            opportunity = await self.session.scalar(
                select(RetrievalOpportunityRow)
                .where(
                    RetrievalOpportunityRow.id == opportunity_id,
                    RetrievalOpportunityRow.user_id == user_id,
                )
                .with_for_update()
            )
            if opportunity is None:
                raise PermissionError("Opportunity was not found for this user.")
            expression_row = await self.session.scalar(
                select(ExpressionRow)
                .where(
                    ExpressionRow.id == opportunity.expression_id, ExpressionRow.user_id == user_id
                )
                .with_for_update()
            )
            daily_session = await self.session.scalar(
                select(SessionRow).where(
                    SessionRow.id == opportunity.session_id,
                    SessionRow.user_id == user_id,
                    SessionRow.session_type == "DAILY",
                    SessionRow.status == "IN_PROGRESS",
                )
            )
            attempt = await self.session.scalar(
                select(AttemptRow).where(
                    AttemptRow.id == attempt_id,
                    AttemptRow.user_id == user_id,
                    AttemptRow.session_id == opportunity.session_id,
                    AttemptRow.status == "ANALYZED",
                )
            )
            if (
                expression_row is None
                or daily_session is None
                or attempt is None
                or not attempt.transcript
                or not attempt.analysis
                or attempt.question != opportunity.question_text
            ):
                raise PermissionError(
                    "A verified user-owned Attempt in the opportunity Session is required."
                )
            if opportunity.status == "CONSUMED":
                return RetrievalResult(
                    opportunity_id=opportunity.id,
                    recorded=False,
                    expression_status=expression_row.status,
                    next_review_at=expression_row.next_review_at,
                )
            if opportunity.status != "CREATED":
                raise ValueError("Retrieval opportunity is not consumable.")
            analysis = TrustedTransferAnalysis.model_validate(attempt.analysis)
            expression = Expression.model_validate(expression_row)
            history_rows = (
                await self.session.scalars(
                    select(ExpressionAttemptRow).where(
                        ExpressionAttemptRow.expression_id == expression.id,
                        ExpressionAttemptRow.user_id == user_id,
                    )
                )
            ).all()
            history = tuple(ExpressionAttempt.model_validate(item) for item in history_rows)
            evidence = _evidence(
                expression=expression,
                opportunity_id=opportunity.id,
                attempt_id=attempt_id,
                session_id=opportunity.session_id,
                context=attempt.transcript[:2000],
                analysis=analysis,
            )
            updated = self.memory_service.evaluate_expression_evidence(
                expression, evidence, history
            )
            self.session.add(ExpressionAttemptRow(**evidence.model_dump()))
            for name, value in updated.model_dump(exclude={"id", "user_id", "created_at"}).items():
                setattr(expression_row, name, value)
            opportunity.status, opportunity.consumed_at = "CONSUMED", datetime.now(UTC)
            await self.session.commit()
            return RetrievalResult(
                opportunity_id=opportunity.id,
                recorded=True,
                expression_status=updated.status,
                next_review_at=updated.next_review_at,
            )
        except Exception:
            await self.session.rollback()
            raise
