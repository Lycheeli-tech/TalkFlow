from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import ErrorPattern, ExpressionAttempt, MasteryRules, Story


def test_evidence_contract_captures_independence_and_links() -> None:
    now = datetime.now(UTC)
    evidence = ExpressionAttempt(
        id=uuid4(),
        expression_id=uuid4(),
        attempt_id=uuid4(),
        session_id=uuid4(),
        user_id=uuid4(),
        context="Why are you changing roles?",
        retrieval_type="TRANSFER",
        hint_used=True,
        independent_evidence=False,
        usage_correct=True,
        result="SUCCESS",
        created_at=now,
    )
    assert evidence.hint_used is True
    assert evidence.independent_evidence is False
    assert evidence.retrieval_type == "TRANSFER"


def test_mastery_rules_are_versioned_defaults() -> None:
    rules = MasteryRules()
    assert rules.version == "mastery_rules_v1"
    assert (
        rules.recall_successes_required,
        rules.transfer_successes_required,
        rules.sessions_required,
    ) == (3, 2, 3)
    assert rules.review_intervals_days == [1, 3, 7, 14]


def test_error_pattern_starts_as_candidate_and_story_requires_confirmation() -> None:
    now = datetime.now(UTC)
    pattern = ErrorPattern(
        id=uuid4(),
        user_id=uuid4(),
        pattern_type="tense",
        original_example="I go yesterday",
        first_seen=now,
        last_seen=now,
    )
    assert pattern.status == "CANDIDATE"
    with pytest.raises(ValidationError):
        Story(
            id=uuid4(),
            user_id=uuid4(),
            title="Candidate",
            content="Draft",
            confirmed_by_user=False,
            created_at=now,
            updated_at=now,
        )
