# FluentLoop Project Status

## Last Updated

- 2026-09-14
- Delivery branch: `main`; source: `codex/course-core-stage-8`
- Safe baseline: pushed P7 main `66de471`; P7 tag `ac360dd`; P8 authorization checkpoint `75716c2`

## Product

FluentLoop (repository: TalkFlow) is an AI Course and interview-practice product. Users freely choose
from 30 fixed Courses and 59 fixed Questions; AI uses real profile data, prior Course Answers, and
source-validated Memory to help users express truthful experience in clearer, more natural English.

## Current Lifecycle

The v1.1 Legacy Loop implementation and Phase 2 local acceptance are complete at `8cc986d`. Product
architecture has moved to Build Spec v2.1. Course Core Stages 1–8 are COMPLETE; P8 and all review fixes are approved for main delivery. All 30 Courses use the isolated English/Chinese Answer engine; About Me
and source-validated AI Memory use dedicated boundaries. Legacy is preserved but unmounted by default.

## Current Work

- Phase: Course Core
- Stage: 8 — Practice V2
- Status: COMPLETE — product owner approved P8 and all review fixes for merge/push on 2026-09-14.
  Delivery checkpoint: `course-core-stage-8-complete`; original implementation tag is preserved.
  TBD-007 approved (ADR-032): 24-hour in-progress TTL, immediate completed/abandoned text deletion.
  Isolated API, persistence, recorder UI and whole-feedback complete; original tag `course-core-stage-8`.
- Review upload fix RESUME-09: Chinese filename PDF upload/parse/list/delete now passes; safe
  ASCII object keys preserve original names. Backend follow-up: 298 passed / 13 opt-in skipped.
- Review facts-save feedback ABOUT-10: saving/saved notices added; persistence was already working.
- AUTH-03 / ADR-033: same-account persistent login and automatic refresh passed; original review data
  preserved. Keep this account/data for the owner's three-day acceptance, with no automatic cleanup.
- REF-12 / ADR-034: initial reference generation verified before any answer; provider-contract
  failures fixed with versioned source IDs and one bounded regeneration, preserving fact checks.
- Uploaded Chinese Drafts support refresh recovery under approved TBD-010 / ADR-031.
- Confirmation is required before History, Feedback, or Memory; discard queues private audio cleanup.
- Transcript-only organization uses exact excerpts, number checks, and a separate fidelity check.
- All Course answering and Practice V2 entries are enabled on the P8 development branch.

## Stable Baseline

The final Legacy code baseline is tag `legacy-loop-final-baseline` at `8cc986d`. Stage 0 is closed at
tag `course-core-stage-0-v2.1`; Stage 1 is merged to `main` and closed at tag
`course-core-stage-1`; Stage 2 is merged to `main` and closed at tag `course-core-stage-2`; Stage 3
is merged to `main` and closed at tag `course-core-stage-3`; Stage 4 is merged to `main` and closed
at tag `course-core-stage-4`. Stage 5 is merged/pushed to `main` at `course-core-stage-5` / `9f08381`.

## Legacy Implementation Preserved

- Onboarding/Profile, confirmed-profile Memory Gate, structured memory/mastery/review/error rules.
- Turn-based Voice Calibration with raw audio, transcript, analysis, assessment, and retry semantics.
- Daily Session shell and deterministic planner; Practice, Quick Review, Journey, My English, XP/Streak.
- Cross-session RetrievalOpportunity and trusted verification path.
- Supabase PostgreSQL/Auth/Storage runtime validation and RLS/user isolation.
- Bailian text, Qwen3-ASR, and Qwen3-TTS runtime adapters behind provider interfaces.

## Course Core Not Yet Implemented

- No later or post-MVP scope is authorized.

## Current Blockers

P7 push connectivity is resolved (GIT-07); P8 TTL is approved (ADR-032).
P8 feedback citation, device-silence and mobile navigation defects are resolved; no current blocker.
P8 migration `202609130021` is applied/registered in the configured development/test database.
TBD-010 is approved in ADR-031.
P6 migration `202609130020` is persistently applied/registered in the configured test database.
User-operated IAB device recording now passed; the previous microphone blocker is resolved.
Failed Answer/Draft audio TTL remains three days under ADR-028.

## Next Steps

1. P8 COMPLETE; publish main/source branch and completion tags, then verify remote refs.
2. No later or post-MVP work is authorized.
3. Preserve the original acceptance account and data; cleanup requires explicit user instruction.

## Stage 4 Verification Snapshot

- Dedicated About Me/Memory tables, RLS, repository/service/API/client and responsive UI are implemented
  without Legacy business imports; authenticated clients cannot write the new tables directly.
- Backend: 130 passed with 6 opt-in real PostgreSQL tests also passed; Ruff format/check passed.
- Frontend: TypeScript, ESLint, and production build passed.
- Real Bailian CREATE, source/excerpt validation, all four actions, all four source types, multi-source
  deletion, source-less rejection, two-user RLS, and Auth account cascade passed.
- Two synthetic PDFs completed private Supabase upload/parse/list/delete with no remaining cleanup jobs.
- Authenticated desktop and 375px About Me checks passed with no console errors or horizontal overflow;
  empty About Me did not block the 30-Course Catalog. Disposable accounts/data were removed.
- P4 migrations `202609120014`–`202609120019` are applied and registered in the configured test database;
  Legacy fields, tables, schema, and data were unchanged.

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
