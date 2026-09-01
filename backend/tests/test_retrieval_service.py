from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.repositories.retrieval import InMemoryRetrievalOpportunityRepository
from app.schemas import Expression
from app.services.retrieval import RetrievalService


def make_expression(user_id, *, status="RECALLED", due=True) -> Expression:
    now = datetime.now(UTC)
    return Expression(
        id=uuid4(),
        user_id=user_id,
        text="hidden target",
        meaning="useful phrase",
        source_type="CURRICULUM",
        status=status,
        next_review_at=now - timedelta(minutes=1) if due else now + timedelta(days=1),
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_due_retrieval_is_user_scoped_and_does_not_expose_target_text() -> None:
    owner, stranger = uuid4(), uuid4()
    repository = InMemoryMemoryRepository()
    await repository.save_expression(make_expression(owner))
    await repository.save_expression(make_expression(stranger))
    await repository.save_expression(make_expression(owner, status="MASTERED"))
    await repository.save_expression(make_expression(owner, due=False))

    opportunities = InMemoryRetrievalOpportunityRepository()
    result = await RetrievalService(repository, opportunities).create_due_opportunity(
        user_id=owner,
        session_id=uuid4(),
        question_family="RELEVANT_EXPERIENCE",
        question_text="How does your previous experience prepare you for this role?",
    )

    assert result is not None
    assert result.user_id == owner
    assert "hidden target" not in result.question_text


@pytest.mark.asyncio
async def test_meta_hint_is_rejected() -> None:
    owner = uuid4()
    memory = InMemoryMemoryRepository()
    await memory.save_expression(make_expression(owner))
    with pytest.raises(ValueError):
        await RetrievalService(
            memory, InMemoryRetrievalOpportunityRepository()
        ).create_due_opportunity(
            user_id=owner,
            session_id=uuid4(),
            question_family="EXPERIENCE",
            question_text="Use a phrase from earlier practice.",
        )
