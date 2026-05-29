"""Theory Matcher — keyword-based theory recommendation."""

from __future__ import annotations

from pathlib import Path
import re
from dataclasses import dataclass


@dataclass
class TheoryCandidate:
    """A theory that matches a research question."""
    id: str
    name_zh: str
    name_en: str
    discipline: list[str]
    core_concepts: list[str]
    applicable_topics: list[str]
    explanation: str
    limitations: list[str]
    match_score: float


# Built-in theory library — minimal Phase 1 set
THEORY_LIBRARY: list[dict] = [
    {
        "id": "tam",
        "name_zh": "技术接受模型",
        "name_en": "Technology Acceptance Model (TAM)",
        "discipline": ["信息管理", "教育技术", "信息系统"],
        "core_concepts": ["感知有用性", "感知易用性", "使用态度", "行为意向"],
        "applicable_topics": ["用户技术接受", "信息系统采纳", "新技术扩散", "数字工具使用"],
        "explanation": "TAM 认为用户对新技术的接受取决于感知有用性和感知易用性，适合研究 AI 工具、数字平台、在线教育系统等被用户采纳的影响因素。",
        "limitations": ["过于简化社会影响因素", "忽略外部变量", "不适用于强制性技术环境"],
    },
    {
        "id": "uses_and_gratifications",
        "name_zh": "使用与满足理论",
        "name_en": "Uses and Gratifications Theory",
        "discipline": ["传播学", "媒介研究", "新闻传播"],
        "core_concepts": ["媒介使用动机", "需求满足", "用户主动性", "社会心理需求"],
        "applicable_topics": ["短视频使用动机", "社交媒体沉迷", "游戏成瘾", "新闻消费行为"],
        "explanation": "从用户视角出发，认为人们主动选择媒介来满足特定社会和心理需求。适合研究大学生为何大量使用短视频/社交媒体，以及满足感如何影响持续使用。",
        "limitations": ["忽视结构性约束", "难以测量主观满足感", "不解释负面效果"],
    },
    {
        "id": "social_support",
        "name_zh": "社会支持理论",
        "name_en": "Social Support Theory",
        "discipline": ["社会学", "心理学", "健康传播"],
        "core_concepts": ["情感支持", "工具性支持", "信息支持", "社会网络"],
        "applicable_topics": ["社会支持与身心健康", "弱势群体援助", "社区治理", "孤独感"],
        "explanation": "认为社会支持是人类应对压力和困境的重要资源。适合研究新银发群体、数字鸿沟下的社会支持、社区治理中的社会资本等话题。",
        "limitations": ["支持与健康因果方向不明确", "难以区分支持类型效应"],
    },
    {
        "id": "media_dependency",
        "name_zh": "媒介依赖理论",
        "name_en": "Media Dependency Theory",
        "discipline": ["传播学", "媒介研究", "社会学"],
        "core_concepts": ["媒介依赖", "信息获取", "社会整合", "理解世界"],
        "applicable_topics": ["AI工具依赖", "手机依赖", "新闻消费", "信息焦虑"],
        "explanation": "个人与媒介之间形成依赖关系，依赖程度取决于媒介满足特定需求的程度。适合研究大学生对 AI 工具、手机、社交媒体逐渐形成依赖的过程和后果。",
        "limitations": ["难以量化依赖程度", "因果方向存在争议"],
    },
    {
        "id": "planned_behavior",
        "name_zh": "计划行为理论",
        "name_en": "Theory of Planned Behavior (TPB)",
        "discipline": ["心理学", "行为科学", "市场营销"],
        "core_concepts": ["行为态度", "主观规范", "感知行为控制", "行为意向"],
        "applicable_topics": ["健康行为", "消费决策", "环境行为", "学习行为意向"],
        "explanation": "行为意向由态度、主观规范和感知行为控制共同决定。适合研究大学生健康行为改变、学习行为意向、环境可持续行为等涉及自主决策的话题。",
        "limitations": ["不适用于无意识行为", "感知控制难以准确测量"],
    },
    {
        "id": "digital_labor",
        "name_zh": "数字劳动理论",
        "name_en": "Digital Labor Theory",
        "discipline": ["媒介研究", "传播政治经济学", "社会学"],
        "core_concepts": ["用户生成内容", "平台资本", "数据剥削", "免费劳动"],
        "applicable_topics": ["平台用户劳动", "内容创作者", "注意力经济", "数字不平等"],
        "explanation": "将用户在社交媒体、短视频平台上的活动视为一种无偿或低偿的数字劳动，揭示平台如何从用户行为中提取价值。适合研究大学生作为内容消费者和生产者的双重身份及其经济后果。",
        "limitations": ["理论边界模糊", "与马克思主义劳动理论的衔接存在争议"],
    },
    {
        "id": "empowerment",
        "name_zh": "赋权理论",
        "name_en": "Empowerment Theory",
        "discipline": ["社会学", "公共管理", "社会工作"],
        "core_concepts": ["心理赋权", "社会赋权", "政治赋权", "自我效能感"],
        "applicable_topics": ["弱势群体能力建设", "公民参与", "数字赋权", "社区治理"],
        "explanation": "强调通过提升个体的控制感、能力和参与机会来实现社会变革。适合研究 AI 如何赋权大学生或弱势群体，或数字鸿沟如何阻碍赋权过程。",
        "limitations": ["赋权效果难以量化", "忽视结构性障碍"],
    },
    {
        "id": "ecosystems",
        "name_zh": "生态系统理论",
        "name_en": "Ecosystems Theory (Bronfenbrenner)",
        "discipline": ["心理学", "教育学", "社会学"],
        "core_concepts": ["微观系统", "中观系统", "外部系统", "宏观系统", "时间系统"],
        "applicable_topics": ["儿童/青少年发展", "环境影响", "家庭与学校", "数字环境影响"],
        "explanation": "将个体发展置于多层嵌套的环境中理解。适合研究 AI、手机等技术如何通过家庭（微观）、学校（中观）、社会文化（宏观）等层次影响大学生发展。",
        "limitations": ["层次过多难以操作化", "各系统边界模糊"],
    },
    {
        "id": "governance_modernization",
        "name_zh": "治理现代化理论",
        "name_en": "Modernization of Governance",
        "discipline": ["公共管理", "政治学", "行政学"],
        "core_concepts": ["多中心治理", "协同治理", "数字治理", "公共服务"],
        "applicable_topics": ["社区治理数字化", "政务服务", "基层治理创新", "智慧城市"],
        "explanation": "研究政府治理模式从传统科层制向数字化、协同化转型的过程。适合研究社区治理数字化转型、公共服务创新、数字政府建设等话题。",
        "limitations": ["西方理论移植局限", "缺乏对技术工具性的批判视角"],
    },
    {
        "id": "ai_capability_reconstruction",
        "name_zh": "AI时代能力重构",
        "name_en": "AI-Era Capability Reconstruction",
        "discipline": ["教育学", "社会学", "未来学"],
        "core_concepts": ["人机协同", "批判性思维", "数字素养", "终身学习", "AI伦理"],
        "applicable_topics": ["AI与教育变革", "大学生能力重构", "AI对职业影响", "终身学习"],
        "explanation": "AI 时代对传统能力体系提出挑战，研究哪些能力被 AI 替代、哪些被放大、哪些是新生的。适合研究 AI 如何影响大学生应当培养的核心能力，以及教育系统如何响应。",
        "limitations": ["理论较新，缺乏实证支撑", "预测性强但不确定性高"],
    },
    {
        "id": "institutional_theory",
        "name_zh": "制度理论",
        "name_en": "Institutional Theory",
        "discipline": ["公共管理", "社会学", "组织研究"],
        "core_concepts": ["制度合法性", "同构", "制度变迁", "制度逻辑", "去耦"],
        "applicable_topics": ["组织行为", "政策扩散", "制度变革", "组织趋同"],
        "explanation": "认为组织行为深受制度环境影响，组织形式和政策通过强制性、模仿性和规范性同构而趋同。适合研究为何不同高校在教育改革中采取相似策略。",
        "limitations": ["过度归因于制度而忽视能动性", "混淆制度与组织", "对制度变迁的解释力弱"],
    },
    {
        "id": "innovation_diffusion",
        "name_zh": "创新扩散理论",
        "name_en": "Innovation Diffusion Theory (Rogers)",
        "discipline": ["传播学", "社会学", "管理学"],
        "core_concepts": ["创新特征", "采纳者分类", "社会系统", "扩散曲线", "相对优势"],
        "applicable_topics": ["新技术采纳", "AI工具推广", "政策传播", "社会创新"],
        "explanation": "创新通过特定渠道在社会成员间传播，采纳者的特征和社会系统影响扩散速度。适合研究 AI 工具如何在大学生群体中从早期采纳者扩散到大多数人。",
        "limitations": ["忽视权力不平等", "假设创新始终有益", "采纳者分类过于简化"],
    },
    {
        "id": "social_cognitive",
        "name_zh": "社会认知理论",
        "name_en": "Social Cognitive Theory (Bandura)",
        "discipline": ["心理学", "教育学", "传播学"],
        "core_concepts": ["自我效能感", "观察学习", "三元交互", "结果期望", "自我调节"],
        "applicable_topics": ["学习行为", "健康行为改变", "媒体影响", "AI辅助学习"],
        "explanation": "个体行为受认知、环境和行为三者交互影响，自我效能感是关键中介变量。适合研究 AI 工具如何通过提升自我效能感来促进学生学习行为改变。",
        "limitations": ["忽略生物因素", "自我效能感测量主观"],
    },
    {
        "id": "self_determination",
        "name_zh": "自我决定理论",
        "name_en": "Self-Determination Theory (SDT)",
        "discipline": ["心理学", "教育学", "组织行为学"],
        "core_concepts": ["内在动机", "自主性", "胜任感", "归属感", "外在激励"],
        "applicable_topics": ["学习动机", "工作投入", "创造力", "AI工具使用动机"],
        "explanation": "当自主性、胜任感和归属感三种基本心理需求得到满足时，个体的内在动机最强。适合研究 AI 工具是否激发还是抑制了大学生的内在学习动机。",
        "limitations": ["三种需求的优先性因文化而异", "内在动机难以量化"],
    },
    {
        "id": "knowledge_gap",
        "name_zh": "知识沟理论",
        "name_en": "Knowledge Gap Theory",
        "discipline": ["传播学", "社会学", "教育学"],
        "core_concepts": ["信息不平等", "社会经济地位", "媒介接触", "知识差距", "数字鸿沟"],
        "applicable_topics": ["数字不平等", "AI素养差距", "教育公平", "信息获取差异"],
        "explanation": "社会经济地位较高者比地位较低者更快获取信息，导致知识差距扩大。适合研究 AI 工具使用如何加剧或缩小大学生群体内部的信息和技能不平等。",
        "limitations": ["难以区分知识与信息", "议题重要性影响差距大小"],
    },
    {
        "id": "agenda_setting",
        "name_zh": "议程设置理论",
        "name_en": "Agenda-Setting Theory",
        "discipline": ["传播学", "新闻学", "政治学"],
        "core_concepts": ["媒介议程", "公众议程", "显著性转移", "框架效应", "议题属性"],
        "applicable_topics": ["AI舆论", "社交媒体议题", "算法推荐影响", "公共认知"],
        "explanation": "媒体通过报道某些议题的频率和方式影响公众对议题重要性的认知。适合研究 AI 推荐算法如何影响大学生对社会议题的认知排序和关注方向。",
        "limitations": ["媒介效果被高估", "忽略受众主动选择"],
    },
    {
        "id": "framing_theory",
        "name_zh": "框架理论",
        "name_en": "Framing Theory",
        "discipline": ["传播学", "新闻学", "心理学"],
        "core_concepts": ["信息框架", "认知基模", "议题建构", "责任归因", "传播效果"],
        "applicable_topics": ["AI风险认知", "新闻报道倾向", "公众态度", "政策接受度"],
        "explanation": "同一议题的不同呈现方式会影响人们的理解和决策。适合研究 AI 工具被正面框架（效率提升）还是负面框架（取代人类）呈现时，大学生接受度的差异。",
        "limitations": ["框架定义模糊", "多种框架同时作用难以分离"],
    },
    {
        "id": "flow_theory",
        "name_zh": "心流理论",
        "name_en": "Flow Theory (Csikszentmihalyi)",
        "discipline": ["心理学", "人机交互", "教育学"],
        "core_concepts": ["心流体验", "挑战-技能平衡", "即时反馈", "沉浸感", "时间扭曲"],
        "applicable_topics": ["游戏化学习", "AI交互体验", "短视频沉浸", "学习投入度"],
        "explanation": "当挑战与技能达到平衡且提供即时反馈时，个体进入高度专注的心流状态。适合研究 AI 辅助学习工具如何设计以促进大学生的心流体验和深度学习。",
        "limitations": ["难以持续维持心流", "个体差异大"],
    },
    {
        "id": "cognitive_load",
        "name_zh": "认知负荷理论",
        "name_en": "Cognitive Load Theory",
        "discipline": ["教育学", "教育心理学", "人机交互"],
        "core_concepts": ["内在认知负荷", "外在认知负荷", "相关认知负荷", "工作记忆", "图示建构"],
        "applicable_topics": ["AI辅助学习", "教学设计", "多媒体学习", "信息呈现"],
        "explanation": "学习效果取决于如何管理工作记忆的有限容量。适合研究 AI 工具是减轻还是增加了学生的认知负荷，以及如何优化 AI 辅助教学的设计。",
        "limitations": ["认知负荷的操作化定义不统一", "测量方法存在争议"],
    },
    {
        "id": "constructivism",
        "name_zh": "建构主义学习理论",
        "name_en": "Constructivism",
        "discipline": ["教育学", "教育心理学", "学习科学"],
        "core_concepts": ["主动建构", "先验知识", "社会协商", "情境学习", "意义建构"],
        "applicable_topics": ["项目式学习", "AI辅助个性化学习", "协作学习", "学习环境设计"],
        "explanation": "学习者基于已有经验主动建构知识，而非被动接收信息。适合研究 AI 工具如何支持学生的个性化知识建构，以及 AI 在 PBL 和协作学习中的角色。",
        "limitations": ["对教师要求高", "评估难以标准化"],
    },
    {
        "id": "connectivism",
        "name_zh": "联通主义学习理论",
        "name_en": "Connectivism",
        "discipline": ["教育学", "教育技术", "网络科学"],
        "core_concepts": ["网络学习", "知识联结", "信息节点", "持续学习", "技术中介"],
        "applicable_topics": ["AI时代学习", "MOOC学习行为", "知识网络", "终身学习"],
        "explanation": "学习是建立信息节点之间连接的过程，在数字时代学会在哪里找到知识比记住知识更重要。适合研究大学生如何在 AI 工具帮助下构建个人知识网络。",
        "limitations": ["与传统学习理论的边界不清", "实证研究不足"],
    },
    {
        "id": "social_capital",
        "name_zh": "社会资本理论",
        "name_en": "Social Capital Theory",
        "discipline": ["社会学", "政治学", "管理学"],
        "core_concepts": ["社会网络", "信任", "互惠规范", "桥接型资本", "粘合型资本"],
        "applicable_topics": ["社区参与", "社会信任", "网络社交", "职业生涯"],
        "explanation": "社会关系和网络中的信任与规范构成一种资本，可转化为经济或其他形式的利益。适合研究大学生如何通过社交媒体和 AI 工具积累社会资本。",
        "limitations": ["社会资本的测量标准不一", "因果方向不明确"],
    },
    {
        "id": "rational_choice",
        "name_zh": "理性选择理论",
        "name_en": "Rational Choice Theory",
        "discipline": ["经济学", "社会学", "政治学"],
        "core_concepts": ["效用最大化", "成本-收益分析", "偏好排序", "信息有限", "机会成本"],
        "applicable_topics": ["学习决策", "职业选择", "消费行为", "教育投资"],
        "explanation": "个体在有限信息和资源约束下做出最优选择。适合研究大学生在使用 AI 工具与否、选择何种学习策略时如何进行理性计算和权衡。",
        "limitations": ["过度简化人类行为", "忽视情感和社会规范"],
    },
    {
        "id": "actor_network",
        "name_zh": "行动者网络理论",
        "name_en": "Actor-Network Theory (ANT)",
        "discipline": ["STS研究", "社会学", "科学技术哲学"],
        "core_concepts": ["行动者", "网络", "转译", "黑箱", "异质性"],
        "applicable_topics": ["技术与社会", "AI系统分析", "科技创新", "人机关系"],
        "explanation": "人和非人（技术、算法、文本）都被视为网络中的行动者，技术并非被动工具而是积极参与社会建构。适合研究 AI 系统如何在人机共生的学术网络中主动重塑知识生产。",
        "limitations": ["过于平等看待人与物", "政治批判力不足"],
    },
    {
        "id": "symbolic_interactionism",
        "name_zh": "符号互动论",
        "name_en": "Symbolic Interactionism",
        "discipline": ["社会学", "社会心理学", "传播学"],
        "core_concepts": ["符号意义", "自我概念", "角色扮演", "情境定义", "意义协商"],
        "applicable_topics": ["AI交互中的身份建构", "网络社交", "自我呈现", "在线社区"],
        "explanation": "人们通过互动中的符号交换来建构意义和自我认同。适合研究大学生在社交媒体和 AI 对话中如何呈现自我、建构身份认同。",
        "limitations": ["忽略宏观社会结构", "难以系统验证"],
    },
    {
        "id": "principal_agent",
        "name_zh": "委托代理理论",
        "name_en": "Principal-Agent Theory",
        "discipline": ["经济学", "公共管理", "管理学"],
        "core_concepts": ["信息不对称", "激励机制", "道德风险", "逆向选择", "监督成本"],
        "applicable_topics": ["公共服务外包", "高校治理", "AI监管", "平台治理"],
        "explanation": "当委托人委托代理人执行任务时，由于信息不对称和利益不一致，代理人可能追求自身利益而非委托人利益。适合研究高校如何设计激励机制以规范学生对 AI 工具的使用。",
        "limitations": ["过于依赖经济人假设", "忽视信任和关系"],
    },
    {
        "id": "collaborative_governance",
        "name_zh": "协同治理理论",
        "name_en": "Collaborative Governance",
        "discipline": ["公共管理", "政治学", "行政学"],
        "core_concepts": ["多元参与", "共识导向", "协商", "公共价值", "网络治理"],
        "applicable_topics": ["社区治理", "公共服务", "AI政策制定", "多方协作"],
        "explanation": "政府、市场和社会主体通过协同合作解决公共问题。适合研究数字治理时代 AI 技术如何改变政府-公众-企业三方的协同关系和服务模式。",
        "limitations": ["参与不平等", "共识达成成本高"],
    },
    {
        "id": "street_level_bureaucracy",
        "name_zh": "街头官僚理论",
        "name_en": "Street-Level Bureaucracy (Lipsky)",
        "discipline": ["公共管理", "社会学", "社会政策"],
        "core_concepts": ["自由裁量权", "资源约束", "应对策略", "公共服务", "政策执行"],
        "applicable_topics": ["基层治理", "公共服务供给", "AI辅助决策", "政策执行偏差"],
        "explanation": "基层公共服务提供者在面对资源约束、需求矛盾时通过自由裁量权形成应对策略。适合研究 AI 工具引入公共服务后如何影响基层工作者的判断和裁量行为。",
        "limitations": ["将裁量权视为被动应对", "忽略组织环境差异"],
    },
    {
        "id": "digital_divide",
        "name_zh": "数字鸿沟理论",
        "name_en": "Digital Divide Theory",
        "discipline": ["社会学", "传播学", "公共政策"],
        "core_concepts": ["接入鸿沟", "使用鸿沟", "技能鸿沟", "数字排斥", "信息贫困"],
        "applicable_topics": ["数字不平等的多层次表现", "AI素养", "数字包容", "教育公平"],
        "explanation": "数字鸿沟从最初的接入不平等发展到使用和效果的多级不平等。适合研究 AI 时代大学生群体中新的数字技能分层，以及 AI 工具是否加剧或缩小了这些差距。",
        "limitations": ["分层边界模糊", "与知识沟理论重叠"],
    },
    {
        "id": "policy_feedback",
        "name_zh": "政策反馈理论",
        "name_en": "Policy Feedback Theory",
        "discipline": ["公共管理", "政治学", "公共政策"],
        "core_concepts": ["政策遗产", "锁定效应", "资源效应", "解释效应", "制度惯性"],
        "applicable_topics": ["政策延续性", "教育改革", "数字政策", "公共资源分配"],
        "explanation": "既有政策通过资源分配和认知塑造反过来影响未来的政策制定和政治参与。适合研究高校AI使用规范的制定如何通过反馈效应影响师生行为。",
        "limitations": ["资源效应和解释效应难以分离", "部分场景反馈微弱"],
    },
    {
        "id": "punctuated_equilibrium",
        "name_zh": "间断均衡理论",
        "name_en": "Punctuated Equilibrium Theory",
        "discipline": ["公共管理", "政治学", "政策科学"],
        "core_concepts": ["政策稳定", "政策突变", "注意力转移", "制度摩擦", "政策垄断"],
        "applicable_topics": ["教育政策变动", "AI政策制定", "政策议程", "制度变迁"],
        "explanation": "政策在长期稳定之后可能发生急剧变化，原因是注意力转移和制度摩擦。适合解释为何高校AI相关政策的制定往往是被突发技术事件（如ChatGPT问世）而推动。",
        "limitations": ["难以预测突变时机", "对不同政策领域的解释力不均"],
    },
    {
        "id": "resource_dependence",
        "name_zh": "资源依赖理论",
        "name_en": "Resource Dependence Theory",
        "discipline": ["组织管理学", "管理学", "社会学"],
        "core_concepts": ["外部资源依赖", "自主性", "权力不平衡", "战略联盟", "组织适应"],
        "applicable_topics": ["高校-企业合作", "AI供应商关系", "组织策略", "校企合作"],
        "explanation": "组织为获取关键资源而依赖外部环境，这种依赖影响组织行为和战略选择。适合研究高校在AI工具采购上如何应对对技术供应商的依赖关系。",
        "limitations": ["忽视内部动态", "对资源定义过于宽泛"],
    },
    {
        "id": "stakeholder_theory",
        "name_zh": "利益相关者理论",
        "name_en": "Stakeholder Theory",
        "discipline": ["管理学", "商业伦理", "公共管理"],
        "core_concepts": ["利益相关者识别", "利益平衡", "价值共创", "责任分配", "参与治理"],
        "applicable_topics": ["AI伦理治理", "高校决策", "多方参与", "政策评估"],
        "explanation": "组织决策应平衡所有利益相关者的利益，而不仅仅是股东利益。适合分析高校在制定AI使用政策时应如何考虑学生、教师、管理者、技术供应商等各方利益。",
        "limitations": ["利益相关者边界难以界定", "利益冲突的解决缺乏明确标准"],
    },
    {
        "id": "spiral_of_silence",
        "name_zh": "沉默的螺旋理论",
        "name_en": "Spiral of Silence",
        "discipline": ["传播学", "政治学", "社会心理学"],
        "core_concepts": ["意见气候", "孤立恐惧", "沉默多数", "多数无知", "舆论表达"],
        "applicable_topics": ["AI使用态度表达", "社交媒体舆论", "学术讨论", "少数意见"],
        "explanation": "人们因害怕被孤立而在感知到自己的观点属于少数时倾向于沉默，导致主流声音越来越大。适合研究大学生在使用AI的争议话题上是否存在公开态度与私下想法的差异。",
        "limitations": ["个人特征影响表达意愿", "跨文化适用性存疑"],
    },
    {
        "id": "structural_functionalism",
        "name_zh": "结构功能主义",
        "name_en": "Structural Functionalism",
        "discipline": ["社会学", "人类学", "教育学"],
        "core_concepts": ["社会结构", "社会功能", "系统整合", "适应性", "社会稳定"],
        "applicable_topics": ["教育功能分析", "AI的社会角色", "社会制度演变", "技术功能"],
        "explanation": "社会各子系统通过满足特定功能需求来维持整体稳定。适合宏观分析 AI 在高等教育体系中扮演的角色和功能，以及AI引入如何影响教育系统的功能平衡。",
        "limitations": ["过于强调稳定而忽视冲突", "功能解释可能沦为循环论证"],
    },
    {
        "id": "privacy_calculus",
        "name_zh": "隐私计算理论",
        "name_en": "Privacy Calculus Theory",
        "discipline": ["信息管理", "信息系统", "消费者行为"],
        "core_concepts": ["隐私风险感知", "感知收益", "信息披露", "隐私权衡", "信任机制"],
        "applicable_topics": ["AI数据隐私", "个人信息披露", "算法透明", "平台信任"],
        "explanation": "用户在决定是否披露个人信息时进行风险-收益权衡计算。适合研究大学生在享受AI工具便利与保护个人数据隐私之间的权衡过程和边界。",
        "limitations": ["假设用户是理性的", "忽略情感决策"],
    },
]


class TheoryMatcher:
    """Match research questions to theories using keyword overlap."""

    STOPWORDS = {
        "的", "了", "和", "是", "在", "与", "对", "为", "有", "也", "就", "都", "而",
        "及", "着", "或", "以", "一个", "可以", "这个", "研究", "问题", "如何",
        "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "can",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "that", "this", "it", "they", "them", "their",
    }

    def __init__(self) -> None:
        self.theories = THEORY_LIBRARY

    def extract_keywords(self, text: str) -> list[str]:
        """Extract significant keywords from research question.

        English: uses word boundaries (\b).
        Chinese: splits into character n-grams (2-4 chars) that form meaningful units.
        """
        words: list[str] = []

        # English word-boundary extraction
        english_part = re.sub(r"[\u4e00-\u9fff]", "", text.lower())
        english_words = re.findall(r"\b[a-zA-Z]{2,}\b", english_part)
        words.extend(w for w in english_words if w not in self.STOPWORDS)

        # Chinese character n-gram extraction (no word boundaries in Chinese text)
        chinese_text = re.sub(r"[a-zA-Z0-9]", "", text)
        for n in range(2, 5):  # 2, 3, 4 character grams
            for i in range(len(chinese_text) - n + 1):
                gram = chinese_text[i : i + n]
                if gram not in self.STOPWORDS:
                    words.append(gram)

        # Deduplicate while preserving order
        seen: set[str] = set()
        result: list[str] = []
        for w in words:
            if w not in seen:
                seen.add(w)
                result.append(w)
        return result

    def match(self, research_question: str, top_k: int = 5) -> list[TheoryCandidate]:
        """Match a research question to theories.

        Returns top_k theories sorted by keyword overlap score.
        """
        query_words = set(self.extract_keywords(research_question))
        if not query_words:
            return []

        scored: list[tuple[TheoryCandidate, float]] = []

        for theory in self.theories:
            # Score against: applicable_topics + core_concepts + discipline
            theory_words: set[str] = set()
            for topic in theory["applicable_topics"]:
                theory_words.update(self.extract_keywords(topic))
            for concept in theory["core_concepts"]:
                theory_words.update(self.extract_keywords(concept))
            for discipline in theory["discipline"]:
                theory_words.update(self.extract_keywords(discipline))
            # Also add Chinese theory name words
            theory_words.update(self.extract_keywords(theory["name_zh"]))

            overlap = len(query_words & theory_words)
            if overlap == 0:
                continue

            # Jaccard-like score
            union = len(query_words | theory_words)
            score = overlap / union if union > 0 else 0

            candidate = TheoryCandidate(
                id=theory["id"],
                name_zh=theory["name_zh"],
                name_en=theory["name_en"],
                discipline=theory["discipline"],
                core_concepts=theory["core_concepts"],
                applicable_topics=theory["applicable_topics"],
                explanation=theory["explanation"],
                limitations=theory["limitations"],
                match_score=round(score, 3),
            )
            scored.append((candidate, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_k]]

    def export_candidates_as_context(
        self, candidates: list[TheoryCandidate], output_path: str | Path
    ) -> None:
        """Write selected theory candidates as a Markdown context file."""
        out = Path(output_path)
        lines = ["# Theory Context\n"]
        for c in candidates:
            lines.append(f"\n## {c.name_zh} ({c.name_en})")
            lines.append(f"\n**匹配度:** {c.match_score:.0%}")
            lines.append(f"\n**学科:** {' · '.join(c.discipline[:3])}")
            lines.append(f"\n**核心理论概念:** {' · '.join(c.core_concepts[:4])}")
            lines.append(f"\n**适用话题:** {' · '.join(c.applicable_topics[:3])}")
            lines.append(f"\n**理论解释:** {c.explanation}")
            lines.append(f"\n**局限:** {'；'.join(c.limitations)}")
        out.write_text("\n".join(lines), encoding="utf-8")
