from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.repositories.memory import InMemoryMemoryRepository
from app.schemas import ErrorPattern, Expression, Story
from app.services.memory import MemoryApplicationService


@pytest.mark.asyncio
async def test_my_english_is_user_scoped_and_only_includes_confirmed_stories() -> None:
    now, user_id, other_user = datetime.now(UTC), uuid4(), uuid4()
    repository = InMemoryMemoryRepository()
    await repository.save_expression(
        Expression(
            id=uuid4(),
            user_id=user_id,
            text="relevant",
            meaning="related",
            source_type="CURRICULUM",
            created_at=now,
            updated_at=now,
        )
    )
    await repository.save_expression(
        Expression(
            id=uuid4(),
            user_id=other_user,
            text="private",
            meaning="private",
            source_type="CURRICULUM",
            created_at=now,
            updated_at=now,
        )
    )
    await repository.save_error_pattern(
        ErrorPattern(
            id=uuid4(),
            user_id=user_id,
            pattern_type="tense",
            original_example="I go yesterday",
            first_seen=now,
            last_seen=now,
        )
    )
    await repository.save_story(
        Story(
            id=uuid4(),
            user_id=user_id,
            title="Project",
            content="A confirmed project story",
            confirmed_by_user=True,
            created_at=now,
            updated_at=now,
        )
    )

    result = await MemoryApplicationService(repository).my_english(user_id)

    assert [item.text for item in result.expressions] == ["relevant"]
    assert [item.pattern_type for item in result.patterns] == ["tense"]
    assert [item.title for item in result.stories] == ["Project"]
