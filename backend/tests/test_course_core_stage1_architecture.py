import ast
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app as default_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FREEZE_MANIFEST_PATH = REPOSITORY_ROOT / "architecture" / "legacy_freeze_v1.json"


def load_freeze_manifest() -> dict[str, object]:
    return json.loads(FREEZE_MANIFEST_PATH.read_text(encoding="utf-8"))


def iter_python_files(relative_roots: list[str]):
    for relative_root in relative_roots:
        root = REPOSITORY_ROOT / relative_root
        if root.is_file() and root.suffix == ".py":
            yield root
        elif root.is_dir():
            yield from root.rglob("*.py")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def iter_frontend_source_files(relative_roots: list[str]):
    for relative_root in relative_roots:
        root = REPOSITORY_ROOT / relative_root
        if root.is_file() and root.suffix in {".ts", ".tsx"}:
            yield root
        elif root.is_dir():
            for suffix in ("*.ts", "*.tsx"):
                yield from root.rglob(suffix)


def test_default_runtime_mounts_no_legacy_product_routes(client: TestClient) -> None:
    manifest = load_freeze_manifest()
    legacy_prefixes = manifest["legacy_route_prefixes"]

    api_paths = {
        path: frozenset(methods)
        for path, methods in default_app.openapi()["paths"].items()
        if path.startswith("/api/v1")
    }

    assert api_paths == {"/api/v1/health": frozenset({"get"})}
    for prefix in legacy_prefixes:
        assert client.get(prefix).status_code == 404


def test_stage_one_runtime_exposes_no_product_write_path() -> None:
    write_methods = {"POST", "PUT", "PATCH", "DELETE"}
    product_writes = [
        (path, method.upper())
        for path, methods in default_app.openapi()["paths"].items()
        if path.startswith("/api/v1")
        for method in methods
        if method.upper() in write_methods
    ]

    assert product_writes == []


def test_frozen_legacy_files_match_the_approved_baseline() -> None:
    manifest = load_freeze_manifest()
    frozen_files = manifest["frozen_files"]

    mismatches = []
    for relative_path, expected_hash in frozen_files.items():
        path = REPOSITORY_ROOT / relative_path
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"
        if actual_hash != expected_hash:
            mismatches.append(f"{relative_path}: {actual_hash}")

    assert mismatches == [], (
        "Frozen Legacy files changed without an approved exception record:\n"
        + "\n".join(mismatches)
    )


def test_new_backend_modules_cannot_import_legacy_business_modules() -> None:
    manifest = load_freeze_manifest()
    roots = list(manifest["new_backend_roots"])
    roots.extend(
        [
            "backend/app/api/v1/courses.py",
            "backend/app/api/v1/about_me.py",
            "backend/app/api/v1/practice_v2.py",
        ]
    )
    forbidden_prefixes = manifest["forbidden_backend_import_prefixes"]
    violations = []

    for path in iter_python_files(roots):
        for imported in imported_modules(path):
            if any(imported.startswith(prefix) for prefix in forbidden_prefixes):
                violations.append(f"{path.relative_to(REPOSITORY_ROOT)} imports {imported}")

    assert violations == [], "Course Core imports frozen Legacy code:\n" + "\n".join(violations)


def test_new_frontend_modules_cannot_import_legacy_components_or_client() -> None:
    manifest = load_freeze_manifest()
    forbidden_imports = manifest["forbidden_frontend_imports"]
    violations = []

    for path in iter_frontend_source_files(manifest["new_frontend_roots"]):
        source = path.read_text(encoding="utf-8")
        for forbidden in forbidden_imports:
            if forbidden in source:
                violations.append(f"{path.relative_to(REPOSITORY_ROOT)} imports {forbidden}")

    assert violations == [], "Course Core imports frozen Legacy frontend code:\n" + "\n".join(
        violations
    )


def test_stage_one_entry_bypasses_legacy_gates_and_old_pages_redirect() -> None:
    home = (REPOSITORY_ROOT / "frontend/app/page.tsx").read_text(encoding="utf-8")
    entry = (REPOSITORY_ROOT / "frontend/components/course-core/stage-one-entry.tsx").read_text(
        encoding="utf-8"
    )

    assert "StageOneEntry" in home
    assert "getApplicationEntry" not in entry
    assert "@/lib/api" not in entry
    assert "fetch(" not in entry
    for legacy_name in ("OnboardingFlow", "VoiceCalibration", "TodaySession"):
        assert legacy_name not in home
        assert legacy_name not in entry

    for relative_path in (
        "frontend/app/practice/page.tsx",
        "frontend/app/journey/page.tsx",
        "frontend/app/my-english/page.tsx",
    ):
        source = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
        assert 'redirect("/")' in source
        assert "@/components/" not in source
