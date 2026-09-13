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
| 阶段 5 | COMPLETE | 功能与验证已完成；产品负责人已确认 TBD-003 / TBD-004 并授权 merge/push；checkpoint 为 `course-core-stage-5` |
| 阶段 6 | COMPLETE | 中文 Answer 闭环与用户设备录音验收通过；产品负责人已授权合并、推送 |
| 阶段 7 | COMPLETE | 全部 30 Course / 59 Question 已合并、推送并核对远程 refs |
| 阶段 8 | COMPLETE | Practice V2 功能与验收通过；TTL 已批准（ADR-032），等待 review |

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

### 阶段 5 完成记录

- 状态：COMPLETE；2026-09-13 产品负责人已确认 AI 参考回答入口位置（TBD-003）和 Feedback 面板排列（TBD-004），稳定决定记录于 ADR-030，并明确授权 merge/push；不自动开始阶段 6。
- 分支：`codex/course-core-stage-5`；实现 commit：`50d6d48`；checkpoint tag：`course-core-stage-5`。
- Course Context Builder 只按 authenticated user 装配固定 Catalog、当前 Question / 回答重点、少量 About Me / Resume / Memory / 同题 Answer；非当前 Answer 证据总计最多 10,000 字符，Feedback 当前 Transcript 最多 5,000 字符。
- 已实现独立的提示、表达素材、AI 参考回答 API，以及按 Answer 单行幂等的 Feedback / retry；四份行为 Prompt 均版本化，未建设通用 AI Coach Orchestrator。
- Feedback 只绑定当前 `SAVED` Answer，提供 1–3 条“精确用户原话 + 修改建议”，禁止评分、Mastery、完成度和来源外数字；失败只将 Feedback 标记为 `FAILED`，Answer 与 Transcript 保持 `SAVED`。
- 真实 Bailian smoke 暴露并修复了无资料参考回答编造项目、职责和数字的问题：无可信上下文时现在使用代码控制的显式占位符模板；有上下文时 grounded 段必须附带可精确匹配的来源摘录，来源外数字被拒绝。
- 前端批准布局：参考回答入口与提示、表达素材并列；提示、表达素材、参考回答、Feedback 和 History 使用同一个互斥右侧辅助面板；Feedback 先展示摘要，再展示 1–3 条原话与建议。桌面为 Questions / Answer / Assistant 三栏，375px 为右侧 fixed 抽屉。面板状态独立于 Recorder，切换面板不停止录音。
- 后端完整测试：141 passed；Ruff format/check passed。P3/P4/P5 真实 PostgreSQL 集成：7 passed；最终 P5 单项复跑：1 passed。真实 Bailian 回归：passed。
- 前端 TypeScript、ESLint、production build：passed。认证浏览器：真实提示、安全参考模板、单 Answer Feedback 1–3 条建议、1280px 三栏、375px 抽屉、无横向溢出和 0 console errors 均通过。
- 数据库 migration：无变更；复用阶段 3 已存在的 `course_feedback` 一对一表、RLS 与 ownership 约束。一次性账号、synthetic Answer / Feedback 和临时浏览器 profile 已清理。
- Legacy 隔离：P5 真实数据库测试确认 `current_day`、`current_phase`、XP、streak 及 `sessions`、`attempts`、`expressions`、`expression_attempts`、`retrieval_opportunities` 前后完全不变。
- 尚未实现：中文 Answer、其余 29 个 Course 的 Answer、Practice V2、Course 完成/解锁/自动下一题；这些仍属于阶段 6–8 或明确禁止范围。

## 阶段 6：中文 Answer 闭环

- 分支：`codex/course-core-stage-6`；安全基线：`course-core-stage-5` / `9f08381`。
- 2026-09-13 产品负责人授权开始 P6，并批准支持未确认中文 Draft 跨刷新恢复。
- Draft 仅为可恢复暂存，确认前不进入 History、Feedback 或 Memory；放弃/重新回答清理旧 Draft。

1. 中文录音和最终 STT；
2. 中文转英文整理；
3. 同时展示中文与英文稿；
4. 用户确认后保存；
5. 重新回答和放弃 Draft；
6. 接入最近两条录音；
7. 验证不补充用户未表达事实。

### 阶段 6 完成 checkpoint

- 状态：COMPLETE；设备验收完成，checkpoint tag 为 `course-core-stage-6` / `3f71595`；2026-09-13 产品负责人授权 merge/push 并确认远程目的地和 refs，已快进合并至 `main`；`main`、P6 分支及完成标签已推送到 `Lycheeli-tech/TalkFlow` 并核对远程提交；不自动开始 P7。
- 已实现：中文录音/最终 STT、独立组织 Prompt 与忠实度检查、持久 Draft 列表/恢复、双稿只读展示、确认幂等、放弃/重新回答、确认后 Feedback/Memory 与按语言最近两条录音。
- 整理只接收当前中文 Transcript；逐段来源摘录和来源外数字由代码验证，语义忠实度由独立结构化检查过滤。不使用 About Me、Resume、Memory 或历史补全中文事实。
- 新迁移：`202609130020_chinese_answer_drafts.sql` 已获授权持久应用并登记于配置的测试库；迁移前后 Legacy 全用户进度字段及五张表计数不变。最终 fidelity Prompt 字段真实库回归通过。
- 后端：153 passed、10 opt-in skipped；Ruff check/format passed。组合真实 PostgreSQL/中文 Bailian 回归：9 passed；新增晚到清理失败保护真实库复跑：1 passed。
- 前端：TypeScript、ESLint、production build passed。中文 STT 使用独立 zh 配置，英文默认 en 不变；P6 放弃/重新回答使用页内二次确认。
- 真实服务：一次性账号、合成中文 TTS 音频经实际上传→中文 ASR→忠实整理→待确认→确认保存，重复确认幂等；双稿与 fidelity Prompt 版本实际落库。三个同题同语言确认 Answer 的最旧音频 EXPIRED，最近两条 RETAINED；真实服务操作前后 Legacy 快照不变。
- 浏览器：认证后桌面 1280px 恢复双稿、刷新再恢复、确认及 History 通过；375px 双稿、History 抽屉、放弃和重新回答进入中文引导通过，无横向溢出或最终页面控制台错误。
- 剩余发布门仅为真实设备麦克风录音 smoke：用户已批准 localhost 麦克风及改用 Chrome，但内置浏览器 getUserMedia 请求不返回，当前浏览器工具报告 Chrome 不可用。没有伪造录音或将合成音频测试等同于设备录音；P6 保持 IN PROGRESS，不创建完成 tag。
- 2026-09-13 本次恢复复核：后端 153 passed / 10 opt-in skipped、Ruff check/format、前端 TypeScript/ESLint/production build、20 个 migration 校验均通过；只读真实库登记核对确认 `202609130020` 已存在，未重复迁移。系统 Chrome 窗口存在，但 browser connector 不可用；原生 sky 读取被自动审批拒绝（要求使用 cua_repl，其原生控制当前禁用）。需用户在 Chrome 完成设备 smoke，不能追认为阶段完成。
- 2026-09-13 最终设备门：用户在内置浏览器使用已确认的独立测试账号完成真实设备录音，未注入模拟麦克风或合成音频。两条英文和一条中文 Answer 均为 SAVED；中文设备录音为 `audio/webm;codecs=opus`、31,226 ms，实际 Bailian STT/organizer、两份版本化 Prompt、中文原稿与英文整理稿、confirmed_at/saved_at 及 READY Feedback 已落库。服务日志确认 answers 201、confirm 200、History 200；刷新后 History 仍为三条，中文双稿与时长可查看，核心问题仍选中，中文 Feedback 界面正常。此前设备权限不返回的阻塞已解除。
- 验收证据分工：本次直接核对用户设备录音、确认、保存、刷新持久性与 Feedback；录音期间导航/互斥及 375px Draft 行为沿用已通过的自动/浏览器检查，不声称本次直接观察了用户录音中的每个操作。
- 清理：一次性 Auth 账号、Answer/Feedback/Memory、私有音频及本地凭据/合成音频已删除；持久 Answer 与 Storage 对象残留计数为零。
- 最终 review 账号暂保留：三条用户设备 Answer 与三个私有音频对象供 review；OS 临时状态记录于 HANDOFF，仅由 owner-scoped cleanup 清理，不提交凭据或真实稿件。
- 已知限制：Auth 仍为 sessionStorage 生命周期；未上传设备录音不能跨刷新恢复，只有已归属服务端的 Draft 可恢复；忠实度语义检查依赖模型，不能把精确摘录当作完整语义证明。
- 范围：仍只有 Course 11 可回答；P7/P8 未开始；Legacy 保持冻结。

## 阶段 7：开放其余 29 个 Course

- 2026-09-13 产品负责人授权开始 P7。
- 分支：`codex/course-core-stage-7`；安全基线：已推送的 `main` / `71f606b`，P6 完成标签 `course-core-stage-6` / `3f71595`。
- 范围：全部 Catalog Course 的英文/中文 Answer、TTS、按需 AI 帮助与 Feedback 复用既有引擎；不增加 Catalog 内容或 P8 Practice，不修改 Legacy。

1. 使用同一引擎加载其余 Course；
2. 验证完整 Catalog；
3. 验证全部核心问题和追问；
4. 验证 Course 30 无追问；
5. 禁止 Course 11 特例；
6. 完成全部 Course 响应式 smoke test。

### 阶段 7 完成 checkpoint

- 状态：COMPLETE；完成 checkpoint `course-core-stage-7` / `ac360dd`。2026-09-13 产品负责人授权 merge/push，已快进合并；网络重试后 atomic push 成功，远程 `main` / `66de471`、P7 分支和完成标签 / `ac360dd` 已核对（GIT-07 CLOSED）。
- 移除前后端 Course 11 rollout allowlist；全部 30 Course / 59 Question 复用英文/中文录音、确认、History、TTS、按需支持和 Feedback 引擎。Catalog 内容、ID、顺序和回答重点未变，Course 30 的 follow-up 为 null，非法或跨 Course Question 请求返回 404。
- Course Workspace 按 Course ID 重新挂载；加载时核对当前 ID，忽略过期 Catalog 请求，避免沿用上一门 Course 的题目与状态。页眉动态显示课程序号。
- 空上下文参考回答改为当前静态 Question 加中性真实细节占位符；不再默认要求项目职责/决策/结果，不创建用户经历。
- 自动回归：后端 273 passed / 11 opt-in skipped；Ruff check/format passed；前端 TypeScript、ESLint、production build passed。新增 59 题 API 参数化回归覆盖 TTS 固定文本、回答重点、三类辅助内容、英文幂等保存、中文确认前隔离/确认后 Feedback、按题 History 和直接回答追问；另有全部 59 题无上下文生产 fallback 检查。
- 真实 PostgreSQL：P7 opt-in 检查 1 passed（368.77s），59 题英文保存及 4 个代表性 Course 中文 Draft/确认通过；repository ownership、跨用户 RLS、禁止客户端 INSERT、全用户 Legacy 进度和五表计数不变。外层事务已回滚，未创建真实音频或调用 STT/AI。
- 浏览器：认证后 1280×900 和 375×812 下各遍历 30 Course；桌面全部 59 题可选择，移动题目抽屉打开/切题/关闭通过，Course 30 仅一题。全部页面无横向溢出，英文和中文入口齐全；页面内 Course 01 追问→Catalog→Course 30 重置为 core，History 为当前题。Course 30 实际 Bailian hints、静态回答重点及安全 reference fallback 正常，移动辅助面板在视口内，最终页面无控制台 error。
- 验收对照：阶段 7 六项及 20.3 中任意 Course/直接追问/固定 Catalog/无完成或自动推进/用户隔离/Legacy 写隔离/通用引擎的相关标准通过。录音互斥、导航保护、音频保留和删除、Memory 验证复用 P3–P6，相关自动回归通过；本阶段未逐题重复人工麦克风录音。
- 限制：无新增 migration；未上传录音不跨刷新恢复，已上传中文 Draft 恢复遵循 ADR-031。空 About Me 的参考回答仅提供真实细节占位模板。P6 临时设备 review 数据继续保留，P7 数据库合成记录已回滚。Practice V2 保持禁用；Legacy 冻结。

## 阶段 8：Practice V2

- 2026-09-13 P7 main `66de471`、分支及 `course-core-stage-7` / `ac360dd` 已 atomic push 并核对远程 refs；开始 P8，分支 `codex/course-core-stage-8`。
- 已阅读 Practice 选题、语音过程、整场 Feedback、临时数据/API 和 Legacy 边界要求；TBD-007 已批准，见 ADR-032。
- 已批准：进行中 Run 从创建起保留 24 小时；完成/放弃立即删除临时文本，音频进入幂等清理；无已完成 History。
- 状态：COMPLETE；本地完成标签 `course-core-stage-8`。完成后等待产品负责人 review；未授权 P8 merge/push 或 post-MVP 工作。

1. 随机抽取 3 / 5 题；
2. 逐题语音回答；
3. 暂停、跳题、返回和重答；
4. 整场 Feedback；
5. 鼓励性评分；
6. 不提供 History；
7. 不触发 Legacy 状态。

### 阶段 8 完成 checkpoint

- 独立 `practice_v2` model/repository/service/API/client/UI；新 `practice_runs` 保存进行中 Run 的版本化 JSON 聚合和录音 attempts，`practice_audio_cleanup_jobs` 仅保存清理元数据。不复用 Legacy Session/Attempt、Course Answer、Memory 或旧 Practice。
- 静态 59 Question 随机无放回抽取 3/5 题；测试可注入 seed，生产请求拒绝 seed 和额外字段。未引入 Profile/History/Memory 选题、自由追问、提示、素材、参考回答或逐题纠错/Feedback。
- 英文 turn-based 录音、问题 TTS、原音频回放、最终只读转写、暂停/恢复、跳题、返回和重答已实现。上传先登记所有权，重复请求不复制录音；失败保留音频并限制重试。录音锁定题目、导航、语言和退出，后退/刷新/关闭有保护；音频播放互斥，晚到播放请求不会打断录音。
- 整场结束才调用版本化 `practice_feedback_v1`，输出优点、改进建议、0–100 鼓励分及非能力/正式测评/通过率说明。模型选择 transcript-only quote ID，代码还原精确摘录和 Question ID 后验证；生成失败保留已保存回答。完成立即删除 Run/临时文字，仅当前响应显示报告，无已完成 History。
- ADR-032 固定 24 小时 TTL 不因暂停延长；完成、放弃、过期和删号通过事务触发器登记私有音频清理。失败指数退避且任务持久保留；晚到上传重新登记已删除任务，旧 worker 不删除新登记的任务。CAS revision/处理 lease 防止晚到 STT 或 Feedback 覆盖/删除新状态。
- 后端最终完整回归：292 passed / 13 opt-in skipped；Ruff check/format passed。真实 PostgreSQL P8：1 passed（18.81s），覆盖 ownership、RLS、客户端无直写权限、幂等/CAS、完成删除、过期隔离、失败退避和重新登记并发保护；合成数据外层事务回滚，Legacy 全用户进度及五表、Course/Transcript/Feedback/Memory 快照不变。
- 前端 TypeScript、ESLint、production build passed；21 个 migration 校验 passed。迁移 `202609130021_practice_v2_runs.sql` 已应用并登记于配置的 development/test 数据库，Legacy/Course/Memory 快照不变；未对 production 执行迁移。
- 真实服务：固定稿 Bailian Feedback fixture 1 passed（9.72s）；3 题合成语音完整 TTS→私有上传→STT→精确回放→整场 Feedback 95 分→完成 GET 404 通过，Legacy/Course/Memory owner 快照不变。5 题服务场次（一题合成语音、四题显式跳过）在浏览器完成并展示 92 分报告，刷新后无旧报告。
- 浏览器：3/5 题、暂停刷新恢复、跳题/返回、结束前无 Feedback、录音保护、实际设备静音失败及原录音重试、双语状态保持、1280px/375px 无横向溢出通过。移动 App Shell backdrop-filter 导致导航遮挡语言按钮，已在原 mobile breakpoint 修复；Practice/Course 11 实际语言点击及导航边界复核通过，最终 console errors 为零。
- 清理：P8 disposable owner 的 Run、cleanup job、私有 Practice Storage 对象均为 0；P6 原三条设备 Course Answer/录音及 Auth 保留。用户原账号 Course 数据未修改。
- 验收对照：阶段 8 七项，以及 20.3 的 1/2、7/9/10、22–29 相关条目通过；其余 Course/About Me 合约沿用 P3–P7 并通过完整自动回归。无 Legacy 文件/schema/进度变更，无后续或 post-MVP 范围。
- 限制：报告仅在完成响应当前页面显示，刷新或完成响应丢失不能恢复。未上传设备录音不跨刷新恢复，已上传进行中回答在 24 小时内可恢复。音频异步清理，失败保留任务重试；反馈语义质量依赖模型，精确摘录不等于正式能力评测。本次未声称三/五题均完成真人口述，设备静音测试和合成语音闭环分别记录。
- Git：`codex/course-core-stage-8`；批准 checkpoint `75716c2`，完成 HEAD 由 `course-core-stage-8` 标签确定。仅原有 `frontend/next-env.d.ts` 改动保留并排除提交。下一步 review，不自动 merge/push。

### Review 修复：中文文件名简历上传

- RESUME-09 CLOSED：私有存储拒绝中文对象名，未捕获异常导致浏览器 `Failed to fetch`。
  存储对象统一使用 owner/document 下的 `resume.pdf`，SourceDocument 保留完整原文件名；
  存储/网络失败返回可读 503。旧路径、用户资料、schema 和 Legacy 业务不变。
- 合成探针 Unicode 400 / ASCII 200 复现；修复后独立账号中文 PDF 上传 201、解析、列表、
  原名显示和删除通过，账号及 source/job/Storage 残留均为 0。完整后端 298 passed / 13 skipped，
  Ruff check/format passed。后端已重启，About Me 已刷新，原文件可直接重传。
- 修复作为 P8 后续本地 checkpoint；完成标签 `course-core-stage-8` / `04fbfce` 保持不变，仍待 review。

## 阶段更新规则

每次开始、恢复或结束一个阶段时，必须更新：

1. 当前阶段状态；
2. 已完成范围；
3. 验证证据；
4. 已知限制或阻塞；
5. Git branch、HEAD 和 checkpoint；
6. 下一项明确动作。

阶段完成前必须对照 Build Spec 中对应阶段要求以及第 20.3 节的相关关键验收标准。未经明确授权，不得自动开始下一阶段。
