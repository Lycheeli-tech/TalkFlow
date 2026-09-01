from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID


class ExpressionStatus(StrEnum):
    NEW = "NEW"
    LEARNING = "LEARNING"
    RECALLED = "RECALLED"
    TRANSFERRED = "TRANSFERRED"
    MASTERED = "MASTERED"


class RetrievalType(StrEnum):
    LEARNING = "LEARNING"
    RECALL = "RECALL"
    TRANSFER = "TRANSFER"


@dataclass(frozen=True)
class MasteryPolicy:
    version: str
    recall_required: int
    transfer_required: int
    session_count_required: int
    review_intervals_days: tuple[int, ...]


MVP_MASTERY_POLICY = MasteryPolicy(
    version="mvp-1",
    recall_required=3,
    transfer_required=2,
    session_count_required=3,
    review_intervals_days=(1, 3, 7, 14),
)


@dataclass(frozen=True)
class Expression:
    id: UUID
    user_id: UUID
    text: str
    status: ExpressionStatus
    successful_recall: int = 0
    transfer_success: int = 0
    successful_session_ids: frozenset[UUID] = frozenset()
    review_stage: int = 0
    next_review_at: datetime | None = None
    policy_version: str = MVP_MASTERY_POLICY.version


@dataclass(frozen=True)
class ExpressionAttemptEvidence:
    id: UUID
    expression_id: UUID
    user_id: UUID
    session_id: UUID
    retrieval_type: RetrievalType
    context: str
    hint_used: bool
    usage_correct: bool
    independently_retrieved: bool
    created_at: datetime

    @property
    def qualifies(self) -> bool:
        return self.usage_correct and self.independently_retrieved and not self.hint_used


class ReviewScheduler:
    def __init__(self, policy: MasteryPolicy = MVP_MASTERY_POLICY) -> None:
        self._policy = policy

    def after_attempt(self, expression: Expression, *, succeeded: bool, at: datetime) -> Expression:
        if succeeded:
            interval_index = min(
                expression.review_stage, len(self._policy.review_intervals_days) - 1
            )
            interval_days = self._policy.review_intervals_days[interval_index]
            next_stage = min(
                expression.review_stage + 1, len(self._policy.review_intervals_days) - 1
            )
        else:
            interval_days = self._policy.review_intervals_days[0]
            next_stage = 0
        return replace(
            expression,
            review_stage=next_stage,
            next_review_at=at + timedelta(days=interval_days),
        )


class MasteryEngine:
    def __init__(self, policy: MasteryPolicy = MVP_MASTERY_POLICY) -> None:
        self._policy = policy

    def apply(self, expression: Expression, evidence: ExpressionAttemptEvidence) -> Expression:
        if evidence.expression_id != expression.id or evidence.user_id != expression.user_id:
            raise ValueError("Evidence does not belong to this expression.")
        if not evidence.qualifies:
            return expression

        recall_count = expression.successful_recall
        transfer_count = expression.transfer_success
        status = expression.status

        if evidence.retrieval_type is RetrievalType.RECALL:
            recall_count += 1
            if status in {ExpressionStatus.NEW, ExpressionStatus.LEARNING}:
                status = ExpressionStatus.RECALLED
        elif evidence.retrieval_type is RetrievalType.TRANSFER:
            transfer_count += 1
            if status is not ExpressionStatus.MASTERED:
                status = ExpressionStatus.TRANSFERRED

        session_ids = expression.successful_session_ids | {evidence.session_id}
        if (
            recall_count >= self._policy.recall_required
            and transfer_count >= self._policy.transfer_required
            and len(session_ids) >= self._policy.session_count_required
        ):
            status = ExpressionStatus.MASTERED

        return replace(
            expression,
            status=status,
            successful_recall=recall_count,
            transfer_success=transfer_count,
            successful_session_ids=frozenset(session_ids),
        )
