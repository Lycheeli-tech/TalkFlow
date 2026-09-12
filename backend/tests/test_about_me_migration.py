from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/migrations/202609120014_about_me_memory.sql"
INVARIANT = ROOT / "supabase/migrations/202609120015_memory_source_invariant.sql"
INVARIANT_FIX = ROOT / "supabase/migrations/202609120016_fix_memory_source_invariant_trigger.sql"
CASCADE_FIX = ROOT / "supabase/migrations/202609120017_allow_user_cascade_memory_cleanup.sql"
SECURITY_FIX = ROOT / "supabase/migrations/202609120018_memory_invariant_security_definer.sql"
DOCUMENT_CLEANUP = ROOT / "supabase/migrations/202609120019_resume_cleanup_jobs.sql"


def test_p4_migration_has_isolated_tables_rls_sources_and_write_boundary() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    for table in (
        "about_me_profiles",
        "target_roles",
        "memory_items",
        "memory_sources",
        "course_audio_cleanup_jobs",
    ):
        assert f"create table public.{table}" in sql
        assert f"alter table public.{table} enable row level security" in sql
    for source_type in ("profile", "source_document", "user_input", "course_answer"):
        assert source_type in sql
    assert "memory_sources_item_owner_fk" in sql
    assert "revoke insert, update, delete" in sql
    assert "references public.sessions" not in sql
    assert "references public.attempts" not in sql


def test_memory_prompt_is_versioned_and_forbids_fabrication() -> None:
    prompt = (ROOT / "backend/app/ai/prompts/memory_decision_v1.txt").read_text(encoding="utf-8")
    assert "CREATE, UPDATE, MERGE, or IGNORE" in prompt
    assert "Never infer" in prompt
    assert "exact" in prompt


def test_database_defers_but_enforces_the_no_source_less_memory_invariant() -> None:
    sql = INVARIANT.read_text(encoding="utf-8").lower()
    assert "constraint trigger memory_items_require_source" in sql
    assert "constraint trigger memory_source_removal_keeps_item_sourced" in sql
    assert "deferrable initially deferred" in sql
    assert "must have at least one source" in sql
    fix = INVARIANT_FIX.read_text(encoding="utf-8").lower()
    assert "create or replace function public.assert_memory_item_has_source" in fix
    assert "if tg_table_name = 'memory_items'" in fix
    cascade = CASCADE_FIX.read_text(encoding="utf-8").lower()
    assert "if not exists (select 1 from public.users" in cascade
    assert "parent-account deletion" in cascade
    security = SECURITY_FIX.read_text(encoding="utf-8").lower()
    assert "security definer" in security
    assert "revoke all" in security
    document_cleanup = DOCUMENT_CLEANUP.read_text(encoding="utf-8").lower()
    assert "create table public.document_cleanup_jobs" in document_cleanup
    assert "revoke all" in document_cleanup
