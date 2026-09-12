from dataclasses import dataclass
from typing import Literal

# Fixed product copy intentionally stays one field per line for catalog review.
# ruff: noqa: E501

CATALOG_VERSION = "course_catalog_v1"


@dataclass(frozen=True, slots=True)
class QuestionDefinition:
    id: str
    kind: Literal["CORE", "FOLLOW_UP"]
    text: str


@dataclass(frozen=True, slots=True)
class CourseDefinition:
    id: str
    order: int
    name_en: str
    name_zh_cn: str
    answer_focus_en: str
    answer_focus_zh_cn: str
    core_question: QuestionDefinition
    follow_up_question: QuestionDefinition | None

    @property
    def questions(self) -> tuple[QuestionDefinition, ...]:
        if self.follow_up_question is None:
            return (self.core_question,)
        return (self.core_question, self.follow_up_question)


_CATALOG_CONTENT: tuple[tuple[str, str, str, str, str, str | None], ...] = (
    (
        "Introduce Yourself",
        "自我介绍",
        "Current positioning → most relevant experience → target direction. Mention a career transition only when it is true.",
        "当前定位→最相关经历→应聘方向。转行经历仅在真实存在时使用。",
        "Tell me about yourself.",
        "What would you like us to remember about you?",
    ),
    (
        "Why This Role",
        "为什么是这个岗位",
        "Understanding of the role → matching evidence → where you hope to contribute or grow.",
        "对岗位的理解→匹配证据→希望贡献或成长的方向。",
        "Why are you interested in this role?",
        "What aspect of this role appeals to you most, and why?",
    ),
    (
        "Why This Company",
        "为什么是这家公司",
        "Specific company information → genuine personal connection → relevance to the role. Do not invent company facts.",
        "具体公司信息→真实个人连接→岗位相关性；不得编造公司事实。",
        "Why do you want to work for this company?",
        "What specifically stood out to you?",
    ),
    (
        "Relevant Experience",
        "相关经历",
        "Select the experience most relevant to the role instead of repeating your entire resume.",
        "从履历中筛选最相关的经历，而不是复述全部简历。",
        "What experience best prepares you for this role?",
        "Which skill could you apply immediately?",
    ),
    (
        "Why We Should Hire You",
        "为什么应该聘用你",
        "Distinctive value combination → one or two pieces of evidence → practical contribution you can make.",
        "独特价值组合→一至两个证据→能带来的实际贡献。",
        "Why should we hire you?",
        "What makes you different from other candidates?",
    ),
    (
        "Why You Are Looking Now",
        "为什么现在寻找新机会",
        "Explain the reason honestly and positively, then focus on what you want next. Support variants such as new graduate, layoff, or employment gap.",
        "真实、正向说明离开原因，重点转向下一份工作的诉求；支持应届、裁员、空档期等变体。",
        "Why are you looking for a new opportunity now?",
        "What are you looking for next?",
    ),
    (
        "Core Strength",
        "核心优势",
        "Choose one important strength, prove it with recent real behavior, and connect it to the target role.",
        "只选一个重要优势，用近期真实行为证明，并连接目标岗位。",
        "What is one of your greatest strengths?",
        "Can you give me a recent example?",
    ),
    (
        "A Weakness You Are Improving",
        "正在改善的弱项",
        "A real but improvable weakness → specific action → change already observed. Do not disguise a strength as a weakness.",
        "真实但可改善的弱项→具体行动→已经出现的变化；不使用伪装优点。",
        "What is a weakness you are working on?",
        "What have you done to improve it?",
    ),
    (
        "Where You Want to Grow",
        "下一步成长方向",
        "Near-term capability goal → longer-term direction → why this role is a reasonable next step.",
        "近期能力目标→较长期方向→当前岗位为何是合理下一步。",
        "Where do you want to grow next?",
        "How does this role fit that direction?",
    ),
    (
        "Salary Expectations",
        "薪资期望",
        "Discuss a range, its basis, total compensation, and flexibility. Do not invent market figures without reliable information.",
        "表达区间、依据、整体薪酬和灵活性；没有可靠信息时不得虚构市场数字。",
        "What are your salary expectations?",
        "How flexible are you?",
    ),
    (
        "A Project You Are Proud Of",
        "自豪的项目",
        "Project goal → personal responsibility → key decisions → process and result, emphasizing what you did.",
        "项目目标→个人职责→关键决策→过程与结果，重点解释“我做了什么”。",
        "Tell me about a project you are proud of.",
        "What was specifically your contribution?",
    ),
    (
        "A Meaningful Achievement",
        "最有意义的成就",
        "Why it mattered → difficulty → personal contribution → verifiable impact. Distinct from Course 11's focus on project process.",
        "为什么重要→难度→个人贡献→可验证影响。不同于 Course 11 的项目过程深挖。",
        "Tell me about an achievement that matters to you.",
        "Why does this achievement matter to you?",
    ),
    (
        "Setting and Achieving an Ambitious Goal",
        "定高目标并实现",
        "Why the goal was challenging → how you broke it down and tracked it → obstacles → final evidence.",
        "目标为什么有挑战→如何拆解和跟踪→障碍→最终证据。",
        "Tell me about a time you set an ambitious goal and achieved it.",
        "What almost prevented you from succeeding?",
    ),
    (
        "Taking Initiative",
        "主动承担",
        "How you noticed the opportunity or problem → why you acted → what risk you took → result.",
        "如何发现机会或问题→为什么主动行动→承担了什么风险→结果。",
        "Tell me about a time you took initiative without being asked.",
        "Why had nobody acted before?",
    ),
    (
        "Introducing a Better Way",
        "提出并落地新方法",
        "Problem with the old approach → basis for the idea → testing and implementation → actual impact.",
        "旧方法的问题→创意依据→试验与落地→实际影响。",
        "Tell me about a time you introduced a better way of doing something.",
        "How did you test that the idea would work?",
    ),
    (
        "Overcoming a Difficult Challenge",
        "克服困难挑战",
        "External obstacle → response → persistence or adjustment → result, with emphasis on resilience.",
        "外部障碍→应对行动→坚持或调整→结果，重点是韧性。",
        "Tell me about a difficult challenge you overcame.",
        "What made it especially difficult?",
    ),
    (
        "Navigating Ambiguity",
        "处理模糊问题",
        "How you defined the problem, formed hypotheses, reduced risk, and moved forward with incomplete information.",
        "信息不完整时如何定义问题、建立假设、降低风险并推进。",
        "Tell me about a time you had to make sense of an ambiguous problem.",
        "Which assumptions did you test first?",
    ),
    (
        "Gathering Information and Making a Decision",
        "搜集信息并决策",
        "Information sources → key questions → options → decision criteria → result.",
        "信息来源→关键问题→备选方案→判断标准→结果。",
        "Tell me about a time you gathered information and made an important decision.",
        "What alternatives did you consider?",
    ),
    (
        "Prioritizing Competing Work",
        "在多项任务中抓重点",
        "Prioritization criteria → resource trade-offs → communication of the decision → protecting quality and deadlines.",
        "排序标准→资源取舍→沟通决定→保护质量与期限。",
        "Tell me about a time you had competing priorities and had to decide what mattered most.",
        "What did you defer or say no to?",
    ),
    (
        "Solving a Role-Specific Problem",
        "解决专业难题",
        "Adapt to the target role: diagnosis → professional judgment → solution trade-offs → validated result.",
        "按目标岗位适配；问题诊断→专业判断→方案权衡→验证结果。",
        "Tell me about a difficult technical or role-specific problem you solved.",
        "What trade-offs did you make?",
    ),
    (
        "Leading Without Authority",
        "没有头衔也能带动他人",
        "Set direction → mobilize others → handle resistance → shared result. A management title is not required.",
        "定方向→调动他人→处理阻力→共同结果；不要求管理职位。",
        "Tell me about a time you led others toward an important result, even without formal authority.",
        "How did you gain their commitment?",
    ),
    (
        "Making Teamwork Work",
        "让团队协作真正运转",
        "Division of work, dependencies, your contribution, and how you helped the team deliver.",
        "分工、依赖关系、本人贡献、如何帮助团队完成任务。",
        "Tell me about a time you worked with others to deliver an important result.",
        "What did you do that others did not?",
    ),
    (
        "Resolving Conflict or Disagreement",
        "解决冲突或分歧",
        "Source of disagreement → listening and clarification → how you handled it → result and relationship change.",
        "分歧来源→倾听和澄清→处理方式→结果及关系变化。",
        "Tell me about a disagreement or conflict you helped resolve.",
        "What did you do when the other person resisted?",
    ),
    (
        "Gaining Support with Evidence",
        "用证据争取支持",
        "Why the other party disagreed → evidence used → adapting to their concerns → whether support was truly gained.",
        "对方为何不同意→使用什么事实→如何适配对方关注点→是否真正获得支持。",
        "Tell me about a time you used evidence to gain support for an idea.",
        "Why did they disagree initially?",
    ),
    (
        "Explaining Complex Information",
        "解释复杂信息",
        "Understand the audience → simplify or adapt the explanation → check understanding → resulting action.",
        "理解受众→简化或调整表达→检查对方是否理解→行动结果。",
        "Tell me about a time you explained a complex idea to someone.",
        "How did you know they understood you?",
    ),
    (
        "Learning from Failure",
        "从失败中改变",
        "State your responsibility → impact → lesson → real behavior change afterward.",
        "明确本人责任→造成的影响→教训→之后发生的真实行为改变。",
        "Tell me about a failure or mistake and what you learned.",
        "What would you do differently now?",
    ),
    (
        "Learning and Applying a New Skill",
        "快速学习并应用",
        "Why learning was necessary → learning method → first application → actual result.",
        "为什么需要学习→学习方法→首次应用→实际结果。",
        "Tell me about a time you learned a new skill and applied it to a real problem.",
        "How did you know you had learned it well enough?",
    ),
    (
        "Adapting to Major Change",
        "适应重大变化",
        "Impact of the change → initial response → adjustment → new result.",
        "变化带来的影响→最初反应→调整方法→新结果。",
        "Tell me about a time you had to adapt to a major change.",
        "What did you change about your approach?",
    ),
    (
        "Acting on Difficult Feedback",
        "接受并使用反馈",
        "The feedback → how you evaluated and processed it → action taken → later evidence.",
        "反馈内容→如何判断和消化→采取行动→后续证据。",
        "Tell me about a time you received difficult feedback and acted on it.",
        "What changed as a result?",
    ),
    (
        "Questions for the Interviewer",
        "向面试官提问",
        "Ask genuine questions about the work, team, success criteria, and challenges based on the role and interview. Do not memorize generic questions.",
        "根据岗位和面试内容提出关于工作、团队、成功标准和挑战的真实问题；不背诵空泛问题。",
        "What questions do you have for us?",
        None,
    ),
)


def _build_catalog() -> tuple[CourseDefinition, ...]:
    courses: list[CourseDefinition] = []
    for order, content in enumerate(_CATALOG_CONTENT, start=1):
        name_en, name_zh_cn, focus_en, focus_zh_cn, core_text, follow_up_text = content
        course_id = f"course-{order:02d}"
        courses.append(
            CourseDefinition(
                id=course_id,
                order=order,
                name_en=name_en,
                name_zh_cn=name_zh_cn,
                answer_focus_en=focus_en,
                answer_focus_zh_cn=focus_zh_cn,
                core_question=QuestionDefinition(
                    id=f"{course_id}.core", kind="CORE", text=core_text
                ),
                follow_up_question=(
                    QuestionDefinition(
                        id=f"{course_id}.follow-up", kind="FOLLOW_UP", text=follow_up_text
                    )
                    if follow_up_text is not None
                    else None
                ),
            )
        )
    return tuple(courses)


COURSE_CATALOG_V1 = _build_catalog()
COURSES_BY_ID = {course.id: course for course in COURSE_CATALOG_V1}
