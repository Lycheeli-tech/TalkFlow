# 稳定架构决策（中文审阅译本）

> 本文件是当前工作树中 `docs/DECISIONS.md` 的中文审阅译本，不是当前生效的 ADR 文件。
> 如译文与英文原文存在差异，以 `docs/DECISIONS.md` 为准。对本译本的修改意见经审阅并同步回英文原文后才会生效。

如果本摘要与 Build Spec 存在差异，以 `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md` 为准。
`FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md` 和 `FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md` 仅作为历史保留。

未来的决策通常应当追加，而不是静默改写历史决策。
如果后续决策取代较早的 ADR，必须明确引用被取代的 ADR。

### ADR-001 — 模块化单体

MVP 使用模块化单体架构。

### ADR-002 — 应用技术栈

前端使用 Next.js，后端使用 FastAPI。

### ADR-003 — 数据平台

通过 Supabase 使用 PostgreSQL、认证和 Storage。

### ADR-004 — 结构化 Memory 优先

优先使用结构化 Memory。提取出的候选信息只有通过 Memory Gate 后才算已确认。

### ADR-005 — Agent 角色

Coach 和 Interviewer 共享用户数据，但采用不同的政策和交互行为。

### ADR-006 — 确定性 Mastery

Mastery 状态转换必须是确定性且有证据支持的。不得让 LLM 决定持久化的 Mastery 状态。

### ADR-007 — Turn-Based Voice

MVP 使用 turn-based voice，不使用 realtime voice。

### ADR-008 — 不引入 Agent Framework

MVP 不引入 LangChain 或 LangGraph。

### ADR-009 — Curriculum 策略

使用固定 Curriculum 骨架和自适应复习层。

### ADR-010 — Provider 抽象

LLM、STT 和 TTS 必须位于 Provider 抽象之后。具体 Provider 和模型可以在相应里程碑选择。

### ADR-011 — 版本化演进

使用版本化数据库 migration；会改变行为的 prompt 必须具有显式版本。

### ADR-012 — 共享 Calibration Session

Voice Calibration 使用通用 Session model，并设置 `session_type = CALIBRATION`；这不代表可以调用 Daily Session 编排。

### ADR-013 — 历史 Learner Assessment

口语能力保存在独立且可版本化的 LearnerAssessment 中，并与 Calibration Session 关联；它不属于已确认的背景 Profile。

### ADR-014 — 定性的 Calibration 等级

MVP 使用 NEEDS_WORK、DEVELOPING、FUNCTIONAL 和 STRONG，并提供定性观察，避免根据三次回答制造虚假的数字精度。

### ADR-015 — 受约束的混合 Question

Question 类别和顺序是确定性的：EXPERIENCE、MOTIVATION、PROJECT。
Provider 可以根据已确认的 Profile 个性化措辞，但不得改变类别或编造经历。

### ADR-016 — 可恢复的语音处理顺序

先保存用户音频并关联 Attempt，再执行 STT；先保存 Transcript，再执行分析。
下游失败必须保留已有产物，并以幂等方式重试同一个 Attempt。

### ADR-017 — 有边界的自适应 Daily 规划

30-Day Interview Bootcamp 采用固定的 BUILD → TRANSFER → PERFORM 阶段骨架、范围受限的 MVP inventory、确定性的目标选择和 LLM 生成的个性化课程内容。
Day 1 是 Career Transition；Day 2–30 的主题由 Planner 选择，而不是硬编码在日历中。

### ADR-018 — 经过 Gate 的持久化 Memory 写入

生产环境的 Memory 使用 PostgreSQL repository。
正常的持久化写入通过 Memory application service 和 Memory Gate；repository 保持为底层持久化边界。
内存存储只用于确定性测试和 fixture。

### ADR-019 — 原子化的跨 Session 处理

处理已持久化的 Daily Attempt 时使用小型跨 Session unit of work。
经过验证的证据、确定性的 Expression Mastery/Review 更新和 RetrievalOpportunity 消耗在一个 PostgreSQL transaction 中提交；fixture 在内存中模拟相同的回滚和幂等语义。

### ADR-020 — 版本化的确定性 Reward

XP 和 streak 更新是 `RewardRules` 版本化契约之后的确定性应用规则。
后续 Practice 流程可以发送 Reward event，但 LLM/Provider 输出不得直接决定 XP、streak 或持久化 Progress 状态。

### ADR-021 — 原子化 Daily Completion Progress

有效的 Daily Session 完成操作在一个持久化 transaction 中记录 Session 状态，并执行版本化的被动学习 Reward、streak 更新和 Journey 推进。
重复调用已完成 Session 时返回其 Progress 状态，不得再次发放 XP。

### ADR-022 — 用户本地 Reward 日期

streak 和完成 Reward 使用服务端时间戳，并根据用户保存的 IANA timezone 进行转换。
客户端提供的本地日期不具有权威性。

### ADR-023 — 服务端控制的 Daily Progress

Daily 步骤进度保存在 Session 中。
只有配置中的最后一个 Recap 步骤可以把进行中的 Daily Session 转换为可获得 Reward 的完成状态；MVP 不得伪造语音证据。

### ADR-024 — 中国大陆 Live AI Provider

Phase 2 的 live activation 使用中国北京区域的阿里云百炼，提供文本 LLM、speech-to-text 和 text-to-speech。
Provider 抽象保持不变，确定性 Domain 规则位于模型控制之外。
运行时 OpenAI adapter 和 credential 已移除；fake provider 继续用于确定性测试和本地 fallback。

### ADR-025 — Course Core 取代 Legacy Daily Loop

**状态：** 已接受

**日期：** 2026-09-12

**权威来源：** `FLUENTLOOP_MVP_BUILD_SPEC_v2.0.md`

#### 背景

已完成的 v1.1 产品以 Today、30 天 Daily Session、BUILD/TRANSFER/PERFORM 阶段、seven-step learning loop、Voice Calibration、确认式 Memory、跨 Session Mastery、XP、streak、Quick Review 和 Journey 为核心。
产品审阅后，这一模式被用户自主控制的 Course 产品取代。

#### 决策

- 当前产品有三个同级入口：Courses、Practice 和 About Me；
- 版本化的静态 Catalog 包含 30 个 Course 和 59 道 Question，是学习内容骨架；
- 用户自主选择任何 Course 和 Question；Course 没有解锁、完成、Mastery 或自动推进；
- 新的 Course Answer、Transcript、Feedback、History、About Me、Memory 和 Practice V2 模块使用新的 Domain model、repository、service、API 和前端状态；
- 现有 Auth、数据库连接、私有文件/音频 Storage、Resume/text parsing 及具有 Provider 抽象的 LLM/STT/TTS 继续作为可复用基础设施；
- Legacy Loop 保留在仓库中，用于回滚和历史检查，但不再作为新产品 runtime 挂载，也不得被新的 Course Core 模块 import；
- 新 AI Memory 在通过确定性的来源、ownership、动作和目标验证后自动保存。AI 只决定信息是否值得保留，以及执行 CREATE、UPDATE、MERGE 或 IGNORE；
- 提示、表达素材、参考回答、中文转英文整理和反馈是 AI 生成内容，不具备改变产品状态的权限；
- Course 11 是第一个垂直切片，但必须与其他 Course 使用同一通用引擎。

#### 取代范围

对于当前 Course Core，本 ADR 取代：

- ADR-004 中要求用户确认后才能持久化 Memory 的部分；结构化来源要求仍然有效；
- ADR-005 中把 Coach/Interviewer 作为主要产品控制角色的部分；
- ADR-006 对当前产品 Mastery 的要求；确定性 Mastery Engine 作为 Legacy 行为冻结保留；
- ADR-009 的固定 Curriculum 加自适应 Review；
- ADR-012 至 ADR-015 的 Voice Calibration 和 Calibration Question 规则；
- ADR-017 的有边界 Daily Planning；
- ADR-018 的确认式 Legacy Memory 写入；
- ADR-019 的原子化跨 Session Retrieval 处理；
- ADR-020 至 ADR-023 的 Reward、streak、Daily Completion 和 Day Progression。

被取代的 ADR 仍然是冻结 Legacy 实现的有效历史描述。

ADR-001、ADR-002、ADR-003、ADR-007、ADR-008、ADR-010、ADR-011、ADR-016 和 ADR-024 在不与 Build Spec v2.0 冲突的范围内继续生效。

#### 后果

- 仓库必须维护具体的 Legacy Freeze Manifest 和 Legacy Code Freeze Rules；
- 新代码不得给 Legacy Session 或 Attempt 增加 Course 语义；
- 新路由不得读取或写入 Legacy Progress、Reward、Mastery 或 Retrieval 状态；
- 关闭 Legacy 路由并启用新 App Shell 时，必须有架构测试和 no-old-write 测试；
- Freeze 的任何例外都必须说明明确原因并进行范围受限的审阅；如果例外会改变 Build Spec，还必须获得产品批准。

### ADR-026 — Course Core 的 30 条关键验收标准

**状态：** Accepted

**日期：** 2026-09-12

**权威来源：** `FLUENTLOOP_MVP_BUILD_SPEC_v2.1.md`

#### 背景

Build Spec v2.0 使用 50 项详细检查表达 MVP 总体验收门槛。产品负责人批准了一组更精简、明确的 30 条关键产品验收标准，使审阅聚焦于产品不可违反的行为。Build Spec 其他位置的详细要求仍然具有规范效力并且可以测试，但默认不会因此成为额外的关键产品验收项。

批准清单中的第 14 条为空。该位置由现有的“保存 Answer 后不得自动进入追问或下一门 Course”规则补齐。这保留了已经批准的用户控制边界，没有引入新行为。

#### 决策

- Build Spec v2.1 第 20.3 节是具有权威性的 30 条 MVP 关键验收清单；
- 验收证据和发布报告必须直接映射到这 30 个编号；
- Course 问题和回答重点继续由静态 Catalog 决定，AI 不得修改；
- Course Answer 可以反复产生并按 Question 管理，不设完成或 Mastery 状态，也不自动推进；
- 中文草稿必须确认，未确认草稿不保留；
- Memory 只有在来源可验证时才自动保存，并且始终对用户可见、可删除；
- Practice 只使用 59 道静态 Course Question，只生成整场 Feedback，不保留 Practice History；
- 新路径不得创建 Daily Session、更新 Legacy 进度或导入旧学习记录；
- 用户数据隔离、已保存 Answer 的持久性和通用 Course 引擎仍然是发布门槛。

#### 后果

- 测试计划必须用 v2.1 第 20.3 节的编号标识每一条标准；
- 早先的 50 条清单只保留在历史 Build Spec v2.0 中；
- 从关键清单中移除的要求，不会从对应的产品、架构、安全或失败处理章节中被暗中删除；
- 以后对这 30 条清单的任何修改，都必须经过 Build Spec 变更控制流程。
