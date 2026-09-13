from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_stage_five_has_versioned_prompts_and_separate_support_contracts() -> None:
    for prompt in (
        "course_hints_v1",
        "course_expression_materials_v1",
        "course_reference_answer_v1",
        "course_feedback_v1",
    ):
        content = source(f"backend/app/ai/prompts/{prompt}.txt")
        assert "invent" in content.casefold()
    api = source("backend/app/api/v1/courses.py")
    for endpoint in ("/hints", "/expression-materials", "/reference-answer"):
        assert endpoint in api
    assert "/{answer_id}/feedback/retry" in source("backend/app/api/v1/course_answers.py")


def test_stage_five_support_is_bounded_and_has_no_legacy_business_dependency() -> None:
    context = source("backend/app/course/context.py")
    assert "CONTEXT_EVIDENCE_CHAR_LIMIT = 10_000" in context
    assert "count=3" in context and "count=6" in context
    combined = "".join(
        source(path)
        for path in (
            "backend/app/course/context.py",
            "backend/app/course/support_entities.py",
            "backend/app/course/support_provider.py",
            "backend/app/course/support_service.py",
        )
    )
    for legacy in (
        "app.services.daily",
        "app.services.progress",
        "app.services.rewards",
        "app.services.mastery",
        "app.services.memory_gate",
        "app.repositories.memory",
        "SessionRow",
        "AttemptRow",
    ):
        assert legacy not in combined
    assert "score" not in source("backend/app/course/support_entities.py").casefold()


def test_auxiliary_panel_is_independent_from_recording_state() -> None:
    workspace = source("frontend/components/course-core/course-workspace.tsx")
    assert 'type AuxiliaryPanel = "NONE"' in workspace
    assert (
        'setState(language === "CHINESE" ? "RECORDING_CHINESE" : "RECORDING_ENGLISH")' in workspace
    )
    assert "setAuxiliaryPanel(panel)" in workspace
    assert "generateCourseHints" in workspace
    assert "retryCourseFeedback" in workspace
    assert "speechSynthesis?.cancel" in workspace
    assert "feedbackStage5" not in workspace
