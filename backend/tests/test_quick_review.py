from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.schemas import Expression
from app.services.quick_review import QuickReviewService


@pytest.mark.asyncio
async def test_quick_review_is_due_sorted_and_user_scoped() -> None:
    now = datetime.now(UTC)
    user_id, other_user = uuid4(), uuid4()
    repository = InMemoryMemoryRepository()
    due_later = Expression(
        id=uuid4(),
        user_id=user_id,
        text="later",
        meaning="later meaning",
        source_type="CURRICULUM",
        next_review_at=now - timedelta(hours=1),
        created_at=now,
        updated_at=now,
    )
    due_first = due_later.model_copy(
        update={"id": uuid4(), "text": "first", "next_review_at": now - timedelta(days=1)}
    )
    hidden = due_later.model_copy(update={"id": uuid4(), "user_id": other_user})
    for item in (due_later, due_first, hidden):
        await repository.save_expression(item)

    result = await QuickReviewService(repository).list_due(user_id, now=now)

    assert [item.text for item in result] == ["first", "later"]
    assert all(item.expression_id != hidden.id for item in result)


@pytest.mark.asyncio
async def test_quick_review_rejects_unbounded_limit() -> None:
    with pytest.raises(ValueError):
        await QuickReviewService(InMemoryMemoryRepository()).list_due(uuid4(), limit=0)
