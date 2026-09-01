import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from app.domain.learning import (
    MVP_MASTERY_POLICY,
    Expression,
    ExpressionAttemptEvidence,
    ExpressionStatus,
    MasteryEngine,
    RetrievalType,
)
from app.repositories.learning import InMemoryLearningRepository
from app.services.learning_loop import LearningLoopService


@pytest.fixture
def day1_day2_case() -> dict[str, Any]:
    fixture_path = Path(__file__).parent / "fixtures" / "day1_day2_slice.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


async def test_day1_to_day2_cross_session_learning_loop(day1_day2_case: dict[str, Any]) -> None:
    user_id = UUID(day1_day2_case["user_id"])
    expression_id = UUID(day1_day2_case["expression_id"])
    day1 = day1_day2_case["day1"]
    day2 = day1_day2_case["day2"]
    repository = InMemoryLearningRepository()

    day1_service = LearningLoopService(repository)
    day1_progress = await day1_service.learn_and_recall(
        expression=Expression(
            id=expression_id,
            user_id=user_id,
            text=day1["expression"],
            status=ExpressionStatus.NEW,
        ),
        session_id=UUID(day1["session_id"]),
        evidence_id=UUID(day1["evidence_id"]),
        context=day1["context"],
        occurred_at=datetime.fromisoformat(day1["occurred_at"]),
    )

    assert day1_progress.expression.status is ExpressionStatus.RECALLED
    assert day1_progress.expression.successful_recall == 1
    assert day1_progress.expression.next_review_at == datetime.fromisoformat(day2["occurred_at"])
    assert day1_progress.recap_message is None

    day2_service = LearningLoopService(repository)
    opportunity = await day2_service.create_hidden_transfer_opportunity(
        user_id=user_id,
        session_id=UUID(day2["session_id"]),
        question=day2["question"],
        due_at=datetime.fromisoformat(day2["occurred_at"]),
    )
    assert day1["expression"].casefold() not in opportunity.question.casefold()

    day2_progress = await day2_service.record_transfer(
        user_id=user_id,
        opportunity=opportunity,
        evidence_id=UUID(day2["evidence_id"]),
        context=day2["answer"],
        occurred_at=datetime.fromisoformat(day2["occurred_at"]),
        hint_used=False,
        usage_correct=True,
        independently_retrieved=True,
    )

    assert day2_progress.expression.status is ExpressionStatus.TRANSFERRED
    assert day2_progress.expression.transfer_success == 1
    assert day2_progress.expression.next_review_at == datetime.fromisoformat(
        day2["occurred_at"]
    ) + timedelta(days=3)
    assert day2_progress.expression.successful_session_ids == {
        UUID(day1["session_id"]),
        UUID(day2["session_id"]),
    }
    assert day2_progress.evidence_count == 2
    assert day2_progress.recap_message is not None
    assert day2_progress.expression.status is not ExpressionStatus.MASTERED
    assert day2_progress.expression.policy_version == MVP_MASTERY_POLICY.version

    evidence = await repository.list_evidence(expression_id, user_id)
    assert [item.retrieval_type for item in evidence] == [
        RetrievalType.RECALL,
        RetrievalType.TRANSFER,
    ]


async def test_hidden_target_guard_rejects_literal_leak(day1_day2_case: dict[str, Any]) -> None:
    user_id = UUID(day1_day2_case["user_id"])
    day1 = day1_day2_case["day1"]
    day2 = day1_day2_case["day2"]
    repository = InMemoryLearningRepository()
    service = LearningLoopService(repository)
    await service.learn_and_recall(
        expression=Expression(
            id=UUID(day1_day2_case["expression_id"]),
            user_id=user_id,
            text=day1["expression"],
            status=ExpressionStatus.NEW,
        ),
        session_id=UUID(day1["session_id"]),
        evidence_id=UUID(day1["evidence_id"]),
        context=day1["context"],
        occurred_at=datetime.fromisoformat(day1["occurred_at"]),
    )
    with pytest.raises(ValueError, match="leaked"):
        await service.create_hidden_transfer_opportunity(
            user_id=user_id,
            session_id=UUID(day2["session_id"]),
            question=f"Which skill is {day1['expression']}?",
            due_at=datetime.fromisoformat(day2["occurred_at"]),
        )


async def test_direct_hint_records_evidence_without_qualifying_as_transfer(
    day1_day2_case: dict[str, Any],
) -> None:
    user_id = UUID(day1_day2_case["user_id"])
    day1 = day1_day2_case["day1"]
    day2 = day1_day2_case["day2"]
    repository = InMemoryLearningRepository()
    service = LearningLoopService(repository)
    await service.learn_and_recall(
        expression=Expression(
            id=UUID(day1_day2_case["expression_id"]),
            user_id=user_id,
            text=day1["expression"],
            status=ExpressionStatus.NEW,
        ),
        session_id=UUID(day1["session_id"]),
        evidence_id=UUID(day1["evidence_id"]),
        context=day1["context"],
        occurred_at=datetime.fromisoformat(day1["occurred_at"]),
    )
    opportunity = await service.create_hidden_transfer_opportunity(
        user_id=user_id,
        session_id=UUID(day2["session_id"]),
        question=day2["question"],
        due_at=datetime.fromisoformat(day2["occurred_at"]),
    )
    progress = await service.record_transfer(
        user_id=user_id,
        opportunity=opportunity,
        evidence_id=UUID(day2["evidence_id"]),
        context=day2["answer"],
        occurred_at=datetime.fromisoformat(day2["occurred_at"]),
        hint_used=True,
        usage_correct=True,
        independently_retrieved=False,
    )

    assert progress.expression.status is ExpressionStatus.RECALLED
    assert progress.expression.transfer_success == 0
    assert progress.evidence_count == 2
    assert progress.expression.next_review_at == datetime.fromisoformat(
        day2["occurred_at"]
    ) + timedelta(days=1)


def test_versioned_mvp_policy_requires_full_cross_session_evidence() -> None:
    user_id = UUID(int=1)
    expression = Expression(
        id=UUID(int=2),
        user_id=user_id,
        text="highly transferable",
        status=ExpressionStatus.LEARNING,
    )
    attempts = [
        (RetrievalType.RECALL, UUID(int=11)),
        (RetrievalType.RECALL, UUID(int=12)),
        (RetrievalType.RECALL, UUID(int=13)),
        (RetrievalType.TRANSFER, UUID(int=12)),
        (RetrievalType.TRANSFER, UUID(int=13)),
    ]
    engine = MasteryEngine(MVP_MASTERY_POLICY)

    assert MVP_MASTERY_POLICY.version == "mvp-1"
    assert MVP_MASTERY_POLICY.review_intervals_days == (1, 3, 7, 14)
    for index, (retrieval_type, session_id) in enumerate(attempts, start=1):
        expression = engine.apply(
            expression,
            ExpressionAttemptEvidence(
                id=UUID(int=100 + index),
                expression_id=expression.id,
                user_id=user_id,
                session_id=session_id,
                retrieval_type=retrieval_type,
                context="fixture evidence",
                hint_used=False,
                usage_correct=True,
                independently_retrieved=True,
                created_at=datetime(2026, 9, index, tzinfo=UTC),
            ),
        )
        if index < len(attempts):
            assert expression.status is not ExpressionStatus.MASTERED

    assert expression.status is ExpressionStatus.MASTERED
