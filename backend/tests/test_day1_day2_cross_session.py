from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.schemas import Expression, ExpressionAttempt
from app.services.daily_attempts import DailyAttemptService
from app.services.hidden_transfer import HiddenTransferService
from app.services.memory import MemoryApplicationService
from app.services.retrieval import RetrievalService


@pytest.mark.asyncio
async def test_day_one_learning_reappears_as_day_two_hidden_transfer() -> None:
    now = datetime.now(UTC)
    user_id = uuid4()
    expression = Expression(
        id=uuid4(),
        user_id=user_id,
        text="transition into AI",
        meaning="change fields",
        source_type="CURRICULUM",
        successful_recall=3,
        status="RECALLED",
        next_review_at=now - timedelta(minutes=1),
        created_at=now,
        updated_at=now,
    )
    repository = InMemoryMemoryRepository()
    await repository.save_expression(expression)

    opportunities = await RetrievalService(repository).due_opportunities(user_id=user_id, now=now)
    assert len(opportunities) == 1
    hidden = HiddenTransferService().create_opportunity(
        opportunity=opportunities[0], session_id=uuid4()
    )
    assert expression.text not in hidden.interviewer_prompt

    evidence = ExpressionAttempt(
        id=uuid4(),
        expression_id=expression.id,
        attempt_id=uuid4(),
        session_id=hidden.session_id,
        user_id=user_id,
        context="Why are you changing careers?",
        retrieval_type="TRANSFER",
        hint_used=False,
        independent_evidence=True,
        usage_correct=True,
        result="SUCCESS",
        created_at=now,
    )
    updated = await DailyAttemptService(
        MemoryApplicationService(repository)
    ).record_hidden_transfer(opportunity=hidden, evidence=evidence)

    assert updated.transfer_success == 1
    assert updated.status == "TRANSFERRED"
    assert len(repository.evidence) == 1
