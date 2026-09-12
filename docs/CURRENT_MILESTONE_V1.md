# FluentLoop Course Core V1 当前阶段

## 文档角色

- 本文件是 Course Core V1 阶段执行状态和阶段交接的当前入口。
- 产品与架构要求以 `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md` 为准。
- `docs/CURRENT_MILESTONE.md` 仅保留旧项目和既往里程碑历史，不再作为 Course Core V1 的当前阶段入口。
- 阶段范围发生变化时，必须先按照 Build Spec 第 26 节完成变更审批，再同步更新本文件。

## 当前状态

| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 阶段 0 | COMPLETE | 全部阶段 0 文档已通过产品负责人审阅；安全 checkpoint 为 `course-core-stage-0-v2.1` |
| 阶段 1 | COMPLETE | 已由产品负责人确认并合并、推送；checkpoint 为 `course-core-stage-1` |
| 阶段 2 | COMPLETE | 新 App Shell、三入口首页、只读 Catalog 和 30 / 59 确定性校验已完成 |
| 阶段 3 | COMPLETE | Course 11 英文 Answer 最小闭环已确认、合并并推送；checkpoint 为 `course-core-stage-3` |
| 阶段 4 | COMPLETE | 已由产品负责人确认并合并、推送；checkpoint 为 `course-core-stage-4` |
| 阶段 5 | IN PROGRESS | 功能与验证已完成；等待产品负责人确认 TBD-003 / TBD-004 后方可关闭 |
| 阶段 6 | 未开始 | 复用阶段 3 的 Answer、Audio 和 Transcript 基础设施 |
| 阶段 7 | 未开始 | 所有 Course 必须复用同一通用引擎 |
| 阶段 8 | 未开始 | 依赖 Catalog、录音、STT 和 Feedback 基础设施 |

## 阶段 0：规格和安全边界

1. 审核并批准本 Build Spec；
2. 将本文件定版为正式 Build Spec；
3. 更新 `AGENTS.md`；
4. 追加 superseding ADR；
5. 建立 Legacy Freeze Manifest；
6. 建立 Legacy Code Freeze Rules；
7. 创建 Git 安全 checkpoint。

阶段 0 必须把第 18 节转化为正式工程约束。

## 阶段 1：停止旧路径运行并封存 Legacy

1. 新登录入口不再进入 Onboarding / Calibration / Today；
2. 停止默认挂载 Daily、Calibration、Journey、Quick Review；
3. 将旧页面 URL 重定向；
4. 标记全部 Legacy 模块；
5. 禁止 Course Core import 或调用 Legacy；
6. 限制 Legacy 修改类型；
7. 加入“新路径不修改旧进度”测试；
8. 加入“Course Core 不依赖 Legacy”架构测试。

阶段 1 的重定向不得指向不存在的页面。开发时可以先完成阶段 2 路由壳；部署时阶段 1 和 2 必须共同通过发布门。

### 阶段 1 完成记录

- 状态：COMPLETE；已由产品负责人确认并合并、推送后开始阶段 2。
- 分支：`codex/course-core-stage-1`；checkpoint tag：`course-core-stage-1`。
- 默认后端 runtime 仅挂载 `/api/v1/health`；Legacy users、profiles、calibration、daily、memory、practice、journey 和 entry router 仅在历史回归测试的显式 rollback app 中挂载。
- `/` 使用独立的 Stage 1 Auth 安全入口；登录不查询 Profile、Calibration、Daily Session 或旧进度，也不 import Legacy UI/API client。
- `/practice`、`/journey`、`/my-english` 均重定向到已存在的 `/`，不再挂载旧页面。
- `architecture/legacy_freeze_v1.json` 以路径、分类和 SHA-256 标记冻结文件；架构测试校验冻结文件、禁止依赖、默认 router、零产品写入口和旧 URL 重定向。
- 完整后端测试：94 passed；Ruff check/format：passed；前端 TypeScript、ESLint、production build：passed。
- Production HTTP smoke：`/` 返回 200；三个旧页面均返回 307 且 Location 为 `/`。
- 数据库 migration：无变更；未创建或修改 Course、About Me、Practice V2 schema。
- 已知限制：Stage 1 安全入口有意不显示 P2 的 Courses、Practice、About Me 功能入口；Stage 1 没有新产品写路径，因此当前“不写旧进度”覆盖为默认 runtime 零产品写 endpoint 与静态依赖隔离，后续每个新写路径仍须按第 18.8 节加入前后快照测试。

## 阶段 2：新 App Shell、首页与 Catalog

1. 建立不依赖 Today 的新 App Shell；
2. 首页显示三个并列入口；
3. 建立独立路由边界；
4. 建立 `course_catalog_v1`；
5. 实现只读 Course 列表；
6. 完成 30 / 59 确定性校验；
7. 接入旧 URL 重定向；
8. 完成登录落点、导航和 Legacy 不挂载 smoke test。

未完成功能的入口在开发中必须通过 feature flag 隔离。

### 阶段 2 完成记录

- 状态：COMPLETE；等待产品负责人 review，不自动开始阶段 3。
- 分支：`codex/course-core-stage-2`；checkpoint tag：`course-core-stage-2`。
- `/` 在认证后进入不依赖 Today 的新 App Shell；桌面端和移动端均提供 Courses、Practice、About Me 三个并列入口。
- Courses 已启用；尚未进入实施阶段的 Practice V2 和 About Me 通过显式 feature flag 禁用，直达路由显示安全占位，不挂载 Legacy。
- 建立独立只读 Course API 与前端 client；`course_catalog_v1` 固定 30 个 Course、59 个 Question、稳定顺序、稳定 ID、固定问题文案与中英文名称/回答重点。
- 产品负责人批准将现有中文定稿忠实翻译为英文定稿，不增加或改变语义；稳定决定记录于 ADR-027。
- Course 列表与单 Course 只读页面已完成；Answer、History、录音、Feedback、自动下一题等阶段 3+ 能力均未实现。
- `/journey`、`/my-english` 继续重定向到 `/`；Legacy API 仍未在默认 runtime 挂载。
- 后端完整测试：102 passed；Ruff check/format：passed；前端 TypeScript、ESLint、production build：passed。
- HTTP smoke：Catalog 返回 30 / 59，Course 30 无追问；新路由返回 200，两个旧 URL 返回 307 到 `/`，Legacy API 返回 404。
- 浏览器 smoke：使用一次性已确认测试账号验证登录后直接进入新首页、三个同级入口、30 门 Course 列表、任意 Course 详情、中英文切换、Practice/About Me feature gate，以及 `/journey`、`/my-english` 重定向；未出现 Today、Calibration、Daily、Journey 或 Quick Review UI。测试后已退出并删除一次性账号。
- 数据库 migration：无变更；阶段 2 仅提供静态只读 Catalog，不创建 Course Answer、About Me 或 Practice V2 schema。
- 已知限制：Practice 和 About Me 有意保持禁用；Course 页面仅只读；认证 session 仍沿用 Stage 1 的 sessionStorage 生命周期；Stage 3 的 Answer 写路径上线时必须加入 Legacy 字段及表数量前后快照集成测试。

## 阶段 3：Course 11 英文 Answer 最小闭环

1. 创建 Course Answer、Transcript、Feedback schema、RLS 和 Repository；
2. 建立 Single Course Page；
3. 实现 Question 自由切换；
4. 实现 TTS、英文录音和最终 STT；
5. 实现音频互斥和离页、切题保护；
6. 保存 Answer 并提供 History；
7. 从第一次保存起执行最近两条录音；
8. 实现幂等、失败恢复和 Legacy 写入禁令测试。

阶段结束后，即使没有 About Me、帮助、中文回答或 Practice，Course 11 英文流程也必须独立运行。

### 阶段 3 完成记录

- 状态：COMPLETE；等待产品负责人 review，不自动开始阶段 4。
- 分支：`codex/course-core-stage-3`；checkpoint tag：`course-core-stage-3`。
- 新增独立 Course Answer、Transcript、Feedback schema、RLS、Repository、Service、API 和前端 client；authenticated 只能通过 RLS 读取自己的数据，不能绕过 API 直接写入。
- Course 11 使用通用 Answer 引擎开放英文流程：核心问题与追问自由切换、Catalog 原文 TTS、turn-based 录音、先保存私有原始音频、最终 STT、只读 Transcript、History 和录音回放；其余 29 个 Course 继续只读。
- 录音时锁定 Question、返回 Courses、App Shell 导航和退出；浏览器后退、刷新、关闭触发保护；History 面板可继续开关但录音期间禁止播放，所有音频播放互斥。
- 幂等键按用户唯一；中断在音频已归属后可对同一 Answer 重试；STT 失败保留同一音频和 Answer。失败音频在最近一次处理失败 3 天后到期并自动清理，稳定决定记录于 ADR-028。
- 同一 `user_id + question_id + answer_language` 只保留最新两条已保存录音；第三条保存成功后清理最旧对象，保留 Answer、Transcript 和 History；清理失败不会回滚新 Answer，并保留可重试状态。
- 后端完整测试：121 passed、2 个真实 PostgreSQL 集成测试按显式环境门单独 passed；Ruff check：passed；前端 TypeScript、ESLint、production build：passed。
- 数据库集成：真实 RLS 两用户隔离、authenticated 无直写权限，以及 Course Service 写入前后 `current_day`、`current_phase`、XP、streak 和 Legacy 五张表计数完全不变；测试数据已回滚或删除。
- 真实服务 smoke：Catalog TTS、Supabase 私有音频、Bailian 最终 STT、保存、History 和回放通过；连续保存三条后音频状态为 `[RETAINED, RETAINED, EXPIRED]`，最旧 Transcript 仍保留。
- 浏览器 smoke：认证后 Course 11、自由切题、History/回放、桌面端和 375px 布局通过，375px 无横向溢出；一次性账号、三条 Answer/Transcript 和剩余音频对象已删除。
- 数据库 migration：`202609120012_course_answers.sql` 和 `202609120013_course_answer_write_boundary.sql` 已应用并登记到当前配置的测试库；无 Legacy schema 或数据变更。
- 已知限制：浏览器设备麦克风授权出现后未由自动化代替用户批准，因此真实设备的按钮录音未纳入本次自动 smoke；录音状态机、互斥和导航守卫由 TypeScript/ESLint/build、静态界面契约和真实上传闭环共同覆盖。Practice、About Me、中文 Answer、AI 帮助与 Feedback 生成仍按阶段 4–8 禁用；Feedback 阶段 3 仅建立 schema。

## 阶段 4：About Me 与 AI Memory

1. 建立 About Me schema、RLS 和 Repository；
2. 支持多目标岗位、多份 Resume 和补充资料；
3. 实现 Memory CREATE / UPDATE / MERGE / IGNORE；
4. 实现来源验证和事务；
5. 支持全部 Memory 查看和删除；
6. 实现 Answer 删除、Audio 清理和多来源 Memory 处理；
7. 验证 About Me 为空时 Course 仍可用。

### 阶段 4 完成记录

- 状态：COMPLETE；等待产品负责人 review，不自动开始阶段 5。
- 分支：`codex/course-core-stage-4`；checkpoint tag：`course-core-stage-4`。
- 新增独立 `about_me_profiles`、`target_roles`、`memory_items`、`memory_sources` schema、RLS、Repository、Service、API 与前端 client；About Me 支持多个目标岗位、多份独立私有 Resume、补充资料，以及全部 Memory 的查看和删除。
- About Me 为空不构成 gate；认证后可直接打开任意 Course，未增加 Onboarding、Calibration、完成度或自动进度行为。Practice V2 仍由 feature flag 禁用。
- 新 `memory_decision_v1` 只允许 AI 提议 CREATE / UPDATE / MERGE / IGNORE；应用层在事务中验证用户所有权、来源类型、来源 ID、字段路径、逐字可核对摘录和目标 Memory，数据库使用延迟约束禁止无来源 Memory。AI 不持有数据库执行权，失败不回滚已保存 Source 或 Answer。
- Memory 支持多来源；删除 Resume、目标岗位、补充资料或 Course Answer 时只移除对应来源，仍有其他来源则保留 Memory，最后一个来源消失时在同一事务中删除 Memory。
- Course History 新增 Answer 删除确认；Answer、Transcript、Feedback 级联删除，相关 Memory 来源/孤儿同步清理。Answer 音频和 Resume 对象均先登记持久 cleanup job，再尝试对象删除；失败不恢复产品数据，由后台任务幂等重试。
- 后端完整测试：130 passed；6 个真实 PostgreSQL 集成测试按显式环境门单独 passed；Ruff format/check：passed。前端 TypeScript、ESLint、production build：passed。
- 真实数据库验证：CREATE / UPDATE / MERGE / IGNORE、四种来源、伪造摘录拒绝、无来源提交拒绝、两用户 RLS、authenticated 无直写权限、多来源删除、Resume cleanup job 与 P3 回归均通过；`current_day`、`current_phase`、XP、streak 和 Legacy 五张表前后完全不变。
- 真实服务 smoke：Bailian 对完全合成 Course Answer 返回 CREATE，经来源验证后自动保存；两份合成 PDF 使用 Supabase 私有存储完成解析、独立列出、逐份删除，数据库与对象 cleanup job 均归零；账号级联删除已验证。
- 浏览器 smoke：一次性认证账号验证 About Me 空态、两个目标岗位、来源聚合 Memory、补充资料、双语切换、Courses 仍可直接打开，以及 375px `scrollWidth <= innerWidth`；控制台无 error，测试账号和数据已删除。
- 数据库 migration：`202609120014` 至 `202609120019` 已应用并登记到当前配置的测试库；其中 `015` 建立延迟无来源约束，`016`–`018`按不可变迁移历史修复触发器跨表记录解析、删号级联和 Auth 执行权限，`019` 增加 Resume cleanup job。无 Legacy schema 或数据变更。
- 已知限制：About Me 当前只显示 Memory 的来源类型与摘录，不提供来源对象详情跳转；AI Memory 没有公开 action endpoint；Practice、AI 帮助/Feedback、中文 Answer 和其余 Course 回答仍按阶段 5–8 禁用。

## 阶段 5：按需 AI 生成与 Course Feedback

1. 建立 Course Context Builder；
2. 实现需要提示；
3. 实现表达素材；
4. 实现 AI 参考回答；
5. 实现单次 Answer Feedback；
6. 完成三栏与移动端抽屉；
7. 实现每项 AI 能力的失败隔离；
8. 验证生成能力不能改变页面、Answer 或 Legacy 状态。

不建设通用 AI Coach Orchestrator。

### 阶段 5 当前记录

- 状态：IN PROGRESS；功能实现与技术验证完成，等待产品负责人确认 AI 参考回答入口位置（TBD-003）和 Feedback 面板排列（TBD-004）。
- 分支：`codex/course-core-stage-5`；尚未创建完成 tag、merge 或 push。
- Course Context Builder 只按 authenticated user 装配固定 Catalog、当前 Question / 回答重点、少量 About Me / Resume / Memory / 同题 Answer；非当前 Answer 证据总计最多 10,000 字符，Feedback 当前 Transcript 最多 5,000 字符。
- 已实现独立的提示、表达素材、AI 参考回答 API，以及按 Answer 单行幂等的 Feedback / retry；四份行为 Prompt 均版本化，未建设通用 AI Coach Orchestrator。
- Feedback 只绑定当前 `SAVED` Answer，提供 1–3 条“精确用户原话 + 修改建议”，禁止评分、Mastery、完成度和来源外数字；失败只将 Feedback 标记为 `FAILED`，Answer 与 Transcript 保持 `SAVED`。
- 真实 Bailian smoke 暴露并修复了无资料参考回答编造项目、职责和数字的问题：无可信上下文时现在使用代码控制的显式占位符模板；有上下文时 grounded 段必须附带可精确匹配的来源摘录，来源外数字被拒绝。
- 前端候选布局：提示、表达素材、参考回答、Feedback 和 History 使用同一个互斥右侧辅助面板；桌面为 Questions / Answer / Assistant 三栏，375px 为右侧 fixed 抽屉。面板状态独立于 Recorder，切换面板不停止录音。
- 后端完整测试：141 passed；Ruff format/check passed。P3/P4/P5 真实 PostgreSQL 集成：7 passed；最终 P5 单项复跑：1 passed。真实 Bailian 回归：passed。
- 前端 TypeScript、ESLint、production build：passed。认证浏览器：真实提示、安全参考模板、单 Answer Feedback 1–3 条建议、1280px 三栏、375px 抽屉、无横向溢出和 0 console errors 均通过。
- 数据库 migration：无变更；复用阶段 3 已存在的 `course_feedback` 一对一表、RLS 与 ownership 约束。一次性账号、synthetic Answer / Feedback 和临时浏览器 profile 已清理。
- Legacy 隔离：P5 真实数据库测试确认 `current_day`、`current_phase`、XP、streak 及 `sessions`、`attempts`、`expressions`、`expression_attempts`、`retrieval_opportunities` 前后完全不变。
- 尚未实现：中文 Answer、其余 29 个 Course 的 Answer、Practice V2、Course 完成/解锁/自动下一题；这些仍属于阶段 6–8 或明确禁止范围。

## 阶段 6：中文 Answer 闭环

1. 中文录音和最终 STT；
2. 中文转英文整理；
3. 同时展示中文与英文稿；
4. 用户确认后保存；
5. 重新回答和放弃 Draft；
6. 接入最近两条录音；
7. 验证不补充用户未表达事实。

## 阶段 7：开放其余 29 个 Course

1. 使用同一引擎加载其余 Course；
2. 验证完整 Catalog；
3. 验证全部核心问题和追问；
4. 验证 Course 30 无追问；
5. 禁止 Course 11 特例；
6. 完成全部 Course 响应式 smoke test。

## 阶段 8：Practice V2

1. 随机抽取 3 / 5 题；
2. 逐题语音回答；
3. 暂停、跳题、返回和重答；
4. 整场 Feedback；
5. 鼓励性评分；
6. 不提供 History；
7. 不触发 Legacy 状态。

## 阶段更新规则

每次开始、恢复或结束一个阶段时，必须更新：

1. 当前阶段状态；
2. 已完成范围；
3. 验证证据；
4. 已知限制或阻塞；
5. Git branch、HEAD 和 checkpoint；
6. 下一项明确动作。

阶段完成前必须对照 Build Spec 中对应阶段要求以及第 20.3 节的相关关键验收标准。未经明确授权，不得自动开始下一阶段。
