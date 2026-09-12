# Current Agent Handoff

## Updated

- 2026-09-12
- Branch: `codex/course-core-stage-2`
- Checkpoint: Course Core Stage 2 App Shell and Catalog closeout, tagged `course-core-stage-2`

## Current State

Course Core Stage 2 — New App Shell, Home, and Catalog is complete. The default backend mounts health
and the read-only Course catalog API; the frontend has an independent authenticated App Shell,
three equal entry points, and read-only Course list/detail routes. Frozen Legacy code and data remain
preserved for rollback and historical inspection.

Read `docs/CURRENT_MILESTONE_V1.md` for the current Course Core V1 stage and execution sequence.
`docs/CURRENT_MILESTONE.md` is historical only.

The Legacy implementation remains unchanged at baseline `8cc986d`, tagged
`legacy-loop-final-baseline`. Historical API regressions explicitly mount a rollback-only test app;
that app is not used by the default runtime.

## Stage 2 Result

- `backend/app/course/catalog_v1.py` is the immutable 30-Course/59-Question product catalog with
  stable IDs, order, fixed English questions, and approved bilingual names/answer focus.
- `GET /api/v1/courses` and `GET /api/v1/courses/{course_id}` are the only new APIs and are read-only.
- `/` uses the new App Shell after authentication. Courses is enabled; Practice V2 and About Me are
  visible but disabled through explicit feature flags and safe route shells.
- `/courses` and `/courses/[courseId]` provide read-only catalog/list/detail views through a dedicated
  Course Core client that has no Legacy dependency.
- `/journey` and `/my-english` continue to redirect to `/`; default runtime still excludes all Legacy
  product routers.
- ADR-027 records the product-owner approval of faithful English catalog translations.
- No frozen business file, schema, migration, table, prompt, or data changed.

## Verification Evidence

- Backend: 102 tests passed; Ruff format/check passed.
- Frontend: TypeScript, ESLint, and production build passed.
- HTTP smoke: Catalog returned 30 Courses/59 Questions; Course 30 had no follow-up; new routes returned
  200, old URLs redirected to `/`, and Legacy APIs returned 404.
- Browser smoke used a disposable confirmed test account to verify direct authenticated landing,
  all three peer entries, the 30-Course list, an arbitrary Course detail, bilingual switching,
  Practice/About Me feature gates, and real Legacy URL redirects without mounting Legacy UI. The
  disposable account was signed out and deleted after verification.
- Default OpenAPI contains only health and the two Course GET routes; there are no product write endpoints.
- All machine-marked frozen files match their approved SHA-256 values.
- Migrations: unchanged; no database command was required.

## Known Limitations

- Stage 2 intentionally keeps Practice and About Me disabled and Course pages read-only.
- Because Stage 2 introduces no product data write path, no-old-write coverage still proves the
  default API has zero product write endpoints. Stage 3 Answer writes must add before/after Legacy
  field and table-count integration assertions.
- The Auth safety entry retains the existing sessionStorage token lifecycle; refresh-token work is
  outside Stage 2.
- One known Starlette/httpx deprecation warning remains in backend tests.

## Next Action

Stop after the Stage 2 checkpoint. Do not merge, push, or begin Stage 3 without explicit
product-owner instruction.

## Do Not Change

- Do not modify Build Spec v2.1 without a reviewed product proposal.
- Do not begin Stage 3 or enable unfinished Practice/About Me entries without explicit approval.
- Do not import Legacy business modules from new Course Core code.
- Do not print or commit `.env`/`.env.local`, database URLs, Supabase keys, Bailian keys, tokens,
  user identifiers, private object paths, or audio content.
- Preserve unrelated user work, especially `frontend/next-env.d.ts`.
