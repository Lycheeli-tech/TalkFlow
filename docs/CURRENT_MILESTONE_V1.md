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
| 阶段 3 | 未开始 | 依赖阶段 2 的 App Shell 和 Catalog |
| 阶段 4 | 未开始 | 依赖新的 Course Core 数据边界 |
| 阶段 5 | 未开始 | 不建设通用 AI Coach Orchestrator |
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
- 浏览器 smoke：未登录入口和 `/courses` 认证边界正常；`/journey` 实际落到 `/`，未出现 Today、Calibration、Daily、Journey 或 Quick Review UI。因未使用个人凭据，认证后落点与导航由静态架构/界面契约测试覆盖。
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

## 阶段 4：About Me 与 AI Memory

1. 建立 About Me schema、RLS 和 Repository；
2. 支持多目标岗位、多份 Resume 和补充资料；
3. 实现 Memory CREATE / UPDATE / MERGE / IGNORE；
4. 实现来源验证和事务；
5. 支持全部 Memory 查看和删除；
6. 实现 Answer 删除、Audio 清理和多来源 Memory 处理；
7. 验证 About Me 为空时 Course 仍可用。

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
