# FluentLoop 仓库指南（中文审阅译本）

> 本文件是当前工作树中 `AGENTS.md` 的中文审阅译本，不是当前生效的代理指令文件。
> 如译文与英文原文存在差异，以 `AGENTS.md` 为准。对本译本的修改意见只有在审阅通过并同步回英文原文后才会生效。

`FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md` 是产品与架构的权威规格。
`FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md` 和 `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md` 仅作为历史规格保留。
本文件只是编码代理的操作与导航地图；不得把对话历史当作事实来源。

## 里程碑阅读协议

开始或恢复任何里程碑之前：

1. 阅读 `AGENTS.md`；
2. 阅读 `docs/CURRENT_MILESTONE_V1.md`；
3. 阅读 `docs/DECISIONS.md`；
4. 阅读 `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md` 中与当前阶段相关的章节；
5. 如果任务可能影响产品行为、架构边界、数据模型、Memory、Mastery 或跨 Session 行为，实施前必须查阅完整的相关规格。

- 只实施已经明确授权的 Course Core 阶段。不得推断后续阶段或 MVP 之后的范围。
- 保持 `course_catalog_v1` 不变：30 个 Course、59 道 Question、稳定顺序、固定措辞和固定回答重点。
- Question 的选择权属于用户。不得增加 Course 完成、解锁、按天推进、Phase、Mastery、XP、streak 或自动进入下一题等行为。
- 将 Today、Daily Planner、Daily Session、Journey、BUILD/TRANSFER/PERFORM、`current_day`、seven-step loop、Quick Review、XP/streak、Mastery/Aha、Onboarding 和 Voice Calibration 视为冻结的 Legacy。
- 修改路由、共享接缝或任何与 Legacy 相邻的文件之前，必须完整阅读 `docs/LEGACY_FREEZE_MANIFEST.md` 和 `docs/LEGACY_CODE_FREEZE_RULES.md`。
- 新 Course Core、About Me 和 Practice V2 代码不得 import 或调用 Legacy UI、Service、Repository、Session/Attempt、Progress、Reward、Mastery、Retrieval 或旧 Memory Gate。
- 以下产品契约必须保持确定性：ownership、RLS、状态转换、音频互斥、录音导航保护、中文草稿确认、Answer 删除、录音保留、Memory 来源验证和 Legacy 写入隔离。
- AI 对产品机制的决策仅限：判断 Memory 候选是否值得保留，以及选择 CREATE/UPDATE/MERGE/IGNORE。AI 生成的提示、表达素材、参考回答、翻译和反馈属于内容生成，不具备改变产品状态的权限。
- 不允许 AI 编造用户的经历、职责、数字、结果或公司事实。
- 新 AI Memory 只有通过确定性的来源、目标、动作和 ownership 验证后才能自动保存。不得复用或绕过旧的确认式 Memory Gate。
- 新 Course Answer 数据必须使用新的 model、table、repository、service 和 API；不得给 Legacy Session 或 Attempt 增加 Course 语义。
- 使用版本化数据库 migration 和版本化 prompt。
- 进行风险较高的修改前，按照 Build Spec 第 18、22、23 和 26 节建立 Git checkpoint。
- 先检查 Git status，绝不覆盖无关的用户工作。
- 声明里程碑完成前，运行相关测试和检查。

## 里程碑收尾

声明里程碑完成前：

1. 运行所有与当前里程碑相关的测试和检查；
2. 对照 Build Spec 中当前阶段及 MVP 的验收标准检查实现；
3. 明确记录已知限制；
4. 在 `docs/CURRENT_MILESTONE_V1.md` 中更新当前 Course Core 阶段；
5. 只有确实形成或改变了稳定架构决策时，才更新 `docs/DECISIONS.md`；
6. 确认没有意外实现后续 Course Core 阶段、Legacy 行为或 MVP 之后的范围；
7. 报告 Git branch、HEAD、working tree 状态、commit、测试/检查和剩余限制；
8. 除非得到明确指令，否则在 merge、push 或开始下一里程碑前停下等待审阅。

## 代理会话协议

### 开始或恢复

普通的新编码会话按以下顺序阅读：

1. `AGENTS.md`；
2. `docs/PROJECT_STATUS.md`；
3. `docs/HANDOFF.md`；
4. 只有在存在活动 blocker、进行调试或 HANDOFF 引用了 issue 时才阅读 `docs/ISSUES.md`；
5. 当前 Course Core 阶段的执行文档；
6. Build Spec 中与任务相关的章节；
7. 当任务涉及架构边界时阅读 `docs/DECISIONS.md`。

不要自动重新阅读整份 Build Spec，也不要依赖对话历史。
只有当行为、架构、schema、Memory/Mastery、跨 Session 规则或歧义需要时，才扩大上下文范围。

### 工作半径

实施前，明确唯一的当前任务，检查 Git status，识别相关文件，并保护无关工作。
优先进行最小而完整的变更；没有明确需要时，不得进行全仓库重构或重新设计稳定架构。

### 会话交接

保持编码会话简短：目标是完成一个一致的 checkpoint，或大约 15–25 个 turn。
交接前，应达到安全 checkpoint，运行相关检查，更新 `HANDOFF.md`；只有项目状态变化时才更新 `PROJECT_STATUS.md`；调试认知变化时更新 `ISSUES.md`；执行状态变化时更新当前 Phase 文档；只有稳定决策变化时才更新 `DECISIONS.md`。
适当时记录恢复信息并提交一个完整 checkpoint。

### 调试连续性

对于实质性 bug，在稳定的 `ISSUES.md` 条目中记录证据、尝试过的诊断、已排除的原因、相关文件和下一步诊断动作。
没有新证据时，不要重复已经记录的诊断。

### 仓库记忆的职责归属

- `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md`：权威产品与架构要求；
- `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md`：上一版 Course Core 规格，作为历史保留；
- `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md`：仅保存 Legacy Loop 历史要求；
- `docs/LEGACY_FREEZE_MANIFEST.md`：被冻结的文件、路由、符号、数据表和迁移接缝；
- `docs/LEGACY_CODE_FREEZE_RULES.md`：允许和禁止的 Legacy 修改；
- `DECISIONS.md`：稳定架构决策和 ADR 历史；
- `PROJECT_STATUS.md`：精简的项目状态面板；
- `HANDOFF.md`：提供给下一位代理的短期操作上下文；
- `ISSUES.md`：调试连续性和已知问题状态；
- `CURRENT_MILESTONE_V1.md`：当前 Course Core V1 的执行状态与验收状态；
- `CURRENT_MILESTONE.md`：仅保留历史里程碑和生命周期记录。

避免在这些文件之间复制大量内容。
保持这一套文档体系与具体工具无关，使 Codex、Zcode、Claude Code 和其他代理都能使用。

### 上下文效率

优先记录精简摘要、路径、commit hash、issue ID、精确的下一步动作和指定的 Spec 章节。
不要把项目记忆文件变成 changelog、对话记录、bug 日记或 Build Spec 副本。
绝不保存 secret 或 credential。
