from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.repositories.retrieval import InMemoryRetrievalOpportunityRepository
from app.schemas import Expression, ExpressionAttempt, TrustedTransferAnalysis
from app.services.daily_attempts import DailyAttemptService
from app.services.memory import MemoryApplicationService
from app.services.retrieval import RetrievalService
from app.services.verification import VerificationService


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
        created_at=now,
        updated_at=now,
    )
    repository = InMemoryMemoryRepository(strict_provenance=True)
    memory = MemoryApplicationService(repository)
    expression = await memory.create_expression(expression)
    day1_session = uuid4()
    repository.register_session(day1_session, user_id)
    for _ in range(3):
        attempt_id = uuid4()
        repository.register_attempt(attempt_id, day1_session, user_id)
        expression = await memory.record_expression_evidence(
            ExpressionAttempt(
                id=uuid4(),
                expression_id=expression.id,
                attempt_id=attempt_id,
                session_id=day1_session,
                user_id=user_id,
                context="Day 1 recall",
                retrieval_type="RECALL",
                independent_evidence=True,
                usage_correct=True,
                result="SUCCESS",
                created_at=now,
            )
        )
    assert expression.next_review_at is not None

    day2_session, day2_attempt = uuid4(), uuid4()
    repository.register_session(day2_session, user_id)
    repository.register_attempt(day2_attempt, day2_session, user_id)
    opportunities = InMemoryRetrievalOpportunityRepository()
    opportunity = await RetrievalService(repository, opportunities).create_due_opportunity(
        user_id=user_id,
        session_id=day2_session,
        question_family="RELEVANT_EXPERIENCE",
        question_text="How does your previous experience prepare you for this role?",
        now=expression.next_review_at,
    )
    assert opportunity is not None
    assert expression.text not in opportunity.question_text
    verifier = VerificationService(opportunities=opportunities, memory=memory)
    updated = await DailyAttemptService(verifier).record_hidden_transfer(
        user_id=user_id,
        opportunity_id=opportunity.id,
        attempt_id=day2_attempt,
        session_id=day2_session,
        context=opportunity.question_text,
        analysis=TrustedTransferAnalysis(
            target_used=True,
            usage_correct=True,
            direct_hint_used=False,
            verifier_version="fixture_v1",
        ),
    )

    assert updated.transfer_success == 1
    assert updated.status == "TRANSFERRED"
    assert len(repository.evidence) == 4
