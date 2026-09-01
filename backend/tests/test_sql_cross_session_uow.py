from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.db.models import AttemptRow, ExpressionAttemptRow, ExpressionRow, RetrievalOpportunityRow
from app.services.cross_session_uow import SQLCrossSessionUnitOfWork


class ScalarRows:
    def all(self) -> list[ExpressionAttemptRow]:
        return []


class FakeAsyncSession:
    def __init__(self, scalar_values: list[object], *, fail_commit: bool = False) -> None:
        self.scalar_values = scalar_values
        self.fail_commit = fail_commit
        self.added: list[object] = []
        self.commit_count = 0
        self.rollback_count = 0

    async def scalar(self, statement) -> object:
        return self.scalar_values.pop(0)

    async def scalars(self, statement) -> ScalarRows:
        return ScalarRows()

    def add(self, value: object) -> None:
        self.added.append(value)

    async def commit(self) -> None:
        self.commit_count += 1
        if self.fail_commit:
            raise RuntimeError("simulated database commit failure")

    async def rollback(self) -> None:
        self.rollback_count += 1


def sql_fixture(*, fail_commit: bool = False):
    now = datetime.now(UTC)
    user_id, session_id, attempt_id, expression_id, opportunity_id = (
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
    )
    question = "How does your previous experience prepare you for this role?"
    opportunity = RetrievalOpportunityRow(
        id=opportunity_id,
        user_id=user_id,
        expression_id=expression_id,
        session_id=session_id,
        question_family="RELEVANT_EXPERIENCE",
        question_text=question,
        retrieval_type="TRANSFER",
        status="CREATED",
        created_at=now,
        consumed_at=None,
    )
    expression = ExpressionRow(
        id=expression_id,
        user_id=user_id,
        text="highly transferable",
        meaning="useful in another context",
        source_type="CURRICULUM",
        source_id=None,
        status="RECALLED",
        successful_recall=3,
        failed_recall=0,
        transfer_success=0,
        next_review_at=now,
        created_at=now,
        updated_at=now,
    )
    attempt = AttemptRow(
        id=attempt_id,
        session_id=session_id,
        user_id=user_id,
        question=question,
        question_type="RELEVANT_EXPERIENCE",
        audio_path="private/test.webm",
        audio_content_type="audio/webm",
        response_duration_ms=1000,
        transcript="My prior experience is highly transferable to this role.",
        analysis={
            "target_used": True,
            "usage_correct": True,
            "direct_hint_used": False,
            "verifier_version": "fixture_v1",
        },
        status="ANALYZED",
        provider_error=None,
        stt_provider="fake",
        analyzer_version="fixture_v1",
        created_at=now,
        updated_at=now,
    )
    daily_session = object()
    session = FakeAsyncSession(
        [opportunity, expression, daily_session, attempt], fail_commit=fail_commit
    )
    return session, opportunity, expression, attempt


@pytest.mark.asyncio
async def test_sql_uow_stages_all_changes_and_commits_once() -> None:
    session, opportunity, expression, attempt = sql_fixture()

    result = await SQLCrossSessionUnitOfWork(session).resolve(
        user_id=opportunity.user_id,
        opportunity_id=opportunity.id,
        attempt_id=attempt.id,
    )

    assert result.recorded is True
    assert session.commit_count == 1
    assert session.rollback_count == 0
    assert opportunity.status == "CONSUMED"
    assert opportunity.consumed_at is not None
    assert expression.transfer_success == 1
    assert len(session.added) == 1
    evidence = session.added[0]
    assert isinstance(evidence, ExpressionAttemptRow)
    assert evidence.retrieval_opportunity_id == opportunity.id
    assert evidence.attempt_id == attempt.id


@pytest.mark.asyncio
async def test_sql_uow_rolls_back_when_the_single_commit_fails() -> None:
    session, opportunity, _, attempt = sql_fixture(fail_commit=True)

    with pytest.raises(RuntimeError, match="commit failure"):
        await SQLCrossSessionUnitOfWork(session).resolve(
            user_id=opportunity.user_id,
            opportunity_id=opportunity.id,
            attempt_id=attempt.id,
        )

    assert session.commit_count == 1
    assert session.rollback_count == 1
