from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.schemas import Expression, ExpressionAttempt


def expression(user_id=None) -> Expression:
    now = datetime.now(UTC)
    return Expression(
        id=uuid4(),
        user_id=user_id or uuid4(),
        text="strong fit",
        meaning="good match",
        source_type="CURRICULUM",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_evidence_is_user_scoped() -> None:
    repo = InMemoryMemoryRepository()
    owner = expression()
    await repo.save_expression(owner)
    evidence = ExpressionAttempt(
        id=uuid4(),
        expression_id=owner.id,
        attempt_id=uuid4(),
        session_id=uuid4(),
        user_id=uuid4(),
        context="answer",
        retrieval_type="RECALL",
        independent_evidence=True,
        usage_correct=True,
        result="SUCCESS",
        created_at=datetime.now(UTC),
    )
    with pytest.raises(PermissionError):
        await repo.add_evidence(evidence)
