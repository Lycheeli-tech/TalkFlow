# FluentLoop / TalkFlow 跨窗口交接

本文档是新 Codex 窗口的导航入口，不替代
`FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md`。Build Spec 始终是产品和架构事实来源。

## 新窗口必读顺序

1. `AGENTS.md`
2. `docs/PROJECT_HANDOFF.md`
3. `docs/HANDOFF.md`
4. `docs/CURRENT_MILESTONE.md`
5. `docs/DECISIONS.md`
6. `docs/PHASE2_MVP_ACTIVATION.md`
7. Build Spec 中与 Gate E、跨 Session Retrieval、Memory/Mastery 相关的完整章节

开始工作前必须先运行 `git status`、确认分支/HEAD 和本地服务。不要依赖旧对话历史。

## 当前事实

- Phase 1 M0–M7：COMPLETE；没有 M8。
- Phase 2 Gate A — Live Infrastructure：COMPLETE。
- Phase 2 Gate B — Live AI Providers：COMPLETE。
- Phase 2 Gate C — Real Voice Pipeline：COMPLETE。
- Phase 2 Gate D — Real Daily Learning Loop：COMPLETE。
- Phase 2 Gate E — Real Day 1 → Day 2 Cross-Session Aha：COMPLETE。
- Phase 2 Gate F — Local MVP Acceptance：NOT STARTED。
- Gate D 完成分支：`feat/real-daily-learning-loop`。
- Gate D checkpoint：`97bee4f feat: complete phase 2 gate d daily loop`。
- Gate D 合并/推送状态应由新代理重新检查；本文件随后会随 merge 一起进入 `main`。

## Gate D 已验证基线

- Daily 的 RECALL、IMITATE、RETRIEVE、TRANSFER、INTERVIEW 使用 turn-based
  MediaRecorder → 私有 `learner-audio` → Attempt → Bailian Qwen3-ASR → transcript →
  Bailian analysis；LEARN/RECAP 保持被动步骤。
- 服务端在当前语音 Attempt 达到 `ANALYZED` 前拒绝 advance；非当前/被动步骤拒绝录音。
- 分析失败保留原始音频和 transcript；retry 复用同一 Attempt ID/audio path，不创建重复
  Attempt。自动化回归已覆盖。
- 真实 Day 1 完成至 Recap，保存 `+1 XP`、streak 并推进 Day 2；刷新和下一日 Session
  持久化通过。
- 三个真实 Daily Attempt 只读核验为 `ANALYZED`，Bailian STT/analysis、transcript、
  analysis 和非空私有音频对象均存在。
- `202609080011_daily_voice_attempts.sql` 已通过本地迁移序列验证并应用到当前 Supabase。
- English/简体中文、Today/Practice/My English/Journey、约 375px、production build、刷新与
  hydration/console 检查通过。
- Gate D closeout：后端 87 tests、Ruff、TypeScript、ESLint、Next.js build、11 migrations
  均通过；详细证据和限制见 `docs/HANDOFF.md` 与 `docs/PHASE2_MVP_ACTIVATION.md`。

## Gate E 完成事实

真实 Day 1 → Day 2 跨 Session Aha 已验证：

1. 从前一 Session 已学习/确认的 Expression 产生到期或合适的 RetrievalOpportunity。
2. 下一 Daily Session 在不泄露目标表达的自然新语境中进行隐藏式提取。
3. 真实语音 Attempt 完成 STT 和结构化分析。
4. `VerificationService` 只读取可信、同用户、同 Session、已分析的 Attempt；调用方不得
   提交 mastery/正确性标志。
5. `MemoryApplicationService` 和版本化确定性规则写入 ExpressionAttempt、更新 recall /
   transfer 证据、review schedule 与 mastery；LLM 不做规则判定。
6. RetrievalOpportunity 消费、证据写入和状态更新保持同一事务、可重试、幂等。
7. 在 UI 中验证用户能看到跨 Session 的“以前学过的内容现在能说出来”的结果，同时不在
   回答前暴露目标表达。
8. 验证刷新/重连、用户隔离、失败恢复、English/简体中文、主路由、约 375px 和 console。

全部 Gate E 条件通过；checkpoint 见 `feat/real-cross-session-aha`。完成后停止，不自动开始 Gate F。

## 下一步

- 审查 `feat/real-cross-session-aha` 上的 Gate E checkpoint。
- 未经明确请求，不要合并、推送或开始 Gate F。
- Gate E 的详细实现、live evidence 和限制见 `docs/HANDOFF.md` 与
  `docs/PHASE2_MVP_ACTIVATION.md`。

## 运行环境

- 仓库：`D:\Code\TalkFlow`
- 后端虚拟环境：优先 `D:\Code\TalkFlow\backend\.venv`，备用
  `D:\Code\TalkFlow\backend.venv`
- 前端依赖：`D:\Code\TalkFlow\frontend\node_modules`
- 后端通常运行于 `http://127.0.0.1:8000`
- 前端通常运行于 `http://localhost:3000`
- 当前真实 provider：Alibaba Cloud Model Studio/Bailian；fake provider 保留用于测试。
- 后端必须在允许访问已配置 Supabase/Bailian 的环境运行，否则 JWKS 验证会返回 401。

## 不可违反的边界

- 模块化单体：Next.js + FastAPI + PostgreSQL/Supabase。
- LLM/STT/TTS 必须走 provider abstraction；MVP 仅 turn-based voice，不做 realtime。
- 不使用 LangChain/LangGraph。
- Memory Gate、Mastery、Review、Reward、Progress、Planner 等确定性规则不能交给 LLM。
- 提取候选不是事实；只有用户确认后才能成为 durable profile/story truth。
- 原始音频和 Attempt 在 STT/分析失败时必须保留；retry 必须复用同一 Attempt。
- 使用 versioned migrations/prompts/rules；高风险改动前创建 Git checkpoint。
- 不修改 Build Spec，不实现 V1.5/V2，不创建 M8，不开始 Gate F。
- 不打印、提交或粘贴 `.env`、Supabase/Bailian/数据库密钥、JWT、用户标识、私有路径或
  音频内容。
- 不覆盖用户修改，尤其是 `frontend/next-env.d.ts`。

## 文档职责

- `docs/PROJECT_HANDOFF.md`：跨窗口导航入口。
- `docs/HANDOFF.md`：最近一次 Gate 的具体实现、验证和运行状态。
- `docs/PHASE2_MVP_ACTIVATION.md`：Gate 状态与 live evidence。
- `docs/CURRENT_MILESTONE.md`：历史里程碑和当前生命周期。
- `docs/PROJECT_STATUS.md`：精简项目仪表盘。
- `docs/ISSUES.md`：已知问题、根因、修复和回归证据。
- `docs/DECISIONS.md`：仅记录稳定架构决策。
