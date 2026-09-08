# Phase 2 — MVP Activation

This document tracks activation of the implemented FluentLoop MVP after Phase 1
(M0–M7). The Build Spec remains authoritative; this is an execution/status
document, not a replacement specification. There is no Milestone 8.

## Activation gates

| Gate | Scope | Status |
| --- | --- | --- |
| A | Live Infrastructure | COMPLETE — live Supabase project configured and validated |
| B | Live AI Providers | COMPLETE — Bailian text, ASR, and TTS validated live |
| C | Real Voice Pipeline | COMPLETE — real browser recording, private audio persistence, Bailian ASR/analysis, recovery, retry, reconnection, and bilingual route checks validated |
| D | Real Daily Learning Loop | IN PROGRESS — validating live Daily content, durable ordered steps, Recap progress, and the required turn-based Daily voice evidence |
| E | Real Day 1 → Day 2 Cross-Session Aha | NOT STARTED |
| F | Local MVP Acceptance | NOT STARTED |

## Gate A completion inventory

The repository and live `TalkFlow` Supabase project were validated from the
M7-merged `main` state. Secrets remain in ignored local environment files.

| Capability | Classification | Evidence / next action |
| --- | --- | --- |
| Supabase configuration | VALIDATED LIVE | Browser publishable key, protected server Secret Key, and asymmetric JWKS validation are configured. |
| PostgreSQL repositories | VALIDATED LIVE | SQLAlchemy/asyncpg connected through the regional Supabase Session Pooler using the application `DATABASE_URL`. |
| Migrations | VALIDATED LIVE | Ten versioned migrations are applied; local PGlite migration/provisioning validation also passed. |
| Auth and provisioning | VALIDATED LIVE | Temporary confirmed users signed in and the Auth trigger created matching public user rows. |
| RLS | VALIDATED LIVE | All eleven user-data tables have RLS/policies; two-user probes confirmed cross-user read/write isolation. |
| Profile persistence | VALIDATED LIVE | Preferences, source document, and confirmed profile survived a new database engine/session. |
| Resume storage | VALIDATED LIVE | Private `resumes` owner access passed and cross-user path access was rejected. |
| Audio storage | VALIDATED LIVE | Private `learner-audio` owner access passed and cross-user path access was rejected. |
| Session and Attempt persistence | VALIDATED LIVE | Daily Session and transcript-bearing analyzed Attempt survived reconnection. |
| Memory persistence | VALIDATED LIVE | An Expression written through `MemoryApplicationService` and `SQLMemoryRepository` survived reconnection. |
| RetrievalOpportunity persistence | VALIDATED LIVE | A user/session/expression-owned opportunity written through its SQL repository survived reconnection. |
| Progress persistence | VALIDATED LIVE | Preferences, XP, streak, and completion date written through `SQLUserRepository` survived reconnection. |

## Gate A configuration contract

- Root `.env` holds server/database configuration and remains ignored.
- `frontend/.env.local` holds the browser-safe URL and publishable key and remains ignored.
- The publishable key maps to the existing `NEXT_PUBLIC_SUPABASE_ANON_KEY` client contract.
- The server Secret Key maps to `SUPABASE_SERVICE_ROLE_KEY` and is used only by protected backend code.
- `SUPABASE_JWT_SECRET` remains empty because Auth uses the project JWKS endpoint and
  `authenticated` audience.
- The database uses the regional Session Pooler because the direct database hostname was not
  resolvable from the validation machine.

## Current status

- Phase 1 (M0–M7): COMPLETE and merged/tagged on `main`.
- Phase 2 Gate A: COMPLETE under the DEFAULT PASS protocol.
- Live validation passed for database connectivity, ten migrations, Auth/user provisioning,
  all-table RLS, private Resume/Audio Storage, durable repositories, reconnection recovery, and
  tracked-file secret leakage.
- A missing-RLS gap on five durable learning-memory tables was fixed by
  `202609050010_harden_memory_rls.sql`; all eleven user-data tables now have RLS and policies.
- Remaining Gate A limitations: deployment-host environment configuration has not been performed;
  live checks used temporary synthetic users and fixtures; provider and real voice behavior belong
  to Gates B and C.
- No M8 exists. Later gates require the human review boundaries defined in the
  activation instructions, including real provider, microphone, Daily Session,
  cross-session, and local golden-path use.

## Gate B — Live AI Providers

**Status:** COMPLETE

- Alibaba Cloud Model Studio (Bailian), China (Beijing), replaces OpenAI for all runtime AI calls.
- Qwen structured text providers cover profile extraction, calibration questions, answer analysis,
  and Daily Lesson content.
- Qwen3-ASR covers turn-based English speech transcription from browser audio data.
- Qwen3-TTS covers English question speech synthesis.
- Fake providers remain available for deterministic tests and recovery.
- Provider contract tests and the full backend regression suite pass.
- The Beijing API key and model entitlements passed live validation.
- Live structured outputs passed for profile extraction, calibration questions, answer analysis,
  and Daily Lesson content.
- Qwen3-TTS and Qwen3-ASR passed a real English TTS → STT round trip with an exact transcript.
- The user accepted the generated English voice for pronunciation, naturalness, speed, and volume.
- Runtime dependency inspection confirmed all six AI boundaries resolve to Bailian providers, and
  the configured API key is absent from Git-tracked files.
- Gate C is now IN PROGRESS for real browser microphone, recording-format, upload, persistence,
  failure-recovery, and retry validation.

## Gate C — Real Voice Pipeline

**Status:** COMPLETE

### Confirmed in the real local browser path

- A real user completed login and onboarding through Voice Calibration.
- Three English calibration answers were recorded successfully in the browser.
- The user proceeded from calibration into Today.
- Today displayed five persisted-looking step markers; the final Recap boundary completed and
  displayed `+1 XP`.
- The existing M2/M6 runtime path is therefore reachable from onboarding through calibration and
  the Today completion shell.
- After a fresh login and reload, the authenticated entry correctly resumed at Today, confirming
  the persisted calibration-stage route for this user.
- A 375px browser viewport smoke check passed with no horizontal overflow (`scrollWidth =
  clientWidth = 375`) and no browser console errors or warnings observed during the check.
- A read-only live Supabase aggregate check found two completed Calibration Sessions, each with
  three Attempts; all six Attempts were `ANALYZED` and had non-empty audio paths, transcripts, and
  analysis records, with two LearnerAssessment rows present. This confirms database-level shape
  and processing persistence, but does not yet prove the private Storage objects or identify which
  aggregate rows belong to the current user.
- A recursive read-only listing of the private `learner-audio` bucket found 6 nested audio files
  totaling 1,696,172 bytes. Paths and content were not exposed; current-user attribution remains
  covered by the user-scoped path convention and still needs a focused exact-match check.
- Anonymous aggregate comparison found database Attempts grouped per user as `[3, 3]` and private
  Storage files grouped per user directory as `[3, 3]`, matching the expected three-attempt shape
  without exposing user IDs or paths.
- On 2026-09-08, two independently created live database connections each found seven analyzed
  Attempts with seven audio references, transcripts, and analyses across three users, plus two
  LearnerAssessment rows. Each connection loaded the same non-empty private audio object. No audio
  content, path, user identifier, or credential was printed.

These are human-observed results from the local browser session. They are not yet a substitute for
database/provider evidence.

### Code and debug evidence recorded

- Auth-01 debugging identified stale/expired Supabase access-token handling as the cause of the
  later authentication error; token storage synchronization and 401 cleanup were added.
- A hydration mismatch caused by reading `sessionStorage` during the initial render was fixed by
  using a client-synchronized token subscription in `AppEntry`.
- Local frontend/backend reachability and the 8000-port stale Python process conflict were
  investigated; the current frontend and backend endpoints respond locally.
- `backend/tests/test_voice_calibration_service.py` passed (4 tests). Its controlled analyzer
  outage confirms `ANALYSIS_FAILED` retains original audio and transcript, and retry reuses the
  exact Attempt ID and audio path without adding an Attempt.
- An automated real-browser silent recording on 2026-09-08 captured `audio/webm;codecs=opus`,
  uploaded a non-empty private object, and reached `STT_FAILED` with the Bailian no-text response.
  The live aggregate count moved from 7 to 8 Attempts; clicking Retry did not create a ninth
  Attempt. A transient Supabase Session Pooler disconnect during the initial Attempt lookup caused
  an HTTP 500/`Failed to fetch`; invalidated-connection retry now recovers that safe read, and the
  same browser Retry returned normally to `STT_FAILED` without a duplicate Attempt.
- The working tree still contains uncommitted debug changes; it has not yet been made a Gate C
  checkpoint.

### Final bilingual route evidence

- In an authenticated session, the app-shell 中文 control changed the navigation and Today content
  to Simplified Chinese without refresh.
- Practice, My English, and Journey each loaded from the Chinese navigation with localized content.
- No Gate D, Gate E, Gate F, M8, V1.5, or V2 scope was started.

## Gate D — Real Daily Learning Loop

**Status:** IN PROGRESS

### Scope

- Validate the existing real Daily Session path: deterministic plan, Bailian versioned lesson
  content, persisted ordered steps, server-gated Recap completion, and deterministic progress.
- Add only the minimum Daily turn-based voice evidence required by the Build Spec if the current
  low-fidelity Today shell cannot satisfy the live loop. Keep raw-audio preservation and provider
  abstractions intact.
- Gate E cross-day retrieval/Aha, Gate F acceptance, realtime voice, M8, V1.5, and V2 remain out
  of scope.
