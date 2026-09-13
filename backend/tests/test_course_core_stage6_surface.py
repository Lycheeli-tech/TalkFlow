from pathlib import Path


def test_stage_six_has_explicit_confirmation_and_no_editable_or_legacy_draft_path():
    root = Path(__file__).resolve().parents[2]
    ui = (root / "frontend/components/course-core/course-workspace.tsx").read_text(encoding="utf-8")
    for contract in (
        "RECORDING_CHINESE",
        "PROCESSING_CHINESE",
        "AWAITING_CHINESE_CONFIRMATION",
        "getCourseDrafts",
        "confirmCourseDraft",
        "discardCourseDraft",
        "CHINESE_GUIDE",
        "recordingActiveRef",
        "audioGenerationRef",
        "feedbackAnswer",
        "draftAction",
        "aria-label={copy.discardDraftConfirm}",
    ):
        assert contract in ui
    assert "textarea" not in ui and "contentEditable" not in ui
    assert "window.confirm(copy.discardDraftConfirm)" not in ui
    migration = (root / "supabase/migrations/202609130020_chinese_answer_drafts.sql").read_text(
        encoding="utf-8"
    )
    assert "confirmed_at is not null" in migration
    assert "public.sessions" not in migration and "public.attempts" not in migration
