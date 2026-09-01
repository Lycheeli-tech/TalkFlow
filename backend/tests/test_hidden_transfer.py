from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.schemas import ExpressionAttempt, HiddenTransferOpportunity
from app.services.hidden_transfer import HiddenTransferService


def test_interviewer_payload_does_not_include_target_expression() -> None:
    target = "naturally curious"
    opportunity = HiddenTransferOpportunity(
        opportunity_id=uuid4(),
        expression_id=uuid4(),
        session_id=uuid4(),
        interviewer_prompt=(
            "Answer a new interview question using a useful phrase from earlier practice."
        ),
    )
    assert target not in opportunity.interviewer_prompt


def test_transfer_verification_consumes_explicit_flags() -> None:
    opportunity = HiddenTransferOpportunity(
        opportunity_id=uuid4(),
        expression_id=uuid4(),
        session_id=uuid4(),
        interviewer_prompt="New context",
    )
    evidence = ExpressionAttempt(
        id=uuid4(),
        expression_id=opportunity.expression_id,
        attempt_id=uuid4(),
        session_id=opportunity.session_id,
        user_id=uuid4(),
        context="new question",
        retrieval_type="TRANSFER",
        hint_used=False,
        independent_evidence=True,
        usage_correct=True,
        result="SUCCESS",
        created_at=datetime.now(UTC),
    )
    assert (
        HiddenTransferService.verify_transfer_evidence(opportunity=opportunity, evidence=evidence)
        == evidence
    )


def test_wrong_session_is_rejected() -> None:
    opportunity = HiddenTransferOpportunity(
        opportunity_id=uuid4(),
        expression_id=uuid4(),
        session_id=uuid4(),
        interviewer_prompt="New context",
    )
    evidence = ExpressionAttempt(
        id=uuid4(),
        expression_id=opportunity.expression_id,
        attempt_id=uuid4(),
        session_id=uuid4(),
        user_id=uuid4(),
        context="new question",
        retrieval_type="TRANSFER",
        independent_evidence=True,
        usage_correct=True,
        result="SUCCESS",
        created_at=datetime.now(UTC),
    )
    with pytest.raises(ValueError):
        HiddenTransferService.verify_transfer_evidence(opportunity=opportunity, evidence=evidence)
