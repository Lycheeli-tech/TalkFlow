from uuid import UUID

from app.schemas import ExpressionAttempt, HiddenTransferOpportunity, RetrievalOpportunity


class HiddenTransferService:
    """Keeps target text out of interviewer-facing payloads and trusts verified flags."""

    def create_opportunity(
        self, *, opportunity: RetrievalOpportunity, session_id: UUID
    ) -> HiddenTransferOpportunity:
        if opportunity.session_id != session_id or opportunity.status != "CREATED":
            raise ValueError("Opportunity is not active for this session.")
        return HiddenTransferOpportunity(
            opportunity_id=opportunity.id,
            expression_id=opportunity.expression_id,
            session_id=session_id,
            interviewer_prompt=opportunity.question_text,
        )

    @staticmethod
    def verify_transfer_evidence(
        *,
        opportunity: HiddenTransferOpportunity,
        evidence: ExpressionAttempt,
    ) -> ExpressionAttempt:
        if (
            evidence.expression_id != opportunity.expression_id
            or evidence.session_id != opportunity.session_id
        ):
            raise ValueError("Transfer evidence does not belong to this opportunity.")
        if evidence.retrieval_type != "TRANSFER":
            raise ValueError("A hidden transfer opportunity requires TRANSFER evidence.")
        return evidence
