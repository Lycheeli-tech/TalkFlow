from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.repositories.retrieval import InMemoryRetrievalOpportunityRepository
from app.schemas import Expression, RetrievalOpportunity, TrustedTransferAnalysis
from app.services.cross_session_uow import InMemoryCrossSessionUnitOfWork
from app.services.daily_attempts import DailyAttemptService
from app.services.verification import VerificationService


@pytest.mark.asyncio
async def test_daily_transfer_flows_through_verified_memory_path() -> None:
    now = datetime.now(UTC)
    expression = Expression(
        id=uuid4(),
        user_id=uuid4(),
        text="transferable",
        meaning="usable elsewhere",
        source_type="CURRICULUM",
        created_at=now,
        updated_at=now,
    )
    repository = InMemoryMemoryRepository(strict_provenance=True)
    await repository.save_expression(expression)
    session_id, attempt_id = uuid4(), uuid4()
    repository.register_session(session_id, expression.user_id)
    repository.register_attempt(
        attempt_id,
        session_id,
        expression.user_id,
        TrustedTransferAnalysis(
            target_used=True,
            usage_correct=True,
            direct_hint_used=False,
            verifier_version="fixture_v1",
        ),
        question="New context",
    )
    opportunities = InMemoryRetrievalOpportunityRepository()
    opportunity = await opportunities.create(
        RetrievalOpportunity(
            id=uuid4(),
            user_id=expression.user_id,
            expression_id=expression.id,
            session_id=session_id,
            question_family="EXPERIENCE",
            question_text="New context",
            created_at=now,
        )
    )

    verifier = VerificationService(InMemoryCrossSessionUnitOfWork(repository, opportunities))
    result = await DailyAttemptService(verifier).record_hidden_transfer(
        user_id=expression.user_id,
        opportunity_id=opportunity.id,
        attempt_id=attempt_id,
    )

    assert result.recorded is True
    assert (
        await repository.get_expression(expression.id, expression.user_id)
    ).transfer_success == 1
    assert len(repository.evidence) == 1
    assert (await opportunities.get(opportunity.id, expression.user_id)).status == "CONSUMED"
    replay = await DailyAttemptService(verifier).record_hidden_transfer(
        user_id=expression.user_id,
        opportunity_id=opportunity.id,
        attempt_id=attempt_id,
    )
    assert replay.recorded is False
    assert len(repository.evidence) == 1
