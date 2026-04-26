"""
db_plagiarism_service_optimized.py — 优化版学术数据库查重服务

性能优化：
1. 并发 API 请求（使用线程池）
2. 本地缓存机制（避免重复查询）
3. 智能句子过滤（跳过短句、通用句）
4. 批量处理优化

预期性能提升：
- 原版：50句 ~150-250秒
- 优化版：50句 ~15-30秒（提升 5-10倍）
"""

import hashlib
import json
import logging
import pickle
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

# ── 缓存配置 ──
CACHE_DIR = Path.home() / ".thesisx" / "plagiarism_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_EXPIRY_DAYS = 7  # 缓存有效期


# ── 数据模型 ──


@dataclass
class SearchMatch:
    """一条来自真实数据库的匹配结果。"""

    source: str = ""
    title: str = ""
    url: str = ""
    score: float = 0.0
    snippet: str = ""
    authors: str = ""
    year: int = 0


@dataclass
class SentenceDbResult:
    """单句的数据库查重结果。"""

    sentence_index: int
    matches: list = field(default_factory=list)
    risk: str = "low"


# ── 缓存机制 ──


def _get_cache_key(sentence: str, source: str) -> str:
    """生成缓存键。"""
    text = f"{source}:{sentence[:200]}"
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _load_from_cache(cache_key: str) -> list | None:
    """从缓存加载结果。"""
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    if not cache_file.exists():
        return None
    try:
        # 检查缓存是否过期
        mtime = cache_file.stat().st_mtime
        if time.time() - mtime > CACHE_EXPIRY_DAYS * 86400:
            cache_file.unlink()
            return None
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        logger.warning(f"缓存加载失败: {e}")
        return None


def _save_to_cache(cache_key: str, results: list):
    """保存结果到缓存。"""
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    try:
        with open(cache_file, "wb") as f:
            pickle.dump(results, f)
    except Exception as e:
        logger.warning(f"缓存保存失败: {e}")


# ── 智能过滤 ──


def _should_skip_sentence(sentence: str) -> bool:
    """判断句子是否应该跳过查重。

    跳过条件：
    1. 太短（<15字符）
    2. 纯数字/符号
    3. 常见模板句（如"本文研究了"）
    """
    text = sentence.strip()

    # 太短
    if len(text) < 15:
        return True

    # 纯数字/符号
    if not any(c.isalpha() or '\u4e00' <= c <= '\u9fff' for c in text):
        return True

    # 常见模板句（可扩展）
    skip_patterns = [
        "本文研究",
        "本文分析",
        "本文探讨",
        "本文介绍",
        "本章",
        "第一章",
        "第二章",
        "摘要",
        "关键词",
        "abstract",
        "keywords",
    ]
    text_lower = text.lower()
    if any(pattern in text_lower for pattern in skip_patterns):
        return True

    return False


# ── API 搜索函数（带缓存） ──

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


def search_semantic_scholar_cached(sentence: str, limit: int = 3) -> list:
    """搜索 Semantic Scholar（带缓存）。"""
    # 检查缓存
    cache_key = _get_cache_key(sentence, "ss")
    cached = _load_from_cache(cache_key)
    if cached is not None:
        logger.debug(f"从缓存加载 Semantic Scholar 结果: {sentence[:30]}...")
        return cached

    # 调用 API
    results = []
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

            # 计算相似度
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
    except Exception as e:
        logger.warning(f"Semantic Scholar 搜索失败: {e}")

    # 保存到缓存
    _save_to_cache(cache_key, results)
    return results


def search_crossref_cached(sentence: str, limit: int = 3) -> list:
    """搜索 CrossRef（带缓存）。"""
    # 检查缓存
    cache_key = _get_cache_key(sentence, "cr")
    cached = _load_from_cache(cache_key)
    if cached is not None:
        logger.debug(f"从缓存加载 CrossRef 结果: {sentence[:30]}...")
        return cached

    # 调用 API
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

            # 清理 HTML 标签
            import re
            abstract = re.sub(r"<[^>]+>", "", abstract)

            # 作者
            authors_list = item.get("author", [])
            authors = ", ".join(
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in (authors_list or [])[:3]
            )
            if len(authors_list or []) > 3:
                authors += " et al."

            # 年份
            pub_date = item.get("published-print", {}) or item.get("published-online", {})
            year = 0
            if pub_date and "date-parts" in pub_date:
                parts = pub_date["date-parts"]
                if parts and parts[0]:
                    year = parts[0][0]

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
    except Exception as e:
        logger.warning(f"CrossRef 搜索失败: {e}")

    # 保存到缓存
    _save_to_cache(cache_key, results)
    return results


# ── 并发搜索单个句子 ──


def _search_sentence_concurrent(sentence_obj, limit: int = 3) -> tuple:
    """并发搜索单个句子（Semantic Scholar + CrossRef）。

    Returns:
        (sentence_index, matches)
    """
    sentence = sentence_obj.text

    # 智能过滤
    if _should_skip_sentence(sentence):
        logger.debug(f"跳过句子 [{sentence_obj.index}]: {sentence[:30]}...")
        return (sentence_obj.index, [])

    matches = []

    # 使用线程池并发调用两个 API
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_ss = executor.submit(search_semantic_scholar_cached, sentence, limit)
        future_cr = executor.submit(search_crossref_cached, sentence, limit)

        # 等待结果
        try:
            ss_results = future_ss.result(timeout=20)
            matches.extend(ss_results)
        except Exception as e:
            logger.warning(f"Semantic Scholar 搜索失败 [{sentence_obj.index}]: {e}")

        try:
            cr_results = future_cr.result(timeout=20)
            matches.extend(cr_results)
        except Exception as e:
            logger.warning(f"CrossRef 搜索失败 [{sentence_obj.index}]: {e}")

    # 限速（Semantic Scholar 要求 1 req/sec）
    time.sleep(0.5)

    return (sentence_obj.index, matches)


# ── 风险评估 ──


def _assess_risk(matches: list) -> str:
    """根据匹配结果评估风险等级。"""
    if not matches:
        return "low"
    max_score = max(m.score for m in matches)
    if max_score >= 0.7:
        return "high"
    elif max_score >= 0.4:
        return "medium"
    else:
        return "low"


# ── 批量并发查重 Worker ──


class DbPlagiarismWorkerOptimized(QThread):
    """优化版：使用线程池并发搜索，大幅提升速度。"""

    progress = pyqtSignal(int, int)  # (已完成, 总数)
    finished_ok = pyqtSignal(list)  # list[SentenceDbResult]
    error_occurred = pyqtSignal(str)

    def __init__(self, sentences: list, max_workers: int = 5, parent=None):
        """
        Args:
            sentences: list[Sentence]
            max_workers: 最大并发线程数（建议 3-5，避免触发 API 限流）
        """
        super().__init__(parent)
        self._sentences = sentences
        self._max_workers = max_workers
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            results = []
            total = len(self._sentences)
            completed = 0

            # 使用线程池并发处理多个句子
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                # 提交所有任务
                future_to_sent = {
                    executor.submit(_search_sentence_concurrent, sent): sent
                    for sent in self._sentences
                }

                # 收集结果
                for future in as_completed(future_to_sent):
                    if self._cancelled:
                        executor.shutdown(wait=False, cancel_futures=True)
                        return

                    try:
                        sent_index, matches = future.result()
                        # 过滤低相似度匹配
                        relevant = [m for m in matches if m.score >= 0.25]
                        risk = _assess_risk(relevant)
                        results.append(
                            SentenceDbResult(
                                sentence_index=sent_index,
                                matches=relevant,
                                risk=risk,
                            )
                        )
                        completed += 1
                        self.progress.emit(completed, total)
                    except Exception as e:
                        logger.warning(f"句子搜索失败: {e}")
                        completed += 1
                        self.progress.emit(completed, total)

            # 按 index 排序
            results.sort(key=lambda r: r.sentence_index)

            if not self._cancelled:
                self.finished_ok.emit(results)
        except Exception as e:
            if not self._cancelled:
                self.error_occurred.emit(f"数据库查重失败: {str(e)}")


# ── 合并结果函数 ──


def merge_results(ai_results: list, db_results: list) -> list:
    """合并 AI 分析结果和数据库搜索结果。

    Args:
        ai_results: list[CheckResult] from AI analysis
        db_results: list[SentenceDbResult] from database search

    Returns:
        list[CheckResult] with merged sources
    """
    from app.core.plagiarism_service import CheckResult

    # 构建 db_results 索引
    db_map = {r.sentence_index: r for r in db_results}

    merged = []
    for ai_r in ai_results:
        db_r = db_map.get(ai_r.index)
        if db_r and db_r.matches:
            # 合并来源
            sources = []
            for m in db_r.matches[:3]:
                sources.append(
                    {
                        "title": m.title,
                        "url": m.url,
                        "source": m.source,
                        "authors": m.authors,
                        "year": m.year,
                        "score": m.score,
                        "snippet": m.snippet,
                    }
                )
            # 提升风险等级（如果数据库发现高相似度）
            if db_r.risk == "high" and ai_r.risk != "high":
                risk = "high"
            elif db_r.risk == "medium" and ai_r.risk == "low":
                risk = "medium"
            else:
                risk = ai_r.risk

            merged.append(
                CheckResult(
                    index=ai_r.index,
                    text=ai_r.text,
                    risk=risk,
                    dup_type=ai_r.dup_type or "数据库匹配",
                    suggestion=ai_r.suggestion,
                    sources=sources,
                )
            )
        else:
            # 只有 AI 结果
            merged.append(ai_r)

    return merged
