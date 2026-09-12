# FluentLoop Legacy Freeze Manifest

## 0. Status

- Status: ACTIVE
- Effective date: 2026-09-12
- Product authority: `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md`
- Superseding decision: `docs/DECISIONS.md` ADR-025
- Legacy code baseline commit: `8cc986d`
- Legacy code baseline tag: `legacy-loop-final-baseline`
- Companion rules: `docs/LEGACY_CODE_FREEZE_RULES.md`

This manifest answers what is frozen. The companion rules define which changes are prohibited,
which exceptions are allowed, and how an exception is reviewed.

The manifest must be re-audited at the beginning of every Course Core stage that changes routing,
dependencies, data models, repositories, or shared infrastructure.

---

# 1. Freeze Meaning

Legacy code is retained for:

- rollback;
- historical inspection;
- legacy-data verification;
- critical bug fixes;
- security fixes.

Legacy code is not an extension point for Course Core.

The following product concepts are frozen:

- Today;
- Daily Planner;
- Daily Session;
- Journey;
- BUILD / TRANSFER / PERFORM;
- `current_day`;
- Recall / Learn / Imitate / Retrieve / Transfer / Interview / Recap;
- Quick Review;
- XP / streak;
- Mastery / Aha;
- Onboarding;
- Voice Calibration;
- confirmation-gated Legacy Memory;
- hidden cross-session retrieval.

---

# 2. Classification

Every Legacy-adjacent file belongs to one of four classes.

| Class | Meaning | Course Core use |
| --- | --- | --- |
| FROZEN | Legacy business implementation | Must not import, call, or extend |
| SHARED_INFRASTRUCTURE | Product-neutral technical capability | May reuse through stable interfaces |
| MIGRATION_SEAM | Composition or route file that must change to activate the new product | Minimal scoped edits only |
| HISTORICAL_DATA | Existing tables, fields, migrations, and records | Preserve; new runtime must not treat as Course state |

If a file does not fit clearly into one class, stop and classify it before changing it.

---

# 3. Backend Frozen Files

## 3.1 Legacy API Modules

```text
backend/app/api/v1/calibration.py
backend/app/api/v1/daily.py
backend/app/api/v1/journey.py
backend/app/api/v1/memory.py
backend/app/api/v1/practice.py
backend/app/api/v1/profiles.py
```

These modules may remain importable only while rollback support requires them. Course Core must not
call their endpoints or reuse their handlers.

## 3.2 Legacy Curriculum and Domain

```text
backend/app/curriculum/interview_bootcamp_v1.py
backend/app/domain/learning.py
```

Frozen concepts include:

- 30-day curriculum units;
- Day-based stage selection;
- Expression status;
- review scheduling;
- deterministic mastery;
- cross-session retrieval evidence.

The new 30-Course Catalog must live in a separate module and must not modify
`interview_bootcamp_v1.py`.

## 3.3 Legacy Repositories

```text
backend/app/repositories/calibration.py
backend/app/repositories/daily_sessions.py
backend/app/repositories/learning.py
backend/app/repositories/memory.py
backend/app/repositories/profiles.py
backend/app/repositories/retrieval.py
```

Frozen repository types include:

- `CalibrationRepository`;
- `VoiceAttemptRepository`;
- `DailySessionRepository`;
- `LearningRepository`;
- `MemoryRepository`;
- `ProfileRepository`;
- `RetrievalOpportunityRepository`;
- their SQL and in-memory implementations.

Course Core must introduce new repositories rather than adding Course methods to these interfaces.

## 3.4 Legacy Services

```text
backend/app/services/calibration.py
backend/app/services/cross_session_uow.py
backend/app/services/daily_attempts.py
backend/app/services/daily_lesson_content.py
backend/app/services/daily_planner.py
backend/app/services/daily_voice.py
backend/app/services/hidden_transfer.py
backend/app/services/journey.py
backend/app/services/learning_loop.py
backend/app/services/mastery.py
backend/app/services/memory.py
backend/app/services/memory_gate.py
backend/app/services/mock_interview.py
backend/app/services/profiles.py
backend/app/services/progress.py
backend/app/services/quick_review.py
backend/app/services/retrieval.py
backend/app/services/rewards.py
backend/app/services/verification.py
```

Frozen service types include:

- `CalibrationService`;
- `CrossSessionUnitOfWork`;
- `DailyAttemptService`;
- `DailyLessonContentService`;
- `DailyPlanner`;
- `DailyVoiceService`;
- `HiddenTransferService`;
- `JourneyService`;
- `LearningLoopService`;
- `MasteryEngine`;
- `ReviewScheduler`;
- `MemoryApplicationService`;
- `MemoryGate`;
- `MockInterviewService`;
- `ProfileService`;
- `ProgressService`;
- `QuickReviewService`;
- `RetrievalService`;
- `RewardEngine`;
- `VerificationService`.

New Course, About Me, AI Memory, and Practice V2 services must not invoke these services.

## 3.5 Legacy Prompt Files

```text
backend/app/ai/prompts/answer_analyzer_v1.txt
backend/app/ai/prompts/calibration_questions_v1.txt
backend/app/ai/prompts/profile_extractor_v1.txt
```

These versioned prompts describe Legacy behavior. New behavior requires new prompt files and versions.
Do not silently rewrite a Legacy prompt to produce Course output.

---

# 4. Frontend Frozen Files

## 4.1 Frozen Components

```text
frontend/components/onboarding-flow.tsx
frontend/components/voice-calibration.tsx
frontend/components/today-session.tsx
frontend/components/today-session-live.tsx
frontend/components/practice-hub.tsx
frontend/components/journey-map.tsx
frontend/components/my-english.tsx
```

Course Core pages must not import these components.

Frozen component behavior includes:

- unauthenticated Onboarding as the product shell;
- Profile-confirmation gating;
- Voice Calibration gating;
- Today rendering;
- seven-step Daily progression;
- XP/streak completion display;
- old Quick Review;
- old one-question Mock Interview;
- My English projection;
- Journey map.

## 4.2 Frozen Legacy API Client Surface

`frontend/lib/api.ts` is a mixed Legacy client and must not receive new Course Core API types or
functions.

The following exports are Legacy:

```text
getApplicationEntry
savePreferences
importProfileText
importProfilePdf
confirmProfile
startCalibration
calibrationTts
submitCalibrationAttempt
retryCalibrationAttempt
getCalibration
createDailySession
advanceDailySession
getDailyAttempts
dailyStepTts
submitDailyAttempt
retryDailyAttempt
completeDailySession
startQuickReview
resolveRetrieval
submitQuickReview
getQuickReview
getMockInterviewPrompt
evaluateMockInterview
getJourney
getMyEnglish
```

New clients must be added in:

```text
frontend/lib/course-api.ts
frontend/lib/about-me-api.ts
frontend/lib/practice-api.ts
```

---

# 5. Legacy Routes and Endpoints

## 5.1 Backend Route Prefixes

The following current prefixes represent Legacy product runtime:

```text
/api/v1/profiles
/api/v1/calibration
/api/v1/daily
/api/v1/memory
/api/v1/practice
/api/v1/journey
/api/v1/entry
```

`/api/v1/practice` is reserved for Practice V2 after Legacy unmounting. New Practice handlers must
come from a new `practice_v2` module, not by extending `backend/app/api/v1/practice.py`.

## 5.2 Concrete Legacy Endpoints

```text
POST /api/v1/profiles/sources/text
POST /api/v1/profiles/sources/pdf
POST /api/v1/profiles/confirm
GET  /api/v1/profiles/me

POST /api/v1/calibration/sessions
GET  /api/v1/calibration/sessions/{session_id}/questions/{category}/tts
POST /api/v1/calibration/sessions/{session_id}/attempts
POST /api/v1/calibration/attempts/{attempt_id}/retry
GET  /api/v1/calibration/sessions/{session_id}

POST /api/v1/daily/sessions
POST /api/v1/daily/sessions/{session_id}/complete
GET  /api/v1/daily/sessions/{session_id}/attempts
GET  /api/v1/daily/sessions/{session_id}/steps/{step}/tts
POST /api/v1/daily/sessions/{session_id}/attempts
POST /api/v1/daily/attempts/{attempt_id}/retry
POST /api/v1/daily/sessions/{session_id}/advance

GET  /api/v1/memory/expressions
GET  /api/v1/memory/my-english
GET  /api/v1/memory/quick-review
POST /api/v1/memory/quick-review/start
POST /api/v1/memory/quick-review/{opportunity_id}/submit
GET  /api/v1/memory/retrieval/due
POST /api/v1/memory/retrieval/{opportunity_id}/resolve

GET  /api/v1/practice/mock-interview/prompt
POST /api/v1/practice/mock-interview/evaluate

GET  /api/v1/journey
GET  /api/v1/entry
```

Stage 1 must stop default runtime mounting or redirect product entry as specified by Build Spec v2.0.
Stage 0 does not change these routes.

## 5.3 Frontend Routes

Current Legacy route behavior:

```text
/            → AppEntry → Onboarding / Calibration / Today
/practice    → PracticeHub → Quick Review / Legacy Mock Interview
/my-english  → MyEnglish
/journey     → JourneyMap
```

Stage 1 and Stage 2 will replace or redirect these routes. Until then, they remain frozen Legacy
runtime.

---

# 6. Historical Data and Schema

## 6.1 Immutable Existing Migrations

The following migrations are historical and must never be edited:

```text
supabase/migrations/202609010001_foundation.sql
supabase/migrations/202609010002_onboarding_profile.sql
supabase/migrations/202609010003_voice_calibration.sql
supabase/migrations/202609010004_daily_session_contracts.sql
supabase/migrations/202609010005_memory_mastery_contracts.sql
supabase/migrations/202609010006_retrieval_opportunities.sql
supabase/migrations/202609010007_progress_rewards.sql
supabase/migrations/202609010008_quick_review_attempts.sql
supabase/migrations/202609010009_daily_progress_gate.sql
supabase/migrations/202609050010_harden_memory_rls.sql
supabase/migrations/202609080011_daily_voice_attempts.sql
```

New schema starts with a new migration after `202609080011`.

## 6.2 Legacy Tables

The following tables must not become Course Core storage:

```text
profiles
sessions
attempts
learner_assessments
expressions
expression_attempts
error_patterns
stories
retrieval_opportunities
```

Special cases:

- `profiles` and confirmed `stories` may be read by an approved one-time migration adapter;
- `stories` must not be written by the new Course Answer flow;
- `sessions` and `attempts` must never receive Course semantics;
- all Legacy records remain user-owned historical data.

## 6.3 Shared Tables with Restricted Fields

### `users`

Allowed shared identity/preferences:

```text
id
interface_language
support_language
timezone
created_at
updated_at
```

Migration-only or product-review-required fields:

```text
target_role
primary_goal
coaching_style
```

Legacy progress fields that new runtime must not read or write:

```text
default_session_length
current_day
current_phase
xp
current_streak
last_completed_date
program_completed_at
```

### `source_documents`

`source_documents` is reusable infrastructure for About Me Resume storage and provenance.

Allowed shared fields:

```text
id
user_id
source_type
filename
storage_path
raw_text
parse_status
created_at
```

Legacy extraction fields:

```text
candidate_profile
extractor_version
```

New About Me behavior must use a new Repository and versioned extraction behavior. It must not
restore the old Profile-confirmation gate.

## 6.4 Legacy Row Classes

The following classes in `backend/app/db/models.py` describe Historical Data:

```text
ProfileRow
SessionRow
AttemptRow
LearnerAssessmentRow
ExpressionRow
ExpressionAttemptRow
ErrorPatternRow
StoryRow
RetrievalOpportunityRow
```

New Course models must live in dedicated modules. Do not append Course columns or relationships to
these classes.

`UserRow` and `SourceDocumentRow` are mixed shared models subject to the field restrictions above.

---

# 7. Migration Seams

The following files are not wholesale frozen because they compose the application:

```text
backend/app/main.py
backend/app/api/dependencies.py
backend/app/api/v1/router.py
backend/app/api/v1/entry.py

frontend/app/layout.tsx
frontend/app/page.tsx
frontend/app/practice/page.tsx
frontend/app/journey/page.tsx
frontend/app/my-english/page.tsx
frontend/components/app-entry.tsx
```

Permitted future changes are limited to:

- mounting new Course Core routers;
- removing Legacy routers from default runtime;
- changing authenticated entry to the new homepage;
- redirecting Legacy pages;
- introducing the new App Shell;
- wiring shared infrastructure through product-neutral interfaces.

Prohibited in migration seams:

- Course business logic;
- direct database manipulation;
- reuse of Legacy Session/Attempt as Course storage;
- hidden calls to Daily, Progress, Reward, Mastery, Retrieval, or Legacy Memory;
- temporary writes to Legacy progress.

Stage 0 records these seams but does not modify their runtime behavior.

---

# 8. Shared Infrastructure

The following capabilities may be reused after their interface is confirmed product-neutral:

```text
backend/app/core/config.py
backend/app/core/security.py
backend/app/db/base.py
backend/app/db/session.py
backend/app/storage/audio.py
backend/app/storage/documents.py
backend/app/services/documents.py
backend/app/ai/interfaces.py
backend/app/ai/bailian.py
backend/app/ai/fakes.py
backend/app/api/dependencies.py

frontend/lib/auth.ts
frontend/lib/i18n.ts
frontend/components/interface-locale-provider.tsx
frontend/components/ui/button.tsx
frontend/components/ui/card.tsx
```

Reuse conditions:

- no dependency from shared infrastructure back into Course business rules;
- no Legacy side effect;
- no cross-user access;
- provider adapters remain behind interfaces;
- Legacy schemas must not leak into new public contracts;
- if a currently mixed file requires broad edits, add a new product-neutral module instead.

`backend/app/ai/bailian.py`, `backend/app/ai/fakes.py`, and `backend/app/api/dependencies.py` are
currently mixed composition files. Their modification requires a small reviewed diff and may not be
used to import Legacy business logic into Course Core.

---

# 9. No Background Legacy Activity

The current repository has no separate Redis/Celery scheduler, but Legacy work can still be triggered
synchronously through route and service composition.

After Stage 1:

- no login or page load may create a Daily Session;
- no Course save may enqueue or call retrieval, mastery, reward, or progress behavior;
- no Course Answer may create Expression or RetrievalOpportunity rows;
- no automatic resume may reopen a Legacy Session;
- no application startup hook may schedule Legacy work;
- no Practice V2 completion may update Legacy state.

If a background runner, scheduled job, database trigger, or webhook is later discovered, it must be
added to this manifest before Stage 1 can close.

---

# 10. Legacy Tests

Existing Legacy tests are historical regression coverage and must not be rewritten to make new
Course behavior appear compatible with Legacy contracts.

Examples include:

```text
backend/tests/test_entry.py
backend/tests/test_profile_api.py
backend/tests/test_voice_calibration_api.py
backend/tests/test_voice_calibration_service.py
backend/tests/test_daily_api_contract.py
backend/tests/test_daily_session_contracts.py
backend/tests/test_daily_attempts.py
backend/tests/test_daily_voice.py
backend/tests/test_daily_completion.py
backend/tests/test_daily_planner.py
backend/tests/test_memory_gate.py
backend/tests/test_memory_application_service.py
backend/tests/test_memory_repository.py
backend/tests/test_mastery_engine.py
backend/tests/test_retrieval_api_contract.py
backend/tests/test_retrieval_service.py
backend/tests/test_rewards.py
backend/tests/test_journey.py
backend/tests/test_quick_review.py
backend/tests/test_mock_interview.py
backend/tests/test_my_english.py
```

Allowed test changes:

- adapting a test harness after Legacy routers are intentionally unmounted;
- critical bug or security regression coverage;
- rollback verification;
- historical-data integrity checks.

New Course behavior requires new test modules. Do not change old expected values to redefine Legacy
objects as Course objects.

---

# 11. Stage 1 Enforcement Targets

Stage 1 must add automated checks for:

1. forbidden imports from new modules into frozen modules;
2. forbidden service calls;
3. unchanged Legacy user progress before and after each new write path;
4. no new rows in `sessions`, `attempts`, `expressions`, `expression_attempts`, or
   `retrieval_opportunities`;
5. no default mounting of Legacy product routers;
6. new authenticated entry bypassing Onboarding, Calibration, and Today;
7. correct old-page redirects;
8. frozen-file changes requiring an explicit exception record.

Until those checks exist, this document and code review are the enforcement mechanism.

---

# 12. Manifest Maintenance

When repository structure changes:

1. compare the change against `legacy-loop-final-baseline`;
2. classify each touched Legacy-adjacent file;
3. update this manifest only if the classification itself changed;
4. do not remove a frozen item merely because its route is unmounted;
5. append newly discovered hidden dependencies;
6. record approved exceptions in `docs/LEGACY_CODE_FREEZE_RULES.md`;
7. require product approval if the change modifies Build Spec behavior.

The preferred Git comparison is:

```text
legacy-loop-final-baseline..HEAD
```

This manifest is a boundary document, not a deletion plan.
