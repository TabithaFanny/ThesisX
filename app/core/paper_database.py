"""论文数据库服务

对接多个学术论文数据库 API，获取真实论文的表达方式供 AI 参考。

支持的数据源：
- Semantic Scholar: 免费开放，覆盖面广
- arXiv: 免费开放，学术预印本
- CrossRef: 免费开放，文献元数据

使用示例：
    >>> from app.core.paper_database import PaperDatabase
    >>> db = PaperDatabase()
    >>> papers = db.search("deep learning medical imaging", limit=5)
    >>> for p in papers:
    ...     print(p.title, p.abstract[:100])
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

logger = logging.getLogger(__name__)

# API 配置
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
ARXIV_API = "http://export.arxiv.org/api/query"
CROSSREF_API = "https://api.crossref.org/works"

# 请求配置
REQUEST_TIMEOUT = 15
MAX_RETRIES = 2


@dataclass
class Paper:
    """论文数据模型"""
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    source: str = ""  # semantic_scholar / arxiv / crossref
    url: str = ""
    doi: str = ""
    citations: int = 0

    # 提取的优质表达片段
    expressions: List[str] = field(default_factory=list)


class SemanticScholarClient:
    """Semantic Scholar API 客户端

    免费 API，无需密钥，但有速率限制（100次/5分钟）
    文档：https://api.semanticscholar.org/
    """

    def __init__(self):
        self.base_url = SEMANTIC_SCHOLAR_API
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "WenbiaoAI/1.0 (Academic Research Tool)"
        })

    def search(self, query: str, limit: int = 10) -> List[Paper]:
        """搜索论文

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            论文列表
        """
        papers = []
        try:
            url = f"{self.base_url}/paper/search"
            params = {
                "query": query,
                "limit": min(limit, 100),
                "fields": "title,abstract,authors,year,citationCount,url,externalIds"
            }

            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            for item in data.get("data", []):
                if not item.get("abstract"):
                    continue

                paper = Paper(
                    title=item.get("title", ""),
                    abstract=item.get("abstract", ""),
                    authors=[a.get("name", "") for a in item.get("authors", [])[:5]],
                    year=item.get("year") or 0,
                    source="semantic_scholar",
                    url=item.get("url", ""),
                    doi=item.get("externalIds", {}).get("DOI", ""),
                    citations=item.get("citationCount") or 0
                )
                papers.append(paper)

            logger.info(f"Semantic Scholar 搜索到 {len(papers)} 篇论文")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Semantic Scholar API 请求失败: {e}")
        except Exception as e:
            logger.error(f"Semantic Scholar 解析失败: {e}")

        return papers


class ArxivClient:
    """arXiv API 客户端

    完全免费开放，无需密钥
    文档：https://arxiv.org/help/api/
    """

    def __init__(self):
        self.base_url = ARXIV_API
        self.session = requests.Session()

    def search(self, query: str, limit: int = 10) -> List[Paper]:
        """搜索论文"""
        papers = []
        try:
            # arXiv 使用特殊的查询语法
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": min(limit, 50),
                "sortBy": "relevance",
                "sortOrder": "descending"
            }

            response = self.session.get(self.base_url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # 解析 Atom XML
            content = response.text
            papers = self._parse_arxiv_response(content)

            logger.info(f"arXiv 搜索到 {len(papers)} 篇论文")

        except requests.exceptions.RequestException as e:
            logger.warning(f"arXiv API 请求失败: {e}")
        except Exception as e:
            logger.error(f"arXiv 解析失败: {e}")

        return papers

    def _parse_arxiv_response(self, xml_content: str) -> List[Paper]:
        """解析 arXiv XML 响应"""
        papers = []

        # 简单的正则解析，避免引入 xml 库
        entries = re.findall(r'<entry>(.*?)</entry>', xml_content, re.DOTALL)

        for entry in entries:
            title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
            abstract_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)

            if not title_match or not abstract_match:
                continue

            title = title_match.group(1).strip().replace('\n', ' ')
            abstract = abstract_match.group(1).strip().replace('\n', ' ')

            # 提取作者
            authors = re.findall(r'<name>(.*?)</name>', entry)[:5]

            # 提取年份
            published = re.search(r'<published>(\d{4})', entry)
            year = int(published.group(1)) if published else 0

            # 提取链接
            link_match = re.search(r'<id>(.*?)</id>', entry)
            url = link_match.group(1) if link_match else ""

            paper = Paper(
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                source="arxiv",
                url=url
            )
            papers.append(paper)

        return papers


class CrossRefClient:
    """CrossRef API 客户端

    免费开放，无需密钥（但建议提供邮箱以获得更好的速率限制）
    文档：https://api.crossref.org/
    """

    def __init__(self, email: str = ""):
        self.base_url = CROSSREF_API
        self.session = requests.Session()
        self.email = email
        if email:
            self.session.headers.update({"User-Agent": f"WenbiaoAI/1.0 (mailto:{email})"})

    def search(self, query: str, limit: int = 10) -> List[Paper]:
        """搜索论文"""
        papers = []
        try:
            params = {
                "query": query,
                "rows": min(limit, 50),
                "select": "title,abstract,author,published-print,DOI,is-referenced-by-count,URL"
            }

            response = self.session.get(self.base_url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            for item in data.get("message", {}).get("items", []):
                abstract = item.get("abstract", "")
                if not abstract:
                    continue

                # 清理 HTML 标签
                abstract = re.sub(r'<[^>]+>', '', abstract)

                # 提取标题
                title_list = item.get("title", [])
                title = title_list[0] if title_list else ""

                # 提取作者
                authors = []
                for author in item.get("author", [])[:5]:
                    name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                    if name:
                        authors.append(name)

                # 提取年份
                pub_date = item.get("published-print", {}).get("date-parts", [[0]])
                year = pub_date[0][0] if pub_date and pub_date[0] else 0

                paper = Paper(
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    year=year,
                    source="crossref",
                    url=item.get("URL", ""),
                    doi=item.get("DOI", ""),
                    citations=item.get("is-referenced-by-count", 0)
                )
                papers.append(paper)

            logger.info(f"CrossRef 搜索到 {len(papers)} 篇论文")

        except requests.exceptions.RequestException as e:
            logger.warning(f"CrossRef API 请求失败: {e}")
        except Exception as e:
            logger.error(f"CrossRef 解析失败: {e}")

        return papers


class PaperDatabase:
    """论文数据库聚合服务

    同时查询多个数据源，合并去重后返回结果。
    """

    def __init__(self):
        self.semantic_scholar = SemanticScholarClient()
        self.arxiv = ArxivClient()
        self.crossref = CrossRefClient()

    def search(self, query: str, limit: int = 10, sources: List[str] = None) -> List[Paper]:
        """搜索论文

        Args:
            query: 搜索关键词（支持中英文，中文会自动翻译关键词）
            limit: 每个数据源返回的数量
            sources: 指定数据源列表，默认全部

        Returns:
            合并后的论文列表，按引用数排序
        """
        if sources is None:
            sources = ["semantic_scholar", "arxiv", "crossref"]

        all_papers = []

        # 并行查询多个数据源
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}

            if "semantic_scholar" in sources:
                futures[executor.submit(self.semantic_scholar.search, query, limit)] = "semantic_scholar"
            if "arxiv" in sources:
                futures[executor.submit(self.arxiv.search, query, limit)] = "arxiv"
            if "crossref" in sources:
                futures[executor.submit(self.crossref.search, query, limit)] = "crossref"

            for future in as_completed(futures, timeout=30):
                try:
                    papers = future.result()
                    all_papers.extend(papers)
                except Exception as e:
                    source = futures[future]
                    logger.warning(f"{source} 查询失败: {e}")

        # 去重（按标题相似度）
        unique_papers = self._deduplicate(all_papers)

        # 按引用数排序
        unique_papers.sort(key=lambda p: p.citations, reverse=True)

        # 提取优质表达
        for paper in unique_papers:
            paper.expressions = self._extract_expressions(paper.abstract)

        logger.info(f"论文数据库共返回 {len(unique_papers)} 篇去重后的论文")
        return unique_papers

    def _deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """去重"""
        seen_titles = set()
        unique = []

        for paper in papers:
            # 简化标题用于比较
            normalized = paper.title.lower().strip()
            normalized = re.sub(r'[^\w\s]', '', normalized)

            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(paper)

        return unique

    def _extract_expressions(self, abstract: str) -> List[str]:
        """从摘要中提取优质表达片段

        提取学术写作中常用的表达方式，供 AI 参考。
        """
        if not abstract:
            return []

        expressions = []

        # 按句子分割
        sentences = re.split(r'[.!?]', abstract)

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20 or len(sent) > 200:
                continue

            # 筛选包含学术表达模式的句子
            academic_patterns = [
                r'\bwe (propose|present|introduce|demonstrate|show|find|observe)\b',
                r'\b(this|our) (study|research|work|paper|approach|method)\b',
                r'\b(results|findings|experiments) (show|indicate|suggest|demonstrate)\b',
                r'\b(significantly|substantially|notably|remarkably)\b',
                r'\b(compared to|in contrast to|unlike|whereas)\b',
                r'\b(furthermore|moreover|additionally|in addition)\b',
                r'\b(however|nevertheless|nonetheless|although)\b',
            ]

            for pattern in academic_patterns:
                if re.search(pattern, sent, re.IGNORECASE):
                    expressions.append(sent)
                    break

        return expressions[:5]  # 最多返回5个表达


def search_related_papers(text: str, limit: int = 5) -> List[Paper]:
    """便捷函数：根据文本搜索相关论文

    Args:
        text: 用户的文本内容
        limit: 返回数量

    Returns:
        相关论文列表
    """
    # 提取关键词
    keywords = extract_keywords(text)
    if not keywords:
        return []

    query = " ".join(keywords[:5])
    logger.info(f"论文搜索关键词: {query}")

    db = PaperDatabase()
    return db.search(query, limit=limit)


def extract_keywords(text: str) -> List[str]:
    """从文本中提取关键词用于论文搜索

    支持中英文混合文本，中文会映射到常见学术英文词汇。
    """
    keywords = []

    # 1. 提取英文关键词
    english_words = re.findall(r'[a-zA-Z]{4,}', text)
    # 过滤常见停用词
    stopwords = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'will', 'would', 'could', 'should'}
    english_words = [w.lower() for w in english_words if w.lower() not in stopwords]
    keywords.extend(english_words[:5])

    # 2. 中文关键词映射（常见学术领域词汇）
    cn_to_en = {
        # 技术领域
        '深度学习': 'deep learning',
        '机器学习': 'machine learning',
        '人工智能': 'artificial intelligence',
        '神经网络': 'neural network',
        '卷积': 'convolutional',
        '自然语言': 'natural language',
        '计算机视觉': 'computer vision',
        '图像识别': 'image recognition',
        '目标检测': 'object detection',
        '语义分割': 'semantic segmentation',
        '强化学习': 'reinforcement learning',
        '迁移学习': 'transfer learning',
        '注意力机制': 'attention mechanism',
        '大数据': 'big data',
        '云计算': 'cloud computing',
        '区块链': 'blockchain',
        '物联网': 'internet of things',

        # 医学领域
        '医学影像': 'medical imaging',
        '疾病诊断': 'disease diagnosis',
        '临床': 'clinical',
        '病理': 'pathology',
        '基因': 'gene',
        '蛋白质': 'protein',
        '药物': 'drug',
        '癌症': 'cancer',
        '肿瘤': 'tumor',

        # 经济金融
        '金融': 'finance',
        '经济': 'economics',
        '投资': 'investment',
        '风险': 'risk',
        '市场': 'market',
        '股票': 'stock',
        '银行': 'banking',

        # 教育
        '教���': 'education',
        '学习': 'learning',
        '教学': 'teaching',
        '学生': 'student',
        '课程': 'curriculum',

        # 社会科学
        '社会': 'social',
        '心理': 'psychology',
        '行为': 'behavior',
        '文化': 'culture',
        '政策': 'policy',

        # 工程
        '优化': 'optimization',
        '算法': 'algorithm',
        '模型': 'model',
        '系统': 'system',
        '性能': 'performance',
        '效率': 'efficiency',
        '准确率': 'accuracy',
    }

    for cn, en in cn_to_en.items():
        if cn in text:
            keywords.extend(en.split())

    # 去重并限制数量
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    return unique[:8]


def get_paper_expressions(text: str, limit: int = 10) -> List[str]:
    """便捷函数：获取相关论文的优质表达

    Args:
        text: 用户的文本内容
        limit: 返回表达数量

    Returns:
        优质表达片段列表
    """
    papers = search_related_papers(text, limit=5)

    all_expressions = []
    for paper in papers:
        all_expressions.extend(paper.expressions)

    return all_expressions[:limit]
