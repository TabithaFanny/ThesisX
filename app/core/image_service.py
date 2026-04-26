"""
image_service.py — 图片搜索与占位符替换服务

AI 生成的 Markdown 可能包含以下占位标记：
  · 图片: ![描述](IMAGE_SEARCH:keyword)
  · 图表: [CHART:chart_type]  或  [CHART:chart_type:{...json...}]

本模块负责：
  · 识别这些占位符
  · 根据关键词搜索真实图片 URL（可选 GPT 关键词优化）
  · 将图表占位符替换为动态 SVG 图表 HTML（基于 AI 提供的真实数据）
  · 替换占位符为真实内容
"""

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

# ── 图片占位符：![任意描述](IMAGE_SEARCH:关键词) ──
_IMAGE_PLACEHOLDER_RE = re.compile(r"!\[([^\]]*)\]\(IMAGE_SEARCH:([^)]+)\)")


# ------------------------------------------------------------------
# 图片占位符检测
# ------------------------------------------------------------------


def find_image_placeholders(text: str) -> list:
    """返回所有图片占位符 [(full_match, alt_text, keyword), ...]"""
    return [
        (m.group(0), m.group(1), m.group(2).strip()) for m in _IMAGE_PLACEHOLDER_RE.finditer(text)
    ]


# ------------------------------------------------------------------
# 图表占位符检测（支持新旧两种格式）
#   旧格式: [CHART:bar]
#   新格式: [CHART:bar:{"title":"...","labels":[...],"series":[...]}]
# ------------------------------------------------------------------


def _repair_json(s: str) -> str:
    """修复 AI 常见的 JSON 格式错误（增强版）。"""
    # 去除 BOM / 零宽字符
    s = s.strip().lstrip("\ufeff")
    # 移除单行注释 // ...
    s = re.sub(r"//[^\n]*", "", s)
    # 移除多行注释 /* ... */
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
    # 单引号 → 双引号（仅在非双引号包裹内）
    s = re.sub(r"(?<![\\])'", '"', s)
    # 尾逗号: ,] → ] 和 ,} → }
    s = re.sub(r",\s*([\]\}])", r"\1", s)
    # 修复缺少引号的键名: {key: → {"key":
    s = re.sub(r"([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', s)
    # 修复中文全角引号/冒号
    s = s.replace("\u201c", '"').replace("\u201d", '"')  # “”
    s = s.replace("\uff1a", ":")  # ：
    s = s.replace("\uff0c", ",")  # ，
    # 修复未转义的换行符（JSON 字符串内不允许裸\n）
    s = re.sub(r"(?<!\\)\n", " ", s)
    return s


def _extract_json_range(text: str, start: int) -> int:
    """从 start 位置（必须是 '{'）向后找到匹配的 '}'，正确处理字符串内的花括号。

    返回 '}' 的位置索引，找不到返回 -1。
    """
    depth = 0
    in_str = False
    escape = False
    n = len(text)
    k = start
    while k < n:
        ch = text[k]
        if escape:
            escape = False
            k += 1
            continue
        if ch == "\\":
            escape = True
            k += 1
            continue
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return k
        k += 1
    return -1


def find_chart_placeholders(text: str) -> list:
    """返回所有图表占位符。

    返回: [(full_match, chart_type, config_dict_or_None), ...]
    """
    results = []
    i = 0
    marker = "[CHART:"
    while i < len(text):
        idx = text.find(marker, i)
        if idx == -1:
            break
        # 提取 chart_type
        type_start = idx + len(marker)
        j = type_start
        while j < len(text) and text[j] not in (":", "]"):
            j += 1
        if j >= len(text):
            i = idx + 1
            continue
        chart_type = text[type_start:j]
        if not re.match(r"^[a-z_]+$", chart_type):
            i = idx + 1
            continue

        if text[j] == "]":
            # 旧格式 [CHART:type]
            full = text[idx : j + 1]
            results.append((full, chart_type, None))
            i = j + 1
        elif text[j] == ":":
            # 新格式 [CHART:type:{...JSON...}]
            json_start = j + 1
            if json_start < len(text) and text[json_start] == "{":
                end = _extract_json_range(text, json_start)
                if end >= 0 and end + 1 < len(text) and text[end + 1] == "]":
                    json_str = text[json_start : end + 1]
                    full = text[idx : end + 2]
                    config = None
                    try:
                        config = json.loads(json_str)
                    except json.JSONDecodeError:
                        # 尝试修复后再解析
                        try:
                            config = json.loads(_repair_json(json_str))
                            logger.info("图表 JSON 修复成功: %s", chart_type)
                        except json.JSONDecodeError:
                            logger.warning("图表 JSON 解析失败: %s", json_str[:100])
                    results.append((full, chart_type, config))
                    i = end + 2
                else:
                    i = idx + 1
            else:
                i = idx + 1
        else:
            i = idx + 1
    return results


def has_image_placeholders(text: str) -> bool:
    """文本中是否包含图片或图表占位符。"""
    return bool(_IMAGE_PLACEHOLDER_RE.search(text) or "[CHART:" in text)


# ------------------------------------------------------------------
# 关键词优化（中文→英文简易翻译）
# ------------------------------------------------------------------

# 常用中文关键词→英文映射，覆盖学术/商务常见场景
_ZH_EN_MAP = {
    "科技": "technology",
    "人工智能": "artificial intelligence",
    "机器人": "robot",
    "电脑": "computer",
    "网络": "network",
    "数据": "data",
    "云计算": "cloud computing",
    "编程": "programming",
    "软件": "software",
    "硬件": "hardware",
    "教育": "education",
    "学校": "school",
    "大学": "university",
    "学生": "student",
    "老师": "teacher",
    "课堂": "classroom",
    "图书馆": "library",
    "医疗": "medical",
    "医院": "hospital",
    "医生": "doctor",
    "健康": "health",
    "商业": "business",
    "办公": "office",
    "会议": "meeting",
    "团队": "teamwork",
    "金融": "finance",
    "银行": "bank",
    "股票": "stock market",
    "经济": "economy",
    "自然": "nature",
    "森林": "forest",
    "海洋": "ocean",
    "山脉": "mountain",
    "城市": "city",
    "建筑": "architecture",
    "交通": "transportation",
    "环保": "environment",
    "能源": "energy",
    "太阳能": "solar energy",
    "农业": "agriculture",
    "食品": "food",
    "工业": "industry",
    "制造": "manufacturing",
    "体育": "sports",
    "运动": "exercise",
    "足球": "football",
    "篮球": "basketball",
    "艺术": "art",
    "音乐": "music",
    "电影": "movie",
    "设计": "design",
    "旅游": "travel",
    "风景": "landscape",
    "文化": "culture",
    "家庭": "family",
    "儿童": "children",
    "动物": "animal",
    "植物": "plant",
    "航天": "aerospace",
    "宇宙": "space universe",
    "星球": "planet",
    "图表": "chart graph",
    "分析": "analysis",
    "研究": "research",
    "实验": "experiment",
    "化学": "chemistry",
    "物理": "physics",
    "生物": "biology",
    "数学": "mathematics",
    "统计": "statistics",
    "论文": "paper academic",
}


def _translate_keyword(keyword: str) -> str:
    """将中文关键词转换为英文，若已是英文则保持不变。"""
    keyword = keyword.strip()
    if not keyword:
        return keyword

    # 如果全是 ASCII 字符，认为已是英文
    if all(ord(c) < 128 for c in keyword):
        return keyword

    # 精确匹配：查找整个关键词
    lower = keyword.lower()
    if lower in _ZH_EN_MAP:
        return _ZH_EN_MAP[lower]

    # 逻辑拆分：将每个中文词组分别翻译
    parts = []
    for word in keyword.split():
        found = _ZH_EN_MAP.get(word)
        if found:
            parts.append(found)
        else:
            # 尝试拆分较长的中文短语
            matched = False
            for zh, en in sorted(_ZH_EN_MAP.items(), key=lambda x: -len(x[0])):
                if zh in word:
                    parts.append(en)
                    matched = True
                    break
            if not matched:
                parts.append(word)

    return " ".join(parts) if parts else keyword


# ------------------------------------------------------------------
# 真实图片搜索（多源策略）
# ------------------------------------------------------------------


def _search_pixabay(keyword: str, api_key: str) -> str | None:
    """通过 Pixabay API 搜索真实图片，返回图片 URL。"""
    try:
        en_keyword = _translate_keyword(keyword)
        encoded = urllib.parse.quote(en_keyword)
        url = (
            f"https://pixabay.com/api/?key={api_key}"
            f"&q={encoded}&image_type=photo&per_page=5&safesearch=true&lang=en"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "WenBiaoApp/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            hits = data.get("hits", [])
            if hits:
                # 优先使用 webformat（中等尺寸，加载快）
                return hits[0].get("webformatURL") or hits[0].get("largeImageURL")
    except Exception as e:
        logger.debug("Pixabay 搜索失败 (%s): %s", keyword, e)
    return None


def _search_openverse(keyword: str) -> str | None:
    """通过 OpenVerse API 搜索 CC0 真实图片（无需 API key）。

    openverse.org 是 WordPress 基金会支持的开放图片搜索引擎，
    收录数亿张 CC0/CC-BY 授权真实照片，按关键词相关度排序。
    """
    try:
        en_keyword = _translate_keyword(keyword)
        encoded = urllib.parse.quote(en_keyword)
        url = f"https://api.openverse.org/v1/images/" f"?q={encoded}&page_size=5&license_type=all"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "WenBiaoApp/2.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results:
                # 优先取有 thumbnail 的结果，图片尺寸适中
                for item in results:
                    img_url = item.get("url") or item.get("thumbnail")
                    if img_url and img_url.startswith("http"):
                        return img_url
    except Exception as e:
        logger.debug("OpenVerse 搜索失败 (%s): %s", keyword, e)
    return None


def _search_wikimedia(keyword: str) -> str | None:
    """通过 Wikimedia Commons API 搜索真实图片（无需 API key）。

    Wikimedia Commons 收录数千万张高质量真实照片，
    均为自由授权，与学术/百科类搜索关键词匹配度高。
    """
    try:
        en_keyword = _translate_keyword(keyword)
        encoded = urllib.parse.quote(en_keyword)
        # 搜索 File: 命名空间（图片文件）
        url = (
            "https://commons.wikimedia.org/w/api.php"
            f"?action=query&generator=search&gsrsearch={encoded}"
            "&gsrnamespace=6&prop=imageinfo&iiprop=url"
            "&format=json&gsrlimit=8"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "WenBiaoApp/2.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                infos = page.get("imageinfo", [])
                if not infos:
                    continue
                img_url = infos[0].get("url", "")
                # 只接受常见图片格式，排除 SVG/OGG 等
                if img_url and any(
                    img_url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")
                ):
                    return img_url
    except Exception as e:
        logger.debug("Wikimedia 搜索失败 (%s): %s", keyword, e)
    return None


# ------------------------------------------------------------------
# GPT 关键词优化（调用同一 AI API）
# ------------------------------------------------------------------


def _optimize_keyword_via_ai(keyword: str) -> str | None:
    """调用 GPT 将中文/模糊关键词转为精准英文图片搜索词。

    返回优化后的英文关键词（2-4 词），失败返回 None。
    """
    try:
        from app.core.ai_service import AI_API_URL, AI_MODEL, _get_ai_api_key
    except ImportError:
        return None

    api_key = _get_ai_api_key()
    if not api_key:
        return None

    prompt = "将关键词转为2-4个英文图库搜索词。只返回英文单词,无解释,优先具体可视化名词。"
    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": keyword},
        ],
        "stream": False,
        "temperature": 0.3,
        "max_tokens": 30,
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            AI_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"].strip()
            # 清理可能的引号或多余字符
            content = content.strip("\"' \n")
            if content and len(content) < 60:
                logger.info("GPT 关键词优化: %s → %s", keyword, content)
                return content
    except Exception as e:
        logger.debug("GPT 关键词优化失败 (%s): %s", keyword, e)
    return None


# ------------------------------------------------------------------
# URL 可达性验证
# ------------------------------------------------------------------

# 已知可靠的图片域名，跳过 Content-Type 检查，直接信任
_TRUSTED_IMAGE_DOMAINS = (
    "upload.wikimedia.org",
    "pixabay.com",
    "cdn.pixabay.com",
    "openverse.org",
    "live.staticflickr.com",
    "images.openverse.engineering",
)


def _validate_image_url(url: str) -> bool:
    """验证图片 URL 是否可访问（HTTP 2xx 即视为有效）。

    对已知可靠域名直接信任；其他 URL 做 HEAD 检查。
    Content-Type 不严格限制，因为部分 CDN 返回 octet-stream。
    """
    if not url or not url.startswith("http"):
        return False
    # 已知可信域名直接通过
    from urllib.parse import urlparse

    host = urlparse(url).netloc
    if any(host.endswith(d) for d in _TRUSTED_IMAGE_DOMAINS):
        return True
    try:
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "WenBiaoApp/2.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            # 只要 HTTP 2xx 就认为可访问，不强制要求 image Content-Type
            return 200 <= resp.status < 300
    except Exception:
        return False


def _search_image_url(
    keyword: str,
    pixabay_key: str = "",
    use_ai_optimize: bool = False,
) -> str:
    """根据关键词返回真实图片 URL（并行多源搜索 + 可选 GPT 关键词优化）。

    并行搜索所有图源，取第一个成功结果，大幅减少等待时间。
    优先级：Pixabay > OpenVerse > Wikimedia > Picsum 兆底。
    """
    # 0) GPT 优化关键词（仅当明确开启时）
    search_keyword = keyword
    if use_ai_optimize:
        optimized = _optimize_keyword_via_ai(keyword)
        if optimized:
            search_keyword = optimized
            logger.debug("关键词优化: %r → %r", keyword, search_keyword)

    # 并行搜索所有图源，以 (priority, url) 收集结果
    results: dict[str, str | None] = {}  # source_name -> url

    def _try_pixabay():
        if not pixabay_key:
            return None
        url = _search_pixabay(search_keyword, pixabay_key)
        return url if url and _validate_image_url(url) else None

    def _try_openverse():
        url = _search_openverse(search_keyword)
        return url if url and _validate_image_url(url) else None

    def _try_wikimedia():
        url = _search_wikimedia(search_keyword)
        return url if url and _validate_image_url(url) else None

    # 优先级：Pixabay(0) > OpenVerse(1) > Wikimedia(2)
    tasks = [
        ("Pixabay", 0, _try_pixabay),
        ("OpenVerse", 1, _try_openverse),
        ("Wikimedia", 2, _try_wikimedia),
    ]

    best_url = None
    best_priority = 999

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn): (name, prio) for name, prio, fn in tasks}
        for future in as_completed(futures):
            name, prio = futures[future]
            try:
                url = future.result()
                if url and prio < best_priority:
                    best_url = url
                    best_priority = prio
                    logger.info("图片来源 %s: %s", name, url)
                    # 已拿到最高优先级，取消其他
                    if prio == 0:
                        break
            except Exception as e:
                logger.debug("%s 搜索异常: %s", name, e)

    if best_url:
        return best_url

    # 并行全失败 + 有 AI 优化过 → 用原始关键词再尝试一轮
    if use_ai_optimize and search_keyword != keyword:
        fallback_kw = _translate_keyword(keyword)
        for fn in (_search_openverse, _search_wikimedia):
            url = fn(fallback_kw)
            if url and _validate_image_url(url):
                logger.info("图片来源 fallback: %s", url)
                return url

    # Picsum 兆底（语义 seed 保证可访问）
    en_kw = _translate_keyword(keyword)
    seed = abs(hash(en_kw)) % 10000
    logger.info("图片兆底 Picsum seed=%s: %s", seed, keyword)
    return f"https://picsum.photos/seed/{seed}/800/500"


# ------------------------------------------------------------------
# 图表占位符处理
# ------------------------------------------------------------------


def _make_chart_fallback_html(chart_type: str, title: str = "") -> str:
    """生成一个通用图表占位 SVG（当动态生成和默认模板均失败时使用）。"""
    display_title = title or f"{chart_type} 图表"
    import html as _h

    return (
        '<div class="chart-container" style="text-align:center;margin:16px 0;">'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 200" '
        'style="max-width:480px;width:100%;height:auto;">'
        '<rect x="0" y="0" width="500" height="200" rx="8" fill="#FAFBFC" '
        'stroke="#E2E8F0" stroke-width="1"/>'
        f'<text x="250" y="80" text-anchor="middle" font-size="16" '
        f'font-weight="bold" fill="#94A3B8" '
        f'font-family="Microsoft YaHei,sans-serif">{_h.escape(display_title)}</text>'
        '<text x="250" y="120" text-anchor="middle" font-size="13" '
        'fill="#CBD5E1" font-family="Microsoft YaHei,sans-serif">'
        "暂无数据 — 请点击编辑图表数据</text>"
        "</svg></div>"
    )


def _get_chart_html(chart_type: str, ai_config: dict | None = None) -> str:
    """根据图表类型和可选的 AI 配置生成图表 HTML。

    优先级：
    1. AI 提供了 config → 使用 chart_generator 动态生成真实数据图表
    2. 无 config → 回退到 chart_dialog 的默认模板
    3. 全部失败 → 生成占位图表（永不返回 None）
    """
    title = (ai_config or {}).get("title", "")

    # 1) 有 AI config 时，动态生成
    if ai_config:
        try:
            from app.core.chart_generator import generate_chart_html
            from app.ui.chart_dialog import wrap_chart_with_config

            dynamic_html = generate_chart_html(chart_type, ai_config)
            if dynamic_html:
                return wrap_chart_with_config(chart_type, dynamic_html, ai_config)
        except Exception as e:
            logger.warning("动态图表生成失败 (%s): %s", chart_type, e)

    # 2) 回退到默认模板
    try:
        from app.ui.chart_dialog import _CHART_DEFS, wrap_chart_with_config

        for chart_def in _CHART_DEFS:
            if chart_def["key"] == chart_type:
                raw_html = chart_def["html_func"]()
                cfg = chart_def.get("default_config", {})
                return wrap_chart_with_config(chart_type, raw_html, cfg)
    except Exception as e:
        logger.warning("获取默认图表 HTML 失败 (%s): %s", chart_type, e)

    # 3) 兆底占位图（永不返回 None，确保图表占位符不会被保留在文档中）
    logger.warning("图表类型 %s 无法生成，使用占位图", chart_type)
    return _make_chart_fallback_html(chart_type, title)


def process_chart_placeholders(text: str) -> str:
    """处理文本中的图表占位符，替换为 SVG 图表 HTML。

    支持新格式 [CHART:type:{json}] 和旧格式 [CHART:type]。
    """
    placeholders = find_chart_placeholders(text)
    if not placeholders:
        return text
    result = text
    for item in placeholders:
        full_match, chart_type = item[0], item[1]
        ai_config = item[2] if len(item) > 2 else None
        chart_html = _get_chart_html(chart_type, ai_config)
        result = result.replace(full_match, chart_html, 1)
        src = "AI数据" if ai_config else "默认模板"
        logger.info("图表占位符替换 (%s): [CHART:%s]", src, chart_type)
    return result


# ------------------------------------------------------------------
# 统一处理入口
# ------------------------------------------------------------------


def process_image_placeholders(
    text: str,
    pixabay_key: str = "",
    use_ai_optimize: bool = False,
) -> str:
    """同步处理文本中的所有图片和图表占位符（多图并行搜索）。"""
    result = text

    # 先处理图表占位符（同步，无网络请求）
    result = process_chart_placeholders(result)

    # 再处理图片占位符（多图并行搜索）
    img_placeholders = find_image_placeholders(result)
    if not img_placeholders:
        return result

    def _resolve_one(item):
        full_match, alt_text, keyword = item
        try:
            real_url = _search_image_url(
                keyword,
                pixabay_key,
                use_ai_optimize=use_ai_optimize,
            )
            return full_match, f"![{alt_text}]({real_url})"
        except Exception as e:
            logger.warning("图片搜索失败 (%s): %s", keyword, e)
            seed = abs(hash(keyword)) % 10000
            return full_match, f"![{alt_text}](https://picsum.photos/seed/{seed}/800/500)"

    # 多图并行搜索
    with ThreadPoolExecutor(max_workers=min(len(img_placeholders), 4)) as pool:
        futures = [pool.submit(_resolve_one, p) for p in img_placeholders]
        for future in as_completed(futures):
            try:
                full_match, replacement = future.result()
                result = result.replace(full_match, replacement, 1)
                logger.info("图片占位符替换完成: %s", replacement[:80])
            except Exception as e:
                logger.warning("图片并行处理异常: %s", e)
    return result


class ImageProcessWorker(QThread):
    """后台线程：处理 Markdown 文本中的图片和图表占位符。"""

    finished = pyqtSignal(str)  # 替换完成后的完整 Markdown
    error = pyqtSignal(str)

    def __init__(
        self,
        markdown_text: str,
        pixabay_key: str = "",
        use_ai_optimize: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._text = markdown_text
        self._pixabay_key = pixabay_key
        self._use_ai_optimize = use_ai_optimize

    def run(self):
        try:
            result = process_image_placeholders(
                self._text,
                self._pixabay_key,
                use_ai_optimize=self._use_ai_optimize,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("图片/图表处理失败")
            self.error.emit(str(e))
