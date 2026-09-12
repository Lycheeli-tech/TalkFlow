# FluentLoop MVP Build Specification v2.1

## 0. 文档治理

### 0.1 当前状态与权威性

- 文档版本：v2.1；
- 文档语言：简体中文；
- 批准日期：2026-09-12；
- 状态：产品负责人已审阅通过，正式生效；
- 审阅输入：已通过的 `docs/FLUENTLOOP_COURSE_CORE_CHANGE_SPEC_v1.0_zh-CN.md`，以及产品负责人于 2026-09-12 明确批准的 30 条新产品关键验收标准；
- 首个验证切片：Course 11「自豪的项目」。

本文件是 FluentLoop 当前唯一权威的产品与架构 Build Spec。

`FLUENTLOOP_MVP_BUILD_SPEC_v1.1.md` 作为 Legacy 产品历史规格保留，不再指导新 Course Core。发生冲突时，以本文件为准。

### 0.2 生效记录

v2.1 将第 20.3 节收敛为产品负责人批准的 30 条新产品关键验收标准。原 v2.0 保留为历史版本；本次变更不解除本文其他章节中的产品约束、架构边界或 Legacy Freeze。第 14 条沿用已有的“回答保存后不自动推进”规则，以补全批准清单中的空缺编号。

本版本通过后，阶段 0 必须完成以下仓库治理动作：

1. 更新 `AGENTS.md` 的权威 Spec 指向；
2. 追加 superseding ADR；
3. 建立 Legacy Freeze Manifest；
4. 建立 Legacy Code Freeze Rules；
5. 建立开始重构前的 Git 安全 checkpoint。

阶段 0 只授权规格治理和冻结边界，不授权阶段 1 的产品代码、路由或数据库变更。阶段 1 必须在阶段 0 checkpoint 审阅后另行开始。

### 0.3 权威范围

本文件完整取代 v1.1 的产品与架构要求，而不是与旧 Spec 并列生效。

旧系统代码、数据表和历史记录可以继续存在，但以下旧产品规则不再约束新 Course Core：

- Today；
- 30 天 Day progression；
- Daily Planner；
- Daily Session；
- Recall → Learn → Imitate → Retrieve → Transfer → Interview → Recap；
- BUILD / TRANSFER / PERFORM；
- Journey；
- Quick Review；
- XP / streak；
- Mastery / Aha；
- Onboarding；
- Voice Calibration；
- 用户确认式旧 Memory Gate。

仍然保留的通用工程规则包括：

- Git 变更安全；
- 版本化数据库迁移；
- 版本化 Prompt；
- Auth 和用户数据隔离；
- Provider abstraction；
- 原始音频优先保存；
- 失败隔离与幂等重试；
- 不记录秘密和敏感原文；
- 模块化单体架构。

### 0.4 规范用语

本文件中的用语具有以下含义：

- “必须”：MVP 验收所需的强制要求；
- “不得”：不可违反的产品或安全边界；
- “应”：除非存在经过批准的技术理由，否则必须执行；
- “可以”：允许但不强制；
- “待确定”：不得由开发者、模型或编码代理自行补全。

如果实现与本文件存在冲突，必须停止相关实现并请求产品决策，不得通过猜测解决。

---

# 1. 产品定义

## 1.1 产品名称

FluentLoop。

## 1.2 产品定位

FluentLoop 是面向英语求职面试表达的 AI 课程与练习产品。

核心承诺：

> 用户自由选择想练习的面试问题，AI 根据用户真实资料、过去回答和长期 Memory，帮助用户把真实内容表达成更自然、更清楚、更可信的英语。

它不是：

- 30 天训练营；
- 由系统安排每日任务的学习计划；
- 通用聊天机器人；
- 静态参考答案库；
- 正式英语能力测评工具；
- 自动替用户编写虚构经历的求职工具。

## 1.3 主要用户问题

目标用户可能：

- 知道中文里想表达什么，但难以自然地用英语说出来；
- 回答内容真实，却缺少清晰结构；
- 能理解英语，但在面试压力下难以快速组织语言；
- 过度依赖背诵答案，无法把真实经历灵活表达出来；
- 不知道自己的经历中哪些内容与当前问题相关；
- 希望反复练习同一道题，并保留历史回答；
- 希望 AI 记住真实、长期有用的信息，但不希望 AI 编造事实。

## 1.4 MVP 核心假设

MVP 成功的前提是：

1. 用户可以直接选择任意 Course 和 Question；
2. 用户可以不完善资料而直接开始回答；
3. AI 可以基于真实上下文提供按需语言帮助；
4. 同一问题可以反复回答并形成独立历史；
5. AI Feedback 聚焦本次真实回答中最值得修改的少量内容；
6. About Me 与 AI Memory 能提高未来帮助的个性化程度；
7. 系统不会用 Day、Phase、完成度或 Mastery 控制用户；
8. 新产品运行时不会继续在后台修改旧进度。

## 1.5 产品控制权

新产品的控制权属于用户：

- 用户决定练哪个 Course；
- 用户决定练核心问题还是追问；
- 用户决定什么时候开始、结束或再次回答；
- 用户决定是否打开提示、表达素材或参考回答；
- 用户决定是否使用中文先说清内容；
- 用户决定何时停止。

系统不得：

- 锁定 Course；
- 要求按编号练习；
- 自动进入追问；
- 自动进入下一门 Course；
- 根据回答创建 Course 完成状态；
- 根据回答判断 Mastery；
- 强制用户先完成 About Me、Onboarding 或 Voice Calibration。

## 1.6 产品设计原则

当实现细节存在歧义时，按以下顺序决策：

1. 用户自主选择优先于系统安排；
2. 真实经历优先于完整但虚构的答案；
3. 静态 Course 内容优先于 AI 临时改题；
4. 按需帮助优先于固定学习步骤；
5. 保存用户真实回答优先于等待辅助 AI 能力完成；
6. 数据来源和用户隔离优先于便利；
7. 少量、可执行反馈优先于大量评价；
8. 独立模块和可回滚变更优先于改造 Legacy 大文件；
9. 通用 Course 引擎优先于 Course 特例；
10. 每个阶段可运行优先于一次性大重写。

---

# 2. MVP 范围

## 2.1 MVP 必须包含

- 账户、认证和用户隔离；
- 英文与简体中文界面；
- Courses、Practice、About Me 三个并列首页入口；
- 30 个固定 Course；
- 59 道固定 Question；
- Single Course Page；
- 核心问题与追问自由切换；
- 问题文字与 TTS 播放；
- 英文语音回答；
- 中文语音回答与中文转英文整理；
- 结束录音后的最终 STT；
- 需要提示；
- 表达素材；
- AI 参考回答；
- Course 单次回答 Feedback；
- 按 Question 保存 Answer History；
- 同一 Question 多次独立回答；
- 最近两条录音保留策略；
- Answer 删除与来源感知的 Memory 处理；
- 多目标岗位；
- 多份 Resume；
- 用户补充资料；
- 全部 AI Memory 查看与删除；
- AI Memory 自动保存；
- Memory 的 CREATE / UPDATE / MERGE / IGNORE 判断；
- 3 题或 5 题 Practice；
- Practice 整场 Feedback 和鼓励性评分；
- 响应式桌面、平板与手机布局；
- 失败恢复、幂等、版本化迁移、版本化 Prompt 和必要测试。

## 2.2 明确不属于 MVP

- Today；
- Today 推荐；
- 30 天训练框架；
- Day 1–30 推进；
- 10/20/30/60 分钟固定训练；
- Daily Planner；
- Daily Session；
- 七步学习 Loop；
- BUILD / TRANSFER / PERFORM；
- Course 解锁、完成或掌握状态；
- Journey；
- Quick Review；
- XP；
- streak；
- Mastery；
- Aha；
- 自动迁移验证；
- Onboarding；
- Voice Calibration；
- 实时转写；
- realtime speech-to-speech；
- Practice 历史；
- Course 评分或评级；
- 正式英语能力测评；
- 发音音素、重音、节奏或口音评分；
- AI 个性化 Practice 选题；
- AI 临时生成新的 Course 问题或追问；
- 通用 AI Coach Orchestrator；
- AI 决定学习路径、提示时机或下一步页面动作；
- 向量数据库或 semantic memory；
- 微服务、Kubernetes、LangChain 或 LangGraph；
- 复杂后台任务基础设施，除非可靠性验证证明当前边界无法满足。

## 2.3 Legacy 数据的 MVP 处置

- 旧 Daily Session、Attempt、Expression、Review、Retrieval、Mastery 和 Reward 数据不迁移；
- 旧 Day、Phase、XP、streak 和完成状态不进入新产品查询；
- 旧表和旧列暂时保留，支持回滚和历史核查；
- 旧 Profile、Resume、用户资料和已确认 Story 可以作为一次性迁移候选；
- 可迁移资料必须保留来源和用户归属；
- 旧记录不得被解释为新 Course 的完成度、历史回答或 Memory。

---

# 3. 总体架构

## 3.1 架构风格

继续使用模块化单体：

- Frontend：Next.js、React、TypeScript；
- Backend：FastAPI、Python；
- Database：PostgreSQL / Supabase；
- Auth：Supabase Auth；
- File Storage：Supabase Storage 或现有抽象；
- AI：Provider-abstracted LLM、STT、TTS；
- API namespace：`/api/v1`；
- 数据库变更：只使用版本化迁移。

不引入微服务。

## 3.2 三个架构区域

```text
现有通用基础设施
├── Auth
├── Database connection
├── File Storage
├── Resume / Text Parsing
├── Audio Storage
├── STT
├── TTS
└── LLM Provider abstractions

新 Course Core
├── App Shell
├── Course Catalog
├── Course
├── Question
├── Answer Support
├── Course Answer Attempt
├── Transcript
├── AI Feedback
├── Answer History
├── About Me
├── AI Memory
└── Practice V2

Legacy Loop
├── Today
├── Daily Planner
├── Daily Session
├── Journey
├── BUILD / TRANSFER / PERFORM
├── current_day
├── seven-step loop
├── Quick Review
├── XP / streak
├── Mastery / Aha
├── Onboarding
└── Voice Calibration
```

## 3.3 依赖方向

允许：

```text
Course / About Me / Practice V2
            ↓
新 Application Services
            ↓
新 Repositories
            ↓
Database / Storage / AI provider interfaces
```

禁止：

```text
Course Core → Legacy UI
Course Core → Daily Service
Course Core → Legacy Session / Attempt Repository
Course Core → Reward / Progress / Mastery / Retrieval Service
Course Core → Legacy Memory Gate
```

## 3.4 通用基础设施复用规则

可以复用：

- Auth token 验证；
- 数据库连接和事务基础；
- 私有文件 Storage 接口；
- Resume PDF / Text parser；
- 通用音频 Storage；
- STT / TTS / LLM provider interfaces；
- 配置、日志、request id 和安全工具。

复用不等于 import Legacy 业务 Service。新模块应通过通用接口或新的适配层使用基础设施。

## 3.5 新代码建议结构

```text
backend/app/course/
├── catalog_v1.py
├── schemas.py
├── models.py
├── repository.py
├── answer_service.py
├── support_service.py
├── feedback_service.py
├── context_builder.py
└── audio_retention.py

backend/app/about_me/
├── schemas.py
├── models.py
├── repository.py
├── service.py
└── memory_service.py

backend/app/practice_v2/
├── schemas.py
├── models.py
├── repository.py
├── selection.py
├── answer_service.py
└── feedback_service.py

backend/app/api/v1/
├── courses.py
├── about_me.py
└── practice_v2.py

frontend/app/
├── courses/page.tsx
├── courses/[courseId]/page.tsx
├── practice/page.tsx
└── about-me/page.tsx

frontend/components/course/
frontend/components/practice-v2/
frontend/components/about-me/
frontend/hooks/use-recorder.ts
frontend/hooks/use-audio-controller.ts
frontend/lib/course-api.ts
frontend/lib/practice-api.ts
frontend/lib/about-me-api.ts
```

不要求提前创建空文件或空目录。

---

# 4. 信息架构与首次进入

## 4.1 首页

登录后的新首页只有三个同级主入口：

```text
FluentLoop
├── Courses
├── Practice
└── About Me
```

首页不得显示：

- Today；
- 当前 Day；
- 当前 Phase；
- XP；
- streak；
- Daily completion；
- Journey 进度；
- Mastery 或 Aha。

## 4.2 登录路径

```text
未登录
  ↓
登录 / 注册
  ↓
新首页
  ├── Courses
  ├── Practice
  └── About Me
```

登录后不得依据以下状态强制分流：

- Profile 是否确认；
- Onboarding 是否完成；
- Voice Calibration 是否完成；
- 旧 current_day；
- 旧 Daily Session 是否进行中。

## 4.3 三个入口的关系

- 三个入口没有完成顺序；
- About Me 可以为空；
- 用户可以直接打开 Courses；
- 用户可以直接打开 Practice；
- 未完成模块在开发过程中必须受 feature flag 保护；
- 正式发布时三个入口都必须可用，不得暴露死链接或占位页面。

## 4.4 路由要求

目标路由至少包括：

```text
/
/courses
/courses/[courseId]
/practice
/about-me
```

旧 `/journey`、`/my-english` 以及其他 Legacy 页面必须按批准后的路由表重定向，不得继续挂载旧产品体验。

## 4.5 国际化

- MVP 界面语言继续支持 English 和简体中文；
- 学习问题语言为 English；
- 中文可以作为回答支持语言；
- UI 字符串必须通过 i18n catalog 管理；
- 切换界面语言不得改变 Course、Answer、Memory 或 Practice 状态；
- Course 静态内容的本地化必须版本化，不得在运行时由 AI 临时翻译并作为权威内容。

---

# 5. Course Catalog

## 5.1 Catalog 规则

- 第一版固定包含 30 个 Course；
- Course 编号只代表目录顺序，不代表学习日期；
- 用户可以直接打开任意 Course；
- Course 不锁定、不解锁；
- Course 不设置已练习、已完成或已掌握；
- Course 名称、核心问题、追问和回答重点均为静态内容；
- AI 不得改写、替换、新增或重新排列 Question；
- Catalog 必须具有明确版本，首版为 `course_catalog_v1`；
- Course 01–29 各有一个核心问题和一个追问；
- Course 30 只有核心问题；
- Catalog 共 59 道可回答、可播放、可被 Practice 抽取的 Question。

## 5.2 稳定 ID

Question ID 必须稳定：

```text
course-01.core
course-01.follow-up
...
course-29.core
course-29.follow-up
course-30.core
```

Course 30 的追问在数据中必须是 `null`，不能把“无追问”保存成问题文本。

## 5.3 Catalog 确定性校验

自动化测试必须验证：

1. Course ID 从 01 到 30 完整且不重复；
2. 排序稳定；
3. Course 01–29 各有两个唯一 Question；
4. Course 30 只有一个 Question；
5. Question 总数为 59；
6. 每个 Question 都有非空英文文本；
7. 每个 Course 都有非空静态回答重点；
8. Question ID 与 Course ID 匹配；
9. Catalog 内容不会被模型输出覆盖；
10. Catalog 版本会随行为性内容变更而升级。

## 5.4 30 个 Course 定稿内容

| Course | 名称 | 核心问题 | 回答重点 | 追问 |
| --- | --- | --- | --- | --- |
| 01 | 自我介绍 | **Tell me about yourself.** | 当前定位→最相关经历→应聘方向。转行经历仅在真实存在时使用。 | What would you like us to remember about you? |
| 02 | 为什么是这个岗位 | **Why are you interested in this role?** | 对岗位的理解→匹配证据→希望贡献或成长的方向。 | What aspect of this role appeals to you most, and why? |
| 03 | 为什么是这家公司 | **Why do you want to work for this company?** | 具体公司信息→真实个人连接→岗位相关性；不得编造公司事实。 | What specifically stood out to you? |
| 04 | 相关经历 | **What experience best prepares you for this role?** | 从履历中筛选最相关的经历，而不是复述全部简历。 | Which skill could you apply immediately? |
| 05 | 为什么应该聘用你 | **Why should we hire you?** | 独特价值组合→一至两个证据→能带来的实际贡献。 | What makes you different from other candidates? |
| 06 | 为什么现在寻找新机会 | **Why are you looking for a new opportunity now?** | 真实、正向说明离开原因，重点转向下一份工作的诉求；支持应届、裁员、空档期等变体。 | What are you looking for next? |
| 07 | 核心优势 | **What is one of your greatest strengths?** | 只选一个重要优势，用近期真实行为证明，并连接目标岗位。 | Can you give me a recent example? |
| 08 | 正在改善的弱项 | **What is a weakness you are working on?** | 真实但可改善的弱项→具体行动→已经出现的变化；不使用伪装优点。 | What have you done to improve it? |
| 09 | 下一步成长方向 | **Where do you want to grow next?** | 近期能力目标→较长期方向→当前岗位为何是合理下一步。 | How does this role fit that direction? |
| 10 | 薪资期望 | **What are your salary expectations?** | 表达区间、依据、整体薪酬和灵活性；没有可靠信息时不得虚构市场数字。 | How flexible are you? |
| 11 | 自豪的项目 | **Tell me about a project you are proud of.** | 项目目标→个人职责→关键决策→过程与结果，重点解释“我做了什么”。 | What was specifically your contribution? |
| 12 | 最有意义的成就 | **Tell me about an achievement that matters to you.** | 为什么重要→难度→个人贡献→可验证影响。不同于 Course 11 的项目过程深挖。 | Why does this achievement matter to you? |
| 13 | 定高目标并实现 | **Tell me about a time you set an ambitious goal and achieved it.** | 目标为什么有挑战→如何拆解和跟踪→障碍→最终证据。 | What almost prevented you from succeeding? |
| 14 | 主动承担 | **Tell me about a time you took initiative without being asked.** | 如何发现机会或问题→为什么主动行动→承担了什么风险→结果。 | Why had nobody acted before? |
| 15 | 提出并落地新方法 | **Tell me about a time you introduced a better way of doing something.** | 旧方法的问题→创意依据→试验与落地→实际影响。 | How did you test that the idea would work? |
| 16 | 克服困难挑战 | **Tell me about a difficult challenge you overcame.** | 外部障碍→应对行动→坚持或调整→结果，重点是韧性。 | What made it especially difficult? |
| 17 | 处理模糊问题 | **Tell me about a time you had to make sense of an ambiguous problem.** | 信息不完整时如何定义问题、建立假设、降低风险并推进。 | Which assumptions did you test first? |
| 18 | 搜集信息并决策 | **Tell me about a time you gathered information and made an important decision.** | 信息来源→关键问题→备选方案→判断标准→结果。 | What alternatives did you consider? |
| 19 | 在多项任务中抓重点 | **Tell me about a time you had competing priorities and had to decide what mattered most.** | 排序标准→资源取舍→沟通决定→保护质量与期限。 | What did you defer or say no to? |
| 20 | 解决专业难题 | **Tell me about a difficult technical or role-specific problem you solved.** | 按目标岗位适配；问题诊断→专业判断→方案权衡→验证结果。 | What trade-offs did you make? |
| 21 | 没有头衔也能带动他人 | **Tell me about a time you led others toward an important result, even without formal authority.** | 定方向→调动他人→处理阻力→共同结果；不要求管理职位。 | How did you gain their commitment? |
| 22 | 让团队协作真正运转 | **Tell me about a time you worked with others to deliver an important result.** | 分工、依赖关系、本人贡献、如何帮助团队完成任务。 | What did you do that others did not? |
| 23 | 解决冲突或分歧 | **Tell me about a disagreement or conflict you helped resolve.** | 分歧来源→倾听和澄清→处理方式→结果及关系变化。 | What did you do when the other person resisted? |
| 24 | 用证据争取支持 | **Tell me about a time you used evidence to gain support for an idea.** | 对方为何不同意→使用什么事实→如何适配对方关注点→是否真正获得支持。 | Why did they disagree initially? |
| 25 | 解释复杂信息 | **Tell me about a time you explained a complex idea to someone.** | 理解受众→简化或调整表达→检查对方是否理解→行动结果。 | How did you know they understood you? |
| 26 | 从失败中改变 | **Tell me about a failure or mistake and what you learned.** | 明确本人责任→造成的影响→教训→之后发生的真实行为改变。 | What would you do differently now? |
| 27 | 快速学习并应用 | **Tell me about a time you learned a new skill and applied it to a real problem.** | 为什么需要学习→学习方法→首次应用→实际结果。 | How did you know you had learned it well enough? |
| 28 | 适应重大变化 | **Tell me about a time you had to adapt to a major change.** | 变化带来的影响→最初反应→调整方法→新结果。 | What did you change about your approach? |
| 29 | 接受并使用反馈 | **Tell me about a time you received difficult feedback and acted on it.** | 反馈内容→如何判断和消化→采取行动→后续证据。 | What changed as a result? |
| 30 | 向面试官提问 | **What questions do you have for us?** | 根据岗位和面试内容提出关于工作、团队、成功标准和挑战的真实问题；不背诵空泛问题。 | 无追问 |

---

# 6. Single Course Page

## 6.1 页面结构

```text
Single Course Page
│
├── 顶部栏
│   ├── 返回 Courses
│   ├── Course 编号
│   ├── Course 名称
│   └── 当前 Question 的历史回答入口和次数
│
└── 页面工作区
    ├── 左侧：Questions 侧边栏
    ├── 中间：当前问题与回答区域
    └── 右侧：按需辅助面板
```

这是自由练习页面，不是步骤式学习页面。

## 6.2 Questions 侧边栏

- 桌面端必须固定在左侧；
- 不得改为顶部 Tab、步骤条或横向问题列表；
- Course 01–29 显示核心问题和追问；
- Course 30 只显示核心问题；
- 首次打开默认选择核心问题；
- 用户可以未回答核心问题就直接选择追问；
- 当前 Question 必须有明确选中状态；
- 回答结束后不得自动切换；
- 录音期间侧边栏继续显示，但 Question 不可切换。

## 6.3 中间回答区域

准备状态显示：

- 当前 Question 原文；
- 播放问题；
- 开始回答；
- 先用中文回答；
- 需要提示；
- 表达素材；
- AI 参考回答入口。

录音状态显示：

- 正在录音；
- 已录时长；
- 波形或等价录音活动反馈；
- 需要提示；
- 表达素材；
- 结束回答；
- 明确放弃录音。

## 6.4 右侧辅助面板

辅助面板可以承载：

- 需要提示；
- 表达素材；
- 中文回答说明；
- AI 参考回答；
- AI Feedback；
- Answer History；
- Answer Detail。

规则：

- 同一时间只允许打开一个辅助面板；
- 打开、切换和关闭面板不得停止录音；
- 面板加载失败不得改变主回答状态；
- 面板不得覆盖或重建录音组件；
- 桌面宽屏形成三栏；
- 中等宽度从右侧覆盖部分主区域；
- 手机宽度从右侧滑出。

## 6.5 响应式要求

桌面：

```text
Questions 左栏 │ 主回答区 │ 右侧辅助面板
```

中等宽度：

```text
Questions 左栏 │ 主回答区
                     └── 右侧覆盖式辅助面板
```

手机：

- 主要显示当前 Question 和回答区；
- 顶部提供 Questions 入口；
- Questions 必须从左侧滑出；
- Questions 不得变成顶部问题 Tab；
- 辅助面板从右侧滑出；
- 不得出现横向页面溢出。

---

# 7. 音频、录音与播放

## 7.1 语音模式

MVP 只使用 turn-based voice：

```text
显示固定 Question
  ↓
按需播放 TTS
  ↓
用户开始录音
  ↓
用户结束录音
  ↓
保存原始音频
  ↓
调用 STT
  ↓
保存最终转写
```

不实现：

- 实时转写；
- 流式语音识别展示；
- realtime speech-to-speech；
- 中途打断；
- barge-in；
- 录音中的即时纠错。

## 7.2 全局音频互斥

同一时间只能存在一个活动音频状态：

```text
IDLE
PLAYING_QUESTION
PLAYING_REFERENCE
PLAYING_HISTORY
RECORDING
```

开始新播放前必须停止旧播放。

开始录音前必须停止：

- Question TTS；
- AI 参考回答朗读；
- Answer History 录音；
- Practice Question TTS；
- Practice Answer 回放。

录音期间禁止任何播放。

## 7.3 Question TTS

- TTS 文本必须等于当前 Catalog Question；
- 不得先让 AI 改写再播放；
- TTS 失败时继续显示 Question 文字；
- TTS 失败不得阻止录音；
- TTS 缓存不得跨 Question 返回错误内容。

## 7.4 录音保护

录音期间：

- 禁止切换核心问题和追问；
- 禁止返回 Courses；
- 禁止进入其他页面；
- 浏览器后退、刷新或关闭标签必须触发离开确认；
- 用户必须结束或明确放弃后才能离开；
- 打开或关闭辅助面板不得丢失录音；
- 页面布局变化不得重新初始化 Recorder。

## 7.5 原始音频和失败恢复

- 后端必须先保存原始音频并建立用户归属，再调用 STT；
- STT 失败时保留音频并允许对同一 Answer Attempt 重试；
- 重试不得创建重复 Attempt；
- 已保存 Transcript 不得因下游 Feedback 或 Memory 失败而丢失；
- 私有 Storage 路径不得返回给不具有权限的用户；
- 不得在日志中记录音频内容或可直接访问的私有 URL。

---

# 8. Course Answer 生命周期

## 8.1 聚合根

每次回答创建一个独立的 Course Answer Attempt。

同一用户可以对同一 Question 连续创建任意多次 Answer Attempt。

不得：

- 用新回答覆盖旧回答；
- 对 `(user_id, question_id)` 建立唯一约束；
- 复用 Legacy Session / Attempt；
- 因回答成功而完成 Course；
- 因回答成功而自动切换 Question。

## 8.2 核心状态

Answer 核心状态与 Feedback 状态必须分离。

建议核心状态：

```text
PROCESSING
AWAITING_CONFIRMATION
SAVED
PROCESSING_FAILED
DISCARDED
```

建议 Feedback 状态：

```text
NOT_REQUESTED
PENDING
READY
FAILED
```

建议音频清理状态：

```text
NOT_REQUIRED
PENDING
COMPLETE
FAILED
```

`FEEDBACK_FAILED` 不得替代 Answer 的 `SAVED` 状态。一个 Answer 可以是已保存且 Feedback 失败。

## 8.3 英文回答流程

```text
PREPARING
  ↓
RECORDING_ENGLISH
  ↓
结束回答
  ↓
保存原始音频和 Attempt
  ↓
PROCESSING_ENGLISH
  ↓
保存最终英文 Transcript
  ↓
Answer = SAVED
  ↓
Feedback = PENDING
  ├── 成功：READY
  └── 失败：FAILED，Answer 仍为 SAVED
```

规则：

- 录音期间不显示实时 Transcript；
- Transcript 保存后用户不能编辑；
- 保存成功后立即进入“回答已保存”状态；
- Feedback 可以同步返回，也可以随后完成；
- Feedback 失败只影响 Feedback；
- STT 失败时 Answer 不进入正式历史，但原始音频可重试；
- 用户明确放弃失败 Attempt 后才删除其暂存音频；
- 失败 Attempt 的自动过期时间属于待确定事项。

## 8.4 中文回答流程

```text
PREPARING
  ↓
打开中文回答说明
  ↓
RECORDING_CHINESE
  ↓
保存原始音频和 Attempt
  ↓
PROCESSING_CHINESE
  ↓
保存中文 Transcript
  ↓
AI 整理英文回答
  ↓
AWAITING_CONFIRMATION
  ├── 放弃：DISCARDED，并清理草稿数据
  ├── 重新回答：DISCARDED，并创建新 Attempt
  └── 确认：SAVED
```

AI 整理规则：

- 只能整理用户实际说过的内容；
- 可以翻译、压缩、重组和英语化；
- 不得补充用户未表达的经历、职责、数字、结果或公司事实；
- 英文整理稿不得由用户直接编辑；
- 必须同时展示中文 Transcript 和英文整理稿；
- 未确认草稿不得进入 Answer History；
- 未确认草稿不得成为 Memory 来源；
- 确认后不强制用户继续录制英文版本。

## 8.5 回答已保存页面

必须显示：

- 保存成功；
- 本次回答时长；
- 返回当前问题；
- 再次回答；
- 查看 AI Feedback。

“返回问题”必须：

- 保持当前 Question 选中；
- 不删除刚保存的 Answer；
- 不进入追问；
- 不进入下一门 Course。

“再次回答”必须创建新的 Attempt。

顶部“返回 Courses”与结果页“返回问题”是两个不同操作。

## 8.6 幂等

- 创建 Attempt 的客户端请求必须具有幂等标识或等价保护；
- STT 重试复用同一 Attempt；
- 中文整理重试复用同一 Attempt；
- 确认中文稿必须幂等；
- Feedback 重试不得创建多个当前版本 Feedback；
- 删除重试不得错误删除其他 Answer；
- Storage 重试不得覆盖其他用户对象。

---

# 9. 按需 AI 生成能力

## 9.1 触发原则

提示、表达素材和 AI 参考回答由用户主动触发。

Course Feedback 由 Answer 保存流程触发，或在失败后由用户主动重试。

这些能力不是学习步骤，也不构成 AI Coach 对产品机制的判断。

## 9.2 需要提示

提示包含：

- 来自 Catalog 的静态回答重点；
- AI 生成的关键词；
- AI 生成的短语；
- AI 生成的句型。

AI 可以读取：

- 当前 Question；
- 静态回答重点；
- About Me；
- 相关 Resume 内容；
- 已保存的相关 Course Answer；
- AI Memory。

提示不得：

- 修改静态回答重点；
- 显示完整 AI 参考回答；
- 切换 Question；
- 停止录音；
- 创建 Course 完成状态。

## 9.3 表达素材

表达素材是可直接用于英语表达的短语、句型、自然说法和真实经历相关单句。

表达素材不是：

- Resume 原文展示；
- 项目事实卡；
- 完整参考回答；
- AI 新编的用户经历。

当用户资料为空时：

- 仍提供通用英文表达；
- 明确提示完善资料可以提高个性化；
- 不得阻止用户继续练习。

## 9.4 AI 参考回答

- 一次只生成一个参考回答；
- 可以结合用户真实资料；
- 不得编造经历、职责、数字、结果或公司事实；
- 以文字为主；
- 用户可以主动播放 TTS；
- 与中文回答生成的英文整理稿必须作为两个不同概念和接口。

## 9.5 Course Feedback

Feedback 必须绑定某一个已保存 Answer。

显示内容：

- 简短总体反馈；
- 最值得修改的 1–3 处；
- 对应的用户原话；
- 具体、容易执行的修改建议。

Feedback 不得：

- 打分；
- 评级；
- 判断 Mastery；
- 验证 Transfer；
- 自动完成 Course；
- 一次展示大量建议；
- 评论用户没有说过的内容；
- 因失败而回滚 Answer。

## 9.6 Context Builder

AI 能力不得任意查询整个用户历史。

Course Context Builder 应只装配当前任务必要的信息：

- 当前用户；
- Catalog version；
- Course 和 Question；
- 静态回答重点；
- 与当前 Question 相关的目标岗位；
- 少量相关 Resume / About Me 事实；
- 少量相关 Memory；
- 少量相关已保存 Answer；
- 当前 Answer Transcript（Feedback 时）。

必须：

- 所有查询按 authenticated user 过滤；
- 设置上下文条数或 token 上限；
- 记录使用的 Prompt version 和 Provider；
- 不把其他用户数据送入模型；
- 不将未确认中文 Draft 作为真实资料；
- 资料不足时降级为通用内容，而不是补充事实。

## 9.7 AI 失败隔离

- 提示失败：只影响提示面板；
- 表达素材失败：只影响表达素材面板；
- 参考回答失败：只影响参考回答；
- Feedback 失败：Answer 保持 `SAVED`；
- Memory 提取失败：Answer 保持 `SAVED`；
- 中文整理失败：保留音频与中文 Transcript，允许重试或放弃；
- TTS 失败：显示文字；
- 任何辅助 AI 失败都不得更新 Legacy 进度。

---

# 10. Answer History、录音保留与删除

## 10.1 按 Question 的 History

History 必须按 `user_id + question_id` 查询和统计。

示例：

```text
Course 11
├── 核心问题：2 次
└── 追问：1 次
```

切换 Question 后，顶部次数和历史列表必须同步切换。

History 只包含已保存 Answer。

用户可以：

- 查看 Answer Detail；
- 查看不可编辑 Transcript；
- 查看仍存在的录音；
- 查看该 Answer 的 Feedback；
- 删除 Answer；
- 再次回答并新增记录。

## 10.2 最近两条录音

录音保留分组键：

```text
user_id + question_id + answer_language
```

每个分组只保留最近两条已保存 Answer 的录音。

因此：

- 英文和中文分别计算；
- 核心问题和追问分别计算；
- 不同用户分别计算；
- 删除旧音频不删除 Answer 文字；
- 未确认 Draft 不计入正式最近两条，但必须按 Draft 清理策略管理。

## 10.3 第三条录音保存后的处理

当同一分组产生第三条已保存录音：

1. 新 Answer 和 Transcript 先成功提交；
2. 在事务中确定需要过期的旧音频引用；
3. 将旧 Answer 的音频状态标记为待清理；
4. 清理对应私有 Storage 对象；
5. 成功后清空 `audio_path` 或标记为 `EXPIRED`；
6. 保留旧 Answer、Transcript、英文整理稿和 Feedback；
7. History 显示“录音已过保留期”。

数据库与对象 Storage 不能共享事务。

Storage 删除失败时：

- 不回滚 Answer 保存；
- 保留 `audio_cleanup_pending` 或等价状态；
- 允许幂等重试；
- 不暴露 Storage 私有路径。

## 10.4 删除 Answer

用户删除前必须看到明确的二次确认。

确认后删除：

- Course Answer Attempt；
- Transcript；
- Feedback；
- 对应录音对象；
- 对应 Memory Source 关联。

规则：

- 不得用 `ON DELETE RESTRICT` 阻止用户删除自己的 Answer；
- Transcript 和 Feedback 可以随 Answer 级联删除；
- Memory Item 的处理必须经过 Memory Service；
- 音频清理失败按待清理策略处理；
- 删除请求必须验证 authenticated user ownership；
- 用户不能修改 Transcript 来替代删除。

## 10.5 删除 Answer 与 Memory

- 如果 Memory 只来源于被删除的 Answer，删除该 Memory；
- 如果 Memory 还有 Resume、About Me 或其他 Answer 来源，保留 Memory，只删除当前来源；
- 删除来源关系和判断是否删除 Memory 必须在一个数据库事务内完成；
- 删除 Answer 不得删除原始 Resume 或其他用户资料；
- 删除失败不得影响其他用户或其他 Answer。

---

# 11. Practice V2

## 11.1 定义

Practice 是无提示 Mock Interview。

MVP 只提供：

- 3 道题；
- 5 道题。

## 11.2 选题

- 从 `course_catalog_v1` 的 59 道 Question 随机抽取；
- 同一场不得重复 Question；
- AI 不参与选题；
- 不根据 Profile、目标岗位、Answer History 或 Memory 个性化；
- 不生成临时问题；
- 不生成自由追问；
- 抽题算法必须可测试；
- 测试环境应允许注入 seed，生产环境不要求向用户暴露 seed。

## 11.3 过程

- 用户逐题回答；
- 不显示提示；
- 不显示表达素材；
- 不显示 AI 参考回答；
- 不进行即时纠错；
- 可以暂停；
- 可以跳题；
- 可以返回；
- 可以重答；
- 全部结束后才生成整场 Feedback。

## 11.4 整场 Feedback

仅提供整场 Feedback，不提供逐题 Feedback。

包括：

- 做得好的地方；
- 可以改进的地方；
- 百分制鼓励性评分。

评分通常在 90 分以上，目的是鼓励继续练习。

必须明确评分不代表：

- 客观英语能力；
- 正式测评结果；
- 真实面试通过率。

## 11.5 不保存 Practice History

- MVP 不提供 Practice History；
- 用户不能回看已完成的旧 Mock Interview；
- 为支持暂停、返回和重答，可以短期保存进行中的 Practice Run；
- 完成或放弃后的清理策略必须幂等；
- Practice Run 的生产 TTL 必须在阶段 8 开始前批准；
- Practice 不得创建 Daily Session、XP、streak、Mastery、Aha 或 RetrievalOpportunity。

---

# 12. About Me

## 12.1 定位

About Me 是用户资料和 AI 个性化的集中位置。

支持：

- 多个目标岗位；
- 多份 Resume；
- Resume 上传；
- 项目和经历；
- 用户补充资料；
- 已确认 Story；
- 全部 AI Memory；
- 部分精选 Course Answer。

## 12.2 非门槛原则

- About Me 可以为空；
- 不需要先填写才能使用 Courses；
- 不需要先填写才能使用 Practice；
- 不存在资料完成度门槛；
- 不显示强制 Onboarding；
- 不要求 Voice Calibration；
- 资料缺少只降低 AI 个性化程度；
- 通用帮助必须继续可用。

## 12.3 多份 Resume

- 每份 Resume 必须是独立 SourceDocument；
- 必须保留 filename、raw text、parse status、user ownership 和时间；
- 上传必须验证文件类型与大小；
- 私有文件不得公开访问；
- 删除 Resume 时必须处理相关 Memory Source；
- 删除 Resume 不得删除无关 Answer；
- Resume parser 作为通用基础设施复用。

## 12.4 旧资料迁移

允许作为迁移候选：

- 旧 confirmed Profile；
- 旧 Resume SourceDocument；
- 用户已确认的 Story。

不迁移：

- Daily Session；
- Legacy Attempt；
- Expression；
- ExpressionAttempt；
- RetrievalOpportunity；
- Mastery / Review；
- XP / streak；
- Day / Phase。

迁移必须：

- 明确来源；
- 保持用户隔离；
- 可重复运行而不重复创建；
- 在正式迁移前提供 dry run 或等价核查；
- 不把旧推断内容自动提升为新事实。

---

# 13. AI Memory

## 13.1 产品定义

AI Memory 是 AI 从用户资料和已保存 Course Answer 中形成的、未来可能继续有用的长期理解。

新 AI Memory 自动保存，不要求用户逐条确认。

用户必须：

- 能查看全部 Memory；
- 能删除任意 Memory；
- 能看到足以理解来源的来源类型；
- 不需要阅读全部 Course History 才能管理 Memory。

## 13.2 AI 决策范围

当前 MVP 中，AI 在产品机制上的决策只包括：

1. 判断信息是否值得成为长期 Memory；
2. 判断新信息应当 `CREATE`、`UPDATE`、`MERGE` 还是 `IGNORE`；
3. 为 `UPDATE` 或 `MERGE` 指定候选目标；
4. 提供支持该判断的来源引用。

MVP 不建设通用 AI Coach Orchestrator。

AI 不决定：

- 学习路径；
- Question 选择；
- 提示时机；
- 是否重新回答；
- 页面下一步；
- 是否完成 Course；
- 数据删除；
- 用户权限；
- Legacy 进度。

## 13.3 Memory 动作

| 动作 | AI 含义 | 代码执行 |
| --- | --- | --- |
| CREATE | 候选是新的长期信息 | 新建 Memory Item 和 Source |
| UPDATE | 候选补充或修正一条已有 Memory | 校验目标后更新内容并增加 Source |
| MERGE | 候选与多条已有 Memory 表达同一事实 | 在事务中选择 canonical Item、迁移 Sources、删除冗余 Items |
| IGNORE | 信息不值得长期保存或没有新增价值 | 不进行持久化写入 |

AI 只能返回结构化动作建议，无权直接操作数据库。

## 13.4 自动保存管道

```text
Resume / About Me / 已保存 Course Answer
                 ↓
AI 提取候选
                 ↓
AI 判断 CREATE / UPDATE / MERGE / IGNORE
                 ↓
确定性验证
├── source_id 存在
├── source 属于 authenticated user
├── source_excerpt 可以定位
├── UPDATE / MERGE 目标存在
├── 目标 Memory 属于 authenticated user
├── 动作 schema 合法
└── 不包含无来源事实或数字
                 ↓
事务执行
├── CREATE / UPDATE / MERGE：自动持久化
└── IGNORE：不写入
                 ↓
About Me 可见、可删除
```

AI 输出格式错误、来源不存在、来源无法定位、目标不存在或用户归属不一致时：

- 拒绝本次 Memory 动作；
- 不得降级成无来源保存；
- 不影响 Answer 保存；
- 记录不含敏感原文的可诊断错误；
- 可以安全重试。

## 13.5 来源

允许的来源类型：

```text
PROFILE
SOURCE_DOCUMENT
USER_INPUT
COURSE_ANSWER
```

每个 Memory Item 可以有多个 Memory Source。

每个 Source 至少保存：

- `memory_id`；
- `user_id`；
- `source_type`；
- `source_id`；
- `source_excerpt` 或结构化字段路径；
- 创建时间。

不得把以下内容作为正式来源：

- 未确认中文 Draft；
- AI 参考回答；
- AI 生成的提示；
- AI 生成的表达素材；
- Practice 临时 Feedback；
- 其他用户数据；
- AI 自己的无来源推测。

## 13.6 删除

用户直接删除 Memory 时：

- 删除 Memory Item；
- 删除该 Item 的全部 Memory Source 关联；
- 不删除原始 Resume、Profile、Answer 或用户输入。

删除来源对象时：

- 移除对应 Memory Source；
- 如果 Item 不再有任何 Source，删除 Item；
- 如果仍有其他 Source，保留 Item。

## 13.7 不产生旧学习状态

Memory 不得：

- 产生 Expression；
- 产生 Review；
- 产生 RetrievalOpportunity；
- 更新 Mastery；
- 更新 Aha；
- 更新 XP 或 streak；
- 更新 current_day 或 phase；
- 完成 Course。

---

# 14. AI、确定性代码与系统执行边界

## 14.1 不可违反的产品契约

以下规则必须由代码强制执行：

- 30 个 Course 及顺序；
- 固定 Question；
- 固定回答重点；
- 用户自主选择 Question；
- 录音期间不能切题或离开；
- 同一时间只能播放一个音频；
- 中文稿确认后才保存；
- 用户数据隔离；
- Answer 删除和录音清理；
- 每个用户、Question、语言只保留最近两条录音；
- 新 Course 路径不能更新旧进度；
- AI 不能编造用户经历、职责、数字或结果。

模型输出、Prompt 变更或 Provider 升级都不能绕过这些契约。

## 14.2 代码执行职责

确定性代码负责：

- Course Answer Attempt 创建；
- 状态迁移；
- 事务和幂等；
- Question 切换保护；
- 页面离开保护；
- 音频互斥；
- 中文稿确认状态；
- Answer History 查询；
- 用户权限和 RLS；
- 录音保留和清理；
- Answer 删除；
- Memory 来源验证；
- Memory 动作事务；
- Practice 3/5 题随机选择；
- Legacy import 和写入隔离。

这些职责用于保证系统可靠性，不代表代码替用户决定学习内容。

## 14.3 AI 生成职责

AI 可以生成：

- 关键词、短语和句型；
- 表达素材；
- AI 参考回答；
- 中文转英文整理；
- Course Feedback；
- Practice 整场 Feedback 和鼓励性评分；
- Memory 候选和 Memory 动作；
- 对真实资料进行翻译、压缩、重组和英语化。

除 Memory 动作判断外，以上属于内容生成，不属于产品机制决策。

## 14.4 禁止模型直接执行

AI 不得直接：

- 写数据库；
- 删除 Answer、Resume 或 Memory；
- 访问未经过 Context Builder 的任意历史；
- 跨用户查询；
- 修改 Catalog；
- 切换前端状态；
- 创建 Course 完成状态；
- 调用 Legacy Service；
- 修改旧进度；
- 根据 Prompt 中的用户文本扩大工具权限。

---

# 15. 数据模型

## 15.1 总体要求

- 使用新的版本化迁移；
- 不修改或删除已有迁移；
- 不删除旧表或旧列；
- 新用户数据表必须包含 `user_id`；
- 新用户数据表必须启用 RLS；
- 所有 Repository 查询必须显式带 authenticated user；
- 外键和删除行为必须支持用户删除自己的 Answer 和资料；
- 时间使用带时区 timestamp；
- Prompt、Catalog 和 Provider version 必须可追踪；
- 不把新 Course 字段加入 Legacy Session / Attempt。

## 15.2 Course Catalog

Catalog 可以是版本化代码或 seed 数据，但必须是单一权威静态来源。

概念字段：

```text
Course
- catalog_version
- course_id
- order
- localized_name
- answer_focus

Question
- catalog_version
- question_id
- course_id
- kind                 CORE / FOLLOW_UP
- text_en
- order
```

Catalog 不包含用户状态。

## 15.3 Course Answer

建议表：`course_answers`。

```text
- id uuid primary key
- user_id uuid not null
- catalog_version text not null
- course_id text not null
- question_id text not null
- answer_language text not null       ENGLISH / CHINESE
- status text not null
- response_duration_ms integer
- audio_path text nullable
- audio_content_type text nullable
- audio_retention_status text
- audio_cleanup_pending boolean
- provider_error_code text nullable
- created_at timestamptz
- saved_at timestamptz nullable
- confirmed_at timestamptz nullable
```

约束：

- 不允许 `(user_id, question_id)` 唯一约束；
- `question_id` 必须属于指定 `course_id` 和 `catalog_version`；
- History 索引至少覆盖 `(user_id, question_id, saved_at desc)`；
- 录音保留查询至少覆盖 `(user_id, question_id, answer_language, saved_at desc)`。

## 15.4 Course Transcript

建议表：`course_transcripts`。

```text
- answer_id uuid primary key
- user_id uuid not null
- source_language text not null
- transcript text not null
- organized_english text nullable
- stt_provider text
- stt_model text nullable
- organizer_prompt_version text nullable
- created_at timestamptz
- updated_at timestamptz
```

规则：

- Transcript 与 Answer 一对一；
- Transcript 用户不可编辑；
- 中文 Answer 保存后必须同时保留中文 Transcript 和 organized English；
- RLS 必须与 Answer ownership 一致。

## 15.5 Course Feedback

建议表：`course_feedback`。

```text
- answer_id uuid primary key
- user_id uuid not null
- status text not null
- summary text nullable
- priority_changes jsonb nullable
- prompt_version text not null
- provider_name text nullable
- model_name text nullable
- error_code text nullable
- created_at timestamptz
- updated_at timestamptz
```

Feedback 重试更新同一个 Answer 的当前 Feedback，不创建重复历史版本，除非未来 Spec 明确要求版本历史。

## 15.6 About Me

建议新增：

```text
target_roles
- id
- user_id
- role_name
- created_at

about_me_profiles
- user_id primary key
- supplemental_facts jsonb
- created_at
- updated_at
```

现有 `source_documents` 可以继续保存多份 Resume，但必须通过新 About Me Repository 暴露，不得依赖旧 Onboarding confirmation 流程。

## 15.7 Memory

建议表：

```text
memory_items
- id
- user_id
- content
- normalized_content
- extractor_prompt_version
- created_at
- updated_at

memory_sources
- id
- memory_id
- user_id
- source_type
- source_id
- source_excerpt
- source_field_path nullable
- created_at
```

约束：

- `memory_sources.user_id` 必须与 `memory_items.user_id` 一致；
- UPDATE / MERGE 只能操作同一用户的 Item；
- MERGE 必须在一个事务中迁移 Source；
- 无来源 Item 不得持久存在；
- 删除 Item 不删除来源对象。

## 15.8 Practice 临时数据

建议：

```text
practice_runs
- id
- user_id
- question_count          3 / 5
- question_ids
- current_position
- status
- feedback
- score
- expires_at
- created_at
- completed_at nullable

practice_answers
- id
- run_id
- user_id
- question_id
- audio_path nullable
- transcript nullable
- answer_order
- created_at
```

这些数据只用于进行中的运行、恢复和整场 Feedback，不构成用户可见历史。

生产 TTL 待批准。

## 15.9 建议迁移序列

现有迁移必须保持不变。

候选新迁移：

```text
202609120012_course_core.sql
202609120013_about_me_memory.sql
202609120014_practice_v2.sql
```

实际时间戳和拆分可以在实现前根据仓库状态调整，但：

- 顺序必须版本化；
- 每个迁移必须可从空库按序执行；
- 不得通过 destructive reset 解决冲突；
- Migration validator 必须包含全部新 RLS 表；
- 必须验证旧数据仍可保留；
- 必须验证新路径不写旧表。

---

# 16. API 契约

## 16.1 通用 API 原则

- 使用 `/api/v1`；
- 所有用户数据接口必须认证；
- 服务端从认证上下文取得 `user_id`，不得信任客户端提交的用户 ID；
- 创建和重试操作必须幂等；
- 错误响应不得暴露私有 Storage path、Prompt 原文、token 或其他用户信息；
- API 只处理传输和授权，核心规则位于 Service / Domain；
- Catalog GET 可以公开或认证，最终选择必须一致且不泄露用户数据。

## 16.2 Course

```text
GET    /api/v1/courses
GET    /api/v1/courses/{course_id}
GET    /api/v1/courses/{course_id}/questions/{question_id}/history
POST   /api/v1/courses/{course_id}/questions/{question_id}/answers
GET    /api/v1/course-answers/{answer_id}
POST   /api/v1/course-answers/{answer_id}/retry
POST   /api/v1/course-answers/{answer_id}/confirm
DELETE /api/v1/course-answers/{answer_id}/draft
DELETE /api/v1/course-answers/{answer_id}
GET    /api/v1/course-answers/{answer_id}/audio
GET    /api/v1/courses/{course_id}/questions/{question_id}/tts
```

## 16.3 Answer Support

```text
POST /api/v1/courses/{course_id}/questions/{question_id}/hints
POST /api/v1/courses/{course_id}/questions/{question_id}/expression-materials
POST /api/v1/courses/{course_id}/questions/{question_id}/reference-answer
POST /api/v1/course-answers/{answer_id}/feedback/retry
```

## 16.4 About Me 与 Memory

```text
GET    /api/v1/about-me
PATCH  /api/v1/about-me
GET    /api/v1/about-me/target-roles
POST   /api/v1/about-me/target-roles
DELETE /api/v1/about-me/target-roles/{role_id}
GET    /api/v1/about-me/resumes
POST   /api/v1/about-me/resumes
DELETE /api/v1/about-me/resumes/{document_id}
GET    /api/v1/about-me/memories
DELETE /api/v1/about-me/memories/{memory_id}
```

Memory CREATE / UPDATE / MERGE 由可信的 Memory application flow 触发，不提供允许客户端伪造 AI 动作或来源的公共写接口。

## 16.5 Practice

```text
POST   /api/v1/practice/runs
GET    /api/v1/practice/runs/{run_id}
POST   /api/v1/practice/runs/{run_id}/answers
PATCH  /api/v1/practice/runs/{run_id}/position
POST   /api/v1/practice/runs/{run_id}/complete
DELETE /api/v1/practice/runs/{run_id}
```

## 16.6 所有权错误

- 不属于当前用户的资源统一返回不泄露存在性的响应；
- 不得通过区别明显的错误让攻击者枚举其他用户资源；
- Answer、Audio、Resume、Memory 和 Practice Run 都必须执行同样规则。

---

# 17. 前端状态与交互契约

## 17.1 Course 主状态

```text
PREPARING
RECORDING_ENGLISH
PROCESSING_ENGLISH
RECORDING_CHINESE
PROCESSING_CHINESE
AWAITING_CHINESE_CONFIRMATION
ANSWER_SAVED
RECOVERABLE_FAILURE
```

中文回答说明属于辅助面板状态，不改变 `PREPARING`。

## 17.2 辅助面板状态

```text
NONE
HINTS
EXPRESSION_MATERIALS
REFERENCE_ANSWER
CHINESE_GUIDE
HISTORY
ANSWER_DETAIL
FEEDBACK
```

主状态和辅助面板状态必须独立。

`RECORDING_ENGLISH` 或 `RECORDING_CHINESE` 不得因面板变化而改变。

## 17.3 状态转换所有权

代码负责校验合法转换：

- `PREPARING → RECORDING_*` 只能由用户开始录音触发；
- `RECORDING_* → PROCESSING_*` 只能由结束回答触发；
- `RECORDING_* → PREPARING` 只能由用户确认放弃触发；
- `PROCESSING_CHINESE → AWAITING_CHINESE_CONFIRMATION` 需要中文 Transcript 和英文整理稿；
- `AWAITING_CHINESE_CONFIRMATION → ANSWER_SAVED` 需要用户确认；
- 面板事件不得触发 Answer 状态转换。

## 17.4 页面恢复

- 可恢复失败必须显示明确重试；
- 刷新后不得错误创建重复 Answer；
- 已保存 Answer 的结果页应能通过 Answer ID 恢复；
- 未确认中文 Draft 的跨刷新保留不属于已确认需求，必须按 Draft 策略实现或明确提示将被放弃；
- Recorder 的本地未上传数据不能被虚假显示为已保存。

---

# 18. Legacy Code Freeze

## 18.1 冻结模块

以下模块进入 Legacy 代码冻结状态：

- Today；
- Daily Planner；
- Daily Session；
- Journey；
- BUILD / TRANSFER / PERFORM；
- `current_day`；
- seven-step loop；
- Quick Review；
- XP / streak；
- Mastery / Aha；
- Onboarding；
- Voice Calibration。

## 18.2 Legacy Code Freeze Rules

1. 禁止为 Legacy 模块增加新的产品功能；
2. 禁止新 Course Core import Legacy UI、Service、Repository；
3. 禁止新代码调用 Daily、Reward、Mastery、Retrieval 等 Legacy Service；
4. 禁止修改 Legacy 数据模型以适配 Course；
5. 禁止给 Legacy Session / Attempt 增加 Course 语义；
6. 禁止新页面读取或写入 `current_day`、XP、streak、phase、mastery；
7. Legacy 代码仅允许严重 bug 修复、安全修复、回滚支持和历史数据核查；
8. 所有例外修改必须显式说明原因，并在代码审查和变更记录中标出影响范围。

## 18.3 后端 Legacy Freeze Manifest

至少包括：

```text
backend/app/api/v1/calibration.py
backend/app/api/v1/daily.py
backend/app/api/v1/journey.py
backend/app/api/v1/memory.py
backend/app/api/v1/practice.py
backend/app/api/v1/profiles.py

backend/app/curriculum/interview_bootcamp_v1.py
backend/app/domain/learning.py

backend/app/repositories/calibration.py
backend/app/repositories/daily_sessions.py
backend/app/repositories/learning.py
backend/app/repositories/memory.py
backend/app/repositories/profiles.py
backend/app/repositories/retrieval.py

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

正式 Manifest 必须在阶段 0 根据当时仓库重新扫描，不能假设本清单自动覆盖未来新增文件。

## 18.4 前端 Legacy Freeze Manifest

至少包括：

```text
frontend/components/onboarding-flow.tsx
frontend/components/voice-calibration.tsx
frontend/components/today-session.tsx
frontend/components/today-session-live.tsx
frontend/components/practice-hub.tsx
frontend/components/journey-map.tsx
frontend/components/my-english.tsx
```

## 18.5 允许修改的迁移接缝

以下文件可能需要为新路由、依赖注入或模块挂载而修改，不应整体标为只读 Legacy：

```text
backend/app/main.py
backend/app/api/v1/router.py
backend/app/api/v1/entry.py
backend/app/api/dependencies.py
frontend/app/page.tsx
frontend/app/layout.tsx
frontend/components/app-entry.tsx
frontend/app/practice/page.tsx
frontend/app/journey/page.tsx
frontend/app/my-english/page.tsx
```

这些文件只允许承担：

- 挂载新模块；
- 停止挂载 Legacy 路径；
- 路由重定向；
- 通用依赖注入；
- 新 App Shell 接入。

不得把 Course 业务逻辑继续堆入这些迁移接缝。

## 18.6 不继续扩展的混合文件

```text
backend/app/schemas.py
backend/app/db/models.py
frontend/lib/api.ts
frontend/app/globals.css
```

新功能应使用独立 schema、model、API client 和 CSS Module。对混合文件的必要兼容修改必须最小化并说明原因。

## 18.7 Legacy 数据写入禁令

新路径不得：

- 创建 Legacy Daily Session；
- 创建 Legacy Attempt；
- 创建 Expression 或 ExpressionAttempt；
- 创建 RetrievalOpportunity；
- 调用 Reward Engine；
- 调用 Mastery Engine；
- 更新 `current_day`；
- 更新 `current_phase`；
- 更新 `xp`；
- 更新 `current_streak`；
- 更新 `last_completed_date`；
- 更新 `program_completed_at`。

## 18.8 架构测试

必须建立：

1. 新 Course / About Me / Practice V2 包不 import Legacy 包的测试；
2. 新 API 不注册 Legacy runtime dependency 的测试；
3. 新 Answer 保存前后旧进度字段不变的测试；
4. 新路径不创建 Legacy Session / Attempt / Expression / Retrieval 记录的测试；
5. 登录后不挂载 Onboarding / Calibration / Today 的浏览器 smoke test；
6. 旧 URL 重定向测试；
7. Manifest 中被冻结文件发生修改时的审查提示或 CI 检查。

---

# 19. Provider、Prompt、可靠性与安全

## 19.1 Provider abstraction

业务逻辑不得直接依赖具体 Provider SDK：

```text
Application Service
        ↓
LLM / STT / TTS interface
        ↓
Provider adapter
        ↓
Concrete model
```

现有 Bailian、Qwen STT 和 Qwen TTS 可以继续作为当前运行 Provider，但替换 Provider 不得修改 Course 领域规则。

## 19.2 Prompt version

所有影响行为的 Prompt 必须：

- 独立于业务代码；
- 具有显式版本；
- 输出符合结构化 schema；
- 记录 Prompt version、Provider 和 model；
- 包含不得编造用户事实的政策；
- 具有固定 regression fixtures。

建议 Prompt：

```text
course_hints_v1
course_expression_materials_v1
course_reference_answer_v1
course_feedback_v1
chinese_answer_organizer_v1
memory_decision_v1
practice_feedback_v1
```

## 19.3 失败隔离

核心原则：

> 辅助能力失败不得破坏已经安全保存的用户数据。

必须验证：

- TTS 失败不阻止录音；
- Feedback 失败不删除 Answer；
- Memory 失败不删除 Answer；
- Storage 清理失败不回滚 Transcript；
- 中文整理失败保留可重试的中文来源；
- Provider 超时不会重复创建 Attempt；
- 客户端断线后可以根据持久化状态恢复。

## 19.4 后台工作

MVP 可以同步执行短操作，也可以通过轻量后台任务完成：

- Feedback；
- Memory 提取；
- 音频过期清理；
- Practice 整场 Feedback。

不得为了未来可能需求提前引入 Redis、Celery 或复杂队列。

无论同步还是异步，都必须具备：

- 明确状态；
- 幂等；
- 重试上限；
- 可诊断错误；
- 用户 ownership；
- 不影响核心 Answer 保存。

## 19.5 安全与隐私

- Secret 只存在于环境变量；
- 不提交 `.env`、API key、token、私有 URL 或真实用户资料；
- 所有用户数据查询按 authenticated user 过滤；
- Resume 和音频必须私有；
- 上传验证类型和大小；
- API 不信任客户端 user ID；
- 日志不包含完整 Resume、Transcript、Memory、音频或 Prompt 上下文；
- 用户删除动作必须验证 ownership；
- AI 输入中的用户文本不得被当作系统指令或授权；
- Context Builder 必须防止跨用户和无边界历史注入；
- RLS 必须覆盖所有新用户表。

## 19.6 Observability

记录足以诊断的信息：

- request_id；
- user_id 的安全标识；
- answer_id / run_id；
- operation；
- status；
- Provider；
- model；
- Prompt version；
- latency；
- token usage（可用时）；
- error code；
- retry count。

不得记录秘密或敏感原文。

---

# 20. 测试与验收

## 20.1 测试层级

至少包括：

- Catalog unit tests；
- Answer 状态机 unit tests；
- 音频互斥和离页保护 component tests；
- Repository ownership tests；
- RLS / two-user isolation tests；
- Answer 保存与失败恢复 integration tests；
- Memory 动作和来源验证 tests；
- 音频保留与异步清理 tests；
- Legacy architecture fitness tests；
- Provider contract tests；
- AI regression fixtures；
- API tests；
- 桌面与 375px browser smoke tests；
- 关键流程 end-to-end tests。

## 20.2 AI regression fixtures

至少覆盖：

### 不编造经历

来源中不存在职责、数字或结果时，提示、参考回答、中文整理、Feedback 和 Memory 不得把它们作为用户事实。

### 静态 Question 不变

AI 不得改写 Catalog Question 或回答重点。

### Course Feedback 范围

Feedback 只引用当前 Answer，提供 1–3 条重点，不评分、不判断 Mastery。

### 中文整理忠实

英文整理稿只能翻译、压缩和重组中文 Transcript。

### Memory 来源

每个 CREATE / UPDATE / MERGE 必须返回可验证来源；无来源候选被拒绝。

### Practice Feedback

只在整场结束后生成，包含鼓励性说明，不宣称正式能力或通过率。

## 20.3 MVP 总体验收标准

以下 30 条是新产品的关键总体验收标准。本文其他章节中的强制要求仍然有效，但不得擅自扩充或替换本清单作为关键产品验收口径。

1. 登录后直接看到 Courses、Practice、About Me；
2. 没有 Profile 或 Calibration 也能进入 Course 和 Practice；
3. 用户可以打开任意 Course；
4. 用户可以直接回答追问；
5. Course 问题始终来自静态 Catalog；
6. AI 不得改变静态问题和回答重点；
7. 录音期间不能切换问题或离开；
8. 辅助面板不会中断录音；
9. 同时只播放一个音频；
10. 录音期间不显示实时转写；
11. 同一问题可以连续保存多次回答；
12. 历史按问题统计；
13. Course 不设置完成或掌握状态；
14. 回答保存后不自动进入追问或下一门 Course；
15. 中文回答必须经用户确认后保存；
16. 未确认中文草稿不保留；
17. 每个用户、问题、语言只保留最近两条录音；
18. 旧录音删除后文字历史仍保留；
19. 用户可以删除 Course 回答；
20. 用户可以查看和删除全部 AI Memory；
21. AI Memory 自动保存，但必须具有可验证来源；
22. Practice 只随机使用 59 道静态 Course 问题；
23. Practice 只生成整场反馈；
24. Practice 不提供历史；
25. 新路径不会创建 Daily Session；
26. 新路径不会更新 Day、Phase、XP、streak、Mastery 或 Aha；
27. 旧账号学习记录不会进入新产品；
28. 用户数据、Resume、音频、回答和 Memory 保持严格隔离；
29. AI 或 Storage 部分失败不会导致已保存回答丢失；
30. Course 11 与其他 Course 使用同一个通用引擎。

---

# 21. Course 11 首个垂直切片

## 21.1 选择原因

Course 11 没有特殊产品优先级，也不能拥有专用业务逻辑。

它用于集中验证：

- 核心问题和追问；
- 静态回答重点；
- “我做了什么”的个人贡献边界；
- Resume、About Me 和 Memory 上下文；
- 提示、表达素材和参考回答；
- 英文录音、STT、保存、History 和 Feedback；
- 中文录音、整理和确认；
- 最近两条录音；
- Answer 删除和 Memory Source；
- AI 不编造职责或结果。

## 21.2 固定内容

```text
Course 11 · 自豪的项目

核心问题
Tell me about a project you are proud of.

回答重点
项目目标 → 个人职责 → 关键决策 → 过程与结果
重点解释“我做了什么”

追问
What was specifically your contribution?
```

## 21.3 切片验收

1. Course 列表可以打开 Course 11；
2. 核心问题和追问可以自由切换；
3. 录音期间不能切换或离开；
4. Question TTS 和录音互斥；
5. 打开帮助不停止录音；
6. 英文录音结束后生成最终 Transcript；
7. 每次回答创建独立 History；
8. Feedback 只引用用户原话并给 1–3 条建议；
9. 中文回答先展示中英文稿；
10. 中文稿确认后才保存；
11. 放弃 Draft 后不进入 History；
12. 每个 Question、语言只保留最近两条录音；
13. 删除 Answer 正确处理 Memory Source；
14. 没有 About Me 仍可完整使用；
15. 不修改 Legacy 状态；
16. 不存在 `if course_id == 11` 或等价业务特例。

---

# 22. 实施顺序

Course Core V1 的当前阶段状态、验证证据和交接信息统一记录在 `docs/CURRENT_MILESTONE_V1.md`。`docs/CURRENT_MILESTONE.md` 仅作为旧项目里程碑历史保留。

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

## 22.1 硬依赖

1. 数据写入前必须有 schema、RLS、ownership 和 Repository；
2. History、Feedback 和 Memory Source 必须晚于 Answer 稳定保存；
3. 个性化表达依赖 About Me / Memory，上下文为空时只能使用通用模式；
4. 中文确认依赖 Draft / Answer 状态机；
5. Practice 依赖完整 Catalog、录音、STT 和 Feedback 基础设施；
6. 新入口发布前必须通过 Legacy 隔离和不写旧进度测试。

## 22.2 每阶段可运行性

| 模块 | 后续模块缺席时能否运行 | 限制 |
| --- | --- | --- |
| 首页与 Catalog | 可以 | 未完成入口必须由 feature flag 隔离 |
| Course 11 英文闭环 | 可以 | 不依赖 About Me、中文或 Practice |
| About Me 与 Memory | 可以 | Memory 依赖真实来源和 ownership |
| AI 帮助与 Feedback | 可以 | 中文功能缺席不影响英文 Answer |
| 中文 Answer | 可以 | 复用阶段 3 基础设施 |
| 全部 Course | 可以 | 复用通用 Course 引擎 |
| Practice | 不能提前 | 依赖 Catalog、录音/STT 和 Feedback |

实施顺序不等于每阶段都单独向生产发布。

---

# 23. Git 与变更安全

## 23.1 开始前

- 检查 Git branch、HEAD 和 working tree；
- 识别并保护用户未提交修改；
- 在大规模冻结和路由切换前建立干净 checkpoint；
- 使用短期 feature branch；
- 不在 `main` 上直接进行不可逆重构。

## 23.2 数据库安全

- 不修改旧 migration；
- 不执行 destructive reset；
- 不删除 Legacy 表；
- 先在本地验证完整 migration sequence；
- 涉及生产数据前必须提供回滚和核查方案；
- 不把真实用户数据放入 fixture 或日志。

## 23.3 Commit

每个 commit 应是可理解、可测试和可回滚的单元。

建议按以下边界提交：

- Spec / ADR / Freeze Rules；
- Legacy runtime stop；
- App Shell / Catalog；
- Course schema；
- Course 11 English flow；
- About Me / Memory；
- AI support；
- Chinese flow；
- Catalog rollout；
- Practice V2。

## 23.4 合并和推送

未经明确授权：

- 不 merge；
- 不 push；
- 不删除 branch；
- 不 force push；
- 不开始下一阶段。

每阶段结束必须报告：

- branch；
- HEAD；
- working tree；
- commits；
- tests；
- migrations；
- 已知限制；
- 下一阶段前置条件。

---

# 24. 编码代理执行协议

在开始或恢复任一阶段前：

1. 读取 `AGENTS.md`；
2. 读取正式生效的 Build Spec；
3. 读取 `docs/PROJECT_STATUS.md`；
4. 读取 `docs/HANDOFF.md`；
5. 读取当前阶段文档；
6. 架构相关工作读取 `docs/DECISIONS.md`；
7. 检查 Git 状态；
8. 明确当前唯一任务和 working radius；
9. 明确本阶段验收标准；
10. 不根据对话记忆替代仓库文档。

实现中：

- 优先最小一致变化；
- 不修改无关用户文件；
- 不绕过 RLS、Memory 来源验证或 Legacy Freeze；
- 不把待确定事项写成未经批准的产品规则；
- 不扩展下一阶段功能；
- 运行与风险相称的测试。

阶段收尾：

- 对照本 Spec 验收；
- 记录限制；
- 更新阶段文档；
- 稳定决策才写 ADR；
- 到达安全 checkpoint；
- 等待审阅。

---

# 25. 待产品确认事项

以下事项不阻塞 v2.0 生效或阶段 0 收尾，但不得由实现者静默决定：

| ID | 事项 | 最迟决定时间 |
| --- | --- | --- |
| TBD-001 | 30 个 Course 的固定英文名称 | 阶段 2 对英文界面开放前 |
| TBD-002 | 静态回答重点的固定英文版本 | 阶段 2 对英文界面开放前 |
| TBD-003 | AI 参考回答的最终页面入口位置 | 阶段 5 UI 定稿前 |
| TBD-004 | Course Feedback 面板最终排列 | 阶段 5 UI 定稿前 |
| TBD-005 | About Me 最终栏目名称 | 阶段 4 UI 定稿前 |
| TBD-006 | 精选 Course Answer 由用户选择还是 AI 推荐 | 阶段 4 对应功能实现前 |
| TBD-007 | Practice 完成、放弃和过期 Run 的 TTL | 阶段 8 schema 定稿前 |
| TBD-008 | 用户资料变化后是否自动重新整理已有 Memory | 阶段 4 Memory 行为定稿前 |
| TBD-009 | 失败 Answer / Draft 音频的自动过期时间 | 阶段 3 Storage 策略定稿前 |
| TBD-010 | 未确认中文 Draft 是否支持跨刷新恢复 | 阶段 6 状态机定稿前 |

在对应最迟时间之前没有产品决定时：

- 相关功能不得上线；
- 可以继续不依赖该决定的模块；
- 不得由 AI 在运行时决定；
- 不得通过隐藏默认值形成事实上的产品规则。

---

# 26. Build Spec 变更控制

本文件已经产品负责人审阅并正式生效。后续任何会改变以下内容的修改都必须先形成提案，并再次获得产品负责人明确批准：

- 产品核心、MVP 范围或信息架构；
- Course Catalog、Question 或回答重点；
- Answer 保存、历史、删除或录音保留规则；
- About Me 或 AI Memory 行为；
- AI 决策权与确定性代码边界；
- Legacy Freeze 范围或例外规则；
- 数据模型、跨模块依赖或迁移策略；
- 阶段顺序和验收标准。

未经批准：

- 不得直接修改本 Spec 来追认已经完成的代码；
- 不得让实现、Prompt 或模型行为形成事实上的新产品规则；
- 不得删除旧 Spec、ADR 或历史记录来隐藏架构变化；
- 不得解除 Legacy Freeze。

批准后的 Spec 变更必须同步：

1. 递增文档版本；
2. 记录批准日期和变更摘要；
3. 追加或 supersede 对应 ADR；
4. 更新 `AGENTS.md` 和项目状态文档；
5. 在代码变更前建立 Git checkpoint。

---

# 27. 最终 Build Intent

FluentLoop 的新 MVP 应让用户感受到：

```text
打开产品
  ↓
自由选择想练习的面试问题
  ↓
直接用英文或先用中文回答
  ↓
需要时主动获取 AI 帮助
  ↓
保存真实回答
  ↓
获得少量、具体、基于原话的 Feedback
  ↓
反复回答并查看按问题组织的 History
  ↓
让有来源的 AI Memory 改善未来个性化
```

产品不再关心用户是否完成 Day、Phase 或 Loop。

产品最终关注：

> 用户能否围绕自己的真实经历，把面试答案表达得更清楚、更自然、更可信。
