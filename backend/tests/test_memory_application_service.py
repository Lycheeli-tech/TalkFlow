from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.schemas import Expression, ExpressionAttempt
from app.services.memory import MemoryApplicationService


@pytest.mark.asyncio
async def test_official_write_path_validates_ownership_and_applies_mastery() -> None:
    now = datetime.now(UTC)
    expression = Expression(
        id=uuid4(),
        user_id=uuid4(),
        text="strong fit",
        meaning="good match",
        source_type="CURRICULUM",
        created_at=now,
        updated_at=now,
    )
    repository = InMemoryMemoryRepository()
    await repository.save_expression(expression)
    service = MemoryApplicationService(repository)
    evidence = ExpressionAttempt(
        id=uuid4(),
        expression_id=expression.id,
        attempt_id=uuid4(),
        session_id=uuid4(),
        user_id=expression.user_id,
        context="answer",
        retrieval_type="RECALL",
        independent_evidence=True,
        usage_correct=True,
        result="SUCCESS",
        created_at=now,
    )
    updated = await service.record_expression_evidence(evidence)
    assert updated.status == "RECALLED"
    assert len(repository.evidence) == 1


@pytest.mark.asyncio
async def test_unconfirmed_story_cannot_reach_repository() -> None:
    repository = InMemoryMemoryRepository()
    service = MemoryApplicationService(repository)
    with pytest.raises(PermissionError):
        await service.confirm_story(
            user_id=uuid4(), title="Draft", content="Candidate", confirmed_by_user=False
        )
    assert repository.stories == {}
