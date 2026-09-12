# Current Agent Handoff

## Updated

- 2026-09-12
- Branch: `codex/course-core-stage-0`
- Checkpoint: Course Core Stage 0 v2.1 documentation closeout, tagged `course-core-stage-0-v2.1`

## Current State

Course Core Stage 0 — Specification and Safety Boundaries is complete. The product owner approved
Build Spec v2.1. The approved v2.1 Spec, AGENTS rules, ADR-025/ADR-026, Legacy Freeze Manifest,
Legacy Code Freeze Rules, Chinese review translations, and Course Core V1 milestone document are
included in the `course-core-stage-0-v2.1` checkpoint.

Read `docs/CURRENT_MILESTONE_V1.md` for the current Course Core V1 stage and execution sequence.
`docs/CURRENT_MILESTONE.md` is historical only.

The Legacy implementation remains unchanged at baseline `8cc986d`, tagged
`legacy-loop-final-baseline`. The current runtime still serves the Legacy product because Stage 1
has not started.

## Stage 0 Result

- `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md` is now authoritative; v2.0 remains as history.
- Section 20.3 uses the product-approved 30 critical acceptance criteria.
- v1.1 remains in the repository as Legacy history.
- ADR-025 explicitly supersedes Legacy product decisions for the active Course Core.
- The freeze documents cover actual backend/frontend files, endpoints, tables, state fields,
  prompts, tests, migration seams, and exception procedure.
- Stage 1 must add import-boundary, no-old-write, runtime-mount, redirect, and frozen-diff tests.
- No runtime code, schema, migration, prompt, or test changed in Stage 0.

## Verification Evidence

- Backend: 88 tests passed; Ruff format/check passed.
- Frontend: TypeScript, ESLint, and production build passed.
- Migrations: all 11 validate in order locally; Gate D migration applied live.
- Authenticated Day 3 Today created/resumed a persisted Build plan; Practice exposed Quick Review
  state and a working Mock Interview prompt; My English projected Expressions/Patterns/Stories;
  Journey showed the persisted Day 3 position and the complete 30-day phase map.
- English → 简体中文 switching and a full reload preserved route, locale, and Day 3 state.
- User-scoped read-only checks passed for confirmed profile, calibration assessment, two or more
  completed Daily Sessions, analyzed voice Attempts, Expressions, retrieval evidence/opportunities,
  Memory Gate, ownership consistency, two-connection persistence, and non-empty private audio.

## Known Limitations

- The pre-Gate-E live Day 1 Expression required a one-time due backfill from its completed Session.
- Exact phrase verification intentionally treats ASR lexical substitutions as failure.
- The frontend stores a Supabase access token in `sessionStorage` without refresh-token lifecycle;
  expiration returns cleanly to login but requires the user to sign in again.
- One known Starlette/httpx deprecation warning remains in backend tests.
- The live account's 20-minute plan omits IMITATE by deterministic duration design; the shared
  voice path is test-covered. Deployment-host and physical-device coverage remain later work.

## Next Action

Stop after the Stage 0 checkpoint. Do not merge, push, or begin Stage 1 without explicit product-owner
instruction.

## Do Not Change

- Do not modify Build Spec v2.1 without a reviewed product proposal.
- Do not begin Stage 1, unmount Legacy routes, or change runtime behavior without explicit approval.
- Do not import Legacy business modules from new Course Core code.
- Do not print or commit `.env`/`.env.local`, database URLs, Supabase keys, Bailian keys, tokens,
  user identifiers, private object paths, or audio content.
- Preserve unrelated user work, especially `frontend/next-env.d.ts`.
