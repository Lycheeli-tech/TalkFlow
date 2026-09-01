from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.repositories.retrieval import RetrievalOpportunityRepository
from app.schemas import Expression, ExpressionAttempt, TrustedTransferAnalysis
from app.services.memory import MemoryApplicationService


class VerificationService:
    """Creates authoritative evidence from trusted structured analysis."""

    def __init__(
        self,
        *,
        opportunities: RetrievalOpportunityRepository,
        memory: MemoryApplicationService,
    ) -> None:
        self.opportunities, self.memory = opportunities, memory

    async def verify_and_record(
        self,
        *,
        user_id: UUID,
        opportunity_id: UUID,
        attempt_id: UUID,
        session_id: UUID,
        context: str,
        analysis: TrustedTransferAnalysis,
    ) -> Expression:
        opportunity = await self.opportunities.get(opportunity_id, user_id)
        if opportunity is None or opportunity.status != "CREATED":
            raise ValueError("Opportunity is missing, cross-user, or already consumed.")
        if opportunity.session_id != session_id:
            raise ValueError("Attempt session does not match the opportunity.")
        success = analysis.target_used and analysis.usage_correct
        evidence = ExpressionAttempt(
            id=uuid4(),
            expression_id=opportunity.expression_id,
            attempt_id=attempt_id,
            session_id=session_id,
            retrieval_opportunity_id=opportunity.id,
            user_id=user_id,
            context=context,
            retrieval_type="TRANSFER",
            hint_used=analysis.direct_hint_used,
            independent_evidence=success and not analysis.direct_hint_used,
            usage_correct=analysis.usage_correct,
            result="SUCCESS" if success else "FAILURE",
            created_at=datetime.now(UTC),
        )
        updated = await self.memory.record_expression_evidence(evidence)
        await self.opportunities.consume(opportunity.id, user_id)
        return updated
