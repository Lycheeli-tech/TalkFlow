from uuid import UUID

from app.schemas import RetrievalResult
from app.services.verification import VerificationService


class DailyAttemptService:
    """Resolves a persisted, server-analyzed Daily Attempt by identity only."""

    def __init__(self, verifier: VerificationService) -> None:
        self.verifier = verifier

    async def record_hidden_transfer(
        self,
        *,
        user_id: UUID,
        opportunity_id: UUID,
        attempt_id: UUID,
    ) -> RetrievalResult:
        return await self.verifier.verify_and_record(
            user_id=user_id,
            opportunity_id=opportunity_id,
            attempt_id=attempt_id,
        )
