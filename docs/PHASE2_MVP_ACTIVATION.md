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
| D | Real Daily Learning Loop | COMPLETE — live Daily content, ordered voice-gated steps, private audio/Attempt evidence, Recap progress, reconnection, bilingual routes, and responsive UI validated |
| E | Real Day 1 → Day 2 Cross-Session Aha | COMPLETE — hidden Day 2 retrieval, real voice evidence, atomic deterministic update, and Recap Aha validated live |
| F | Local MVP Acceptance | COMPLETE — all 24 Build Spec criteria and the critical cross-session path are covered by integrated local evidence |

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
- Gate C completed real browser microphone, recording-format, upload, persistence,
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

**Status:** COMPLETE

### Completed scope

- Validate the existing real Daily Session path: deterministic plan, Bailian versioned lesson
  content, persisted ordered steps, server-gated Recap completion, and deterministic progress.
- Add only the minimum Daily turn-based voice evidence required by the Build Spec if the current
  low-fidelity Today shell cannot satisfy the live loop. Keep raw-audio preservation and provider
  abstractions intact.
- Gate E cross-day retrieval/Aha, Gate F acceptance, realtime voice, M8, V1.5, and V2 remain out
  of scope.

### Live and automated evidence

- The low-fidelity Today shell was replaced with an evidence-bearing, turn-based Daily voice UI.
  RECALL, IMITATE, RETRIEVE, TRANSFER, and INTERVIEW require an `ANALYZED` Attempt before the
  server permits advancement; LEARN and RECAP remain passive steps according to the persisted
  duration-specific plan.
- Real Day 1 Daily completion passed through RETRIEVE, TRANSFER, INTERVIEW, and RECAP. Each voice
  step used browser `MediaRecorder`, live Bailian TTS, Qwen3-ASR, and versioned Bailian analysis.
  Recap persisted `+1 XP`, a one-day streak, and advanced the account to Day 2.
- A page reload preserved authentication and progression; creating the next session produced a
  persisted Day 2 BUILD plan. Day 2 RECALL also passed the real browser voice path, covering the
  beginning of the canonical loop that the earlier Day 1 shell had already advanced past.
- A user-scoped read-only database/Storage verification found three Day 1 Daily Attempts
  (`RETRIEVE`, `TRANSFER`, `INTERVIEW`) in `ANALYZED` state. All had Bailian STT, analyzer version
  `answer_analyzer_v1`, saved transcripts/analysis, and independently readable non-empty private
  audio objects (448,520; 617,602; and 575,098 bytes). No paths, identifiers, content, or secrets
  were exposed.
- The live database initially rejected Daily question types under the calibration-era CHECK
  constraint. Versioned migration `202609080011_daily_voice_attempts.sql` extends the allowed
  values without deleting or rewriting existing Attempts; all eleven migrations validate locally
  and the migration was applied successfully to the configured live project.
- Controlled automated failure coverage proves analysis failure keeps original audio and
  transcript, retry reuses the exact Attempt ID/audio path, and no duplicate Attempt is created.
  Additional tests prove passive/non-current recording rejection and server-side advancement
  gating.
- English and Simplified Chinese route checks passed for Today, Practice, My English, and Journey.
  A Journey hard-coded-English gap and three secondary-route hydration mismatches were fixed.
  The approximately 375px viewport showed no horizontal breakage, and a clean post-fix reload
  produced no new console warning/error or Next.js Issue badge.

### Known limitations

- The test account uses a 20-minute plan, which intentionally omits IMITATE under the existing
  deterministic duration contract; IMITATE is covered by the shared voice service and tests but
  was not exercised in this live 20-minute session.
- Browser automation recorded audible prompt playback through the available microphone path;
  transcripts were intentionally low-content and validate transport/provider persistence rather
  than answer quality.
- Gate E cross-session retrieval/Aha and Gate F acceptance remain NOT STARTED.

## Gate E — Real Day 1 → Day 2 Cross-Session Aha

**Status:** COMPLETE

### Completed scope and live evidence

- Completing Day 1 now idempotently creates curriculum-backed `LEARNING` Expressions with a
  deterministic next-day review date. Later Daily Session creation/resume selects a due non-mastered
  Expression and creates or restores a single user/session-scoped RetrievalOpportunity.
- The opportunity replaces the Interview prompt only with interviewer-safe data. The live Day 2
  question was natural in its new conflict-resolution context and did not expose the target text or
  a meta-hint before the learner answered.
- Real browser recordings passed MediaRecorder → private learner-audio → Attempt → Bailian
  Qwen3-ASR → structured answer analysis. The resolve API accepted only `attempt_id`; callers could
  not submit correctness, independence, mastery, review, or evidence flags.
- Verification required an analyzed, transcript-bearing, same-user, same-session Attempt whose
  question matched the opportunity. A versioned deterministic exact-usage verifier converted the
  trusted transcript into target-use/correctness flags; the existing MemoryApplicationService and
  mastery/review rules remained authoritative for durable state.
- The existing SQL cross-session unit of work atomically wrote ExpressionAttempt evidence, updated
  Expression counters/status/review, and consumed the opportunity. Replay/idempotency, rollback,
  ownership, and anti-forgery regressions remain covered.
- Live failure recovery was observed: an ASR mismatch produced FAILURE evidence, consumed the first
  opportunity, preserved its analyzed Attempt/private audio, and scheduled the next review. A second
  additive Day 2 recovery Session preserved the original evidence and a new real recording produced
  SUCCESS transfer evidence. Final state was `TRANSFERRED`, not `MASTERED`, with one failure and one
  transfer success across two consumed opportunities.
- Two independent live database connections returned the same state. Both linked Attempts were
  analyzed by live providers, both private audio objects were non-empty, every linked owner matched,
  and resolving with another existing user was rejected without mutation.
- Recap displayed the cross-session win in English and Simplified Chinese, restored it after reload,
  and retained learner state across locale switching. Today, Practice, My English, and Journey passed
  at approximately 375px without horizontal overflow; browser console had no warnings/errors.
- Day 2 completion persisted `+1 XP`, retained the streak, and advanced to Day 3.

### Automated closeout

- Backend: 88 tests passed; Ruff format/check passed.
- Frontend: TypeScript, ESLint, and Next.js production build passed.
- `git diff --check` passed; no migration was needed because Gate E uses the existing M4/M5 schema.

### Known limitations

- The pre-Gate-E live account had completed Day 1 before automatic Expression activation existed,
  so its curriculum Expression was backfilled as due from the persisted completed Day 1 Session.
- Exact phrase verification is intentionally conservative: ASR lexical substitutions count as a
  failed retrieval even if semantically similar, preventing vague model judgment from changing
  mastery. The learner can recover through a later opportunity.
- Gate F is complete. Deployment-host setup, realtime voice, M8, V1.5, and V2 remain out of scope
  and unstarted.

## Gate F — Local MVP Acceptance

**Status:** COMPLETE

### Acceptance result

- All 24 criteria in Build Spec Section 21 are covered. Criteria 1–8 are backed by the Gate C real
  onboarding/calibration path; 9–11 by deterministic duration plans and Gate D Daily voice; 12–16
  by Gate E Expression, hidden retrieval, evidence, and deterministic mastery; 17 by deterministic
  error-pattern domain tests; 18–20 by the live My English, Mock Interview, Journey, XP/streak path;
  21–22 by retained-attempt failure regressions and the full test suite; and 23–24 by bilingual
  live checks plus reload, reconnection, PostgreSQL, and private Storage verification.
- The critical MVP validation passed previously and remains present: an expression learned in one
  session was independently used in a later different question/session, producing trusted evidence
  and an atomic deterministic progress update without revealing the target beforehand.
- An authenticated Day 3 browser pass rechecked Today, Practice/Quick Review, Mock Interview prompt,
  My English Expressions/Patterns/Stories, Journey's 30-day map, English/简体中文 state, and reload
  persistence. The initial real lesson generation completed successfully after provider latency.
- A user-scoped read-only live check confirmed a profile, assessment, at least two completed Daily
  Sessions, analyzed Attempts, memory and retrieval rows, Memory Gate integrity, row ownership,
  identical progress through two database connections, and readable non-empty private audio.
- Automated closeout: backend 88 tests, Ruff format/check, frontend TypeScript/ESLint/production
  build, all 11 migrations, and `git diff --check` passed.
- Gate F required no product-code, schema, prompt, or architecture change. No later scope started.

### Accepted limitations

- Pre-Gate-E Day 1 test accounts may require a one-time due-Expression backfill.
- Conservative exact-phrase verification can false-negative when ASR substitutes vocabulary; it
  reschedules review instead of incorrectly granting evidence.
- The 20-minute live account omits IMITATE by the deterministic duration contract; the shared
  IMITATE voice path is automated-test covered.
- Access tokens have no refresh-token lifecycle; expiry safely returns to login and requires a new
  sign-in. One known Starlette/httpx deprecation warning remains in backend tests.
- Deployment-host setup and physical-device coverage are outside Local MVP Acceptance.
