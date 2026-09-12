# FluentLoop Course Core 产品与架构变更书 v1.0

## 0. 文档信息

- 文档语言：简体中文
- 文档类型：产品与架构变更书
- 状态：产品变更书已审阅通过，作为新 Course Core 正式 Build Spec 和 ADR 的输入
- 变更目标：从旧的 30 天 Daily Loop 产品切换到以 Course 为核心的自由练习产品
- 首个验证切片：Course 11「自豪的项目」

本文件整理已经讨论并确认的产品方向、架构边界、旧系统冻结范围、新系统结构、数据规则和实施顺序。

本文件不会自动修改现有运行代码。正式实施前，应更新 `AGENTS.md`、`docs/DECISIONS.md`、项目状态文档和正式 Build Spec，使新旧规则的优先级清晰可执行。

---

# 1. 变更背景

## 1.1 旧产品核心

旧 FluentLoop 是由系统安排学习内容和学习顺序的 30 天英语面试训练营。

用户进入产品后，系统根据以下状态决定当天训练内容：

- `current_day`；
- BUILD、TRANSFER、PERFORM 阶段；
- 10、20、30、60 分钟固定训练时长；
- Daily Planner；
- 用户已有的 Expression、Review 和 Mastery 状态。

每次训练按照固定七步 Loop 展开：

1. Recall；
2. Learn；
3. Imitate；
4. Retrieve；
5. Transfer；
6. Interview；
7. Recap。

完成 Daily Session 后，系统会继续更新天数、阶段、XP、streak、复习计划和掌握证据。

## 1.2 新产品核心

新 FluentLoop 仍聚焦英语求职面试表达，但产品控制权从系统转向用户。

核心原则是：

> 用户自由选择想练习的面试问题，AI 根据用户真实资料、历史回答和长期 Memory，帮助用户把真实内容表达成更自然的英语。

30 个 Course 取代 30 天训练，成为第一版主要学习内容。

新首页由三个并列入口组成：

- Courses；
- Practice；
- About Me。

三者没有必须先后完成的关系。用户不需要先上传简历、完成 Onboarding 或 Voice Calibration，也可以直接使用 Courses 或 Practice。

## 1.3 核心变化

| 维度 | 旧产品 | 新产品 |
| --- | --- | --- |
| 学习控制权 | 系统决定当天学什么 | 用户自由选择 Course 和问题 |
| 主要学习单位 | Day / Daily Session | Course / Question |
| 学习结构 | 固定七步 Loop | 用户按需使用 AI 帮助 |
| 内容推进 | 自动按天、按阶段推进 | 不解锁、不自动推进 |
| 完成判断 | Daily completion、Mastery、Aha | Course 不设置完成状态 |
| 个性化 | 为固定流程填充内容 | 围绕用户选择的问题生成帮助和反馈 |
| 历史 | 作为学习证据和掌握度来源 | 按问题保存回答历史 |
| 首页 | Today | Courses、Practice、About Me |

---

# 2. 变更原则

## 2.1 旧系统冻结，新核心并行建立

采用以下并行结构：

```text
现有通用基础设施
├── Auth
├── Database
├── File Storage
├── Resume / Text Parsing
├── Audio Storage
├── STT
├── TTS
└── LLM Providers

新 Course Core
├── Course Catalog
├── Course
├── Question
├── Answer Support
├── Course Attempt
├── Transcript
├── AI Feedback
├── Answer History
├── Practice V2
├── About Me
└── AI Memory

旧 Legacy Loop
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

旧 Legacy Loop 暂时不删除，但必须停止作为新产品的运行路径。

## 2.2 禁止把旧 Session 改造成 Course

新 Course Attempt 不复用旧 Daily `Session` 和 `Attempt` 业务模型。

原因包括：

- 旧 Session 强绑定 Daily、Calibration 和 Mock Interview 类型；
- 旧 Attempt 强绑定 Session；
- 旧 Attempt 对 `(session_id, question_type)` 设置唯一约束；
- 旧 question type 被数据库约束为 Calibration、Quick Review 和七步 Loop 类型；
- 旧 Daily completion 会更新 XP、streak、current_day 和 phase；
- 旧 Retrieval/Mastery 会在 Session 之间产生额外副作用；
- 新产品要求同一问题可以连续产生任意多条回答。

新 Course Core 必须使用独立数据表、Repository、Service、API 和前端状态机。

## 2.3 旧代码冻结方式

冻结不等于立即删除。

冻结后应做到：

- 不继续修改旧模块的产品行为；
- 不从新页面 import 旧 UI；
- 不从新 Service 调用旧 Daily、Reward、Mastery 或 Retrieval Service；
- 默认不挂载旧 Daily、Calibration、Journey、Quick Review API；
- 旧前端 URL 重定向到新首页或对应新页面；
- 旧数据库表和旧账号学习记录保留，用于回滚和历史核查；
- 通过自动化测试保证新路径不会修改旧进度字段。

---

# 3. 旧功能处置清单

| 旧概念或功能 | 处置 | 新产品规则 |
| --- | --- | --- |
| Today | 完全废弃产品入口 | 首页改为三个并列入口 |
| Today 推荐 | 完全废弃 | 用户自己选择 Course |
| 30 天训练框架 | 冻结且不运行 | 30 个 Course 只是目录顺序 |
| Day progression | 冻结且不运行 | 不自动推进 |
| Daily Planner | 冻结且不运行 | Course 问题为静态内容 |
| Daily Session 恢复 | 冻结且不运行 | Course 回答彼此独立 |
| 固定训练时长 | 完全废弃 | 用户自行决定练多久 |
| 七步 Loop | 冻结且不运行 | 帮助功能按需打开 |
| BUILD / TRANSFER / PERFORM | 完全废弃新产品概念 | Course 无阶段 |
| Journey | 完全废弃新产品入口 | 不展示 30 天地图 |
| Quick Review | 完全废弃 | Practice 只做 Mock Interview |
| XP | 冻结且不运行 | 新路径不读写 XP |
| streak | 冻结且不运行 | 新路径不读写 streak |
| Daily completion | 冻结且不运行 | Course 不设置完成状态 |
| Mastery | 冻结且不运行 | 回答记录不代表掌握 |
| Aha | 冻结且不运行 | 不生成跨 Session 突破结果 |
| 自动迁移验证 | 冻结且不运行 | Course 反馈不验证迁移 |
| Onboarding | 完全废弃前置流程 | 登录后直接进入新首页 |
| Voice Calibration | 完全废弃前置门槛 | 不影响 Course 或 Practice 可用性 |
| 旧进度 | 不迁移 | 新产品不显示或使用旧学习进度 |
| 旧账号学习记录 | 不迁移 | 保留在旧表但不进入新查询 |
| Auth | 保留 | 继续作为用户数据隔离基础 |
| Resume / Text Parsing | 保留并迁移 | 接入 About Me |
| Audio / STT / TTS | 保留并扩展 | 服务 Course 和 Practice |
| LLM Provider | 保留并扩展 | 新增版本化 Course Prompt |
| 已确认真实资料 | 可迁移 | 进入 About Me，不能作为前置门槛 |
| 已确认 Story | 可评审迁移 | 不迁移其旧 Mastery 或进度状态 |

---

# 4. 新产品信息架构

## 4.1 首页

登录后的首页显示三个并列入口：

```text
FluentLoop
├── Courses
├── Practice
└── About Me
```

规则：

- 不显示 Today；
- 不显示当前 Day、Phase、XP 或 streak；
- 不判断用户是否完成 Profile 或 Calibration；
- 用户没有资料时仍可进入全部入口；
- About Me 的资料完整程度只影响 AI 个性化程度。

## 4.2 登录与首次进入

Auth 保留，但 Auth 与 Onboarding 必须分离。

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

登录后不得再根据 Confirmed Profile 或 Calibration Session 将用户强制分流。

---

# 5. Course Catalog

## 5.1 Catalog 总体规则

- 第一版固定包含 30 个 Course；
- Course 编号只代表目录顺序，不代表学习天数；
- 用户可以直接打开任意 Course；
- 用户不需要按照编号学习；
- Course 不锁定、不解锁；
- Course 不设置已练习、已完成或已掌握状态；
- Course 名称、核心问题、追问和回答重点均为静态内容；
- AI 不得改写、替换、新增或重新排列这些内容；
- Course 内容必须具有明确版本，例如 `course_catalog_v1`。

## 5.2 Question 数量规则

- Course 01–29：一个核心问题和一个追问；
- Course 30：只有核心问题，没有追问；
- Course 30 是“每门 Course 两道题”规则的明确例外；
- 整个 Catalog 共 59 道静态问题。

建议稳定 Question ID：

```text
course-01.core
course-01.follow-up
...
course-29.core
course-29.follow-up
course-30.core
```

Course 30 的追问必须在数据中表示为 `null`，不能把“本课通常不需要追问”保存成可播放或可抽选的问题。

## 5.3 30 个 Course 定稿内容

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
│   └── 当前问题的历史回答入口
│
└── 页面工作区
    ├── 左侧：Questions 侧边栏
    ├── 中间：当前问题和回答区域
    └── 右侧：按需滑出的辅助面板
```

这是自由练习页面，不是步骤式学习页面。

## 6.2 Questions 侧边栏

- 桌面端固定在左侧；
- 不能变成顶部 Tab 或步骤条；
- Course 01–29 显示核心问题和追问；
- Course 30 只显示核心问题；
- 首次打开默认选择核心问题；
- 用户可以不回答核心问题，直接选择追问；
- 回答结束后不自动切换问题；
- 录音期间 Questions 继续显示，但不能切换。

## 6.3 中间回答区域

准备状态显示：

- 当前问题文字；
- 播放问题；
- 开始回答；
- 先用中文回答；
- 需要提示；
- 表达素材；
- AI 参考回答入口。

AI 参考回答的最终视觉位置仍可调整，但后端能力和产品定义保留。

## 6.4 右侧辅助面板

右侧面板可以显示：

- 需要提示；
- 表达素材；
- 先用中文回答说明；
- AI 参考回答；
- AI 反馈；
- 回答历史；
- 回答详情。

同一时间只允许一个右侧辅助面板打开。

打开、切换或关闭辅助面板都不能影响正在进行的录音。

---

# 7. 录音、播放与页面保护

## 7.1 全局音频互斥

同一时间只允许一个音频源播放，包括：

- 当前问题 TTS；
- AI 参考回答朗读；
- 历史回答录音；
- Practice 问题朗读；
- Practice 回答回放。

开始播放新的音频前必须停止旧音频。

开始录音时必须停止所有正在播放的音频。

录音期间不能播放任何问题语音或历史录音。

## 7.2 录音状态

录音期间持续显示：

- 正在录音；
- 录音时长；
- 波形；
- 表达素材入口；
- 需要提示入口；
- 结束回答；
- 明确放弃录音的操作。

## 7.3 不做实时转写

- 录音期间不显示实时转写；
- 用户结束回答后再调用 STT；
- 页面只显示最终转写；
- 中文和英文录音均遵守此规则。

## 7.4 离开与切换保护

录音期间：

- 不能切换核心问题或追问；
- 不能返回 Courses；
- 不能进入其他页面；
- 刷新、关闭标签或浏览器后退应触发离开确认；
- 用户必须结束或明确放弃录音后才能离开；
- 页面布局和辅助面板变化不能丢失已录内容。

---

# 8. 英文回答流程

```text
准备回答
  ↓
开始英文录音
  ↓
录音中
  ├── 可以打开提示
  ├── 可以打开表达素材
  └── 录音不中断
  ↓
结束回答
  ↓
保存原始音频
  ↓
生成最终英文转写
  ↓
保存回答文字
  ↓
生成本次 AI 反馈
  ↓
回答已保存
```

规则：

- 每次回答创建一条新的 Course Attempt；
- 不覆盖上一条回答；
- 转写不能由用户直接修改；
- AI 反馈失败不能删除录音或转写；
- 反馈失败时回答保持已保存，并允许单独重试反馈；
- 回答完成不代表 Course 完成；
- 不自动进入追问或下一门 Course。

---

# 9. 先用中文回答

## 9.1 中文回答流程

```text
准备回答
  ↓
选择“先用中文回答”
  ↓
显示中文回答说明
  ↓
开始中文录音
  ↓
结束录音
  ↓
保存原始音频
  ↓
生成中文转写
  ↓
AI 整理英文回答
  ↓
同时展示中文转写和英文整理稿
  ├── 放弃：删除未确认草稿
  ├── 重新回答
  └── 确认并保存
```

## 9.2 中文整理规则

- AI 只能整理用户实际说过的内容；
- AI 可以翻译、压缩、重组和英语化；
- AI 不得添加用户没有表达过的经历、职责、数字或结果；
- 英文整理稿不能由用户直接编辑；
- 未确认草稿不进入回答历史；
- 放弃未确认草稿后，删除其音频、转写和整理稿；
- 用户确认后才成为正式 Course Answer；
- 确认后不继续强制用户录制英文版本。

---

# 10. 按需 AI 帮助

## 10.1 需要提示

提示面板包含：

- 静态回答重点；
- AI 生成的关键词；
- AI 生成的短语；
- AI 生成的句型。

静态回答重点来自 Course Catalog，AI 不得修改。

关键词、短语和句型可以结合：

- 当前问题；
- 静态回答重点；
- About Me；
- 过去保存的 Course 回答；
- AI Memory。

提示不显示完整参考回答。

提示失败只影响提示面板，不能影响录音和已保存回答。

## 10.2 表达素材

表达素材是与当前问题和用户真实经历相关的英文可用表达，可以包括：

- 英文短语；
- 英文句型；
- 更自然的说法；
- 与用户真实经历相关的单句表达。

表达素材不是原始简历展示，也不是完整参考回答。

用户没有个人资料时：

- 仍提供通用英文表达；
- 显示“完善个人资料，可以让 AI 更了解你，并生成更符合你真实情况的表达”；
- 不能阻止用户继续使用。

## 10.3 AI 参考回答

- 一次只生成一个参考回答；
- 可以结合用户真实资料；
- 不允许编造经历、职责、数字或结果；
- 主要以文字显示；
- 用户可以主动播放 AI 朗读；
- 参考回答与中文整理后的英文回答是两个不同概念。

---

# 11. 回答保存、反馈和历史

## 11.1 回答已保存页面

保存成功后显示：

- 回答已保存；
- 本次回答时长；
- 返回问题；
- 再次回答；
- 查看 AI 反馈。

“返回问题”与顶部“返回 Courses”是不同操作。

## 11.2 Course AI 反馈

反馈对应某一次具体回答。

反馈内容包括：

- 简短总体反馈；
- 最值得修改的 1–3 处；
- 对应的用户原话；
- 具体、容易执行的修改建议。

反馈不得：

- 打分；
- 评级；
- 判断掌握；
- 验证迁移；
- 自动完成 Course；
- 一次展示大量建议；
- 评论用户没有说过的内容。

## 11.3 按问题统计历史

历史必须按单个 Question 统计：

```text
Course 11
├── 核心问题：历史回答 2 次
└── 追问：历史回答 1 次
```

切换问题后，顶部次数和右侧历史列表必须同步切换。

用户可以：

- 查看回答详情；
- 播放仍在保留期内的录音；
- 查看不可编辑的转写；
- 查看该回答的 AI 反馈；
- 删除回答；
- 再次回答并创建新记录。

---

# 12. 音频保留策略

## 12.1 保留维度

音频按照以下组合分别计算：

```text
user_id + question_id + answer_language
```

每个组合只保留最近两条录音。

例如，Course 11 核心问题分别保留：

- 最近两条英文录音；
- 最近两条中文录音。

核心问题和追问分别计算，不互相占用数量。

## 12.2 超过两条后的行为

- 删除较旧的音频对象；
- 将历史记录中的 `audio_path` 清空或标记为已过保留期；
- 保留 Course Attempt；
- 保留转写；
- 保留中文英文整理稿；
- 保留 AI 反馈；
- 历史页面明确显示“录音已过保留期”。

## 12.3 删除失败

数据库与对象 Storage 不能共享事务。

因此音频清理失败时：

- 不回滚已经保存的回答文字；
- 记录 `audio_cleanup_pending`；
- 允许后续安全重试；
- 不向用户暴露私有对象路径。

---

# 13. 删除 Course 回答

## 13.1 删除确认

用户删除回答前必须进行二次确认。

确认后删除：

- Course Attempt；
- 对应 Transcript；
- 对应 AI Feedback；
- 对应音频对象；
- 对应的 Memory Source 关联。

## 13.2 与 AI Memory 的关系

- 如果某条 Memory 只来源于被删除的回答，则级联删除该 Memory；
- 如果某条 Memory 还有 Resume、About Me 或其他回答来源，则保留 Memory，只删除当前来源关系；
- 不允许用 `ON DELETE RESTRICT` 阻止用户删除 Course 回答；
- 删除过程中出现音频清理失败时，按待清理策略处理。

---

# 14. Practice V2

## 14.1 产品定义

Practice 是无提示 Mock Interview。

MVP 只提供：

- 3 道题；
- 5 道题。

## 14.2 选题

- 从 `course_catalog_v1` 的 59 道静态问题中随机抽选；
- AI 不参与选题；
- 不根据用户资料、目标岗位、历史回答或 Memory 个性化选题；
- 不生成临时问题或自由追问；
- 同一场 Practice 内不得重复抽到同一道 Question。

## 14.3 过程

- 用户逐题回答；
- 不显示需要提示；
- 不显示表达素材；
- 不显示 AI 参考回答；
- 不进行即时纠错；
- 可以暂停；
- 可以跳题；
- 可以返回；
- 可以重答；
- 全部结束后再生成整场反馈。

## 14.4 整场反馈

Practice 只提供整场反馈，不提供逐题反馈。

反馈包括：

- 做得好的地方；
- 可以改进的地方；
- 百分制鼓励性评分。

评分通常在 90 分以上，目的是鼓励继续练习，不代表：

- 客观英语能力；
- 正式测评；
- 真实面试通过率。

## 14.5 不保存历史

- MVP 不提供 Practice 历史入口；
- 用户不能回看以前完成的整场 Mock Interview；
- 为支持暂停和返回，可以短期保存进行中的 Practice Run；
- Practice Run 完成后的数据清理时间应在正式实现前明确；
- Practice 不得创建 Daily Session、XP、streak、Mastery 或 RetrievalOpportunity。

---

# 15. About Me

## 15.1 作用

About Me 是用户资料和 AI 个性化的集中位置。

支持：

- 多个目标岗位；
- 多份简历；
- 简历上传；
- 项目和经历；
- 用户补充的资料；
- 已确认 Story；
- 全部 AI Memory；
- 部分精选 Course 回答。

## 15.2 非门槛原则

- About Me 可以为空；
- 不需要先填写才能使用 Course；
- 不需要先填写才能使用 Practice；
- 不存在资料完成度门槛；
- 缺少资料只降低 AI 个性化程度；
- AI 应在资料不足时提供通用帮助。

## 15.3 旧 Profile 数据

旧 Profile、Resume 和已确认 Story 可以作为一次性迁移候选，但：

- 旧 Daily Session 不迁移；
- 旧 Attempt 不迁移；
- 旧 Expression/Mastery/Review 不迁移；
- 旧 XP、streak、Day、Phase 不迁移；
- 迁移必须保留来源和用户隔离。

---

# 16. AI Memory

## 16.1 自动保存

新 AI Memory 明确采用自动保存，不要求用户逐条确认。

AI 可以判断什么内容值得长期保留，但自动保存不代表允许无来源推测。

## 16.2 最低安全边界

- 用户可以查看全部 Memory；
- 用户可以删除任意 Memory；
- Memory 必须来自 Resume、About Me、用户补充资料或真实 Course 回答；
- AI 不能把推测保存成用户事实；
- AI 不能编造项目、职位、职责、数据或结果；
- 每条 Memory 必须保存来源关联和支持片段；
- 无法验证来源的候选不得持久化；
- Memory 不复制全部 Course 历史；
- Memory 不产生 mastery、Aha、XP、streak 或 Course completion。

## 16.3 自动保存管道

```text
Resume / About Me / Course Answer
             ↓
AI 提取 Memory 候选
             ↓
AI 判断 Memory 动作
  ├── CREATE：新建
  ├── UPDATE：更新已有 Memory
  ├── MERGE：与一条或多条已有 Memory 合并
  └── IGNORE：不保存
             ↓
确定性来源验证
  ├── source_id 存在
  ├── source_excerpt 可在来源中定位
  ├── 用户归属一致
  ├── UPDATE / MERGE 的目标 Memory 属于当前用户
  └── 不允许无来源数字或事实
             ↓
代码以事务方式执行 CREATE / UPDATE / MERGE；IGNORE 不写入
             ↓
About Me 全部可见、可删除
```

旧 Memory Gate 属于 Legacy Loop。新系统应建立“AI 判断 Memory 动作 + 确定性来源验证 + 自动执行”的新 Memory Safety Gate，并通过正式 ADR 明确取代旧确认规则。

用户不需要逐条确认 Memory。只有通过来源验证的 CREATE、UPDATE 或 MERGE 才能持久化；AI 输出格式错误、目标不存在、用户归属不一致或来源无法验证时，本次动作必须拒绝，不得降级为无来源保存。

## 16.4 多来源 Memory

建议将 Memory 内容和来源拆分：

```text
memory_items
└── memory_sources
    ├── PROFILE
    ├── SOURCE_DOCUMENT
    ├── USER_INPUT
    └── COURSE_ATTEMPT
```

同一 Memory 可以有多个来源。删除一个来源时，只在没有其他来源后删除 Memory 本身。

---

# 17. AI Memory 决策权、系统执行权与安全边界

## 17.1 不可违反的确定性产品契约

- 30 个 Course 及其顺序；
- 核心问题和追问；
- 静态回答重点；
- 用户自主选择问题；
- 录音期间禁止切换和离开；
- 音频播放互斥；
- 中文稿经用户确认后才能保存；
- 用户数据隔离；
- 回答删除与录音清理；
- 最近两条录音策略；
- 新 Course 路径不得写入旧进度；
- AI 不得编造用户经历、职责、数据或结果。

上述契约必须由代码强制执行。模型输出、提示词调整或模型版本升级都不能绕过这些规则。

## 17.2 必须由代码执行和校验的系统操作

- Course Attempt 创建、状态迁移、幂等和事务；
- Question 切换、录音页面保护和音频播放互斥；
- 中文草稿确认状态；
- 回答历史查询、用户权限和数据隔离；
- 录音保留、删除和来源感知的级联处理；
- Practice 随机抽取 3/5 道题；
- Memory 来源验证和 Memory 写入事务；
- Legacy 写入隔离。

这些代码只负责可靠执行产品契约，不负责判断用户应该如何学习，也不构成 AI Coach 的产品决策层。

## 17.3 当前 MVP 的 AI 决策范围

当前 MVP 不建设通用的 AI Coach Orchestrator，也不让 AI 决定学习路径、提示时机、问题选择、是否重答或下一步页面动作。

AI 在产品机制上的决策仅限 Memory：

- 判断一条信息是否值得形成长期 Memory；
- 判断新信息应当 `CREATE`、`UPDATE`、`MERGE` 还是 `IGNORE`；
- 为 `UPDATE` 或 `MERGE` 指定候选目标；
- 提供支持该判断的来源引用。

AI 只提出结构化 Memory 动作。代码必须校验来源、用户归属、目标存在性和动作合法性，然后才执行持久化。AI 无权直接写数据库、跨用户查询或绕过来源验证。

## 17.4 AI 生成能力不属于机制决策

以下能力仍由 AI 生成，但它们是用户触发或既定流程触发的内容处理能力，不属于 AI Coach 对产品机制的判断：

- 关键词、短语和句型；
- 表达素材；
- AI 参考回答；
- 中文转英文整理；
- Course 回答反馈；
- Practice 整场反馈和鼓励性评分；
- 在真实资料范围内对内容进行翻译、压缩、重组和英语化。

这些能力不能自行改变 Course、切换问题、创建额外学习步骤、写入旧进度、删除数据或改变回答保存状态。

## 17.5 AI 失败隔离

- TTS 失败：显示文字，允许继续；
- 提示失败：仅提示面板失败，录音继续；
- 表达素材失败：仅辅助面板失败，录音继续；
- STT 失败：保留原始音频并允许重试；
- 英文反馈失败：保留回答和转写，允许单独重试；
- 中文整理失败：保留中文音频和转写，但不进入正式历史，允许重试或放弃；
- Memory 提取失败：不影响回答保存。

---

# 18. 建议数据模型

## 18.1 Course Attempt

```text
course_attempts
- id
- user_id
- catalog_version
- course_id
- question_id
- answer_language          ENGLISH / CHINESE
- status                   PROCESSING / AWAITING_CONFIRMATION /
                           SAVED / FEEDBACK_FAILED / FAILED
- audio_path nullable
- audio_content_type nullable
- response_duration_ms
- stt_provider
- provider_error nullable
- audio_cleanup_pending
- created_at
- confirmed_at nullable
```

## 18.2 Transcript

```text
course_transcripts
- attempt_id
- source_language
- transcript
- organized_english nullable
- organizer_prompt_version nullable
- created_at
```

Transcript 保存后不可由用户修改。

## 18.3 Feedback

```text
course_feedback
- attempt_id
- summary
- priority_changes jsonb
- feedback_prompt_version
- provider_name
- created_at
```

## 18.4 About Me

```text
target_roles
- id
- user_id
- role_name
- created_at

about_me_profiles
- user_id
- supplemental_facts jsonb
- updated_at
```

现有 `source_documents` 可继续承载多份 Resume，但应通过新 About Me Repository 提供列表、上传和删除能力，不能继续依赖旧单一 Confirmed Profile 流程。

## 18.5 Memory

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
- created_at
```

所有新表必须启用 RLS，并按 authenticated user 隔离。

---

# 19. 建议 API

## 19.1 Course

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

## 19.2 Answer Support

```text
POST /api/v1/courses/{course_id}/questions/{question_id}/hints
POST /api/v1/courses/{course_id}/questions/{question_id}/expression-materials
POST /api/v1/courses/{course_id}/questions/{question_id}/reference-answer
POST /api/v1/course-answers/{answer_id}/feedback/retry
```

## 19.3 Practice

```text
POST  /api/v1/practice/runs
GET   /api/v1/practice/runs/{run_id}
POST  /api/v1/practice/runs/{run_id}/answers
PATCH /api/v1/practice/runs/{run_id}/position
POST  /api/v1/practice/runs/{run_id}/complete
DELETE /api/v1/practice/runs/{run_id}
```

## 19.4 About Me 和 Memory

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

---

# 20. 前端状态模型

## 20.1 Course 页面主状态

```text
PREPARING
RECORDING_ENGLISH
PROCESSING_ENGLISH
CHINESE_GUIDE
RECORDING_CHINESE
PROCESSING_CHINESE
AWAITING_CHINESE_CONFIRMATION
ANSWER_SAVED
```

辅助面板状态独立于主状态：

```text
NONE
HINTS
EXPRESSION_MATERIALS
REFERENCE_ANSWER
HISTORY
ANSWER_DETAIL
FEEDBACK
CHINESE_GUIDE
```

`RECORDING_*` 状态不得因为辅助面板变化而改变。

## 20.2 全局音频状态

```text
IDLE
PLAYING_QUESTION
PLAYING_REFERENCE
PLAYING_HISTORY
RECORDING
```

任何新状态开始前必须显式停止不兼容的旧状态。

---

# 21. Legacy 代码冻结清单

## 21.1 后端

```text
backend/app/api/v1/daily.py
backend/app/api/v1/calibration.py
backend/app/api/v1/journey.py
backend/app/api/v1/practice.py
backend/app/api/v1/memory.py

backend/app/curriculum/interview_bootcamp_v1.py
backend/app/domain/learning.py

backend/app/repositories/daily_sessions.py
backend/app/repositories/calibration.py
backend/app/repositories/retrieval.py
backend/app/repositories/learning.py

backend/app/services/daily_planner.py
backend/app/services/daily_lesson_content.py
backend/app/services/daily_voice.py
backend/app/services/daily_attempts.py
backend/app/services/learning_loop.py
backend/app/services/hidden_transfer.py
backend/app/services/retrieval.py
backend/app/services/verification.py
backend/app/services/cross_session_uow.py
backend/app/services/mastery.py
backend/app/services/quick_review.py
backend/app/services/progress.py
backend/app/services/rewards.py
backend/app/services/journey.py
backend/app/services/calibration.py
backend/app/services/mock_interview.py
```

## 21.2 前端

```text
frontend/components/onboarding-flow.tsx
frontend/components/voice-calibration.tsx
frontend/components/today-session.tsx
frontend/components/today-session-live.tsx
frontend/components/practice-hub.tsx
frontend/components/journey-map.tsx
frontend/components/my-english.tsx
```

## 21.3 Legacy Code Freeze Rules

Legacy Loop 中以下模块进入代码冻结状态：

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

代码冻结必须执行以下规则：

1. 禁止为 Legacy 模块增加新的产品功能；
2. 禁止新 Course Core import Legacy UI、Service、Repository；
3. 禁止新代码调用 Daily、Reward、Mastery、Retrieval 等 Legacy Service；
4. 禁止修改 Legacy 数据模型以适配 Course；
5. 禁止给 Legacy Session / Attempt 增加 Course 语义；
6. 禁止新页面读取或写入 `current_day`、XP、streak、phase、mastery；
7. Legacy 代码仅允许严重 bug 修复、安全修复、回滚支持和历史数据核查；
8. 所有例外修改必须显式说明原因，并在代码审查和变更记录中标出影响范围。

Manifest 负责列出被冻结的文件、符号、路由、数据表和后台任务；Freeze Rules 负责定义可以和不可以发生的代码变化。两者缺一不可。

## 21.4 不建议继续扩展的大型混合文件

以下文件不必立即移动，但新 Course 模型不应继续堆入其中：

```text
backend/app/schemas.py
backend/app/db/models.py
frontend/lib/api.ts
frontend/app/globals.css
```

新功能应使用独立 schemas、models、API client 和 CSS Module。

---

# 22. 建议新代码结构

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

---

# 23. Course 11 首个垂直切片

## 23.1 选择原因

Course 11 没有特殊产品优先级，也不能拥有专用业务逻辑。

选择它作为首个切片，是因为它可以集中验证：

- 静态核心问题和追问；
- 项目目标、职责、关键决策、结果等回答重点；
- Resume 和 About Me 个性化；
- “我做了什么”的事实边界；
- 禁止 AI 编造职责或数据；
- 提示与表达素材；
- AI 参考回答；
- 英文录音、转写和反馈；
- 中文转写和英文整理；
- 回答历史；
- 最近两条录音策略；
- 删除与 Memory 级联。

Course 11 只是第一个通过同一通用 Course 引擎运行的数据实例。

## 23.2 Course 11 切片内容

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

## 23.3 切片验收范围

首个切片必须同时完成：

1. Course 列表可以打开 Course 11；
2. 核心问题与追问可以自由切换；
3. 录音期间不能切换或离开；
4. 问题播放和录音互斥；
5. 打开提示或表达素材不会中断录音；
6. 英文录音结束后生成最终转写；
7. 每次回答新增独立历史记录；
8. AI 反馈只引用用户原话并给出 1–3 条建议；
9. 中文回答先显示中英文稿，确认后才保存；
10. 未确认中文草稿放弃后不保留；
11. 每个问题、每种语言只保留最近两条录音；
12. 删除回答前确认，并正确处理 Memory 来源；
13. 没有 About Me 资料时仍可完整使用；
14. 整个流程不修改 XP、streak、current_day、phase 或 mastery；
15. Course 11 代码中不存在 `if course_id == 11` 的业务特例。

---

# 24. 数据库迁移策略

- 不修改或删除已有迁移；
- 不删除旧表和旧列；
- 使用新的版本化迁移创建 Course Core 表；
- 新表必须有 user ownership、索引、外键和 RLS；
- 新 Answer 删除规则不能被旧 Story/Expression 外键阻塞；
- 新产品查询默认不读取旧 Session、Attempt、ExpressionAttempt 或 RetrievalOpportunity；
- 新产品写入不得更新 `current_day`、`current_phase`、`xp`、`current_streak`、`last_completed_date`、`program_completed_at`；
- Migration validator 的 RLS 清单必须包含全部新用户数据表。

建议迁移：

```text
202609120012_course_core.sql
202609120013_about_me_memory.sql
202609120014_practice_v2.sql
```

---

# 25. 实施顺序

## 阶段 0：规格和安全边界

1. 审核本变更书；
2. 建立新的正式 Build Spec；
3. 更新 `AGENTS.md`；
4. 追加 superseding ADR；
5. 建立 Legacy Freeze Manifest；
6. 建立 Legacy Code Freeze Rules；
7. 创建 Git 安全 checkpoint。

阶段 0 必须把第 21.3 节的冻结范围和规则写入正式工程约束。不能只保留一份文件清单，也不能只写“旧代码不要修改”。如果工程支持依赖边界检查，应在本阶段同时确定可自动验证的 import、调用和数据写入禁令。

## 阶段 1：停止旧路径运行并封存 Legacy 代码

1. 新登录入口不再进入 Onboarding / Calibration / Today；
2. 停止默认挂载 Daily、Calibration、Journey、Quick Review；
3. 旧页面 URL 重定向；
4. 将 Today、Daily Planner、Daily Session、Journey、seven-step loop、Quick Review、XP/streak、Mastery/Aha、Onboarding、Voice Calibration 明确标记为 Legacy；
5. 新 Course Core 禁止 import 或调用 Legacy UI、Service、Repository、Session、Attempt、Progress、Reward、Mastery、Retrieval；
6. Legacy 代码仅允许安全修复、严重 bug 修复、回滚和历史核查；
7. 加入“新路径不修改旧进度”的测试；
8. 加入“Course Core 不依赖 Legacy 模块”的架构测试。

阶段 1 的重定向不能指向尚不存在的页面。开发时可以先完成阶段 2 的路由壳，再合并重定向；部署时阶段 1 和阶段 2 必须作为同一个发布门通过，避免用户登录后进入空路由。

## 阶段 2：新应用壳、首页和 Course Catalog

1. 建立新的顶层应用壳和导航，不复用 Legacy Today 容器；
2. 首页显示 Courses、Practice、About Me 三个并列入口；
3. 为三个入口建立独立路由边界；
4. 建立 `course_catalog_v1`；
5. 实现只读 Course 列表；
6. 加入 30 Course / 59 Question 确定性校验；
7. 将旧 URL 安全重定向到新首页；
8. 加入登录后落点、导航和 Legacy 不挂载的 smoke test。

首页可以先实现，因为它只依赖 Auth、路由和静态 Catalog，不依赖录音、STT、Memory 或 Practice。实施阶段中尚未完成的入口必须受开发环境或 feature flag 保护，不能在生产环境暴露死链接。正式发布时三个入口都必须可用。

## 阶段 3：Course 11 英文回答最小闭环

1. 创建 Course Attempt、Transcript、Feedback 数据表、RLS 和 Repository；
2. 建立 Single Course Page 的 Questions 左栏和主回答区；
3. 实现核心问题与追问的用户自主切换；
4. 实现 Question TTS、英文录音和最终 STT；
5. 在本阶段完成全局音频互斥和录音离页、切题保护；
6. 保存独立 Answer Attempt 并提供按问题历史；
7. 从第一次保存起执行“用户 + 问题 + 语言最近两条录音”；
8. 实现保存幂等、失败恢复和“不写 Legacy 进度”测试。

该阶段结束后，即使尚无提示、Memory、中文回答或 Practice，Course 11 的英文回答仍然可以独立运行。音频互斥、离页保护和保留策略是首个可运行闭环的安全条件，不能延后到辅助功能阶段。

## 阶段 4：About Me 和 AI Memory

1. 建立 About Me 数据模型、RLS 和 Repository；
2. 支持多目标岗位、多份 Resume 和用户补充资料；
3. 实现 AI 对 Memory 的 `CREATE / UPDATE / MERGE / IGNORE` 判断；
4. 实现 Memory 来源验证和事务执行；
5. 支持全部 Memory 查看和删除；
6. 实现 Answer 删除、录音清理与 Memory 多来源处理；
7. 验证没有 About Me 资料时 Course 仍可完整使用。

Memory 必须晚于至少一种真实来源及其用户归属模型。将本阶段放在个性化生成之前，可以让后续表达素材和反馈直接使用稳定的 About Me、Answer History 和 Memory 上下文。

## 阶段 5：按需 AI 生成能力和 Course Feedback

1. 建立统一的 Course Context Builder；
2. 实现需要提示；
3. 实现表达素材；
4. 实现 AI 参考回答；
5. 实现针对单次 Answer 的 Course Feedback；
6. 完成三栏和移动端抽屉布局；
7. 对每项 AI 能力实现独立失败、重试和超时隔离；
8. 确认这些生成能力不能改变页面状态、保存状态或 Legacy 进度。

本阶段不建设通用 AI Coach Orchestrator。提示、素材、参考回答和反馈均由用户操作或既定保存流程触发。

## 阶段 6：中文回答闭环

1. 实现中文录音和最终中文 STT；
2. 实现 AI 中文转英文整理；
3. 同时展示中文转写和英文整理稿；
4. 用户确认后才保存正式 Answer；
5. 支持重新回答和放弃未确认草稿；
6. 将中文录音接入已有最近两条保留策略；
7. 验证 AI 整理不能补充用户未表达的事实。

该阶段依赖阶段 3 的 Attempt 生命周期和录音基础设施，但不依赖 Practice。缺少中文回答不会影响此前英文 Course 路径运行。

## 阶段 7：开放其余 29 个 Course

1. 用同一通用 Course 引擎加载其余 29 个 Course；
2. 验证全部 30 Course / 59 Question 内容；
3. 验证每门 Course 都能自由选择核心问题和追问；
4. 验证 Course 30 无追问时页面正确降级；
5. 扫描并禁止 `course_id == 11` 等业务特例；
6. 完成全部 Course 的桌面端和移动端 smoke test。

开放其余 Course 只应增加 Catalog 数据覆盖和内容验证，不复制 Course 11 页面、状态机或 Service。完整题库在 Practice 之前开放，使 Practice 直接依赖已经验证的 Catalog 和通用回答引擎。

## 阶段 8：Practice V2

1. 3/5 题随机抽取；
2. 逐题语音回答；
3. 暂停、跳题、返回和重答；
4. 整场反馈；
5. 鼓励性评分；
6. 不提供历史；
7. 不触发任何 Legacy 进度。

Practice 依赖阶段 2 的完整静态 Catalog、阶段 3 的录音和 STT 基础设施，以及阶段 5 的反馈能力，因此适合最后实现。Practice 可以缺席而不影响 Course 和 About Me 独立运行。

## 阶段依赖与可运行性说明

这里的阶段顺序表达的是工程依赖，不代表每个阶段都必须单独向生产环境发布：

| 较早模块 | 是否可在后续模块缺席时运行 | 原因或限制 |
| --- | --- | --- |
| 新首页与 Catalog | 可以 | 只依赖 Auth、路由和静态 Catalog；未完成功能的入口必须由 feature flag 隔离 |
| Course 11 英文闭环 | 可以 | 不依赖 About Me、提示、中文回答或 Practice |
| About Me 与 Memory | 可以 | Memory 依赖真实来源和用户归属，但不依赖 Practice |
| AI 提示、素材与 Feedback | 可以 | 没有中文回答也能服务英文 Answer；个性化上下文来自阶段 4 |
| 中文回答 | 可以 | 复用已有录音、STT 和 Attempt 生命周期，不依赖 Practice |
| 全部 30 个 Course | 可以 | 复用通用 Course 引擎，不依赖 Practice |
| Practice | 否，不能早于基础能力 | 依赖完整 Catalog、录音/STT 和整场反馈能力 |

真正的硬前置依赖只有：

1. 数据写入前必须先有 schema、RLS、用户归属和 Repository；
2. Answer History、Feedback、Memory 来源必须晚于 Answer 的稳定保存；
3. 个性化表达必须晚于 About Me / Memory 上下文接口，通用表达除外；
4. 中文确认保存必须晚于 Draft / Attempt 状态机；
5. Practice 必须晚于完整 Catalog、通用录音组件和反馈基础设施；
6. 任何新入口上线前，Legacy 隔离测试和“不写旧进度”测试必须通过。

因此可以先做首页，再逐个模块实现。为保证每个阶段都处于可运行状态，应使用独立路由、模块边界和 feature flag，而不是在首页里预先耦合尚未完成的 Service。

---

# 26. 新产品关键验收标准

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
14. 英文反馈不评分、不评级，只给 1–3 条重点建议；
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

# 27. 已确认与仍待确定内容

## 27.1 已确认

- 30 个 Course 内容；
- Course 01–29 各有一个核心问题和一个追问；
- Course 30 无追问；
- Course 11 为首个垂直切片；
- AI Memory 自动保存；
- AI Memory 全部可见、可删除；
- 录音按 `用户 + 问题 + 语言`保留最近两条；
- 删除 Course 回答前由用户确认；
- 删除后处理独占来源 Memory；
- 旧 Daily/Loop 不删除但停止运行；
- 新 Course 不复用旧 Session/Attempt 业务模型。

## 27.2 不阻塞 Course 11 后端的待确定项

- 30 个 Course 的固定英文名称；
- 静态回答重点的固定英文版本；
- AI 参考回答在页面中的最终入口位置；
- Course AI Feedback 右侧面板的最终排列；
- About Me 的最终栏目名称；
- 精选 Course 回答由用户选择还是 AI 推荐；
- Practice 完成后的临时数据清理时间；
- 用户资料变化后是否自动重新整理已有 Memory。

这些内容不得在运行时由 AI 临时决定。需要静态产品内容的部分，应在上线前形成版本化、人工确认的 Catalog 或文案文件。

---

# 28. 最终变更意图

新 FluentLoop 不再要求用户完成系统安排的训练流程。

用户打开产品后，应当能够：

```text
选择自己想练的问题
  ↓
直接开口回答
  ↓
需要时查看提示或表达素材
  ↓
得到基于真实内容的具体反馈
  ↓
保留自己的回答历史
  ↓
在未来回答中继续使用真实资料和 AI Memory
```

产品不再关注用户是否完成 Day、Phase 或 Loop，而关注：

> 用户能否围绕真实经历，把面试答案表达得更清楚、更自然、更可信。
