"""Theory Matcher — keyword-based theory recommendation."""

from __future__ import annotations

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
