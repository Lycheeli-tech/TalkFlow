# FluentLoop / TalkFlow 项目交接

本文档用于在新 Codex 窗口恢复项目上下文。它是导航摘要，不替代
`FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md`；Build Spec 始终是产品与架构唯一事实来源。

## 项目目标

产品显示名是 **FluentLoop**，仓库名保持 **TalkFlow**。MVP 目标是帮助学习者把真实经历
转化为可说出口的英文面试表达，并通过跨 Session 的证据积累形成可解释的复习与掌握状态。
核心学习循环：Recall → Learn → Imitate → Retrieve → Transfer → Interview → Recap。

## 已完成范围

Phase 1 的 M0–M7 已完成并合并到 `main`，最新稳定标签为 `m7-hardening`。已实现：

- M0–M2：基础工程、Onboarding/Profile、turn-based Voice Calibration、原始音频/Attempt/Transcript/Analysis 持久化与失败重试。
- M3：Today/Daily Session 外壳、固定 BUILD → TRANSFER → PERFORM 骨架、确定性 Planner。
- M4：结构化 Memory、Memory Gate、ExpressionAttempt 证据、确定性 Mastery/Review/ErrorPattern、确认门控 Story。
- M5：跨 Session RetrievalOpportunity、隐藏目标防泄漏、可信 Verification、Day 1 → Day 2 fixture 闭环与原子事务。
- M6：Practice、Quick Review、Mock Interview（结果暂不持久化）、Journey、My English、XP/Streak/Progress。
- M7：回归/安全/用户隔离、i18n 完整性与跨路由语言持久化、响应式与 setup 文档。

## Phase 2 激活状态

Phase 2 没有 M8，只有 Live Integration gates：

- **Gate A — Live Infrastructure：COMPLETE**。真实 Supabase TalkFlow 项目已验证：10 个迁移、Auth/JWKS、自动 user provisioning、11 张用户数据表 RLS/双用户隔离、私有 `resumes` 与 `learner-audio` Storage、SQL Profile/Session/Attempt/Memory/RetrievalOpportunity/Progress、重连恢复。
- **Gate B — Live AI Providers：COMPLETE**。中国大陆北京 Bailian 已接入并现场验证 profile extraction、校准问题、答案分析、Daily 内容；Qwen3-ASR 与 Qwen3-TTS 通过真实 TTS → STT round trip，用户已确认语音效果通过。
- **Gate C — Real Voice Pipeline：IN PROGRESS**。本地前后端已启动，浏览器已打开 `http://localhost:3000/`，等待用户登录/完成 Onboarding 到 Voice Calibration 页面，然后做真实麦克风录音、上传、持久化、ASR、分析、失败重试与约 375px smoke。
- Gate D Daily Learning Loop：NOT STARTED。
- Gate E Day 1 → Day 2 Cross-Session Aha：NOT STARTED。
- Gate F Local MVP Acceptance：NOT STARTED。

## 当前 Git 状态

当前分支是 `feat/live-ai-providers`，HEAD 为 `d16cbc3`。Gate B 相关提交：

```text
d16cbc3 docs: complete phase 2 gate b
235b902 feat: replace openai runtime with bailian providers
e2615ca docs: complete phase 2 gate a
97a023e fix: enforce rls on durable learning memory
99835fd docs: start phase 2 activation gate a
```

这些 Phase 2 提交目前在本地分支；不要假设已经推送。`origin/main` 仍指向 M7 merge
`cbfed8f`，除非重新检查远端。工作区在最后检查时有一个由 Next.js 开发环境产生的已跟踪修改
`frontend/next-env.d.ts`；不要擅自覆盖或清理它，先确认是否是用户现有工作。此前 Gate B 生成的
临时 `artifacts/gate-b-tts.wav` 已删除。

## 运行环境与配置

- 仓库：`D:\Code\TalkFlow`
- 后端解释器：`D:\Code\TalkFlow\backend\.venv\Scripts\python.exe`
- 前端依赖已存在：`D:\Code\TalkFlow\frontend\node_modules`
- Node：`C:\Users\Galatea\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin`
- pnpm：`C:\Users\Galatea\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd`
- 启动后端：在 `backend` 使用 venv 的 `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- 启动前端：在 `frontend` 将上述 Node/pnpm 路径临时加入 PATH 后执行 `pnpm dev`
- 根 `.env`（忽略）保存数据库、Supabase server key、Bailian key 与 provider 选择；
  `frontend/.env.local`（忽略）只保存浏览器安全配置。绝不打印、提交或粘贴 secret。
- 当前运行 provider：Bailian；模型配置和 URL 见 `.env.example` 与 `backend/app/core/config.py`。
- Supabase 使用 ap-northeast-1 Session Pooler；Auth 使用 JWKS，`SUPABASE_JWT_SECRET` 留空。

## 关键架构约束

- 模块化单体：Next.js + FastAPI + PostgreSQL/Supabase。
- LLM/STT/TTS 必须通过 provider abstraction；当前生产 provider 是 Bailian，fake provider 仍用于 fixture/test。
- MVP 只做 turn-based voice，不做 realtime voice；不引入 LangChain/LangGraph。
- 确定性规则（Memory Gate、Mastery、Review、Reward、Progress、Planner）不能交给 LLM。
- 提取候选不是事实；只有用户确认后才进入 durable memory/Story。
- 生产 durable memory 写入必须走 `MemoryApplicationService`/Memory Gate；Repository 是低层存储边界。
- Mastery 默认 recall ≥ 3、transfer ≥ 2、至少 3 个 distinct sessions；full/direct hint 或非独立证据不计入。
- 原始音频和 Attempt 必须在 STT/分析失败时保留；retry 复用同一 Attempt，不重复创建。
- 使用 versioned migrations、prompt/rule definitions；高风险改动先做 Git checkpoint。
- 不实现 V1.5/V2，也不创建 M8；Phase 2 后续是 Live Integration、部署、真实设备 bug bash。

## Gate C 下一步

1. 先重新 `git status`，保留 `frontend/next-env.d.ts` 等用户修改；确认服务仍运行。
2. 让用户在本地页面登录或创建测试账号并完成 Onboarding，直到显示“开始语音校准”。账号密码只在本地页面输入，不发送到聊天。
3. 用户授权浏览器麦克风并用英文完成三个 EXPERIENCE → MOTIVATION → PROJECT 回答；助手验证 TTS 播放、MediaRecorder 格式、上传、私有 Storage、STT、transcript/analysis/assessment 持久化。
4. 人为制造一次可安全恢复的 provider/网络失败（若不安全则使用已有失败路径），验证失败状态、原始音频保留与 retry；检查重连后的 Session/Attempt。
5. 做 English/简体中文界面、主路由、约 375px viewport、浏览器 console 检查；只在所有 Gate C 条件通过后更新 Phase 2 文档并 checkpoint。
6. Gate C 完成后停止等待 review；不得自动开始 Gate D。

## 验证与文档协议

开始任何 milestone/gate 前读取 `AGENTS.md`、`docs/CURRENT_MILESTONE.md`、`docs/DECISIONS.md`、相关 Build Spec 章节。实现后运行针对性测试；closeout 时按 gate 要求运行完整检查。修改状态时同步 `docs/CURRENT_MILESTONE.md` 与 `docs/PHASE2_MVP_ACTIVATION.md`；稳定架构变化才追加 `docs/DECISIONS.md`。不要修改 Build Spec 两个规格文件。

## 已知限制

Gate B 之前的 M7 limitation 文本仍有历史性 OpenAI 表述，Phase 2 状态文档已明确 Bailian 是当前 runtime provider；以后更新状态时应避免复制旧表述。后续仍需部署主机配置、真实设备/浏览器麦克风覆盖、完整 Daily voice/Attempt integration、Mock Interview durable memory，以及已知 Starlette/httpx deprecation warning 的处理。

