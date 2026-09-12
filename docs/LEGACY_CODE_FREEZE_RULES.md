# FluentLoop Legacy Code Freeze Rules

## 0. Status and Authority

- Status: ACTIVE
- Effective date: 2026-09-12
- Product authority: `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md`
- Architecture decision: `docs/DECISIONS.md` ADR-025
- Frozen inventory: `docs/LEGACY_FREEZE_MANIFEST.md`
- Baseline tag: `legacy-loop-final-baseline`

These rules define how the frozen Legacy Loop may and may not change.

---

# 1. Mandatory Rules

1. 禁止为 Legacy 模块增加新的产品功能；
2. 禁止新 Course Core import Legacy UI、Service、Repository；
3. 禁止新代码调用 Daily、Reward、Mastery、Retrieval 等 Legacy Service；
4. 禁止修改 Legacy 数据模型以适配 Course；
5. 禁止给 Legacy Session / Attempt 增加 Course 语义；
6. 禁止新页面读取或写入 `current_day`、XP、streak、phase、mastery；
7. Legacy 代码仅允许严重 bug 修复、安全修复、回滚支持和历史数据核查；
8. 所有例外修改必须显式说明原因。

These eight rules are normative. The remaining sections make them operational.

---

# 2. Prohibited Changes

## 2.1 Product Behavior

Do not:

- add new Today cards or recommendations;
- add Daily steps, durations, phase rules, rewards, streak behavior, or Journey behavior;
- add new Quick Review or Legacy Mock Interview behavior;
- revive Onboarding or Voice Calibration as a gate;
- add new Mastery, Aha, Expression, Review, or Retrieval rules;
- make Legacy behavior available from the new homepage;
- expose old progress in Course, Practice V2, or About Me.

## 2.2 Dependency Direction

New packages must not import:

```text
app.api.v1.daily
app.api.v1.calibration
app.api.v1.journey
app.api.v1.memory
app.api.v1.practice
app.api.v1.profiles
app.curriculum.interview_bootcamp_v1
app.domain.learning
app.repositories.daily_sessions
app.repositories.calibration
app.repositories.learning
app.repositories.memory
app.repositories.profiles
app.repositories.retrieval
app.services.daily_*
app.services.calibration
app.services.cross_session_uow
app.services.hidden_transfer
app.services.journey
app.services.learning_loop
app.services.mastery
app.services.memory
app.services.memory_gate
app.services.mock_interview
app.services.progress
app.services.quick_review
app.services.retrieval
app.services.rewards
app.services.verification
```

Frontend Course Core must not import:

```text
onboarding-flow
voice-calibration
today-session
today-session-live
practice-hub
journey-map
my-english
```

## 2.3 Data Model

Do not:

- add `course_id` or `question_id` to Legacy `sessions` or `attempts`;
- add Course Answer types to Legacy `question_type`;
- weaken the Legacy Attempt unique constraint to force Course reuse;
- place new Course models in `backend/app/db/models.py`;
- place new Course schemas in `backend/app/schemas.py`;
- store Course History in Expression, Story, RetrievalOpportunity, or LearnerAssessment;
- treat old Attempt rows as new Course History;
- mutate old migrations.

## 2.4 Legacy State

New runtime must not read or write:

```text
users.default_session_length
users.current_day
users.current_phase
users.xp
users.current_streak
users.last_completed_date
users.program_completed_at
```

New runtime must not create or update:

```text
sessions
attempts
learner_assessments
expressions
expression_attempts
error_patterns
retrieval_opportunities
```

An approved one-time migration may read `profiles`, `source_documents`, and confirmed `stories`, but
normal Course runtime must not write Legacy learning state.

## 2.5 Hidden Execution

Do not leave Legacy behavior active only because its UI is hidden.

After Stage 1, the following are forbidden:

- automatic Daily Session creation on login;
- Daily Session resume on app entry;
- Reward or Progress updates after Course Answer;
- automatic review scheduling;
- retrieval opportunity creation;
- Mastery evaluation;
- Aha generation;
- old Practice API calls from the new page;
- database triggers, jobs, or startup hooks that mutate Legacy state for new actions.

---

# 3. Allowed Changes

Legacy files may change only for:

1. a critical bug that affects rollback or historical-data correctness;
2. a security vulnerability;
3. rollback support;
4. historical-data inspection or export;
5. the minimum route unmounting or redirect required by Stage 1;
6. a minimum compatibility fix required to keep shared infrastructure safe.

Allowed does not mean automatic. Every Legacy diff requires the exception process in Section 5,
except the predeclared migration seams listed in the Manifest.

---

# 4. Migration Seam Rules

Files classified as `MIGRATION_SEAM` may change without being treated as a Legacy feature exception
only when the diff is limited to:

- router registration;
- dependency composition;
- authenticated entry destination;
- old-route redirects;
- new App Shell wiring;
- removal of default Legacy mounting.

The same file becomes an exception if it also changes:

- Daily logic;
- Profile/Calibration gate logic beyond bypass/removal;
- Legacy persistence;
- Reward, Mastery, Retrieval, or Progress behavior;
- Legacy response semantics for continued Legacy consumers.

When a migration seam contains mixed logic, prefer extracting a new Course module rather than
growing the seam.

---

# 5. Exception Process

Before modifying a frozen file:

1. identify the exact file and symbol;
2. classify the reason as critical bug, security, rollback, or historical-data verification;
3. explain why a new module or migration seam cannot solve it;
4. list affected Legacy routes, tables, and tests;
5. confirm no Course semantics are introduced;
6. define rollback;
7. obtain explicit review before implementation;
8. record the exception below.

Exception record template:

```text
Exception ID:
Date:
Status:
Reason category:
Files and symbols:
Legacy behavior affected:
Course Core impact:
Why no new-module alternative:
Tests:
Rollback:
Approved by:
Related commit:
```

## 5.1 Approved Exceptions

No exceptions are approved at Stage 0.

---

# 6. Automated Enforcement Required in Stage 1

## 6.1 Import Boundary

Create an architecture test or equivalent static rule that fails if:

- `backend/app/course/**` imports a frozen module;
- `backend/app/about_me/**` imports a frozen module;
- `backend/app/practice_v2/**` imports a frozen module;
- new frontend Course/About Me/Practice V2 components import frozen components or Legacy client
  functions.

## 6.2 No-Old-Write Tests

For every new write path:

1. snapshot Legacy progress fields and relevant table counts;
2. execute the new action;
3. verify all Legacy progress fields are unchanged;
4. verify no Legacy Session, Attempt, Expression, ExpressionAttempt, or RetrievalOpportunity was
   created;
5. verify the new record exists only in new Course Core tables.

At minimum cover:

- Course Answer creation;
- English Answer save;
- Chinese Answer confirmation;
- Course Feedback retry;
- Memory CREATE / UPDATE / MERGE;
- Answer deletion;
- Practice V2 completion.

## 6.3 Runtime Mount Tests

Verify:

- login enters the new homepage;
- Profile confirmation is not required;
- Calibration is not required;
- Today is not rendered;
- Legacy product routers are not mounted by default;
- old frontend URLs redirect according to the approved route table;
- `/api/v1/practice` is served by Practice V2 only after the old handler is unmounted.

## 6.4 Frozen Diff Check

CI or the stage closeout process must compare frozen files with:

```text
legacy-loop-final-baseline..HEAD
```

Any changed frozen file must:

- be a declared migration-seam edit; or
- reference an approved exception record.

---

# 7. Review Checklist

Before closing a Course Core stage, confirm:

- no frozen file changed without declaration;
- no new module imports Legacy;
- no Course schema was added to Legacy models;
- no Course API calls Legacy services;
- no new page reads Legacy progress;
- no new write changes Legacy tables or progress fields;
- shared infrastructure remains product-neutral;
- old data remains available for rollback and inspection;
- tests prove no hidden Legacy activity;
- all approved exceptions are recorded.

---

# 8. Relationship to Deletion

Code freeze is not deletion.

Do not delete Legacy code, tables, migrations, tests, or historical records during Stages 0–8 unless
a later approved Spec explicitly authorizes a deletion plan.

Unmounting a route does not remove its historical implementation.

The preferred order is:

```text
freeze
  ↓
stop runtime mounting
  ↓
build Course Core in parallel
  ↓
verify new product stability
  ↓
separately review deletion candidates
```

No deletion candidate is approved by this document.
