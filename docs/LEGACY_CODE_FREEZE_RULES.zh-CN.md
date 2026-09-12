# FluentLoop Legacy Code Freeze Rules（中文审阅译本）

> 本文件是当前工作树中 `docs/LEGACY_CODE_FREEZE_RULES.md` 的中文审阅译本，不是当前生效的 Freeze Rules。
> 如译文与英文原文存在差异，以英文原文为准。对本译本的修改意见经审阅并同步回英文原文后才会生效。

## 0. 状态和权威来源

- 状态：ACTIVE；
- 生效日期：2026-09-12；
- 产品权威来源：`FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md`；
- 架构决策：`docs/DECISIONS.md` ADR-025；
- 冻结清单：`docs/LEGACY_FREEZE_MANIFEST.md`；
- 基线 tag：`legacy-loop-final-baseline`。

这些规则定义冻结的 Legacy Loop 可以如何修改，以及禁止如何修改。

---

# 1. 强制规则

1. 禁止为 Legacy 模块增加新的产品功能；
2. 禁止新 Course Core import Legacy UI、Service、Repository；
3. 禁止新代码调用 Daily、Reward、Mastery、Retrieval 等 Legacy Service；
4. 禁止修改 Legacy 数据模型以适配 Course；
5. 禁止给 Legacy Session / Attempt 增加 Course 语义；
6. 禁止新页面读取或写入 `current_day`、XP、streak、phase、mastery；
7. Legacy 代码仅允许严重 bug 修复、安全修复、回滚支持和历史数据核查；
8. 所有例外修改必须显式说明原因。

以上八条是强制规范。
其余章节负责将这些规范转化为可执行规则。

---

# 2. 禁止的修改

## 2.1 产品行为

禁止：

- 增加新的 Today card 或 recommendation；
- 增加 Daily step、duration、Phase rule、Reward、streak 行为或 Journey 行为；
- 增加新的 Quick Review 或 Legacy Mock Interview 行为；
- 重新把 Onboarding 或 Voice Calibration 作为 Gate；
- 增加新的 Mastery、Aha、Expression、Review 或 Retrieval 规则；
- 从新首页重新开放 Legacy 行为；
- 在 Course、Practice V2 或 About Me 中展示旧 Progress。

## 2.2 依赖方向

新 Package 不得 import：

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

前端 Course Core 不得 import：

```text
onboarding-flow
voice-calibration
today-session
today-session-live
practice-hub
journey-map
my-english
```

## 2.3 数据模型

禁止：

- 给 Legacy `sessions` 或 `attempts` 增加 `course_id` 或 `question_id`；
- 给 Legacy `question_type` 增加 Course Answer 类型；
- 为了强行复用 Course 而放宽 Legacy Attempt 的 unique constraint；
- 把新的 Course model 放进 `backend/app/db/models.py`；
- 把新的 Course schema 放进 `backend/app/schemas.py`；
- 把 Course History 保存在 Expression、Story、RetrievalOpportunity 或 LearnerAssessment 中；
- 把旧 Attempt row 当作新的 Course History；
- 修改旧 migration。

## 2.4 Legacy 状态

新 runtime 不得读取或写入：

```text
users.default_session_length
users.current_day
users.current_phase
users.xp
users.current_streak
users.last_completed_date
users.program_completed_at
```

新 runtime 不得创建或更新：

```text
sessions
attempts
learner_assessments
expressions
expression_attempts
error_patterns
retrieval_opportunities
```

经过批准的一次性 migration 可以读取 `profiles`、`source_documents` 和已确认的 `stories`，但正常 Course runtime 不得写入 Legacy 学习状态。

## 2.5 隐式运行

不能只隐藏 UI，却让 Legacy 行为继续运行。

阶段 1 完成后，禁止：

- 登录时自动创建 Daily Session；
- 在 App Entry 自动恢复 Daily Session；
- Course Answer 完成后更新 Reward 或 Progress；
- 自动安排 Review；
- 创建 RetrievalOpportunity；
- 执行 Mastery 判断；
- 生成 Aha；
- 新页面调用旧 Practice API；
- 通过 database trigger、job 或 startup hook 为新操作修改 Legacy 状态。

---

# 3. 允许的修改

Legacy 文件只有在以下情况下才允许修改：

1. 影响回滚或历史数据正确性的严重 bug；
2. 安全漏洞；
3. 回滚支持；
4. 历史数据核查或导出；
5. 阶段 1 所需的最小路由取消挂载或重定向；
6. 保持共享基础设施安全所必需的最小兼容修复。

“允许”不等于可以自动修改。
除 Manifest 预先声明的 Migration Seam 外，每个 Legacy diff 都必须执行第 5 节的例外流程。

---

# 4. Migration Seam 规则

被归类为 `MIGRATION_SEAM` 的文件，如果 diff 仅限以下内容，可以不按 Legacy Feature Exception 处理：

- Router 注册；
- Dependency 组合；
- Authenticated Entry 目的地；
- 旧路由重定向；
- 新 App Shell wiring；
- 从默认 runtime 移除 Legacy 挂载。

如果同一文件还修改以下内容，就必须按 exception 处理：

- Daily 逻辑；
- 除跳过或移除外的 Profile/Calibration Gate 逻辑；
- Legacy 持久化；
- Reward、Mastery、Retrieval 或 Progress 行为；
- 仍由 Legacy consumer 使用的 Legacy response 语义。

当 Migration Seam 包含混合逻辑时，应提取新的 Course 模块，而不是继续扩大 Seam。

---

# 5. 例外流程

修改冻结文件前：

1. 指明准确的文件和 symbol；
2. 把原因归类为严重 bug、安全、回滚或历史数据核查；
3. 解释为什么不能通过新模块或 Migration Seam 解决；
4. 列出受影响的 Legacy route、table 和 test；
5. 确认没有引入 Course 语义；
6. 定义回滚方式；
7. 实施前获得明确审阅；
8. 在下方记录例外。

例外记录模板：

```text
Exception ID：
日期：
状态：
原因类别：
文件与 symbol：
受影响的 Legacy 行为：
对 Course Core 的影响：
为什么不能使用新模块方案：
测试：
回滚：
批准人：
关联 commit：
```

## 5.1 已批准例外

阶段 0 没有批准任何例外。

---

# 6. 阶段 1 必须建立的自动化约束

## 6.1 Import Boundary

建立 architecture test 或等价静态规则，在以下情况使检查失败：

- `backend/app/course/**` import 冻结模块；
- `backend/app/about_me/**` import 冻结模块；
- `backend/app/practice_v2/**` import 冻结模块；
- 新的前端 Course/About Me/Practice V2 组件 import 冻结组件或 Legacy client function。

## 6.2 No-Old-Write 测试

对每个新的写入路径：

1. 快照 Legacy Progress 字段和相关 table count；
2. 执行新的操作；
3. 验证全部 Legacy Progress 字段保持不变；
4. 验证没有创建 Legacy Session、Attempt、Expression、ExpressionAttempt 或 RetrievalOpportunity；
5. 验证新记录只存在于新的 Course Core 数据表。

至少覆盖：

- 创建 Course Answer；
- 保存英文 Answer；
- 确认中文 Answer；
- 重试 Course Feedback；
- Memory CREATE / UPDATE / MERGE；
- 删除 Answer；
- 完成 Practice V2。

## 6.3 Runtime Mount 测试

验证：

- 登录后进入新首页；
- 不要求确认 Profile；
- 不要求 Calibration；
- 不渲染 Today；
- 默认不挂载 Legacy 产品 router；
- 旧前端 URL 按批准的路由表重定向；
- 只有旧 handler 被取消挂载后，`/api/v1/practice` 才由 Practice V2 提供。

## 6.4 Frozen Diff 检查

CI 或阶段收尾流程必须使用以下范围比较冻结文件：

```text
legacy-loop-final-baseline..HEAD
```

任何发生变化的冻结文件必须：

- 属于已声明的 Migration Seam 修改；或
- 引用已批准的 Exception Record。

---

# 7. 审阅检查表

关闭 Course Core 阶段前，确认：

- 没有冻结文件在未声明的情况下发生变化；
- 没有新模块 import Legacy；
- 没有把 Course schema 加入 Legacy model；
- 没有 Course API 调用 Legacy Service；
- 没有新页面读取 Legacy Progress；
- 没有新的写入修改 Legacy table 或 Progress 字段；
- 共享基础设施保持与产品无关；
- 旧数据仍可用于回滚和核查；
- 测试证明不存在隐式 Legacy 行为；
- 所有批准的例外都已记录。

---

# 8. 与删除的关系

Code Freeze 不等于删除。

除非后续批准的 Spec 明确授权删除计划，否则阶段 0–8 不得删除 Legacy 代码、数据表、migration、test 或历史记录。

取消挂载路由不等于删除其历史实现。

推荐顺序：

```text
freeze
  ↓
停止 runtime 挂载
  ↓
并行建立 Course Core
  ↓
验证新产品稳定性
  ↓
单独审阅删除候选
```

本文件没有批准任何删除候选。
