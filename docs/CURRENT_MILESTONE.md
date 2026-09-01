# Current Milestone

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

**Verified HEAD:** `aa80e68`

### Implemented

- Versioned mastery and review rules with deterministic evidence-based transitions.
- Explicit ExpressionAttempt evidence fields for recall/transfer, hint usage, independence, correctness, linked attempt/session, context, and timestamp.
- Conservative ErrorPattern lifecycle and confirmation-gated durable Story contract.
- User-scoped memory repository boundary with an in-memory MVP adapter.
- Versioned PostgreSQL migration for expressions, evidence, error patterns, and confirmed stories.

### Verified checks

- Backend: 43 tests passed; Ruff format and lint passed.
- Five versioned migrations validated.
- Frontend lint, TypeScript, and production build checks passed.

### Known limitations

- The current repository adapter is in-memory; wiring the M4 tables to a live SQL repository remains a hardening step before production use.
- M5 hidden retrieval injection, cross-session aha orchestration, and full Daily attempt integration remain out of scope.
- Fake providers remain the default and live Supabase/provider integration is not yet verified.
