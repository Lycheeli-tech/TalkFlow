from app.schemas import Expression, ExpressionAttempt, HiddenTransferOpportunity
from app.services.hidden_transfer import HiddenTransferService
from app.services.memory import MemoryApplicationService


class DailyAttemptService:
    """Bridges a verified Daily transfer result into the gated memory path."""

    def __init__(self, memory: MemoryApplicationService) -> None:
        self.memory = memory

    async def record_hidden_transfer(
        self, *, opportunity: HiddenTransferOpportunity, evidence: ExpressionAttempt
    ) -> Expression:
        verified = HiddenTransferService.verify_transfer_evidence(
            opportunity=opportunity, evidence=evidence
        )
        return await self.memory.record_expression_evidence(verified)
