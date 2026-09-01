from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.schemas import Expression, ExpressionAttempt, HiddenTransferOpportunity
from app.services.daily_attempts import DailyAttemptService
from app.services.memory import MemoryApplicationService


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
    repository = InMemoryMemoryRepository()
    await repository.save_expression(expression)
    opportunity = HiddenTransferOpportunity(
        expression_id=expression.id, session_id=uuid4(), interviewer_prompt="New context"
    )
    evidence = ExpressionAttempt(
        id=uuid4(),
        expression_id=expression.id,
        attempt_id=uuid4(),
        session_id=opportunity.session_id,
        user_id=expression.user_id,
        context="new interview answer",
        retrieval_type="TRANSFER",
        hint_used=False,
        independent_evidence=True,
        usage_correct=True,
        result="SUCCESS",
        created_at=now,
    )

    updated = await DailyAttemptService(
        MemoryApplicationService(repository)
    ).record_hidden_transfer(opportunity=opportunity, evidence=evidence)

    assert updated.transfer_success == 1
    assert len(repository.evidence) == 1
