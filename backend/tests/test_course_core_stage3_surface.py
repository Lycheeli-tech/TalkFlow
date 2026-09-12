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
    for mechanism in ("automaticNext", "current_day", "current_phase", "mastery", "streak", "XP"):
        assert mechanism not in workspace


def test_recording_guard_audio_exclusion_and_final_transcript_are_explicit() -> None:
    workspace = source("frontend/components/course-core/course-workspace.tsx")
    assert 'window.addEventListener("beforeunload"' in workspace
    assert 'window.addEventListener("popstate"' in workspace
    assert "navigationBlocked={recording}" in workspace
    assert "stopAudio();" in workspace
    assert 'recorder.addEventListener("stop"' in workspace
    assert "answer.transcript.transcript" in workspace


def test_stage_three_does_not_enable_chinese_feedback_or_other_courses() -> None:
    workspace = source("frontend/components/course-core/course-workspace.tsx")
    flags = source("frontend/lib/course-core-flags.ts")
    assert "answerInChinese" in workspace
    assert "disabled" in workspace
    assert "feedbackStage5" in workspace
    assert "practice: false" in flags
    assert "aboutMe: false" in flags
