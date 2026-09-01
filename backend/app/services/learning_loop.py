from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from app.domain.learning import (
    MVP_MASTERY_POLICY,
    Expression,
    ExpressionAttemptEvidence,
    ExpressionStatus,
    MasteryEngine,
    MasteryPolicy,
    RetrievalType,
    ReviewScheduler,
)
from app.repositories.learning import LearningRepository


@dataclass(frozen=True)
class HiddenRetrievalOpportunity:
    session_id: UUID
    expression_id: UUID
    question: str


@dataclass(frozen=True)
class LearningProgress:
    expression: Expression
    evidence_count: int
    recap_message: str | None


class LearningLoopService:
    def __init__(
        self,
        repository: LearningRepository,
        policy: MasteryPolicy = MVP_MASTERY_POLICY,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._mastery = MasteryEngine(policy)
        self._scheduler = ReviewScheduler(policy)

    async def learn_and_recall(
        self,
        *,
        expression: Expression,
        session_id: UUID,
        evidence_id: UUID,
        context: str,
        occurred_at: datetime,
    ) -> LearningProgress:
        learning_expression = replace(
            expression,
            status=ExpressionStatus.LEARNING,
            policy_version=self._policy.version,
        )
        await self._repository.save_expression(learning_expression)
        return await self._record_attempt(
            expression=learning_expression,
            evidence_id=evidence_id,
            session_id=session_id,
            retrieval_type=RetrievalType.RECALL,
            context=context,
            occurred_at=occurred_at,
            hint_used=False,
            usage_correct=True,
            independently_retrieved=True,
        )

    async def create_hidden_transfer_opportunity(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        question: str,
        due_at: datetime,
    ) -> HiddenRetrievalOpportunity:
        due = await self._repository.list_due_expressions(user_id, due_at)
        if not due:
            raise LookupError("No expression is due for retrieval.")
        expression = due[0]
        if self._normalized(expression.text) in self._normalized(question):
            raise ValueError("Hidden target leaked into the learner-visible question.")
        return HiddenRetrievalOpportunity(
            session_id=session_id,
            expression_id=expression.id,
            question=question,
        )

    async def record_transfer(
        self,
        *,
        user_id: UUID,
        opportunity: HiddenRetrievalOpportunity,
        evidence_id: UUID,
        context: str,
        occurred_at: datetime,
        hint_used: bool,
        usage_correct: bool,
        independently_retrieved: bool,
    ) -> LearningProgress:
        expression = await self._repository.get_expression(opportunity.expression_id, user_id)
        if expression is None:
            raise LookupError("Expression was not found for this user.")
        return await self._record_attempt(
            expression=expression,
            evidence_id=evidence_id,
            session_id=opportunity.session_id,
            retrieval_type=RetrievalType.TRANSFER,
            context=context,
            occurred_at=occurred_at,
            hint_used=hint_used,
            usage_correct=usage_correct,
            independently_retrieved=independently_retrieved,
        )

    async def _record_attempt(
        self,
        *,
        expression: Expression,
        evidence_id: UUID,
        session_id: UUID,
        retrieval_type: RetrievalType,
        context: str,
        occurred_at: datetime,
        hint_used: bool,
        usage_correct: bool,
        independently_retrieved: bool,
    ) -> LearningProgress:
        evidence = ExpressionAttemptEvidence(
            id=evidence_id,
            expression_id=expression.id,
            user_id=expression.user_id,
            session_id=session_id,
            retrieval_type=retrieval_type,
            context=context,
            hint_used=hint_used,
            usage_correct=usage_correct,
            independently_retrieved=independently_retrieved,
            created_at=occurred_at,
        )
        await self._repository.add_evidence(evidence)
        updated = self._mastery.apply(expression, evidence)
        updated = self._scheduler.after_attempt(
            updated, succeeded=evidence.qualifies, at=occurred_at
        )
        await self._repository.save_expression(updated)
        evidence_items = await self._repository.list_evidence(updated.id, updated.user_id)
        recap = None
        if (
            expression.status is ExpressionStatus.RECALLED
            and updated.status is ExpressionStatus.TRANSFERRED
        ):
            recap = f"You transferred '{updated.text}' into a new context."
        return LearningProgress(updated, len(evidence_items), recap)

    @staticmethod
    def _normalized(value: str) -> str:
        return " ".join(value.casefold().split())
