# Current Agent Handoff

## Updated

- 2026-09-13
- Branch: `codex/course-core-stage-8`
- Completion checkpoint: `course-core-stage-8` (use `git rev-parse` for final HEAD)
- Baseline: verified pushed P7 main `66de471`; P7 tag `ac360dd`; P8 approval checkpoint `75716c2`

## Current State

P7 merge/push is complete: remote main, P7 branch and tag were verified after the authorized retry.
User explicitly authorized P8 and approved TBD-007 / ADR-032. P8 is COMPLETE and waiting for review;
P8 merge/push and post-MVP work are not authorized.

Review follow-up RESUME-09 is fixed: Chinese filenames were rejected as Storage keys. New uploads
use an owner/document ASCII key and preserve the original display filename; provider failures return
readable 503. Real Chinese PDF upload/parse/list/delete passed with disposable data removed. Full
backend is now 298 passed / 13 skipped; Ruff passed. Latest recovery checkpoint is the current HEAD
after `course-core-stage-8`; the stage completion tag remains at `04fbfce`.

Practice V2 uses its own Run/attempt aggregate, repository/service/API/client, private audio and
whole-feedback prompt. Three/five unique static Questions, voice recording, pause/skip/return/
re-answer and final encouragement feedback are enabled. No hints, per-question feedback, completed
history, personalization, Course Answer/Memory writes or Legacy changes. Active Run TTL is fixed
24 hours; completion/abandonment delete text immediately and queue durable audio cleanup.

## Verification / Recovery

- Backend: 292 passed / 13 opt-in skipped; Ruff check/format passed.
- Real PostgreSQL P8: 1 passed (18.81s); ownership/RLS, no direct writes, idempotency/CAS,
  expiry, completion deletion, cleanup backoff/new-registration protection and unchanged
  Legacy/Course/Memory snapshots. Fixtures rolled back.
- Fixed-text real Bailian feedback: 1 passed (9.72s). Three-question real synthetic speech
  TTS/upload/STT/replay/feedback passed (95), completed GET 404 and owner snapshots unchanged.
- Five-question browser completion: one synthetic voiced answer plus four explicit skips,
  real whole-feedback (92), bilingual display, refresh with no report/history.
- Actual device silence: recording locks and retained-audio retry worked; punctuation-only
  ASR is FAILED. Human full three/five-question speaking was not claimed.
- Frontend TypeScript/ESLint/production build and 21 migration validations passed.
- 1280px/375px checks: no overflow/error logs, pause/reload/recovery/skip/back passed. Shared
  mobile navigation overlap fixed and actual locale clicks checked on Practice and Course 11.
- Migration `202609130021` is applied/registered only in configured development/test DB.
- P8 test owner Run/job/private Practice object counts are zero. P6 three Course device Answers
  and Auth retained; original user's Course data were not modified.
- Details/limitations: CURRENT_MILESTONE_V1.md Stage 8; resolved issues PRACTICE-08..11 / SHELL-08.

## Local Review

- Backend: 127.0.0.1:8000, owned escalated exec session 60658, PID 21428.
  Restart with comma-separated `CORS_ORIGINS=http://localhost:3100,http://127.0.0.1:3100`;
  this setting is a string list, not JSON. External database/provider access requires escalation.
- Frontend: production Next 127.0.0.1:3100, owned exec session 45209.
- User IAB tab 1 is at `/about-me`, refreshed after the upload fix; user can reselect the original PDF.
  Existing target roles/answers are preserved. Separate smoke tab closed, viewport restored.
- Retained confirmed P6 disposable review account credentials are only in OS temporary state:
  `C:\Users\Galatea\AppData\Local\Temp\fluentloop-p6-607ae176946542cc96fed5b0c6d1cf67.json`.
  No real inbox is needed. Never commit credentials/transcripts or delete unrelated user data.
  Its `p8_run_id` is a now-completed Run; no active Practice data are retained for review.
- Preserve unrelated `frontend/next-env.d.ts` changes; excluded from checkpoint. Next builds restore
  its original text. Stop/restart only owned services.
- Bundled Node: `C:\Users\Galatea\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe`.
  Invoke local Next/ESLint/TypeScript scripts directly when npm is absent. Python: backend `.venv`.

## Next Action

Review P8 in the browser. Await explicit P8 merge/push authorization. Completed reports cannot be
recovered after refresh/lost response by design; unuploaded device blobs are not refresh recoverable.
Audio cleanup is asynchronous with durable backoff; semantic feedback quality remains model-dependent.
