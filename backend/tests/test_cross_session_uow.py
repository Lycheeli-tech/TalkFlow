from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.repositories.retrieval import InMemoryRetrievalOpportunityRepository
from app.schemas import Expression, RetrievalOpportunity, TrustedTransferAnalysis
from app.services.cross_session_uow import InMemoryCrossSessionUnitOfWork


async def fixture():
    now, user_id, session_id, attempt_id = datetime.now(UTC), uuid4(), uuid4(), uuid4()
    memory = InMemoryMemoryRepository(strict_provenance=True)
    expression = Expression(
        id=uuid4(),
        user_id=user_id,
        text="transferable",
        meaning="usable elsewhere",
        source_type="CURRICULUM",
        created_at=now,
        updated_at=now,
    )
    await memory.save_expression(expression)
    memory.register_session(session_id, user_id)
    memory.register_attempt(
        attempt_id,
        session_id,
        user_id,
        TrustedTransferAnalysis(
            target_used=True,
            usage_correct=True,
            direct_hint_used=False,
            verifier_version="fixture_v1",
        ),
        question="How does your background prepare you for this role?",
    )
    opportunities = InMemoryRetrievalOpportunityRepository()
    opportunity = await opportunities.create(
        RetrievalOpportunity(
            id=uuid4(),
            user_id=user_id,
            expression_id=expression.id,
            session_id=session_id,
            question_family="EXPERIENCE",
            question_text="How does your background prepare you for this role?",
            created_at=now,
        )
    )
    return memory, opportunities, opportunity, attempt_id


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["after_evidence", "expression"])
async def test_failure_rolls_back_all_state_and_retry_succeeds(failure) -> None:
    memory, opportunities, opportunity, attempt_id = await fixture()
    uow = InMemoryCrossSessionUnitOfWork(memory, opportunities)
    with pytest.raises(RuntimeError):
        await uow.resolve(
            user_id=opportunity.user_id,
            opportunity_id=opportunity.id,
            attempt_id=attempt_id,
            fail_at=failure,
        )
    assert memory.evidence == {}
    assert (await opportunities.get(opportunity.id, opportunity.user_id)).status == "CREATED"
    result = await uow.resolve(
        user_id=opportunity.user_id,
        opportunity_id=opportunity.id,
        attempt_id=attempt_id,
    )
    assert result.recorded is True
    replay = await uow.resolve(
        user_id=opportunity.user_id,
        opportunity_id=opportunity.id,
        attempt_id=attempt_id,
    )
    assert replay.recorded is False
    assert len(memory.evidence) == 1


@pytest.mark.asyncio
async def test_cross_user_and_wrong_session_attempts_are_rejected() -> None:
    memory, opportunities, opportunity, _ = await fixture()
    uow = InMemoryCrossSessionUnitOfWork(memory, opportunities)

    with pytest.raises(PermissionError):
        await uow.resolve(user_id=uuid4(), opportunity_id=opportunity.id, attempt_id=uuid4())

    wrong_attempt = uuid4()
    wrong_session = uuid4()
    memory.register_session(wrong_session, opportunity.user_id)
    memory.register_attempt(
        wrong_attempt,
        wrong_session,
        opportunity.user_id,
        TrustedTransferAnalysis(
            target_used=True,
            usage_correct=True,
            direct_hint_used=False,
            verifier_version="fixture_v1",
        ),
        question="wrong session question",
    )
    with pytest.raises(PermissionError):
        await uow.resolve(
            user_id=opportunity.user_id,
            opportunity_id=opportunity.id,
            attempt_id=wrong_attempt,
        )

    assert memory.evidence == {}
    assert (await opportunities.get(opportunity.id, opportunity.user_id)).status == "CREATED"
