# Current Agent Handoff

## Updated

- 2026-09-14
- Branch: `codex/course-core-stage-8`
- Completion checkpoint: `course-core-stage-8` (use `git rev-parse` for final HEAD)
- Baseline: verified pushed P7 main `66de471`; P7 tag `ac360dd`; P8 approval checkpoint `75716c2`

## Current State

P7 merge/push is complete: remote main, P7 branch and tag were verified after the authorized retry.
User explicitly authorized P8 and approved TBD-007 / ADR-032. P8 is COMPLETE. On 2026-09-14 the owner explicitly authorized merge/push of P8 and all
subsequent review fixes (through `6a98e10`) and marking P8 complete. No post-MVP work is authorized.
Delivery checkpoint: `course-core-stage-8-complete`; preserve original stage tag at `04fbfce`.

Review follow-up RESUME-09 is fixed: Chinese filenames were rejected as Storage keys. New uploads
use an owner/document ASCII key and preserve the original display filename; provider failures return
readable 503. Real Chinese PDF upload/parse/list/delete passed with disposable data removed. Full
backend is now 298 passed / 13 skipped; Ruff passed. Latest recovery checkpoint is the current HEAD
after `course-core-stage-8`; the stage completion tag remains at `04fbfce`.

Review follow-up ABOUT-10: facts were already persisted (PATCH/GET 200, owner-scoped DB verified),
but no progress/success UI was displayed. Saving/saved notices and edit-reset/input protection added;
frontend ESLint/TypeScript/build passed. Browser verification uses only existing user facts.
Saving and saved states both passed with no error; user facts were preserved. ABOUT-10 CLOSED.

AUTH-03 CLOSED / ADR-033: original account restored with persistent access/refresh credentials,
single-flight automatic renewal and same-owner 401 retry. Auth lifetime remains 3600s; actual refresh
200, fourteen frontend expiry/concurrency/three-day/logout tests, ESLint/TypeScript/build and backend
298 passed. Original profile/roles/PDF/Memory/Answer/Transcript/Feedback digests unchanged.

## Acceptance Account Retention — Required

REF-12 CLOSED / ADR-034: initial Course 01 reference generation works with zero Answer History,
no recording or Chinese submission. Model excerpt copying caused intermittent validation 503;
v2 selects code-owned source IDs instead, validates cited-source numbers, and allows one bounded
regeneration only for rejected content. Backend 306 passed / 13 opt-in skipped; Ruff passed.
Eight new regressions passed; real reference is displayed
in tab 6. No profile/Answer/Draft/Memory writes. Recovery tag `course-reference-recovery-baseline`.

- Product owner requested one stable account for at least the next three days (2026-09-13 onward).
- Keep the original confirmed P6 account and all user-uploaded/entered/recorded data. Do not run its
  prepare/cleanup/reset helper, delete it, replace it, or create another account for user review.
- Do not automatically clean it after three days either; cleanup requires explicit user instruction.
- Credentials remain only in the existing OS temporary state path below. Auth persists across page
  reopen/expiry; explicit logout can be followed by the same credentials. No password is browser-stored.

Practice V2 uses its own Run/attempt aggregate, repository/service/API/client, private audio and
whole-feedback prompt. Three/five unique static Questions, voice recording, pause/skip/return/
re-answer and final encouragement feedback are enabled. No hints, per-question feedback, completed
history, personalization, Course Answer/Memory writes or Legacy changes. Active Run TTL is fixed
24 hours; completion/abandonment delete text immediately and queue durable audio cleanup.

## Verification / Recovery

- Closeout: backend 306 passed / 13 opt-in skipped; auth-session 14 passed (2026-09-14).
  Prior TypeScript/ESLint/production build and Ruff evidence remains valid; no runtime code changes.
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

- Backend: 127.0.0.1:8000, owned escalated exec session 97278, PID 18812.
  Restart with comma-separated `CORS_ORIGINS=http://localhost:3100,http://127.0.0.1:3100`;
  this setting is a string list, not JSON. External database/provider access requires escalation.
- Frontend: production Next 127.0.0.1:3100, owned exec session 85181.
- AUTH-03: tab 1 returned to `/courses/course-01` under the original account; independent About Me
  restore page verified the same saved data, then closed. Original review account stays signed in.
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

P8 COMPLETE; publish main/source branch and completion tags and verify matching remote refs. Completed reports cannot be
recovered after refresh/lost response by design; unuploaded device blobs are not refresh recoverable.
Audio cleanup is asynchronous with durable backoff; semantic feedback quality remains model-dependent.

2026-09-14 delivery: local main fast-forwarded to `b5bd05b`, matching the P8 source branch and
`course-core-stage-8-complete`. P8 is COMPLETE including all review fixes. Remote fetch and two
atomic push attempts failed (connection reset / GitHub port 443 unreachable). No successful push
or current remote verification is claimed; last verified remote main was `66de471` (GIT-08).
Authorization persists: retry `git push --atomic origin main codex/course-core-stage-8
refs/tags/course-core-stage-8 refs/tags/course-core-stage-8-complete`, then verify remote refs.
