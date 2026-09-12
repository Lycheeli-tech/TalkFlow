# FluentLoop Project Status

## Last Updated

- 2026-09-12
- Branch: `codex/course-core-stage-2`
- HEAD: Course Core Stage 2 closeout checkpoint (tag `course-core-stage-2`)

## Product

FluentLoop (repository: TalkFlow) is an AI Course and interview-practice product. Users freely choose
from 30 fixed Courses and 59 fixed Questions; AI uses real profile data, prior Course Answers, and
source-validated Memory to help users express truthful experience in clearer, more natural English.

## Current Lifecycle

The v1.1 Legacy Loop implementation and Phase 2 local acceptance are complete at `8cc986d`. Product
architecture has moved to Build Spec v2.1. Course Core Stages 1 and 2 are complete: the Legacy
product is preserved for rollback but is no longer mounted by the default runtime, and the new
read-only Course Catalog surface is available behind the independent Auth boundary.

## Current Work

- Phase: Course Core
- Stage: 2 — New App Shell, Home, and Course Catalog
- Status: COMPLETE
- Objective achieved: the authenticated landing surface uses a new App Shell with three equal entry
  points, an immutable 30-Course/59-Question catalog, and read-only list/detail routes.
- Practice V2 and About Me remain explicitly feature-gated; direct routes do not mount Legacy UI.
- Dedicated Course Core API/client boundaries and architecture tests enforce read-only behavior,
  stable catalog content, route isolation, and the continuing Legacy freeze.

## Stable Baseline

The final Legacy code baseline is tag `legacy-loop-final-baseline` at `8cc986d`. Stage 0 is closed at
tag `course-core-stage-0-v2.1`; Stage 1 is merged to `main` and closed at tag
`course-core-stage-1`; Stage 2 is isolated on `codex/course-core-stage-2` and closed at tag
`course-core-stage-2`.

## Legacy Implementation Preserved

- Onboarding/Profile, confirmed-profile Memory Gate, structured memory/mastery/review/error rules.
- Turn-based Voice Calibration with raw audio, transcript, analysis, assessment, and retry semantics.
- Daily Session shell and deterministic planner; Practice, Quick Review, Journey, My English, XP/Streak.
- Cross-session RetrievalOpportunity and trusted verification path.
- Supabase PostgreSQL/Auth/Storage runtime validation and RLS/user isolation.
- Bailian text, Qwen3-ASR, and Qwen3-TTS runtime adapters behind provider interfaces.

## Course Core Not Yet Implemented

- Course Answer data and History, About Me/Memory, AI support, Chinese flow,
  remaining Courses, and Practice V2 are not implemented.
- The catalog is read-only; answering begins only in Stage 3.

## Current Blockers

No Stage 2 blocker. The English catalog copy decision required for Stage 2 was approved and recorded
in ADR-027. Remaining Build Spec Section 25 decisions retain their specified implementation deadlines.

## Next Steps

1. Review the Stage 2 checkpoint and read-only catalog evidence.
2. Do not begin Stage 3, merge, or push Stage 2 without explicit instruction.

## Stage 2 Verification Snapshot

- Default backend runtime exposes health plus read-only Course list/detail endpoints; Legacy product
  endpoints still return 404 and no product write endpoint exists.
- `course_catalog_v1` deterministically contains 30 Courses and 59 Questions; Course 30 has no
  follow-up question.
- Root authenticated landing, three equal entries, route boundaries, feature gates, and dedicated
  non-Legacy Course client are covered by Stage 2 contract tests.
- `/journey` and `/my-english` return 307 redirects to `/`; `/practice` and `/about-me` are safe,
  disabled Stage 2 route shells.
- Frozen Legacy files match the approved SHA-256 inventory; no freeze exception was required.
- Backend: 102 passed; Ruff format/check passed.
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
