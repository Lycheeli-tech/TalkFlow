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

**Status:** IN PROGRESS

**Branch:** `feat/voice-calibration`

**Base:** `m1-profile` (`2c2943c`)

Scope is limited to turn-based Voice Calibration: three confirmed-profile-grounded questions, learner audio preservation, STT, attempts, structured per-attempt analysis, and a provisional versioned learner assessment. Milestone 3 Daily Session behavior is not authorized.
