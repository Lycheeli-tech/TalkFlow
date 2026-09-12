# Current Milestone

> Historical record only. For the current Course Core V1 stage and execution sequence, read
> `docs/CURRENT_MILESTONE_V1.md`.

## Course Core Stage 0 — Specification and Safety Boundaries

**Status:** COMPLETE

**Date:** 2026-09-12

**Branch:** `codex/course-core-stage-0`

**Legacy baseline:** `legacy-loop-final-baseline` at `8cc986d`

**Stage checkpoint:** the Stage 0 closeout commit tagged `course-core-stage-0`

### Objective

Activate the product-approved Course Core Build Spec and establish enforceable Legacy freeze
boundaries before any runtime, route, database, or product-code change.

### Completed

- Originally activated `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md`; the approved v2.1 amendment now supersedes it.
- Retained v1.1 as Legacy Loop history.
- Updated `AGENTS.md` to enforce the Course Core boundaries.
- Appended ADR-025, which explicitly supersedes the active-product Legacy Loop decisions.
- Added `docs/LEGACY_FREEZE_MANIFEST.md`.
- Added `docs/LEGACY_CODE_FREEZE_RULES.md`.
- Recorded the immutable Legacy baseline tag at `8cc986d`.
- Defined Stage 1 architecture, no-old-write, runtime-mount, and frozen-diff test requirements.

### Verification

- Documentation links and required files validated.
- Build Spec contains 30 Course rows and all nine stages, 0 through 8.
- Markdown code fences are balanced.
- `git diff --check` passes.
- Existing `frontend/next-env.d.ts` user work was not modified or included in Stage 0.
- No runtime code, routes, schemas, migrations, prompts, or tests changed.

### Approved Specification Amendment

- Build Spec v2.1 is now authoritative and v2.0 is retained as history.
- Section 20.3 now contains the product-approved 30 critical acceptance criteria.
- ADR-026 records the acceptance-gate change.
- No runtime behavior or Legacy freeze boundary changed.
- The approved documentation amendment is closed at tag `course-core-stage-0-v2.1`.

### Next Action

Stop for review at the Stage 0 checkpoint. Do not begin Stage 1 until the product owner explicitly
authorizes it.

---

## Milestone 1 — Onboarding & Profile

**Status:** COMPLETE  
**Branch:** `feat/onboarding-profile`  
**Verified HEAD:** `2ce8dd2`

**Merged to main:** `2c2943c`

**Stable tag:** `m1-profile`

### Verified checks

- Backend tests: 18 passed.
- Ruff lint and formatting checks passed.
- Frontend ESLint and TypeScript checks passed.
- Next.js production build passed.
- Two database migrations and user provisioning were validated.
- Existing Day 1 → Day 2 regression fixture passed; this does not mean the full cross-session memory/mastery loop has been implemented. The production cross-session loop remains future milestone scope.
- Desktop and 375 px responsive browser QA passed, with no horizontal overflow.
- Bilingual toggle passed; browser console had no errors.
- Both source specification file hashes remained unchanged.

### Known limitations

- Migrations have not been applied to a live Supabase project.
- OpenAI profile extraction and Supabase Storage adapters are implemented and contract-tested, but have not been exercised with live credentials.
- PDF import supports extractable text only; scanned documents do not have OCR support.
- `PROFILE_EXTRACTOR_PROVIDER` and `DOCUMENT_STORAGE_PROVIDER` default to `fake`.
- Backend tests emit one known Starlette/httpx 2 deprecation warning.

## Milestone 2 — Voice Calibration

**Status:** COMPLETE

**Branch:** `feat/voice-calibration`

**Base:** `m1-profile` (`2c2943c`)

**Verified implementation HEAD:** `021667e`

### Implemented

- Three category-constrained, confirmed-profile-grounded calibration questions in EXPERIENCE → MOTIVATION → PROJECT order.
- Turn-based browser recording with TTS playback and visible-text fallback.
- Private learner-audio storage abstraction and Supabase adapter.
- Minimum reusable `Session` model with `session_type = CALIBRATION`.
- Durable, user-scoped attempts with audio references, read-only transcripts, processing status, and structured observations.
- Raw audio persistence before attempt processing, STT, transcript persistence, and analysis.
- Idempotent user-triggered retry/re-analysis without duplicate attempts.
- A separate, historical `LearnerAssessment` using qualitative ordinal levels and versioned assessment output.
- Fake and OpenAI provider adapters for questions, STT, TTS, and answer analysis; fake providers remain the default.

### Verified checks

- Backend: 24 tests passed, including service failure recovery and `/api/v1` fixture golden path.
- Ruff lint and format checks passed.
- Three versioned migrations and user provisioning validated.
- Frontend ESLint, TypeScript, and production build passed.
- Desktop and 375 px browser smoke QA passed with no horizontal overflow or page console errors.
- Existing onboarding, Memory Gate, user isolation, and Day 1 → Day 2 fixture regressions remain passing.

### Known limitations / Live Integration Gate

- The new migration has not been applied to a live Supabase project.
- OpenAI STT/TTS/question/analysis adapters and Supabase learner-audio storage have contract/code coverage but have not been exercised with live credentials.
- Real microphone permission, recording format compatibility, live audio upload, and provider latency/error behavior require a live browser integration pass.
- Fake-provider validation is not equivalent to live-service validation. The Live Integration Gate must pass before FluentLoop is considered deployable for real personal use.
- The known Starlette/httpx 2 deprecation warning remains.
- The production Daily Session and cross-session memory/mastery loop remain future milestone scope.

## Milestone 3 — Core Daily Session

**Status:** COMPLETE

**Branch:** `feat/daily-session`

**Base:** `m2-voice-calibration` (`c910377`)

Scope: bounded inventories, deterministic Daily Planner, minimum daily-session persistence, the canonical session shell, and Today. The fixed backbone is BUILD → TRANSFER → PERFORM, not a hard-coded Day 2–30 topic calendar. Formal Memory/Mastery, Story Bank, Review Scheduler, Mock Interview, and Quick Review remain later-milestone scope.

**Verified HEAD:** `43ece44`

### Implemented

- Bounded interview, language, strategy, and story inventories.
- Deterministic Daily Planner with stage boundaries, scaffolding, duration-specific canonical steps, and cross-day retrieval selection.
- Provider-backed, versioned structured lesson content generation with confirmed-profile constraints.
- Minimal authenticated Daily Session API shell and reusable responsive Today UI.

### Verified checks

- Backend: 32 tests passed; Ruff format and lint passed.
- Four versioned migrations validated.
- Frontend ESLint, TypeScript (`--incremental false`), and production build passed.

### Known limitations

- Daily sessions persist and are idempotently resumed while in progress; completion progression and learner progress remain later work.
- Today UI is a polished low-fidelity MVP entry surface; recording, real TTS/STT, and full seven-step interaction remain later work.
- Fake providers remain the default; live provider and Supabase integration gates are still open.
- Formal Memory/Mastery, Story Bank, Review Scheduler, Mock Interview, and Quick Review remain out of scope.

## Milestone 4 — Memory & Mastery

**Status:** COMPLETE

**Branch:** `feat/memory-mastery`

**Verified implementation HEAD:** `fcb3467`

### Implemented

- Versioned mastery and review rules with deterministic evidence-based transitions.
- Mastery requires recall >= 3, transfer >= 2, and qualifying evidence across >= 3 distinct sessions.
- Direct/full-hint and non-independent evidence do not qualify for recall or transfer mastery counts.
- Review scheduling is deterministic and versioned using the 1 / 3 / 7 / 14 day intervals.
- Explicit ExpressionAttempt evidence fields for recall/transfer, hint usage, independence, correctness, linked attempt/session, context, and timestamp.
- Conservative ErrorPattern lifecycle with versioned, centralized transition rules.
- Confirmation-gated Story records with DOCUMENT / ATTEMPT / USER provenance.
- User-scoped memory repository boundary with PostgreSQL runtime and in-memory fixture adapters.
- `MemoryApplicationService` is the official gated durable write path enforcing Memory Gate, ownership, evidence provenance, and deterministic mastery rules.
- Minimal authenticated expression read API for future M5 consumption.
- Versioned PostgreSQL migration for expressions, evidence, error patterns, and confirmed stories.

### Verified checks

- Backend: 47 tests passed; Ruff format and lint passed.
- Five versioned migrations validated.
- Frontend lint, TypeScript, and production build checks passed.

### Known limitations

- The SQL adapter and migration are implemented but have not been exercised against a live Supabase project.
- Only a minimal expression read API exists; Story Bank and memory-management UI are not implemented.
- M5 hidden retrieval injection, cross-session aha orchestration, and full Daily attempt integration are not implemented.
- The known Starlette/httpx deprecation warning remains.

## Milestone 5 — Cross-Session Retrieval Loop

**Status:** COMPLETE

**Branch:** `feat/cross-session-loop`

**Verified implementation HEAD:** `bab7598`

### Implemented

- Durable, user/session-scoped RetrievalOpportunity records with conditional single consumption.
- Natural cross-context interview questions with deterministic target/meta-hint leakage guards.
- Trusted VerificationService creates authoritative evidence from structured analyzer output; public callers cannot submit mastery flags.
- Daily attempt → VerificationService → MemoryApplicationService integration with auditable opportunity linkage.
- Production-compatible Day 1 → Day 2 fixture using registered Sessions, Attempts, scheduled due state, durable opportunity, and verified evidence.
- Minimal authenticated opportunity-creation API.
- Interviewer-safe opportunity responses that omit the hidden Expression identifier and text.
- Authenticated retrieval-resolution API accepting only a persisted `attempt_id`; request-authored
  mastery/evidence flags are forbidden.
- `VerificationService` loads the user-owned, same-session, analyzed Daily Attempt and delegates to
  a cross-session unit of work.
- One SQL transaction atomically persists verified ExpressionAttempt evidence, applies the shared
  deterministic MemoryApplicationService mastery/review policy, and consumes the opportunity.
- In-memory fixtures emulate rollback and idempotency for deterministic tests.

### Verified checks

- Backend: 62 tests passed; Ruff format and lint passed.
- Six versioned migrations validated.
- Atomic rollback/retry/replay, API anti-forgery, SQL transaction, ownership/provenance,
  Day 1 → Day 2, and hidden-target leakage regressions passed.

### Known limitations

- Live Supabase/provider integration has not been validated.
- The resolve API consumes an already persisted, transcript-bearing, analyzed Daily Attempt; live
  Daily recording/STT/transfer-analyzer provider behavior remains a Live Integration Gate item.
- Only the minimal retrieval orchestration API/service exists; M6 practice/progress features remain
  out of scope.
- The known Starlette/httpx deprecation warning remains.


## Milestone 6 — Practice & Progress

**Status:** COMPLETE

**Branch:** `feat/practice-progress`

**Base:** `m5-cross-session-loop` (`0ab52da`)

**Verified implementation HEAD:** `b15c8c2`

### Implemented

- Versioned deterministic `RewardEngine` for passive learn, imitation, recall, transfer, and mastery XP.
- Deterministic daily streak behavior: same-day idempotency, consecutive-day increment, and gap reset.
- PostgreSQL user progress fields (`xp`, `current_streak`, `last_completed_date`) with a versioned migration.
- `ProgressService` application boundary and focused reward/persistence-contract tests.
- Minimal authenticated Quick Review API returning due, user-scoped expression projections.
- Minimal Mock Interview service/API: bounded prompt selection and one-shot complete-answer analysis.
- Responsive Practice UI at `/practice` with Quick Review and Mock Interview entry cards.
- Deterministic 30-day Journey projection API at `/api/v1/journey`, including phase and day status.
- Responsive Journey UI at `/journey` with the 30-day phase/status map.
- User-scoped My English projection API and responsive `/my-english` UI for Expressions, Patterns,
  and confirmed Stories.
- Authenticated entry routing now reaches Onboarding, Voice Calibration, or Today based on persisted
  profile/calibration state, with Today / Practice / My English / Journey navigation.
- Quick Review creates a hidden-target RetrievalOpportunity and uses the trusted verification path to
  persist evidence and advance review scheduling.
- Daily Sessions persist ordered step progress; only the server-side Recap boundary is reward-eligible.
- Day 30 is terminal and idempotent, and reward dates are derived from the learner timezone.
- Daily Session completion now atomically records the completed session, applies the versioned
  passive-learning reward, preserves streak state, and advances the Journey day without duplicate
  XP on replay.

### Verified checks

- Backend: 80 tests passed.
- Ruff format and lint checks passed.
- Nine versioned migrations and user provisioning validated.
- Frontend ESLint, TypeScript, and production build checks passed.
- M5 cross-session regression and M6 runtime-path tests passed.
- No M7, V1.5, or V2 scope is included.

### Remaining limitations

- Live Supabase/PostgreSQL runtime validation remains unperformed; fake providers remain the default.
- A focused ~375 px browser smoke validation remains unperformed.
- Full Daily voice/Attempt integration is not implemented; Today remains a low-fidelity session shell.
- Mock Interview responses are intentionally ephemeral at M6; no new durable Mock Interview memory
  system was introduced.
- The known Starlette/httpx deprecation warning remains.
- Milestone 7, V1.5, and V2 have not been started.

## Milestone 7 — Hardening

**Status:** COMPLETE

**Branch:** `feat/hardening`

**Base:** `m6-practice-progress` (`669b7d9`)

M7 scope is limited to regression coverage, failure recovery, i18n completeness, logging,
security/data-isolation checks, responsive UX validation, and README/setup documentation. No V1.5,
V2, or new product behavior is authorized in this milestone.

### M7 progress

- Reviewed the documented M0–M6 golden path and existing ownership, Memory Gate, evidence,
  idempotency, and provider-fallback boundaries; no new P1 correctness or security violation was
  identified in this pass.
- Added localized vocabulary keys for Journey phase labels and Practice entry labels in both English
  and Simplified Chinese catalogs.
- Clarified Python environment setup and fake-provider/live-integration expectations in `README.md`.
- Centralized interface locale in an app-level provider backed by the existing session preference and
  synchronized it from the persisted user `interface_language` on authenticated entry.
- Confirmed the interface locale now persists across Today, Practice, My English, and Journey routes,
  including refreshes; learning content remains unchanged.

### M7 validation status

- Recovered `backend/.venv` and verified the full backend suite: 80 passed, with the known
  Starlette/httpx deprecation warning.
- Ruff format/check passed using the project environment.
- Recovered the bundled Node.js 24.19.0 runtime and repository-declared pnpm 11.19.0; the earlier
  failure was caused by the Node directory being absent from the execution PATH.
- Frontend ESLint, TypeScript, and the Next.js production build passed.
- All nine migrations and user provisioning passed the repository PGlite validation command.
- Desktop navigation and approximately 375 px responsive smoke checks passed for Today, Practice,
  My English, and Journey, with no horizontal overflow or browser console warnings/errors.
- English → Simplified Chinese → all main routes, refresh persistence on Practice/My English/Journey,
  and Simplified Chinese → English route checks passed.

### Remaining limitations

- Live Supabase/PostgreSQL, Auth, Storage, and OpenAI/STT/TTS provider integration remains untested
  with real credentials and devices.
- Full Daily voice/Attempt capture remains outside the implemented MVP scope.
- Mock Interview responses remain intentionally ephemeral.
- The known Starlette/httpx deprecation warning remains.
- M7 is the final numbered MVP implementation milestone; the next phase is Live Integration,
  deployment, real-device testing, and bug fixing, not Milestone 8.

## Phase 2 — MVP Activation

### Gate A — Live Infrastructure

**Status:** COMPLETE

- The live `TalkFlow` Supabase project is configured locally through ignored environment files.
- Ten migrations are applied and validated, including RLS hardening for durable learning memory.
- Auth/JWKS, automatic user provisioning, all-table RLS and two-user isolation, private Resume and
  Audio Storage, SQL-backed Profile/Session/Attempt/Memory/RetrievalOpportunity/progress persistence,
  and reconnection recovery passed live validation.
- The application connects through the regional Supabase Session Pooler.
- No live secret or connection string is present in Git-tracked files.

### Remaining activation work

- Gate B — Live AI Providers: COMPLETE; Bailian structured text, Qwen3-ASR, Qwen3-TTS, runtime
  wiring, secret isolation, and human voice experience passed live validation.
- Gate C — Real Voice Pipeline: COMPLETE.
- Gate D — Real Daily Learning Loop: COMPLETE on `feat/real-daily-learning-loop`.
- Gate E — Real Day 1 → Day 2 Cross-Session Aha: COMPLETE on `feat/real-cross-session-aha`.
- Gate F — Local MVP Acceptance: COMPLETE on `chore/phase2-gate-f-local-mvp-acceptance`; all 24
  Build Spec acceptance criteria and the critical cross-session path are evidence-backed.
- Deployment configuration and real-device validation remain later activation work.

### Gate C live-browser progress (2026-09-08)

- Human validation completed login/onboarding, three real English Voice Calibration recordings,
  transition into Today, five Today progress markers, and the final Recap boundary with `+1 XP`.
- A subsequent fresh login/reload resumed at Today; a 375px viewport had no horizontal overflow,
  and no browser console errors or warnings were observed.
- A read-only live Supabase check found two completed Calibration Sessions with three Attempts
  each; all six Attempts were `ANALYZED` with audio paths, transcripts, and analysis present, and
  two LearnerAssessment rows existed. This is aggregate evidence, not yet current-user Storage
  object verification.
- A recursive private `learner-audio` listing found 6 nested audio objects totaling 1,696,172
  bytes; no paths or audio content were exposed.
- Anonymous aggregate comparison matched database Attempts per user `[3, 3]` with Storage files
  per user directory `[3, 3]`, without exposing IDs or paths.
- Two fresh live database connections each found seven analyzed Attempts with audio references,
  transcripts, and analysis across three users, two LearnerAssessment rows, and a successful
  non-empty private-audio load. This is reconnection and persistence evidence.
- The focused service suite passed 4 tests, including a controlled analyzer outage that preserves
  original audio/transcript and retries the same Attempt ID/path without duplication.
- An automated browser recording produced `audio/webm;codecs=opus`, uploaded a non-empty private
  audio object, and reached live `STT_FAILED` on a Bailian no-text response. The Attempt aggregate
  moved from 7 to 8; retry did not add a ninth Attempt. A transient Session Pooler disconnect in
  the initial read was fixed with an invalidated-connection retry, and the same browser Retry now
  returns normally to `STT_FAILED`.
- This confirms the currently implemented calibration and Today completion shell are reachable in
  the local browser.
- Gate C is **COMPLETE**. In an authenticated session, the app-shell 中文 control localized Today,
  Practice, My English, and Journey without refresh; route content loaded normally.
- English, 375px, console, MediaRecorder MIME, live STT failure/audio retention, same-Attempt
  retry, private storage, persistence, analysis, assessment, and reconnection checks passed.
- Gate D completed the live Daily Loop. Gate E and Gate F remain untouched and not started.

### Gate D completion (2026-09-08)

- Added the minimum Daily turn-based voice path using the existing provider and private-audio
  abstractions. Voice steps create durable Attempts and cannot advance until analysis succeeds.
- Added versioned migration `202609080011_daily_voice_attempts.sql` for Daily Attempt types and
  applied it to the configured live project after local validation of all eleven migrations.
- Real browser evidence passed for Daily TTS, `MediaRecorder` upload, Qwen3-ASR, Bailian analysis,
  transcript/analysis persistence, private audio existence, Recap `+1 XP`, streak/day progression,
  and reload/next-day persistence.
- Failure/retry tests confirm original audio and transcript survive analysis failure and retry
  reuses one Attempt. Non-current/passive recording and pre-analysis advancement are rejected.
- Backend: 87 tests passed; Ruff passed. Frontend TypeScript and ESLint passed. English/简体中文,
  main routes, approximately 375px layout, and post-fix hydration/console checks passed.
- Known limits: the live 20-minute plan omits IMITATE by deterministic duration design; its voice
  path is test-covered. Gate E/F, realtime voice, M8, V1.5, and V2 were not started.

### Gate E completion (2026-09-08)

- Day 1 curriculum expressions now enter `LEARNING` with a deterministic next-day review date when
  the Day 1 Daily Session completes; replay does not duplicate expressions.
- Starting/resuming a later Daily Session idempotently attaches one due, user-scoped hidden
  RetrievalOpportunity to its natural Interview prompt without exposing expression text.
- The live Day 2 Interview produced analyzed Bailian STT/analysis Attempts. Trusted verification
  accepted only the persisted same-user/same-session Attempt ID and atomically wrote evidence,
  updated review/mastery state, and consumed the opportunity.
- A first ASR mismatch correctly recorded failure and scheduled another retrieval; an additive
  recovery Session preserved the failure evidence, and a second real recording produced a verified
  transfer, moving the Expression to `TRANSFERRED` without incorrectly marking it `MASTERED`.
- English and Simplified Chinese Recap Aha, refresh recovery, private audio, reconnection,
  cross-user rejection, main routes, 375px layout, and clean console passed.
- Backend 88 tests, Ruff, frontend TypeScript/ESLint/build, and `git diff --check` passed. Gate F
  subsequently completed integrated local acceptance; realtime voice, M8, V1.5, and V2 were not
  started.

### Gate F completion (2026-09-09)

- Mapped all 24 Build Spec Section 21 criteria to Gates A–E implementation/live evidence and
  revalidated the configured MVP as an integrated local system.
- Authenticated Day 3 browser checks passed for Today, Practice/Quick Review, Mock Interview prompt,
  My English, Journey, English/简体中文 switching, and reload persistence.
- Read-only live verification passed for profile/calibration, completed Daily Sessions, analyzed
  Attempts, memory/retrieval evidence, Memory Gate, ownership, two-connection persistence, and
  non-empty private audio.
- No Gate F product change was necessary. Deployment, realtime voice, M8, V1.5, V2, and later scope
  remain unstarted.
