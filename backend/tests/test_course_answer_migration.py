from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = REPOSITORY_ROOT / "supabase/migrations/202609120012_course_answers.sql"
WRITE_BOUNDARY_MIGRATION = (
    REPOSITORY_ROOT / "supabase/migrations/202609120013_course_answer_write_boundary.sql"
)


def test_course_answer_migration_has_new_tables_constraints_indexes_and_rls() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    for table in ("course_answers", "course_transcripts", "course_feedback"):
        assert f"create table public.{table}" in sql
        assert f"alter table public.{table} enable row level security" in sql
        assert "auth.uid()) = user_id" in sql

    assert "unique (user_id, idempotency_key)" in sql
    assert "course_answers_history_idx" in sql
    assert "course_answers_audio_retention_idx" in sql
    assert "course_answers_failed_expiry_idx" in sql
    assert "course_answer_saved_sequence" in sql
    assert "course_id <> 'course-30'" in sql
    assert "references public.sessions" not in sql
    assert "references public.attempts" not in sql
    assert "interval" not in sql
    assert "for select" in sql
    assert "grant select, insert" not in sql

    write_boundary = WRITE_BOUNDARY_MIGRATION.read_text(encoding="utf-8").lower()
    assert 'drop policy if exists "users manage their own course answers"' in write_boundary
    assert "revoke insert, update, delete" in write_boundary
    assert "for select" in write_boundary


def test_failed_audio_ttl_is_a_versioned_application_policy_not_a_hidden_sql_default() -> None:
    service = (REPOSITORY_ROOT / "backend/app/course/answer_service.py").read_text(encoding="utf-8")
    decisions = (REPOSITORY_ROOT / "docs/DECISIONS.md").read_text(encoding="utf-8")
    assert "FAILED_AUDIO_TTL = timedelta(days=3)" in service
    assert "ADR-028 — Three-Day Failed Answer Audio Retention" in decisions
