"""
db_plagiarism_service.py — 真实学术数据库查重服务

通过 Semantic Scholar 和 CrossRef API 搜索句子，返回匹配论文：
  · Semantic Scholar：~2 亿篇论文，语义搜索
  · CrossRef：~1.5 亿条 DOI，文本匹配

所有 HTTP 调用用 urllib（与 ai_service.py 一致），不引入新依赖。
"""

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

# ── 数据模型 ──


@dataclass
class SearchMatch:
    """一条来自真实数据库的匹配结果。"""

    source: str = ""  # 来源数据库名 (Semantic Scholar / CrossRef)
    title: str = ""  # 论文标题
    url: str = ""  # 论文链接
    score: float = 0.0  # 文本相似度 0-1
    snippet: str = ""  # 匹配摘要片段
    authors: str = ""  # 作者
    year: int = 0  # 发表年份


@dataclass
class SentenceDbResult:
    """单句的数据库查重结果。"""

    sentence_index: int
    matches: list = field(default_factory=list)  # list[SearchMatch]
    risk: str = "low"  # 由匹配情况推算


# ── API 搜索函数 ──

_HEADERS = {
    "User-Agent": "ThesisX/1.0 (academic-writing-tool; mailto:support@thesisx.app)",
}

_SS_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
_CR_BASE = "https://api.crossref.org/works"


def _text_similarity(a: str, b: str) -> float:
    """计算两段文本的相似度 (0-1)。"""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def search_semantic_scholar(sentence: str, limit: int = 3) -> list:
    """搜索 Semantic Scholar，返回 SearchMatch 列表。"""
    results = []
    # 截取关键部分作为查询（太长的句子截断）
    query = sentence[:200].strip()
    if len(query) < 10:
        return results
    try:
        params = urllib.parse.urlencode(
            {
                "query": query,
                "limit": limit,
                "fields": "title,abstract,url,year,authors",
            }
        )
        url = f"{_SS_BASE}?{params}"
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for paper in data.get("data", []):
            title = paper.get("title", "")
            abstract = paper.get("abstract", "") or ""
            paper_url = paper.get("url", "")
            year = paper.get("year") or 0
            authors_list = paper.get("authors", [])
            authors = ", ".join(a.get("name", "") for a in (authors_list or [])[:3])
            if len(authors_list or []) > 3:
                authors += " et al."
            # 计算相似度：与标题 + 摘要比较
            sim_title = _text_similarity(sentence, title)
            sim_abstract = _text_similarity(sentence, abstract[:500])
            score = max(sim_title, sim_abstract * 0.8)
            snippet = abstract[:150] + "..." if len(abstract) > 150 else abstract
            results.append(
                SearchMatch(
                    source="Semantic Scholar",
                    title=title,
                    url=paper_url,
                    score=round(score, 3),
                    snippet=snippet,
                    authors=authors,
                    year=year,
                )
            )
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception) as e:
        logger.warning("Semantic Scholar 搜索失败: %s", e)
    return results


def search_crossref(sentence: str, limit: int = 3) -> list:
    """搜索 CrossRef，返回 SearchMatch 列表。"""
    results = []
    query = sentence[:200].strip()
    if len(query) < 10:
        return results
    try:
        params = urllib.parse.urlencode(
            {
                "query": query,
                "rows": limit,
                "select": "DOI,title,author,published-print,abstract,URL",
            }
        )
        url = f"{_CR_BASE}?{params}"
        req = urllib.request.Request(
            url,
            headers={
                **_HEADERS,
                "User-Agent": "ThesisX/1.0 (mailto:support@thesisx.app)",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for item in data.get("message", {}).get("items", []):
            titles = item.get("title", [])
            title = titles[0] if titles else ""
            doi = item.get("DOI", "")
            paper_url = item.get("URL", "") or (f"https://doi.org/{doi}" if doi else "")
            abstract = item.get("abstract", "") or ""
            # 清理 abstract 中的 HTML 标签
            import re

            abstract = re.sub(r"<[^>]+>", "", abstract)
            # 作者
            authors_list = item.get("author", [])
            authors = ", ".join(
                f"{a.get('family', '')} {a.get('given', '')}".strip()
                for a in (authors_list or [])[:3]
            )
            if len(authors_list or []) > 3:
                authors += " et al."
            # 年份
            pub = item.get("published-print", {}) or item.get("published-online", {}) or {}
            parts = pub.get("date-parts", [[]])
            year = parts[0][0] if parts and parts[0] else 0
            # 相似度
            sim_title = _text_similarity(sentence, title)
            sim_abstract = _text_similarity(sentence, abstract[:500])
            score = max(sim_title, sim_abstract * 0.8)
            snippet = abstract[:150] + "..." if len(abstract) > 150 else abstract
            results.append(
                SearchMatch(
                    source="CrossRef",
                    title=title,
                    url=paper_url,
                    score=round(score, 3),
                    snippet=snippet,
                    authors=authors,
                    year=year,
                )
            )
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception) as e:
        logger.warning("CrossRef 搜索失败: %s", e)
    return results


def _assess_risk(matches: list) -> str:
    """根据匹配结果评估风险等级。"""
    if not matches:
        return "low"
    best = max(m.score for m in matches)
    high_count = sum(1 for m in matches if m.score >= 0.5)
    if best >= 0.6 or high_count >= 2:
        return "high"
    if best >= 0.4 or high_count >= 1:
        return "medium"
    return "low"


# ── 批量搜索 Worker ──


class DbPlagiarismWorker(QThread):
    """在后台线程中批量搜索数据库，逐句报告进度。"""

    progress = pyqtSignal(int, int)  # (已完成, 总数)
    finished_ok = pyqtSignal(list)  # list[SentenceDbResult]
    error_occurred = pyqtSignal(str)

    def __init__(self, sentences: list, parent=None):
        """sentences: list[Sentence] (from plagiarism_service.split_sentences)."""
        super().__init__(parent)
        self._sentences = sentences
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            results = []
            total = len(self._sentences)
            for i, sent in enumerate(self._sentences):
                if self._cancelled:
                    return
                # 搜索两个数据库
                matches = []
                ss = search_semantic_scholar(sent.text, limit=3)
                matches.extend(ss)
                # 限速：Semantic Scholar 要求 1 req/sec
                time.sleep(0.3)
                cr = search_crossref(sent.text, limit=3)
                matches.extend(cr)
                time.sleep(0.3)
                # 只保留有一定相似度的匹配
                relevant = [m for m in matches if m.score >= 0.25]
                risk = _assess_risk(relevant)
                results.append(
                    SentenceDbResult(
                        sentence_index=sent.index,
                        matches=relevant,
                        risk=risk,
                    )
                )
                self.progress.emit(i + 1, total)

            if not self._cancelled:
                self.finished_ok.emit(results)
        except Exception as e:
            if not self._cancelled:
                self.error_occurred.emit(f"数据库查重失败: {str(e)}")
