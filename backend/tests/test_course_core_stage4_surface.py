from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_about_me_is_enabled_without_becoming_a_course_gate() -> None:
    flags = source("frontend/lib/course-core-flags.ts")
    page = source("frontend/components/course-core/about-me-page.tsx")
    course = source("frontend/components/course-core/course-workspace.tsx")
    assert "aboutMe: true" in flags
    for feature in ("target_roles", "resumes", "supplemental_facts", "memories"):
        assert feature in source("frontend/lib/about-me-api.ts")
    assert "About Me is optional" not in course
    assert "getAboutMe" not in course
    assert "deleteAboutMeItem" in page


def test_answer_deletion_and_memory_cleanup_are_explicit_and_no_legacy_is_imported() -> None:
    repository = source("backend/app/course/repository.py")
    workspace = source("frontend/components/course-core/course-workspace.tsx")
    assert "course_audio_cleanup_jobs" in repository
    assert "source_type = 'COURSE_ANSWER'" in repository
    assert "not exists (select 1 from public.memory_sources" in repository
    assert "deleteCourseAnswer" in workspace
    combined = "".join(
        source(path)
        for path in (
            "backend/app/about_me/repository.py",
            "backend/app/about_me/service.py",
            "backend/app/api/v1/about_me.py",
        )
    )
    for legacy in (
        "app.services.memory",
        "app.services.memory_gate",
        "app.repositories.memory",
        "app.repositories.profiles",
        "SessionRow",
        "AttemptRow",
    ):
        assert legacy not in combined
