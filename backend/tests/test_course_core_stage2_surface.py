from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def source(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")


def test_new_app_shell_exposes_three_equal_entries_without_legacy_navigation() -> None:
    home = source("frontend/components/course-core/course-core-home.tsx")
    shell = source("frontend/components/course-core/app-shell.tsx")

    assert home.count("entryCard") == 1
    for label in ("copy.courses", "copy.practice", "copy.aboutMe"):
        assert label in home
        assert label in shell
    for legacy_label in ("Today", "Journey", "Quick Review", "My English"):
        assert legacy_label not in home
        assert legacy_label not in shell


def test_unfinished_entries_are_isolated_by_explicit_feature_flags() -> None:
    flags = source("frontend/lib/course-core-flags.ts")
    assert "courses: true" in flags
    assert "practice: false" in flags
    assert "aboutMe: false" in flags

    assert 'feature="practice"' in source("frontend/app/practice/page.tsx")
    assert 'feature="aboutMe"' in source("frontend/app/about-me/page.tsx")


def test_stage_two_route_boundaries_and_legacy_redirects_exist() -> None:
    expected_routes = (
        "frontend/app/page.tsx",
        "frontend/app/courses/page.tsx",
        "frontend/app/courses/[courseId]/page.tsx",
        "frontend/app/practice/page.tsx",
        "frontend/app/about-me/page.tsx",
    )
    assert all((REPOSITORY_ROOT / route).is_file() for route in expected_routes)

    for route in ("frontend/app/journey/page.tsx", "frontend/app/my-english/page.tsx"):
        assert 'redirect("/")' in source(route)


def test_course_frontend_uses_only_the_dedicated_read_only_catalog_client() -> None:
    catalog = source("frontend/components/course-core/course-catalog.tsx")
    detail = source("frontend/components/course-core/course-detail.tsx")
    client = source("frontend/lib/course-api.ts")

    assert "@/lib/course-api" in catalog
    assert "@/lib/course-api" in detail
    assert "@/lib/api" not in catalog + detail + client
    for write_method in ('method: "POST"', 'method: "PATCH"', 'method: "DELETE"'):
        assert write_method not in client
