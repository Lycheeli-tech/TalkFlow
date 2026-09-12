import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def source(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")


def test_stage_three_rollout_is_generic_and_limited_to_course_eleven() -> None:
    backend_rollout = source("backend/app/course/rollout.py")
    frontend_rollout = source("frontend/lib/course-core-flags.ts")
    service = source("backend/app/course/answer_service.py")

    assert 'frozenset({"course-11"})' in backend_rollout
    assert 'new Set(["course-11"])' in frontend_rollout
    assert 'course_id == "course-11"' not in service


def test_course_workspace_has_required_p3_states_and_no_later_stage_mechanisms() -> None:
    workspace = source("frontend/components/course-core/course-workspace.tsx")
    for state in (
        "PREPARING",
        "RECORDING_ENGLISH",
        "PROCESSING_ENGLISH",
        "ANSWER_SAVED",
        "RECOVERABLE_FAILURE",
    ):
        assert state in workspace
    for mechanism in ("automaticNext", "current_day", "current_phase", "mastery", "streak"):
        assert mechanism not in workspace
    assert re.search(r"\bXP\b", workspace) is None


def test_recording_guard_audio_exclusion_and_final_transcript_are_explicit() -> None:
    workspace = source("frontend/components/course-core/course-workspace.tsx")
    assert 'window.addEventListener("beforeunload"' in workspace
    assert 'window.addEventListener("popstate"' in workspace
    assert "navigationBlocked={recording}" in workspace
    assert "stopAudio();" in workspace
    assert 'recorder.addEventListener("stop"' in workspace
    assert "answer.transcript.transcript" in workspace


def test_stage_five_keeps_chinese_and_other_course_rollout_disabled() -> None:
    workspace = source("frontend/components/course-core/course-workspace.tsx")
    flags = source("frontend/lib/course-core-flags.ts")
    assert "answerInChinese" in workspace
    assert "disabled" in workspace
    assert "retryCourseFeedback" in workspace
    assert "practice: false" in flags
