from datetime import UTC, datetime, timedelta

from app.schemas import Expression, ExpressionAttempt, MasteryRules


class MasteryEngine:
    """Applies evidence flags; it never infers independence from transcript text."""

    def __init__(self, rules: MasteryRules | None = None) -> None:
        self.rules = rules or MasteryRules()

    def apply(self, expression: Expression, evidence: ExpressionAttempt) -> Expression:
        if expression.user_id != evidence.user_id or expression.id != evidence.expression_id:
            raise ValueError("Expression evidence must belong to the same user and expression.")
        if evidence.result != "SUCCESS" or not evidence.usage_correct:
            return expression.model_copy(update={"failed_recall": expression.failed_recall + 1})
        if evidence.hint_used or not evidence.independent_evidence:
            return expression

        updates: dict[str, object] = {}
        if evidence.retrieval_type == "RECALL":
            updates["successful_recall"] = expression.successful_recall + 1
        elif evidence.retrieval_type == "TRANSFER":
            updates["transfer_success"] = expression.transfer_success + 1
        updated = expression.model_copy(update=updates)
        updated_status = self._status(updated)
        return updated.model_copy(update={"status": updated_status})

    def _status(self, expression: Expression) -> str:
        if (
            expression.successful_recall >= self.rules.recall_successes_required
            and expression.transfer_success >= self.rules.transfer_successes_required
        ):
            return "MASTERED"
        if expression.transfer_success:
            return "TRANSFERRED"
        if expression.successful_recall:
            return "RECALLED"
        if expression.status == "NEW":
            return "LEARNING"
        return expression.status


class ReviewScheduler:
    def __init__(self, rules: MasteryRules | None = None) -> None:
        self.rules = rules or MasteryRules()

    def next_review_at(
        self, *, expression: Expression, evidence: ExpressionAttempt, now: datetime | None = None
    ) -> datetime:
        anchor = now or datetime.now(UTC)
        if evidence.result != "SUCCESS" or not evidence.usage_correct:
            days = self.rules.review_intervals_days[0]
        else:
            success_count = expression.successful_recall + expression.transfer_success
            index = min(success_count, len(self.rules.review_intervals_days) - 1)
            days = self.rules.review_intervals_days[index]
        return anchor + timedelta(days=days)
