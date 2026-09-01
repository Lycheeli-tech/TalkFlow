from datetime import UTC, datetime
from uuid import uuid4

from app.schemas import Expression, ExpressionAttempt
from app.services.mastery import MasteryEngine, ReviewScheduler


def make_expression() -> Expression:
    now = datetime.now(UTC)
    return Expression(
        id=uuid4(),
        user_id=uuid4(),
        text="naturally curious",
        meaning="curious",
        source_type="CURRICULUM",
        created_at=now,
        updated_at=now,
    )


def evidence(
    expression: Expression,
    *,
    retrieval_type: str = "RECALL",
    hint_used: bool = False,
    independent: bool = True,
    result: str = "SUCCESS",
    session_id=None,
) -> ExpressionAttempt:
    return ExpressionAttempt(
        id=uuid4(),
        expression_id=expression.id,
        attempt_id=uuid4(),
        session_id=session_id or uuid4(),
        user_id=expression.user_id,
        context="interview answer",
        retrieval_type=retrieval_type,
        hint_used=hint_used,
        independent_evidence=independent,
        usage_correct=result == "SUCCESS",
        result=result,
        created_at=datetime.now(UTC),
    )


def test_direct_hint_success_does_not_count_as_recall_or_transfer() -> None:
    expression = make_expression()
    updated = MasteryEngine().apply(
        expression, evidence(expression, hint_used=True, retrieval_type="TRANSFER")
    )
    assert updated.successful_recall == 0
    assert updated.transfer_success == 0
    assert updated.status == "NEW"


def test_mastery_requires_independent_evidence_across_both_retrieval_types() -> None:
    engine = MasteryEngine()
    expression = make_expression()
    history = []
    for _ in range(3):
        item = evidence(expression)
        expression = engine.apply(expression, item, tuple(history))
        history.append(item)
    assert expression.status == "RECALLED"
    for _ in range(2):
        item = evidence(expression, retrieval_type="TRANSFER")
        expression = engine.apply(expression, item, tuple(history))
        history.append(item)
    assert expression.status == "MASTERED"


def test_mastery_requires_three_distinct_sessions() -> None:
    engine = MasteryEngine()
    expression = make_expression()
    session_ids = [uuid4(), uuid4()]
    history = []
    for index in range(3):
        item = evidence(expression, session_id=session_ids[index % 2])
        expression = engine.apply(expression, item, tuple(history))
        history.append(item)
    for index in range(2):
        item = evidence(expression, retrieval_type="TRANSFER", session_id=session_ids[index])
        expression = engine.apply(expression, item, tuple(history))
        history.append(item)
    assert expression.status == "TRANSFERRED"

    third_session = evidence(expression, session_id=uuid4())
    expression = engine.apply(expression, third_session, tuple(history))
    assert expression.status == "MASTERED"


def test_failure_shortens_review_interval() -> None:
    expression = make_expression()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    scheduled = ReviewScheduler().next_review_at(
        expression=expression, evidence=evidence(expression, result="FAILURE"), now=now
    )
    assert scheduled == datetime(2026, 1, 2, tzinfo=UTC)
