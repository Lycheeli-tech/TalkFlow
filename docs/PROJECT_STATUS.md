# FluentLoop Project Status

## Last Updated

- 2026-09-12
- Branch: `codex/course-core-stage-1`
- HEAD: Course Core Stage 1 closeout checkpoint (tag `course-core-stage-1`)

## Product

FluentLoop (repository: TalkFlow) is an AI Course and interview-practice product. Users freely choose
from 30 fixed Courses and 59 fixed Questions; AI uses real profile data, prior Course Answers, and
source-validated Memory to help users express truthful experience in clearer, more natural English.

## Current Lifecycle

The v1.1 Legacy Loop implementation and Phase 2 local acceptance are complete at `8cc986d`. Product
architecture has moved to Build Spec v2.1. Course Core Stage 1 is complete: the Legacy product is
preserved for rollback but is no longer mounted by the default runtime.

## Current Work

- Phase: Course Core
- Stage: 1 — Stop Legacy Runtime and Enforce the Freeze
- Status: COMPLETE
- Objective achieved: authenticated entry bypasses Onboarding, Calibration, and Today; Legacy API
  routers and pages are not mounted by default; old page URLs redirect to the safe entry.
- A machine-readable freeze inventory and architecture tests enforce frozen-file integrity, forbidden
  Course Core dependencies, no default Legacy routes, and no Stage 1 product write endpoints.
- Historical API regression coverage uses an explicit rollback-only test app and remains passing.

## Stable Baseline

The final Legacy code baseline is tag `legacy-loop-final-baseline` at `8cc986d`. Stage 0 is closed at
tag `course-core-stage-0-v2.1`; Stage 1 is isolated on `codex/course-core-stage-1` and closed at tag
`course-core-stage-1`.

## Legacy Implementation Preserved

- Onboarding/Profile, confirmed-profile Memory Gate, structured memory/mastery/review/error rules.
- Turn-based Voice Calibration with raw audio, transcript, analysis, assessment, and retry semantics.
- Daily Session shell and deterministic planner; Practice, Quick Review, Journey, My English, XP/Streak.
- Cross-session RetrievalOpportunity and trusted verification path.
- Supabase PostgreSQL/Auth/Storage runtime validation and RLS/user isolation.
- Bailian text, Qwen3-ASR, and Qwen3-TTS runtime adapters behind provider interfaces.

## Course Core Not Yet Implemented

- Stage 2 App Shell and Course Catalog are not started.
- Course Answer data, About Me/Memory, AI support, Chinese flow,
  remaining Courses, and Practice V2 are not implemented.
- The Stage 1 entry is intentionally a safe authenticated transition page, not the Stage 2 homepage.

## Current Blockers

No Stage 1 blocker. Build Spec Section 25 contains product decisions that must be resolved by their
specified implementation deadlines.

## Next Steps

1. Review the Stage 1 checkpoint and runtime shutdown evidence.
2. Do not begin Stage 2, merge, or push without explicit instruction.

## Stage 1 Verification Snapshot

- Default backend runtime exposes only `/api/v1/health`; all Legacy product endpoints return 404.
- Root entry supports sign-in/sign-up without Profile, Calibration, Daily Session, or Legacy API calls.
- `/practice`, `/journey`, and `/my-english` return 307 redirects to `/` in the production server.
- Frozen Legacy files match the approved SHA-256 inventory; no freeze exception was required.
- Backend: 94 passed; Ruff format/check passed.
- Frontend: TypeScript, ESLint, and production build passed.
- No database migration or Legacy data changed.

## Legacy Verification Snapshot

- Backend: 88 passed after Gate E validation.
- Ruff format/check: passed.
- Frontend ESLint, TypeScript, and production build: passed during M7/Gate B validation.
- Eleven migrations validate locally; the Gate D constraint migration is applied live.
- Bailian live text, TTS→STT, and human voice acceptance: passed in Gate B.
- Gate C real browser microphone/upload/retry validation: complete.
- Gate D real Daily voice/Attempt/Recap/progress/reconnection and bilingual responsive checks:
  complete.
- Gate E live hidden retrieval, real voice evidence, atomic resolution, failure recovery,
  reconnection, isolation, bilingual Recap, 375px routes, and console checks: complete.
- Gate F: all 24 MVP criteria mapped to prior/current evidence; authenticated Day 3 Today,
  Practice, My English, Journey, locale/reload persistence, durable data, ownership, and private
  audio checks passed. Full automated closeout passed again.

## Source of Truth

- `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md`: authoritative product/architecture specification.
- `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md`: previous Course Core specification retained as history.
- `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md`: Legacy Loop historical specification.
- `docs/LEGACY_FREEZE_MANIFEST.md` and `docs/LEGACY_CODE_FREEZE_RULES.md`: frozen boundary.
- `DECISIONS.md`: stable architecture decisions.
- `PHASE2_MVP_ACTIVATION.md`: execution gates and acceptance state.
- `PROJECT_STATUS.md`: compact project dashboard.
- `HANDOFF.md`: immediate operational context.
- `ISSUES.md`: debugging and known-issue continuity.
- `CURRENT_MILESTONE_V1.md`: current Course Core V1 stage, execution, and acceptance state.
- `CURRENT_MILESTONE.md`: historical milestone and lifecycle notes only.
