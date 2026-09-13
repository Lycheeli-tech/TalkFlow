# Current Agent Handoff

## Updated

- 2026-09-13
- Branch: `main`
- Completion checkpoint: `course-core-stage-7`
- Safe baseline: pushed main `71f606b`; P6 tag `course-core-stage-6` / `3f71595`

## Current State

P7 is COMPLETE and locally merged. The product owner authorized P7 merge/push, then P8 on
2026-09-13. All 30 Courses / 59 Questions now reuse the English/Chinese Answer, support, TTS,
History and Feedback engine. Catalog IDs, wording, focus and order are unchanged. Course 30 has
one core Question and no follow-up. No migration was needed; no Legacy file or schema changed.

Local main fast-forwarded to P7 `ac360dd`. Push failed because GitHub HTTPS cannot connect (GIT-07);
P8 is authorized after push completes, so implementation has not begun. Practice V2 remains disabled.
P8 TTL decision TBD-007 is still unapproved; a concrete 24-hour active Run / immediate completion
and abandonment deletion proposal is recorded in CURRENT_MILESTONE_V1.md, not a production rule.
The full acceptance evidence is in `docs/CURRENT_MILESTONE_V1.md`, Stage 7. Stable decisions
remain in DECISIONS.md; Chinese Draft recovery continues under ADR-031.

## Verification

- Backend: 273 passed / 11 opt-in skipped; Ruff check/format passed.
- Frontend: TypeScript, ESLint and production build passed.
- Real PostgreSQL P7 regression: 1 passed, 59 English saves and four representative Chinese
  Draft/confirmation paths, ownership/RLS/direct-write restrictions and Legacy snapshots passed.
  All synthetic records were rolled back; no actual provider calls or Storage uploads in this test.
- Authenticated IAB: all 30 Courses on desktop 1280x900 and mobile 375x812, all desktop Questions,
  mobile question drawers, direct follow-up selection, Course 30 and cross-Course state reset passed.
  No overflow or final console errors; real Course 30 hints and safe reference fallback passed.
- P7 did not repeat human microphone recording for every Question; P6 real-device evidence and
  recorder/retention/Memory/failure-isolation regression remain applicable.

## Local Review / Recovery

- P7 backend: local uvicorn 127.0.0.1:8000, owned exec session 52240 (PID 11376).
- P7 frontend: production Next server 127.0.0.1:3100, owned exec session 42757.
- Existing user IAB tab 2 remains on Course 11 and was refreshed to the P7 build; History still has three Answers.
- Retained P6 disposable confirmed Auth account has two English and one Chinese device Answers
  for review. No real inbox is needed. Credentials are only in the OS temporary state file:
  `C:\Users\Galatea\AppData\Local\Temp\fluentloop-p6-607ae176946542cc96fed5b0c6d1cf67.json`.
  Do not commit credentials or actual transcripts. After review, use the owner-scoped helper
  `backend/tools/course_stage6_acceptance.py cleanup --state <temporary-state-path>`.
- Unrelated existing `frontend/next-env.d.ts` changes are preserved and excluded from checkpoint.
- Node is bundled at `C:\Users\Galatea\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe`;
  invoke local TypeScript/ESLint/Next scripts directly when npm is absent from PATH.
- Python is `backend\.venv\Scripts\python.exe`.

## Next Action

Restore GitHub connectivity; follow GIT-07 to fetch/check, retry the already-authorized P7 atomic
push and verify all refs. Confirm TBD-007 before Practice schema/storage policy is finalized, then
create `codex/course-core-stage-8` from pushed main and implement P8. Preserve retained review data.
Stop only owned local services if restarting; do not kill unrelated processes.
