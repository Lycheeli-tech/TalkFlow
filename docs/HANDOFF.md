# Current Agent Handoff

## Updated

- 2026-09-12
- Branch: `codex/course-core-stage-1`
- Checkpoint: Course Core Stage 1 runtime shutdown closeout, tagged `course-core-stage-1`

## Current State

Course Core Stage 1 — Stop Legacy Runtime and Enforce the Freeze is complete. The default backend
runtime mounts only health; the frontend root is an independent Auth safety entry; old Legacy pages
redirect to `/`. Frozen Legacy code and data remain preserved for rollback and historical inspection.

Read `docs/CURRENT_MILESTONE_V1.md` for the current Course Core V1 stage and execution sequence.
`docs/CURRENT_MILESTONE.md` is historical only.

The Legacy implementation remains unchanged at baseline `8cc986d`, tagged
`legacy-loop-final-baseline`. Historical API regressions explicitly mount a rollback-only test app;
that app is not used by the default runtime.

## Stage 1 Result

- `backend/app/api/v1/router.py` no longer imports or mounts users, profiles, calibration, daily,
  memory, Legacy practice, journey, or entry routers.
- `/` uses `StageOneEntry`, which talks only to Supabase Auth and session storage; it does not query
  Legacy application state or require onboarding/profile/calibration.
- `/practice`, `/journey`, and `/my-english` redirect to `/` and no longer import frozen components.
- `architecture/legacy_freeze_v1.json` marks frozen modules with approved baseline hashes and records
  migration seams, route prefixes, and forbidden dependencies.
- `test_course_core_stage1_architecture.py` enforces the runtime, freeze, dependency, redirect, and
  zero-write boundaries. Existing Legacy API tests use `legacy_client` explicitly.
- No frozen business file, schema, migration, table, prompt, or data changed.

## Verification Evidence

- Backend: 94 tests passed; Ruff format/check passed.
- Frontend: TypeScript, ESLint, and production build passed.
- Production HTTP smoke: `/` returned 200; `/practice`, `/journey`, and `/my-english` returned 307
  with Location `/`.
- Default OpenAPI contains only `GET /api/v1/health`; there are no Stage 1 product write endpoints.
- All machine-marked frozen files match their approved SHA-256 values.
- Migrations: unchanged; no database command was required.

## Known Limitations

- Stage 1 intentionally does not expose the Stage 2 Courses, Practice, or About Me entries.
- Because Stage 1 introduces no product data write path, no-old-write coverage currently proves the
  default API has zero product write endpoints. Each later write path still requires before/after
  Legacy state and table-count assertions.
- The Auth safety entry retains the existing sessionStorage token lifecycle; refresh-token work is
  outside Stage 1.
- One known Starlette/httpx deprecation warning remains in backend tests.

## Next Action

Stop after the Stage 1 checkpoint. Do not merge, push, or begin Stage 2 without explicit
product-owner instruction.

## Do Not Change

- Do not modify Build Spec v2.1 without a reviewed product proposal.
- Do not begin Stage 2 or expose unfinished Course Core entries without explicit approval.
- Do not import Legacy business modules from new Course Core code.
- Do not print or commit `.env`/`.env.local`, database URLs, Supabase keys, Bailian keys, tokens,
  user identifiers, private object paths, or audio content.
- Preserve unrelated user work, especially `frontend/next-env.d.ts`.
