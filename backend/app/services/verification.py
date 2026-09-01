from uuid import UUID

from app.schemas import RetrievalResult
from app.services.cross_session_uow import CrossSessionUnitOfWork


class VerificationService:
    """Trusted boundary from a persisted analyzed Attempt to atomic durable evidence."""

    def __init__(self, unit_of_work: CrossSessionUnitOfWork) -> None:
        self.unit_of_work = unit_of_work

    async def verify_and_record(
        self,
        *,
        user_id: UUID,
        opportunity_id: UUID,
        attempt_id: UUID,
    ) -> RetrievalResult:
        return await self.unit_of_work.resolve(
            user_id=user_id,
            opportunity_id=opportunity_id,
            attempt_id=attempt_id,
        )
