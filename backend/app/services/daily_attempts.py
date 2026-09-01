from uuid import UUID

from app.schemas import Expression, TrustedTransferAnalysis
from app.services.verification import VerificationService


class DailyAttemptService:
    """Accepts attempt identity and trusted analysis, never caller-authored mastery flags."""

    def __init__(self, verifier: VerificationService) -> None:
        self.verifier = verifier

    async def record_hidden_transfer(
        self,
        *,
        user_id: UUID,
        opportunity_id: UUID,
        attempt_id: UUID,
        session_id: UUID,
        context: str,
        analysis: TrustedTransferAnalysis,
    ) -> Expression:
        return await self.verifier.verify_and_record(
            user_id=user_id,
            opportunity_id=opportunity_id,
            attempt_id=attempt_id,
            session_id=session_id,
            context=context,
            analysis=analysis,
        )
