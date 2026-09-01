from uuid import uuid4

import pytest

from app.services.memory_gate import MemoryGate


def test_first_error_is_candidate_until_repeated() -> None:
    gate = MemoryGate()
    pattern = gate.propose_error(
        user_id=uuid4(), pattern_type="tense", original_example="I go yesterday"
    )
    assert pattern.status == "CANDIDATE"
    assert gate.record_error_evidence(pattern, repeated=False).status == "CANDIDATE"
    assert gate.record_error_evidence(pattern, repeated=True).status == "ACTIVE"


def test_active_error_can_improve_then_resolve() -> None:
    gate = MemoryGate()
    pattern = gate.propose_error(
        user_id=uuid4(), pattern_type="article", original_example="I bought book"
    )
    pattern = gate.record_error_evidence(pattern, repeated=True)
    pattern = gate.record_error_evidence(pattern, repeated=False, corrected=True)
    assert pattern.status == "IMPROVING"
    pattern = gate.record_error_evidence(pattern, repeated=False, corrected=True)
    assert pattern.status == "RESOLVED"


def test_story_requires_explicit_confirmation() -> None:
    gate = MemoryGate()
    with pytest.raises(PermissionError):
        gate.confirm_story(
            user_id=uuid4(), title="Draft", content="Candidate", confirmed_by_user=False
        )
    story = gate.confirm_story(
        user_id=uuid4(), title="Project", content="Confirmed story", confirmed_by_user=True
    )
    assert story.confirmed_by_user is True


def test_confirmed_story_preserves_attempt_provenance() -> None:
    attempt_id = uuid4()
    story = MemoryGate().confirm_story(
        user_id=uuid4(),
        title="Incident",
        content="Confirmed",
        confirmed_by_user=True,
        source_type="ATTEMPT",
        source_attempt_id=attempt_id,
    )
    assert story.source_type == "ATTEMPT"
    assert story.source_attempt_id == attempt_id
