# FluentLoop Legacy Freeze Manifest（中文审阅译本）

> 本文件是当前工作树中 `docs/LEGACY_FREEZE_MANIFEST.md` 的中文审阅译本，不是当前生效的 Freeze Manifest。
> 如译文与英文原文存在差异，以英文原文为准。对本译本的修改意见经审阅并同步回英文原文后才会生效。

## 0. 状态

- 状态：ACTIVE；
- 生效日期：2026-09-12；
- 产品权威来源：`FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md`；
- Superseding decision：`docs/DECISIONS.md` ADR-025；
- Legacy 代码基线 commit：`8cc986d`；
- Legacy 代码基线 tag：`legacy-loop-final-baseline`；
- 配套规则：`docs/LEGACY_CODE_FREEZE_RULES.md`。

本 Manifest 回答“哪些内容被冻结”。
配套 Rules 说明哪些修改被禁止、哪些例外被允许，以及如何审阅例外。

每次开始会修改路由、依赖、数据模型、Repository 或共享基础设施的 Course Core 阶段前，都必须重新审核本 Manifest。

---

# 1. Freeze 的含义

保留 Legacy 代码的用途：

- 回滚；
- 历史检查；
- Legacy 数据核查；
- 严重 bug 修复；
- 安全修复。

Legacy 代码不是 Course Core 的扩展点。

以下产品概念被冻结：

- Today；
- Daily Planner；
- Daily Session；
- Journey；
- BUILD / TRANSFER / PERFORM；
- `current_day`；
- Recall / Learn / Imitate / Retrieve / Transfer / Interview / Recap；
- Quick Review；
- XP / streak；
- Mastery / Aha；
- Onboarding；
- Voice Calibration；
- 需要用户确认的 Legacy Memory；
- 隐式跨 Session Retrieval。

---

# 2. 分类

每个与 Legacy 相邻的文件必须归入以下四类之一：

| 分类 | 含义 | Course Core 使用方式 |
| --- | --- | --- |
| FROZEN | Legacy 业务实现 | 不得 import、调用或扩展 |
| SHARED_INFRASTRUCTURE | 与产品无关的技术能力 | 可以通过稳定接口复用 |
| MIGRATION_SEAM | 为启用新产品而必须修改的组合或路由文件 | 只允许范围最小的修改 |
| HISTORICAL_DATA | 现有数据表、字段、migration 和记录 | 保留；新 runtime 不得将其视为 Course 状态 |

如果一个文件无法明确归类，必须先停止修改并完成分类。

---

# 3. 后端冻结文件

## 3.1 Legacy API 模块

```text
backend/app/api/v1/calibration.py
backend/app/api/v1/daily.py
backend/app/api/v1/journey.py
backend/app/api/v1/memory.py
backend/app/api/v1/practice.py
backend/app/api/v1/profiles.py
```

只有在回滚支持仍需要时，这些模块才可以继续被 import。
Course Core 不得调用其 endpoint，也不得复用其 handler。

## 3.2 Legacy Curriculum 和 Domain

```text
backend/app/curriculum/interview_bootcamp_v1.py
backend/app/domain/learning.py
```

被冻结的概念包括：

- 30 天 Curriculum Unit；
- 基于 Day 的阶段选择；
- Expression 状态；
- Review scheduling；
- 确定性 Mastery；
- 跨 Session Retrieval Evidence。

新的 30-Course Catalog 必须位于独立模块中，不得修改 `interview_bootcamp_v1.py`。

## 3.3 Legacy Repository

```text
backend/app/repositories/calibration.py
backend/app/repositories/daily_sessions.py
backend/app/repositories/learning.py
backend/app/repositories/memory.py
backend/app/repositories/profiles.py
backend/app/repositories/retrieval.py
```

被冻结的 Repository 类型包括：

- `CalibrationRepository`；
- `VoiceAttemptRepository`；
- `DailySessionRepository`；
- `LearningRepository`；
- `MemoryRepository`；
- `ProfileRepository`；
- `RetrievalOpportunityRepository`；
- 它们对应的 SQL 和内存实现。

Course Core 必须建立新的 Repository，不得给这些接口增加 Course 方法。

## 3.4 Legacy Service

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

被冻结的 Service 类型包括：

- `CalibrationService`；
- `CrossSessionUnitOfWork`；
- `DailyAttemptService`；
- `DailyLessonContentService`；
- `DailyPlanner`；
- `DailyVoiceService`；
- `HiddenTransferService`；
- `JourneyService`；
- `LearningLoopService`；
- `MasteryEngine`；
- `ReviewScheduler`；
- `MemoryApplicationService`；
- `MemoryGate`；
- `MockInterviewService`；
- `ProfileService`；
- `ProgressService`；
- `QuickReviewService`；
- `RetrievalService`；
- `RewardEngine`；
- `VerificationService`。

新的 Course、About Me、AI Memory 和 Practice V2 Service 不得调用以上 Service。

## 3.5 Legacy Prompt 文件

```text
backend/app/ai/prompts/answer_analyzer_v1.txt
backend/app/ai/prompts/calibration_questions_v1.txt
backend/app/ai/prompts/profile_extractor_v1.txt
```

这些版本化 Prompt 描述的是 Legacy 行为。
新行为需要新的 Prompt 文件和版本。
不得静默改写 Legacy Prompt 来生成 Course 输出。

---

# 4. 前端冻结文件

## 4.1 冻结组件

```text
frontend/components/onboarding-flow.tsx
frontend/components/voice-calibration.tsx
frontend/components/today-session.tsx
frontend/components/today-session-live.tsx
frontend/components/practice-hub.tsx
frontend/components/journey-map.tsx
frontend/components/my-english.tsx
```

Course Core 页面不得 import 这些组件。

被冻结的组件行为包括：

- 把未登录 Onboarding 作为产品 shell；
- Profile 确认 gate；
- Voice Calibration gate；
- Today 渲染；
- seven-step Daily progression；
- XP/streak 完成展示；
- 旧 Quick Review；
- 旧的单问题 Mock Interview；
- My English projection；
- Journey map。

## 4.2 冻结的 Legacy API Client Surface

`frontend/lib/api.ts` 是混合的 Legacy client，不得在其中增加新的 Course Core API type 或 function。

以下 export 属于 Legacy：

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

新 Client 必须分别添加到：

```text
frontend/lib/course-api.ts
frontend/lib/about-me-api.ts
frontend/lib/practice-api.ts
```

---

# 5. Legacy 路由和 Endpoint

## 5.1 后端路由前缀

以下当前前缀代表 Legacy 产品 runtime：

```text
/api/v1/profiles
/api/v1/calibration
/api/v1/daily
/api/v1/memory
/api/v1/practice
/api/v1/journey
/api/v1/entry
```

旧路由取消挂载后，`/api/v1/practice` 预留给 Practice V2。
新的 Practice handler 必须来自新的 `practice_v2` 模块，不得通过扩展 `backend/app/api/v1/practice.py` 实现。

## 5.2 具体 Legacy Endpoint

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

阶段 1 必须按照 Build Spec v2.0 停止默认 runtime 挂载，或重定向产品入口。
阶段 0 不修改这些路由。

## 5.3 前端路由

当前 Legacy 路由行为：

```text
/            → AppEntry → Onboarding / Calibration / Today
/practice    → PracticeHub → Quick Review / Legacy Mock Interview
/my-english  → MyEnglish
/journey     → JourneyMap
```

阶段 1 和阶段 2 将替换或重定向这些路由。
在此之前，它们仍是冻结的 Legacy runtime。

---

# 6. 历史数据与 Schema

## 6.1 不可修改的现有 Migration

以下 migration 属于历史记录，绝不能编辑：

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

新 Schema 从 `202609080011` 之后的新 migration 开始。

## 6.2 Legacy 数据表

以下数据表不得成为 Course Core Storage：

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

特殊情况：

- `profiles` 和用户已确认的 `stories` 可以由经过批准的一次性 migration adapter 读取；
- 新 Course Answer 流程不得写入 `stories`；
- `sessions` 和 `attempts` 绝不能获得 Course 语义；
- 所有 Legacy 记录继续作为用户拥有的历史数据保留。

## 6.3 带有字段限制的共享数据表

### `users`

允许共享的身份和偏好字段：

```text
id
interface_language
support_language
timezone
created_at
updated_at
```

仅限 migration 使用，或需要产品审阅后才能使用的字段：

```text
target_role
primary_goal
coaching_style
```

新 runtime 不得读取或写入的 Legacy Progress 字段：

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

`source_documents` 是 About Me Resume Storage 和 provenance 可以复用的基础设施。

允许共享的字段：

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

Legacy extraction 字段：

```text
candidate_profile
extractor_version
```

新的 About Me 行为必须使用新的 Repository 和版本化 extraction 行为。
不得恢复旧 Profile 确认 gate。

## 6.4 Legacy Row Class

`backend/app/db/models.py` 中以下 Class 描述 Historical Data：

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

新的 Course model 必须位于独立模块。
不得给这些 Class 增加 Course column 或 relationship。

`UserRow` 和 `SourceDocumentRow` 是混合的共享 Model，受以上字段限制约束。

---

# 7. Migration Seam

以下文件负责应用组合，因此不是整体冻结：

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

未来允许的修改仅限：

- 挂载新的 Course Core router；
- 从默认 runtime 移除 Legacy router；
- 把登录后入口改为新首页；
- 重定向 Legacy 页面；
- 引入新 App Shell；
- 通过与产品无关的接口连接共享基础设施。

Migration Seam 中禁止：

- Course 业务逻辑；
- 直接操作数据库；
- 复用 Legacy Session/Attempt 作为 Course Storage；
- 隐式调用 Daily、Progress、Reward、Mastery、Retrieval 或 Legacy Memory；
- 临时写入 Legacy Progress。

阶段 0 只记录这些 Seam，不修改其 runtime 行为。

---

# 8. 共享基础设施

以下能力在确认接口与产品无关后可以复用：

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

复用条件：

- 共享基础设施不得反向依赖 Course 业务规则；
- 不得产生 Legacy 副作用；
- 不得跨用户访问；
- Provider adapter 保持在接口之后；
- Legacy schema 不得泄漏到新的公共契约；
- 如果当前混合文件需要大范围修改，应增加新的产品无关模块。

`backend/app/ai/bailian.py`、`backend/app/ai/fakes.py` 和 `backend/app/api/dependencies.py`
目前是混合的组合文件。
修改这些文件必须保持小范围且经过审阅；不得借此把 Legacy 业务逻辑 import 到 Course Core。

---

# 9. 不允许后台运行 Legacy

当前仓库没有独立的 Redis/Celery scheduler，但 Legacy 工作仍可能通过路由和 Service 组合被同步触发。

阶段 1 之后：

- 登录或页面加载不得创建 Daily Session；
- Course 保存不得 enqueue 或调用 Retrieval、Mastery、Reward 或 Progress；
- Course Answer 不得创建 Expression 或 RetrievalOpportunity；
- 自动恢复不得重新打开 Legacy Session；
- application startup hook 不得调度 Legacy 工作；
- Practice V2 完成不得更新 Legacy 状态。

如果后续发现 background runner、scheduled job、database trigger 或 webhook，必须在阶段 1 结束前把它加入本 Manifest。

---

# 10. Legacy 测试

现有 Legacy 测试属于历史回归覆盖，不得通过重写测试来让新的 Course 行为看起来符合 Legacy 契约。

示例：

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

允许的测试修改：

- Legacy router 被有意取消挂载后，调整 test harness；
- 为严重 bug 或安全问题增加 regression coverage；
- 验证回滚；
- 核查历史数据完整性。

新的 Course 行为需要新的测试模块。
不得修改旧 expected value，把 Legacy object 重新定义为 Course object。

---

# 11. 阶段 1 的强制执行目标

阶段 1 必须增加以下自动化检查：

1. 禁止新模块 import 冻结模块；
2. 禁止调用冻结 Service；
3. 执行每个新写入路径前后，Legacy 用户 Progress 保持不变；
4. `sessions`、`attempts`、`expressions`、`expression_attempts` 或 `retrieval_opportunities` 不产生新记录；
5. 默认不挂载 Legacy 产品 router；
6. 新 authenticated entry 跳过 Onboarding、Calibration 和 Today；
7. 旧页面正确重定向；
8. 修改冻结文件时必须提供显式 exception record。

在这些检查建立前，本文件和 Code Review 是执行规则的手段。

---

# 12. Manifest 维护

仓库结构变化时：

1. 对照 `legacy-loop-final-baseline` 检查变更；
2. 对每个触及的 Legacy 相邻文件进行分类；
3. 只有文件分类本身变化时才更新本 Manifest；
4. 不得因为路由已经取消挂载就从冻结清单移除文件；
5. 追加新发现的隐式依赖；
6. 在 `docs/LEGACY_CODE_FREEZE_RULES.md` 中记录批准的例外；
7. 如果变更会修改 Build Spec 行为，必须获得产品批准。

建议使用以下 Git 比较范围：

```text
legacy-loop-final-baseline..HEAD
```

本 Manifest 是边界文件，不是删除计划。
