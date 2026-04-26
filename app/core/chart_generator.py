"""图表生成器 - 动态 SVG 图表生成

根据 AI 提供的配置（title, labels, series）动态计算坐标并生成内联 SVG HTML。

支持的图表类型：
- bar: 柱状图
- grouped: 分组柱状图
- stacked: 堆叠柱状图
- line: 折线图
- area: 面积图
- pie: 饼图
- donut: 环形图
- scatter: 散点图
- bubble: 气泡图
- radar: 雷达图
- funnel: 漏斗图
- gauge: 仪表盘
- waterfall: 瀑布图
- progress: 进度条
- heatmap: 热力图
- gantt: 甘特图
- boxplot: 箱线图
- dual_axis: 双轴图
- diverging: 发散图
- treemap: 树状图

配置格式：
    {
        "title": "图表标题",
        "labels": ["A", "B", ...],
        "series": [{"name": "系列名", "values": [1, 2, ...]}],
        // 部分图表有额外字段如 centerText, max, unit 等
    }

Example:
    >>> config = {
    ...     "title": "销售数据",
    ...     "labels": ["Q1", "Q2", "Q3", "Q4"],
    ...     "series": [{"name": "2023", "values": [100, 120, 150, 180]}]
    ... }
    >>> html = generate_chart_html("bar", config)
"""

import html as _html_mod
import json as _json
import logging
import math

logger = logging.getLogger(__name__)

# ============================================================================
# 公共常量
# ============================================================================

# 图表颜色方案
CHART_COLORS = ["#4A90D9", "#27AE60", "#F39C12", "#E74C3C", "#9B59B6", "#1ABC9C"]

# 默认图表尺寸
CHART_WIDTH = 500
CHART_HEIGHT = 300

# 默认字体样式
DEFAULT_FONT_STYLE = 'font-family="Microsoft YaHei,sans-serif"'


# ====================================================================
# 入口
# ====================================================================


def _no_data_placeholder(title: str) -> str:
    """生成“暂无数据”占位 SVG，用于数据缺失时替代返回 None。"""
    return (
        _head(title) + f'<text x="{CHART_WIDTH/2}" y="{CHART_HEIGHT/2}" text-anchor="middle" '
        f'font-size="14" fill="#94A3B8" {DEFAULT_FONT_STYLE}>暂无数据</text>\n'
        + f'<text x="{CHART_WIDTH/2}" y="{CHART_HEIGHT/2 + 24}" text-anchor="middle" '
        f'font-size="12" fill="#CBD5E1" {DEFAULT_FONT_STYLE}>请点击编辑图表数据</text>\n' + _TAIL
    )


def generate_chart_html(chart_type: str, config: dict) -> str | None:
    """根据 chart_type 和 config 动态生成图表 HTML（含 chart-container div）。

    返回 None 表示该类型暂不支持动态生成。
    """
    func = _GENERATORS.get(chart_type)
    if func is None:
        return None

    # 基本 config 校验：确保有可用数据
    if not isinstance(config, dict):
        return _no_data_placeholder(chart_type)

    try:
        result = func(config)
        # 如果生成器返回 None（数据不足），用占位图替代
        if result is None:
            title = config.get("title", chart_type)
            return _no_data_placeholder(title)
        return result
    except Exception as e:
        logger.warning("动态生成图表失败 (%s): %s", chart_type, e)
        title = config.get("title", chart_type) if isinstance(config, dict) else chart_type
        return _no_data_placeholder(title)


# ====================================================================
# 辅助
# ====================================================================


def _esc(text: str) -> str:
    """XML 转义。"""
    return _html_mod.escape(str(text), quote=True)


def _head(title: str) -> str:
    return (
        f'<div class="chart-container" style="text-align:center;margin:16px 0;'
        f'page-break-inside:avoid;">\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CHART_WIDTH} {CHART_HEIGHT}" '
        f'style="max-width:480px;width:100%;height:auto;">\n'
        f'<rect x="0" y="0" width="{CHART_WIDTH}" height="{CHART_HEIGHT}" rx="8" fill="#FAFBFC" '
        f'stroke="#E2E8F0" stroke-width="1"/>\n'
        f'<text x="{CHART_WIDTH/2}" y="28" text-anchor="middle" font-size="16" '
        f'font-weight="bold" fill="#1E293B" {DEFAULT_FONT_STYLE}>{_esc(title)}</text>\n'
    )


def _head_custom(title: str, vb_w: int, vb_h: int) -> str:
    return (
        f'<div class="chart-container" style="text-align:center;margin:16px 0;'
        f'page-break-inside:avoid;">\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vb_w} {vb_h}" '
        f'style="max-width:480px;width:100%;height:auto;">\n'
        f'<rect x="0" y="0" width="{vb_w}" height="{vb_h}" rx="8" fill="#FAFBFC" '
        f'stroke="#E2E8F0" stroke-width="1"/>\n'
        f'<text x="{vb_w/2}" y="28" text-anchor="middle" font-size="16" '
        f'font-weight="bold" fill="#1E293B" {DEFAULT_FONT_STYLE}>{_esc(title)}</text>\n'
    )


_TAIL = "</svg>\n</div>"


def _axes(left, top, right, bottom) -> str:
    return (
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" '
        f'stroke="#CBD5E1" stroke-width="1"/>\n'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" '
        f'stroke="#CBD5E1" stroke-width="1"/>\n'
    )


def _y_labels(left, top, bottom, max_val, steps=4, right=470) -> str:
    parts = []
    chart_h = bottom - top
    for i in range(steps + 1):
        y = bottom - (chart_h * i / steps)
        v = max_val * i / steps
        label = str(int(v)) if v == int(v) else f"{v:.1f}"
        parts.append(
            f'<text x="{left - 5}" y="{y + 4}" text-anchor="end" '
            f'font-size="10" fill="#94A3B8">{label}</text>'
        )
        if i > 0:
            parts.append(
                f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" '
                f'stroke="#F1F5F9" stroke-width="0.5"/>'
            )
    return "\n".join(parts) + "\n"


def _safe_max(values, fallback=1):
    m = max(values) if values else fallback
    return m if m > 0 else fallback


# ====================================================================
# 柱状图 (bar)
# ====================================================================


def _gen_bar(cfg: dict) -> str:
    title = cfg.get("title", "柱状图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [{}])
    values = series[0].get("values", []) if series else []
    if not values:
        return None
    n = len(values)
    left, top, right, bottom = 60, 45, 470, 260
    chart_h = bottom - top
    chart_w = right - left
    max_v = _safe_max(values)
    bar_w = chart_w / (n * 1.5 + 0.5)
    gap = bar_w * 0.5

    s = _head(title) + _axes(left, top, right, bottom)
    s += _y_labels(left, top, bottom, max_v)
    for i, v in enumerate(values):
        x = left + gap + i * (bar_w + gap)
        h = (v / max_v) * chart_h
        y = bottom - h
        c = CHART_COLORS[i % len(CHART_COLORS)]
        s += (
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" rx="3" fill="{c}"/>\n'
        )
        if i < len(labels):
            s += (
                f'<text x="{x + bar_w/2:.1f}" y="{bottom + 18}" '
                f'text-anchor="middle" font-size="11" fill="#64748B" '
                f"{DEFAULT_FONT_STYLE}>{_esc(labels[i])}</text>\n"
            )
        s += (
            f'<text x="{x + bar_w/2:.1f}" y="{y - 5:.1f}" '
            f'text-anchor="middle" font-size="11" font-weight="bold" '
            f'fill="{c}">{v}</text>\n'
        )
    s += _TAIL
    return s


# ====================================================================
# 分组柱状图 (grouped)
# ====================================================================


def _gen_grouped(cfg: dict) -> str:
    title = cfg.get("title", "分组柱状图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [])
    if not series or not labels:
        return None
    n_groups = len(labels)
    n_series = len(series)
    left, top, right, bottom = 60, 45, 470, 260
    chart_h = bottom - top
    chart_w = right - left
    all_vals = [v for s in series for v in s.get("values", [])]
    max_v = _safe_max(all_vals)
    group_w = chart_w / (n_groups + 0.5)
    bar_w = group_w / (n_series + 1)

    s = _head(title) + _axes(left, top, right, bottom)
    s += _y_labels(left, top, bottom, max_v)
    for g in range(n_groups):
        gx = left + (g + 0.5) * group_w
        if g < len(labels):
            s += (
                f'<text x="{gx + group_w/2 - bar_w/2:.1f}" y="{bottom + 18}" '
                f'text-anchor="middle" font-size="11" fill="#64748B" '
                f"{DEFAULT_FONT_STYLE}>{_esc(labels[g])}</text>\n"
            )
        for si, ser in enumerate(series):
            vals = ser.get("values", [])
            v = vals[g] if g < len(vals) else 0
            x = gx + si * bar_w
            h = (v / max_v) * chart_h
            y = bottom - h
            c = CHART_COLORS[si % len(CHART_COLORS)]
            s += (
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w * 0.85:.1f}" '
                f'height="{h:.1f}" rx="2" fill="{c}"/>\n'
            )
    # 图例 — 动态定位避免溢出
    legend_w = min(70, (CHART_WIDTH - left) // max(n_series, 1))
    legend_start = max(left, CHART_WIDTH - n_series * legend_w)
    for si, ser in enumerate(series):
        lx = legend_start + si * legend_w
        c = CHART_COLORS[si % len(CHART_COLORS)]
        name = ser.get("name", f"系列{si+1}")
        s += (
            f'<circle cx="{lx}" cy="46" r="5" fill="{c}"/>'
            f'<text x="{lx+10}" y="50" font-size="10" fill="#334155">'
            f"{_esc(name)}</text>\n"
        )
    s += _TAIL
    return s


# ====================================================================
# 堆叠柱状图 (stacked)
# ====================================================================


def _gen_stacked(cfg: dict) -> str:
    title = cfg.get("title", "堆叠柱状图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [])
    if not series or not labels:
        return None
    n = len(labels)
    n_series = len(series)
    left, top, right, bottom = 60, 45, 470, 260
    chart_h = bottom - top
    chart_w = right - left
    # 每组总高
    totals = []
    for g in range(n):
        t = sum(s.get("values", [0])[g] if g < len(s.get("values", [])) else 0 for s in series)
        totals.append(t)
    max_v = _safe_max(totals)
    bar_w = chart_w / (n * 1.6 + 0.6)
    gap = bar_w * 0.6

    s = _head(title) + _axes(left, top, right, bottom)
    s += _y_labels(left, top, bottom, max_v)
    for g in range(n):
        x = left + gap + g * (bar_w + gap)
        cum_h = 0
        # 从第一个系列画起（底部），与 JS 渲染器一致
        for si in range(n_series):
            vals = series[si].get("values", [])
            v = vals[g] if g < len(vals) else 0
            h = (v / max_v) * chart_h
            y = bottom - cum_h - h
            c = CHART_COLORS[si % len(CHART_COLORS)]
            s += (
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
                f'height="{h:.1f}" rx="2" fill="{c}"/>\n'
            )
            cum_h += h
        if g < len(labels):
            s += (
                f'<text x="{x + bar_w/2:.1f}" y="{bottom + 18}" '
                f'text-anchor="middle" font-size="12" fill="#64748B" '
                f"{DEFAULT_FONT_STYLE}>{_esc(labels[g])}</text>\n"
            )
    # 图例 — 动态定位避免溢出
    legend_w = min(65, (CHART_WIDTH - left) // max(n_series, 1))
    legend_start = max(left, CHART_WIDTH - n_series * legend_w)
    for si, ser in enumerate(series):
        lx = legend_start + si * legend_w
        c = CHART_COLORS[si % len(CHART_COLORS)]
        name = ser.get("name", f"系列{si+1}")
        s += (
            f'<circle cx="{lx}" cy="46" r="5" fill="{c}"/>'
            f'<text x="{lx+10}" y="50" font-size="10" fill="#334155">'
            f"{_esc(name)}</text>\n"
        )
    s += _TAIL
    return s


# ====================================================================
# 条形图 (h_bar)
# ====================================================================


def _gen_h_bar(cfg: dict) -> str:
    title = cfg.get("title", "条形图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [{}])
    values = series[0].get("values", []) if series else []
    if not values:
        return None
    n = len(values)
    label_x = 100
    left, top, right, bottom = label_x, 50, 470, 265
    chart_w = right - left
    max_v = _safe_max(values)
    bar_h = min(30, (bottom - top) / (n * 1.3))
    gap = bar_h * 0.4

    s = _head(title)
    s += (
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" '
        f'stroke="#CBD5E1" stroke-width="1"/>\n'
    )
    s += (
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" '
        f'stroke="#CBD5E1" stroke-width="1"/>\n'
    )
    for i, v in enumerate(values):
        y = top + gap + i * (bar_h + gap)
        w = (v / max_v) * chart_w
        c = CHART_COLORS[i % len(CHART_COLORS)]
        if i < len(labels):
            s += (
                f'<text x="{left - 10}" y="{y + bar_h/2 + 4:.1f}" '
                f'text-anchor="end" font-size="12" fill="#334155" '
                f"{DEFAULT_FONT_STYLE}>{_esc(labels[i])}</text>\n"
            )
        s += (
            f'<rect x="{left}" y="{y:.1f}" width="{w:.1f}" '
            f'height="{bar_h:.1f}" rx="3" fill="{c}"/>\n'
        )
        s += (
            f'<text x="{left + w + 8:.1f}" y="{y + bar_h/2 + 4:.1f}" '
            f'font-size="12" font-weight="bold" fill="{c}">{v}</text>\n'
        )
    s += _TAIL
    return s


# ====================================================================
# 折线图 (line)
# ====================================================================


def _gen_line(cfg: dict) -> str:
    title = cfg.get("title", "折线图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [])
    if not series:
        return None
    left, top, right, bottom = 60, 45, 470, 260
    chart_h = bottom - top
    chart_w = right - left
    all_vals = [v for ser in series for v in ser.get("values", [])]
    max_v = _safe_max(all_vals)
    n_pts = max(len(ser.get("values", [])) for ser in series)
    if n_pts < 2:
        return None
    step = chart_w / (n_pts - 1) if n_pts > 1 else chart_w

    s = _head(title) + _axes(left, top, right, bottom)
    s += _y_labels(left, top, bottom, max_v)
    for si, ser in enumerate(series):
        vals = ser.get("values", [])
        pts = []
        for i, v in enumerate(vals):
            x = left + i * step
            y = bottom - (v / max_v) * chart_h
            pts.append(f"{x:.1f},{y:.1f}")
        c = CHART_COLORS[si % len(CHART_COLORS)]
        dash = "" if si == 0 else ' stroke-dasharray="6,3"'
        s += (
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{c}" '
            f'stroke-width="2.5" stroke-linecap="round" '
            f'stroke-linejoin="round"{dash}/>\n'
        )
        for i, v in enumerate(vals):
            x = left + i * step
            y = bottom - (v / max_v) * chart_h
            s += (
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#fff" '
                f'stroke="{c}" stroke-width="2"/>\n'
            )
    # X 轴标签
    for i, lb in enumerate(labels):
        if i < n_pts:
            x = left + i * step
            s += (
                f'<text x="{x:.1f}" y="{bottom + 18}" text-anchor="middle" '
                f'font-size="11" fill="#64748B">{_esc(lb)}</text>\n'
            )
    # 图例
    for si, ser in enumerate(series):
        lx = 370 + si * 70
        c = CHART_COLORS[si % len(CHART_COLORS)]
        name = ser.get("name", f"系列{si+1}")
        s += (
            f'<circle cx="{lx}" cy="46" r="4" fill="{c}"/>'
            f'<text x="{lx+8}" y="50" font-size="10" fill="#64748B">'
            f"{_esc(name)}</text>\n"
        )
    s += _TAIL
    return s


# ====================================================================
# 面积图 (area)
# ====================================================================


def _gen_area(cfg: dict) -> str:
    title = cfg.get("title", "面积图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [])
    if not series:
        return None
    left, top, right, bottom = 60, 45, 470, 260
    chart_h = bottom - top
    chart_w = right - left
    all_vals = [v for ser in series for v in ser.get("values", [])]
    max_v = _safe_max(all_vals)
    n_pts = max(len(ser.get("values", [])) for ser in series)
    if n_pts < 2:
        return None
    step = chart_w / (n_pts - 1)

    s = _head(title) + _axes(left, top, right, bottom)
    s += _y_labels(left, top, bottom, max_v)
    for si, ser in enumerate(series):
        vals = ser.get("values", [])
        pts = []
        for i, v in enumerate(vals):
            x = left + i * step
            y = bottom - (v / max_v) * chart_h
            pts.append((x, y))
        c = CHART_COLORS[si % len(CHART_COLORS)]
        # 面积
        area_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        area_pts += f" {pts[-1][0]:.1f},{bottom} {pts[0][0]:.1f},{bottom}"
        opacity = max(0.1, 0.3 - si * 0.08)
        s += (
            f'<path d="M{" L".join(f"{x:.1f},{y:.1f}" for x, y in pts)} '
            f'L{pts[-1][0]:.1f},{bottom} L{pts[0][0]:.1f},{bottom} Z" '
            f'fill="{c}" opacity="{opacity:.2f}"/>\n'
        )
        # 折线
        line_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        s += (
            f'<polyline points="{line_pts}" fill="none" stroke="{c}" '
            f'stroke-width="2" stroke-linecap="round"/>\n'
        )
    for i, lb in enumerate(labels):
        if i < n_pts:
            x = left + i * step
            s += (
                f'<text x="{x:.1f}" y="{bottom + 18}" text-anchor="middle" '
                f'font-size="11" fill="#64748B">{_esc(lb)}</text>\n'
            )
    s += _TAIL
    return s


# ====================================================================
# 饼图 (pie)
# ====================================================================


def _gen_pie(cfg: dict) -> str:
    title = cfg.get("title", "饼图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [{}])
    values = series[0].get("values", []) if series else []
    if not values:
        return None
    total = sum(values)
    if total <= 0:
        return None
    n = len(values)
    # 动态高度：确保图例不溢出
    legend_h = 100 + n * 30 + 10
    vb_h = max(CHART_HEIGHT, legend_h)
    cx, cy, r = 210, min(165, vb_h // 2 + 10), min(105, (vb_h - 50) // 2 - 10)

    s = _head_custom(title, CHART_WIDTH, vb_h)
    start_angle = -90  # 从顶部开始
    for i, v in enumerate(values):
        frac = v / total
        end_angle = start_angle + frac * 360
        c = CHART_COLORS[i % len(CHART_COLORS)]
        if frac >= 1.0:
            s += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c}"/>\n'
        else:
            x1 = cx + r * math.cos(math.radians(start_angle))
            y1 = cy + r * math.sin(math.radians(start_angle))
            x2 = cx + r * math.cos(math.radians(end_angle))
            y2 = cy + r * math.sin(math.radians(end_angle))
            large = 1 if frac > 0.5 else 0
            s += (
                f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} '
                f'A{r},{r} 0 {large},1 {x2:.1f},{y2:.1f} Z" '
                f'fill="{c}"/>\n'
            )
        start_angle = end_angle
    # 图例
    for i, v in enumerate(values):
        ly = 100 + i * 30
        c = CHART_COLORS[i % len(CHART_COLORS)]
        pct = f"{v / total * 100:.0f}%"
        lb = labels[i] if i < len(labels) else f"项{i+1}"
        s += (
            f'<circle cx="390" cy="{ly}" r="6" fill="{c}"/>'
            f'<text x="402" y="{ly + 4}" font-size="12" fill="#334155" '
            f"{DEFAULT_FONT_STYLE}>{_esc(lb)} {pct}</text>\n"
        )
    s += _TAIL
    return s


# ====================================================================
# 环形图 (donut)
# ====================================================================


def _gen_donut(cfg: dict) -> str:
    title = cfg.get("title", "环形图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [{}])
    values = series[0].get("values", []) if series else []
    center_text = cfg.get("centerText", "")
    center_label = cfg.get("centerLabel", "")
    if not values:
        return None
    total = sum(values)
    if total <= 0:
        return None
    n = len(values)
    # 动态高度：确保图例不溢出
    legend_h = 110 + n * 30 + 10
    vb_h = max(CHART_HEIGHT, legend_h)
    cx, cy, r = 210, min(165, vb_h // 2 + 10), min(105, (vb_h - 50) // 2 - 10)
    inner_r = int(r * 0.52)

    s = _head_custom(title, CHART_WIDTH, vb_h)
    start_angle = -90
    for i, v in enumerate(values):
        frac = v / total
        end_angle = start_angle + frac * 360
        c = CHART_COLORS[i % len(CHART_COLORS)]
        if frac >= 1.0:
            s += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c}"/>\n'
        else:
            x1 = cx + r * math.cos(math.radians(start_angle))
            y1 = cy + r * math.sin(math.radians(start_angle))
            x2 = cx + r * math.cos(math.radians(end_angle))
            y2 = cy + r * math.sin(math.radians(end_angle))
            large = 1 if frac > 0.5 else 0
            s += (
                f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} '
                f'A{r},{r} 0 {large},1 {x2:.1f},{y2:.1f} Z" '
                f'fill="{c}"/>\n'
            )
        start_angle = end_angle
    # 中心圆
    s += f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="#FAFBFC"/>\n'
    if center_text:
        s += (
            f'<text x="{cx}" y="{cy - 5}" text-anchor="middle" font-size="22" '
            f'font-weight="bold" fill="#1E293B">{_esc(center_text)}</text>\n'
        )
    if center_label:
        s += (
            f'<text x="{cx}" y="{cy + 15}" text-anchor="middle" font-size="12" '
            f'fill="#64748B" {DEFAULT_FONT_STYLE}>{_esc(center_label)}</text>\n'
        )
    # 图例
    for i, v in enumerate(values):
        ly = 110 + i * 30
        c = CHART_COLORS[i % len(CHART_COLORS)]
        pct = f"{v / total * 100:.0f}%"
        lb = labels[i] if i < len(labels) else f"项{i+1}"
        s += (
            f'<circle cx="390" cy="{ly}" r="6" fill="{c}"/>'
            f'<text x="402" y="{ly + 4}" font-size="12" fill="#334155" '
            f"{DEFAULT_FONT_STYLE}>{_esc(lb)} {pct}</text>\n"
        )
    s += _TAIL
    return s


# ====================================================================
# 散点图 (scatter)
# ====================================================================


def _gen_scatter(cfg: dict) -> str:
    title = cfg.get("title", "散点图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [])
    x_label = cfg.get("xLabel", "X 轴")
    y_label = cfg.get("yLabel", "Y 轴")
    if not series:
        return None
    left, top, right, bottom = 60, 50, 470, 260
    chart_h = bottom - top
    chart_w = right - left
    all_vals = [v for ser in series for v in ser.get("values", [])]
    max_v = _safe_max(all_vals)

    s = _head(title) + _axes(left, top, right, bottom)
    s += _y_labels(left, top, bottom, max_v)
    n_pts = max(len(ser.get("values", [])) for ser in series) if series else 0
    for si, ser in enumerate(series):
        vals = ser.get("values", [])
        c = CHART_COLORS[si % len(CHART_COLORS)]
        opacity = max(0.5, 0.8 - si * 0.15)
        for i, v in enumerate(vals):
            x = left + (i / max(n_pts - 1, 1)) * chart_w
            y = bottom - (v / max_v) * chart_h
            s += (
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{c}" '
                f'opacity="{opacity:.2f}"/>\n'
            )
    s += (
        f'<text x="{CHART_WIDTH/2}" y="290" text-anchor="middle" font-size="11" '
        f'fill="#64748B" {DEFAULT_FONT_STYLE}>{_esc(x_label)}</text>\n'
    )
    s += (
        f'<text x="35" y="{(CHART_HEIGHT)/2}" text-anchor="middle" font-size="11" '
        f'fill="#64748B" {DEFAULT_FONT_STYLE} transform="rotate(-90,35,{(CHART_HEIGHT)/2})">'
        f"{_esc(y_label)}</text>\n"
    )
    s += _TAIL
    return s


# ====================================================================
# 气泡图 (bubble)
# ====================================================================


def _gen_bubble(cfg: dict) -> str:
    title = cfg.get("title", "气泡图")
    series = cfg.get("series", [])
    x_label = cfg.get("xLabel", "X 轴")
    y_label = cfg.get("yLabel", "Y 轴")
    if len(series) < 1:
        return None
    left, top, right, bottom = 60, 50, 470, 260
    chart_h = bottom - top
    chart_w = right - left
    values = series[0].get("values", [])
    sizes = series[1].get("values", values) if len(series) > 1 else values
    max_v = _safe_max(values)
    max_sz = _safe_max(sizes)
    n = len(values)

    s = _head(title) + _axes(left, top, right, bottom)
    for i in range(n):
        v = values[i] if i < len(values) else 0
        sz = sizes[i] if i < len(sizes) else 20
        x = left + ((i + 0.5) / n) * chart_w
        y = bottom - (v / max_v) * chart_h * 0.85
        r = max(8, (sz / max_sz) * 40)
        c = CHART_COLORS[i % len(CHART_COLORS)]
        s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" ' f'fill="{c}" opacity="0.5"/>\n'
    s += (
        f'<text x="{CHART_WIDTH/2}" y="290" text-anchor="middle" font-size="11" '
        f'fill="#64748B" {DEFAULT_FONT_STYLE}>{_esc(x_label)}</text>\n'
    )
    s += (
        f'<text x="35" y="{CHART_HEIGHT/2}" text-anchor="middle" font-size="11" '
        f'fill="#64748B" {DEFAULT_FONT_STYLE} transform="rotate(-90,35,{CHART_HEIGHT/2})">'
        f"{_esc(y_label)}</text>\n"
    )
    s += _TAIL
    return s


# ====================================================================
# 雷达图 (radar)
# ====================================================================


def _gen_radar(cfg: dict) -> str:
    title = cfg.get("title", "雷达图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [{}])
    values = series[0].get("values", []) if series else []
    if not values:
        return None
    n = len(values)
    if n < 3:
        return None
    cx, cy, r = 250, 170, 100
    max_v = _safe_max(values)

    s = _head(title)
    # 外框和轴
    pts_outline = []
    for i in range(n):
        angle = math.radians(-90 + i * 360 / n)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        pts_outline.append((px, py))
        s += (
            f'<line x1="{cx}" y1="{cy}" x2="{px:.1f}" y2="{py:.1f}" '
            f'stroke="#CBD5E1" stroke-width="0.8"/>\n'
        )
    outline = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts_outline)
    s += f'<polygon points="{outline}" fill="none" stroke="#CBD5E1" stroke-width="1"/>\n'
    # 数据多边形
    data_pts = []
    for i, v in enumerate(values):
        ratio = v / max_v
        angle = math.radians(-90 + i * 360 / n)
        px = cx + r * ratio * math.cos(angle)
        py = cy + r * ratio * math.sin(angle)
        data_pts.append((px, py))
    data_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_pts)
    s += (
        f'<polygon points="{data_str}" fill="#4A90D9" fill-opacity="0.3" '
        f'stroke="#4A90D9" stroke-width="2.5"/>\n'
    )
    # 标签
    for i in range(n):
        angle = math.radians(-90 + i * 360 / n)
        lx = cx + (r + 18) * math.cos(angle)
        ly = cy + (r + 18) * math.sin(angle)
        lb = labels[i] if i < len(labels) else f"指标{i+1}"
        s += (
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
            f'font-size="12" fill="#334155" {DEFAULT_FONT_STYLE}>{_esc(lb)}</text>\n'
        )
    s += _TAIL
    return s


# ====================================================================
# 漏斗图 (funnel)
# ====================================================================


def _gen_funnel(cfg: dict) -> str:
    title = cfg.get("title", "漏斗图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [{}])
    values = series[0].get("values", []) if series else []
    if not values:
        return None
    n = len(values)
    max_v = _safe_max(values)
    top_y, total_h = 50, 230
    step_h = total_h / n
    cx = 250
    max_half_w = 200

    s = _head(title)
    for i, v in enumerate(values):
        frac = v / max_v
        next_frac = (values[i + 1] / max_v) if i + 1 < n else frac * 0.6
        w_top = max_half_w * frac
        w_bot = max_half_w * next_frac
        y1 = top_y + i * step_h
        y2 = y1 + step_h - 4
        c = CHART_COLORS[i % len(CHART_COLORS)]
        s += (
            f'<polygon points="{cx - w_top:.0f},{y1:.0f} '
            f"{cx + w_top:.0f},{y1:.0f} "
            f"{cx + w_bot:.0f},{y2:.0f} "
            f'{cx - w_bot:.0f},{y2:.0f}" fill="{c}"/>\n'
        )
        lb = labels[i] if i < len(labels) else ""
        s += (
            f'<text x="{cx}" y="{(y1 + y2) / 2 + 5:.0f}" '
            f'text-anchor="middle" font-size="13" fill="white" '
            f'font-weight="bold">{_esc(lb)} {v}</text>\n'
        )
    s += _TAIL
    return s


# ====================================================================
# 仪表盘 (gauge)
# ====================================================================


def _gen_gauge(cfg: dict) -> str:
    title = cfg.get("title", "仪表盘")
    series = cfg.get("series", [{}])
    values = series[0].get("values", [75]) if series else [75]
    val = values[0] if values else 75
    max_val = cfg.get("max", 100)
    unit = cfg.get("unit", "%")
    frac = min(val / max_val, 1.0) if max_val > 0 else 0

    cx, cy, radius = 250, 230, 150

    def arc_pt(angle_rad):
        """上半圆弧坐标，angle_rad 从 0(右) 到 π(左)。
        使用 cy - r*sin 修正 SVG Y 轴向下的问题。"""
        return cx + radius * math.cos(angle_rad), cy - radius * math.sin(angle_rad)

    # 背景弧：从左端 (π) 到右端 (0) 的上半圆
    sx, sy = arc_pt(math.pi)  # 左端点
    ex, ey = arc_pt(0)  # 右端点
    # 值弧：从左端到 frac 对应位置
    val_angle = math.pi * (1 - frac)
    vx, vy = arc_pt(val_angle)

    s = _head(title)
    # 背景弧（完整上半圆）
    s += (
        f'<path d="M{sx:.0f},{sy:.0f} A{radius},{radius} 0 0,1 '
        f'{ex:.0f},{ey:.0f}" fill="none" stroke="#E2E8F0" '
        f'stroke-width="28" stroke-linecap="round"/>\n'
    )
    # 值弧
    large = 1 if frac > 0.5 else 0
    s += (
        f'<path d="M{sx:.0f},{sy:.0f} A{radius},{radius} 0 {large},1 '
        f'{vx:.0f},{vy:.0f}" fill="none" stroke="#4A90D9" '
        f'stroke-width="28" stroke-linecap="round"/>\n'
    )
    # 数值
    s += (
        f'<text x="{cx}" y="{cy - 30}" text-anchor="middle" font-size="48" '
        f'font-weight="bold" fill="#1E293B">{val}</text>\n'
    )
    s += (
        f'<text x="{cx}" y="{cy}" text-anchor="middle" font-size="16" '
        f'fill="#64748B" {DEFAULT_FONT_STYLE}>{_esc(unit)}</text>\n'
    )
    # 刻度标签
    s += (
        f'<text x="{sx:.0f}" y="{sy + 25:.0f}" text-anchor="middle" '
        f'font-size="11" fill="#94A3B8">0</text>\n'
    )
    mid_x, mid_y = arc_pt(math.pi / 2)  # 顶部中点
    s += (
        f'<text x="{mid_x:.0f}" y="{mid_y - 15:.0f}" text-anchor="middle" '
        f'font-size="11" fill="#94A3B8">{max_val // 2}</text>\n'
    )
    s += (
        f'<text x="{ex:.0f}" y="{ey + 25:.0f}" text-anchor="middle" '
        f'font-size="11" fill="#94A3B8">{max_val}</text>\n'
    )
    s += _TAIL
    return s


# ====================================================================
# 瀑布图 (waterfall)
# ====================================================================


def _gen_waterfall(cfg: dict) -> str:
    title = cfg.get("title", "瀑布图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [{}])
    values = series[0].get("values", []) if series else []
    if not values:
        return None
    n = len(values)
    left, top, right, bottom = 60, 50, 470, 260
    chart_h = bottom - top
    chart_w = right - left

    # 计算累计值以确定坐标
    cum = [0] * n
    cum[0] = values[0]
    for i in range(1, n):
        cum[i] = cum[i - 1] + values[i]
    all_vals = [0] + cum + values
    min_v = min(all_vals)
    max_v = max(all_vals)
    span = max_v - min_v if max_v != min_v else 1
    bar_w = chart_w / (n * 1.5 + 0.5)
    gap = bar_w * 0.5

    def y_pos(val):
        return bottom - ((val - min_v) / span) * chart_h

    s = _head(title) + _axes(left, top, right, bottom)
    prev_top = y_pos(0)
    for i, v in enumerate(values):
        x = left + gap + i * (bar_w + gap)
        if i == 0 or i == n - 1:
            # 起始/合计
            bar_top = y_pos(cum[i])
            bar_bot = y_pos(0)
            color = "#4A90D9" if i == 0 else "#9B59B6"
        elif v >= 0:
            bar_top = y_pos(cum[i])
            bar_bot = y_pos(cum[i - 1])
            color = "#27AE60"
        else:
            bar_top = y_pos(cum[i - 1])
            bar_bot = y_pos(cum[i])
            color = "#E74C3C"
        h = abs(bar_bot - bar_top)
        y = min(bar_top, bar_bot)
        s += (
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" rx="2" fill="{color}"/>\n'
        )
        # 连接线
        if i > 0:
            s += (
                f'<line x1="{x - gap:.1f}" y1="{prev_top:.1f}" '
                f'x2="{x:.1f}" y2="{prev_top:.1f}" stroke="#94A3B8" '
                f'stroke-width="1" stroke-dasharray="3,2"/>\n'
            )
        prev_top = y
        # 值标签
        lbl_v = f"+{v}" if v > 0 and i > 0 and i < n - 1 else str(v)
        s += (
            f'<text x="{x + bar_w/2:.1f}" y="{y - 5:.1f}" '
            f'text-anchor="middle" font-size="11" font-weight="bold" '
            f'fill="{color}">{lbl_v}</text>\n'
        )
        if i < len(labels):
            s += (
                f'<text x="{x + bar_w/2:.1f}" y="{bottom + 18}" '
                f'text-anchor="middle" font-size="10" fill="#64748B">'
                f"{_esc(labels[i])}</text>\n"
            )
    s += _TAIL
    return s


# ====================================================================
# 进度条 (progress)
# ====================================================================


def _gen_progress(cfg: dict) -> str:
    title = cfg.get("title", "进度条")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [{}])
    values = series[0].get("values", []) if series else []
    if not values:
        return None
    n = len(values)
    row_h = min(40, 180 / n)
    vb_h = 50 + n * row_h + 10
    bar_left, bar_right = 130, 430
    bar_w = bar_right - bar_left

    s = _head_custom(title, 500, int(vb_h))
    for i, v in enumerate(values):
        y = 50 + i * row_h
        lb = labels[i] if i < len(labels) else f"项目{i+1}"
        c = CHART_COLORS[i % len(CHART_COLORS)]
        pct = min(v, 100) / 100
        s += (
            f'<text x="60" y="{y + 14}" font-size="12" fill="#334155" '
            f"{DEFAULT_FONT_STYLE}>{_esc(lb)}</text>\n"
        )
        s += (
            f'<rect x="{bar_left}" y="{y + 2}" width="{bar_w}" '
            f'height="18" rx="9" fill="#E2E8F0"/>\n'
        )
        s += (
            f'<rect x="{bar_left}" y="{y + 2}" width="{bar_w * pct:.0f}" '
            f'height="18" rx="9" fill="{c}"/>\n'
        )
        s += (
            f'<text x="{bar_right + 15}" y="{y + 15}" font-size="12" '
            f'font-weight="bold" fill="{c}">{v}%</text>\n'
        )
    s += _TAIL
    return s


# ====================================================================
# 热力图 (heatmap)
# ====================================================================


def _gen_heatmap(cfg: dict) -> str:
    title = cfg.get("title", "热力图")
    rows = cfg.get("labels", [])
    cols = cfg.get("colLabels", rows)
    series = cfg.get("series", [{}])
    flat_vals = series[0].get("values", []) if series else []
    if not flat_vals or not rows:
        return None
    n_rows = len(rows)
    n_cols = len(cols) if cols else n_rows
    # 颜色映射
    min_v = min(flat_vals) if flat_vals else 0
    max_v = max(flat_vals) if flat_vals else 1
    span = max_v - min_v if max_v != min_v else 1

    def color_for(val):
        t = (val - min_v) / span
        # 蓝色渐变 #DBEAFE → #1D4ED8
        r = int(219 + (29 - 219) * t)
        g = int(234 + (78 - 234) * t)
        b = int(254 + (216 - 254) * t)
        return f"rgb({r},{g},{b})"

    def text_color(val):
        t = (val - min_v) / span
        return "#fff" if t > 0.55 else "#1E293B"

    cell_w = min(68, 340 // n_cols)
    cell_h = min(42, 210 // n_rows)
    x_start = 110
    y_start = 58

    s = _head(title)
    # 列标签
    for c_i, cl in enumerate(cols):
        s += (
            f'<text x="{x_start + c_i * cell_w + cell_w/2:.0f}" y="52" '
            f'text-anchor="middle" font-size="11" fill="#334155" {DEFAULT_FONT_STYLE}>'
            f"{_esc(cl)}</text>\n"
        )
    # 行标签 + 单元格
    for r_i in range(n_rows):
        ry = y_start + r_i * cell_h
        s += (
            f'<text x="{x_start - 10}" y="{ry + cell_h/2 + 4:.0f}" '
            f'text-anchor="end" font-size="11" fill="#334155" {DEFAULT_FONT_STYLE}>'
            f"{_esc(rows[r_i])}</text>\n"
        )
        for c_i in range(n_cols):
            idx = r_i * n_cols + c_i
            val = flat_vals[idx] if idx < len(flat_vals) else 0
            cx_ = x_start + c_i * cell_w
            s += (
                f'<rect x="{cx_}" y="{ry}" width="{cell_w - 4}" '
                f'height="{cell_h - 4}" rx="4" fill="{color_for(val)}"/>\n'
            )
            s += (
                f'<text x="{cx_ + (cell_w-4)/2:.0f}" y="{ry + (cell_h-4)/2 + 4:.0f}" '
                f'text-anchor="middle" font-size="12" fill="{text_color(val)}">'
                f"{val}</text>\n"
            )
    s += _TAIL
    return s


# ====================================================================
# 甘特图 (gantt)
# ====================================================================


def _gen_gantt(cfg: dict) -> str:
    title = cfg.get("title", "甘特图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [])
    if len(series) < 2 or not labels:
        return None
    starts = series[0].get("values", [])
    durations = series[1].get("values", [])
    n = len(labels)
    vb_h = max(280, 60 + n * 40 + 20)
    left, right = 120, 470
    chart_w = right - left
    all_ends = [starts[i] + durations[i] for i in range(min(len(starts), len(durations)))]
    max_t = max(all_ends) if all_ends else 1

    s = _head_custom(title, 500, vb_h)
    # 时间网格
    n_cols = min(6, int(max_t) + 1)
    for c in range(n_cols + 1):
        x = left + (c / max_t) * chart_w
        s += (
            f'<line x1="{x:.0f}" y1="40" x2="{x:.0f}" y2="{vb_h - 20}" '
            f'stroke="#E2E8F0" stroke-width="0.5"/>\n'
        )
    for i in range(n):
        y = 60 + i * 40
        start = starts[i] if i < len(starts) else 0
        dur = durations[i] if i < len(durations) else 0
        x = left + (start / max_t) * chart_w
        w = (dur / max_t) * chart_w
        c = CHART_COLORS[i % len(CHART_COLORS)]
        s += (
            f'<text x="{left - 10}" y="{y + 14}" text-anchor="end" '
            f'font-size="12" fill="#334155" {DEFAULT_FONT_STYLE}>{_esc(labels[i])}</text>\n'
        )
        s += f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="22" ' f'rx="11" fill="{c}"/>\n'
    s += _TAIL
    return s


# ====================================================================
# 箱线图 (boxplot)
# ====================================================================


def _gen_boxplot(cfg: dict) -> str:
    title = cfg.get("title", "箱线图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [])
    # 需要 min, q1, median, q3, max 五个系列
    if len(series) < 5 or not labels:
        return None
    mins = series[0].get("values", [])
    q1s = series[1].get("values", [])
    meds = series[2].get("values", [])
    q3s = series[3].get("values", [])
    maxs = series[4].get("values", [])
    n = len(labels)
    left, top, right, bottom = 60, 50, 470, 260
    chart_h = bottom - top
    chart_w = right - left
    all_v = mins + maxs
    data_min = min(all_v) if all_v else 0
    data_max = max(all_v) if all_v else 100
    span = data_max - data_min if data_max != data_min else 1
    box_w = min(60, chart_w / (n * 2))

    def calculate_y_position(value):
        """计算数值在 Y 轴上的像素位置

        Args:
            value: 数据值

        Returns:
            Y 轴像素坐标
        """
        return bottom - ((value - data_min) / span) * chart_h

    s = _head(title) + _axes(left, top, right, bottom)
    s += _y_labels(left, top, bottom, data_max)
    for i in range(n):
        cx_ = left + (i + 0.5) * (chart_w / n)
        c = CHART_COLORS[i % len(CHART_COLORS)]
        mn = mins[i] if i < len(mins) else 0
        q1 = q1s[i] if i < len(q1s) else 25
        med = meds[i] if i < len(meds) else 50
        q3 = q3s[i] if i < len(q3s) else 75
        mx = maxs[i] if i < len(maxs) else 100
        # 须
        s += (
            f'<line x1="{cx_}" y1="{calculate_y_position(mx):.1f}" x2="{cx_}" '
            f'y2="{calculate_y_position(q3):.1f}" stroke="{c}" stroke-width="2"/>\n'
        )
        s += (
            f'<line x1="{cx_}" y1="{calculate_y_position(q1):.1f}" x2="{cx_}" '
            f'y2="{calculate_y_position(mn):.1f}" stroke="{c}" stroke-width="2"/>\n'
        )
        # 箱
        s += (
            f'<rect x="{cx_ - box_w/2:.1f}" y="{calculate_y_position(q3):.1f}" '
            f'width="{box_w}" height="{calculate_y_position(q1) - calculate_y_position(q3):.1f}" rx="4" '
            f'fill="{c}" opacity="0.2" stroke="{c}" stroke-width="2"/>\n'
        )
        # 中位线
        s += (
            f'<line x1="{cx_ - box_w/2:.1f}" y1="{calculate_y_position(med):.1f}" '
            f'x2="{cx_ + box_w/2:.1f}" y2="{calculate_y_position(med):.1f}" '
            f'stroke="{c}" stroke-width="3"/>\n'
        )
        # 端线
        hw = box_w * 0.4
        s += (
            f'<line x1="{cx_ - hw:.1f}" y1="{calculate_y_position(mx):.1f}" '
            f'x2="{cx_ + hw:.1f}" y2="{calculate_y_position(mx):.1f}" '
            f'stroke="{c}" stroke-width="2"/>\n'
        )
        s += (
            f'<line x1="{cx_ - hw:.1f}" y1="{calculate_y_position(mn):.1f}" '
            f'x2="{cx_ + hw:.1f}" y2="{calculate_y_position(mn):.1f}" '
            f'stroke="{c}" stroke-width="2"/>\n'
        )
        if i < len(labels):
            s += (
                f'<text x="{cx_}" y="{bottom + 18}" text-anchor="middle" '
                f'font-size="12" fill="#64748B" {DEFAULT_FONT_STYLE}>'
                f"{_esc(labels[i])}</text>\n"
            )
    s += _TAIL
    return s


# ====================================================================
# 双轴图 (dual_axis)
# ====================================================================


def _gen_dual_axis(cfg: dict) -> str:
    title = cfg.get("title", "双轴图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [])
    if len(series) < 2 or not labels:
        return None
    bar_vals = series[0].get("values", [])
    line_vals = series[1].get("values", [])
    bar_name = series[0].get("name", "柱")
    line_name = series[1].get("name", "线")
    n = len(labels)
    left, top, right_ax, bottom = 65, 50, 435, 260
    chart_h = bottom - top
    chart_w = right_ax - left
    bar_max = _safe_max(bar_vals)
    line_max = _safe_max(line_vals)
    bar_w = chart_w / (n * 1.8)
    gap = bar_w * 0.4

    s = _head(title)
    # 双轴
    s += (
        f'<line x1="{left}" y1="{bottom}" x2="{right_ax}" y2="{bottom}" '
        f'stroke="#CBD5E1" stroke-width="1"/>\n'
    )
    s += (
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" '
        f'stroke="#4A90D9" stroke-width="1"/>\n'
    )
    s += (
        f'<line x1="{right_ax}" y1="{top}" x2="{right_ax}" y2="{bottom}" '
        f'stroke="#E74C3C" stroke-width="1"/>\n'
    )
    # 柱
    for i, v in enumerate(bar_vals):
        x = left + gap + i * (chart_w / n)
        h = (v / bar_max) * chart_h
        y = bottom - h
        s += (
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" rx="3" fill="#4A90D9" opacity="0.55"/>\n'
        )
    # 线
    pts = []
    for i, v in enumerate(line_vals):
        x = left + gap + i * (chart_w / n) + bar_w / 2
        y = bottom - (v / line_max) * chart_h
        pts.append((x, y))
    if pts:
        s += (
            f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" '
            f'fill="none" stroke="#E74C3C" stroke-width="3" '
            f'stroke-linecap="round" stroke-linejoin="round"/>\n'
        )
        for x, y in pts:
            s += (
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#fff" '
                f'stroke="#E74C3C" stroke-width="2.5"/>\n'
            )
    # X 标签
    for i, lb in enumerate(labels):
        x = left + gap + i * (chart_w / n) + bar_w / 2
        s += (
            f'<text x="{x:.1f}" y="{bottom + 18}" text-anchor="middle" '
            f'font-size="11" fill="#64748B">{_esc(lb)}</text>\n'
        )
    # 图例
    s += (
        f'<rect x="140" y="42" width="10" height="10" rx="2" fill="#4A90D9" '
        f'opacity="0.55"/><text x="155" y="51" font-size="10" fill="#334155">'
        f"{_esc(bar_name)}</text>\n"
    )
    s += (
        f'<line x1="220" y1="47" x2="240" y2="47" stroke="#E74C3C" '
        f'stroke-width="2.5"/><text x="245" y="51" font-size="10" '
        f'fill="#334155">{_esc(line_name)}</text>\n'
    )
    s += _TAIL
    return s


# ====================================================================
# 对比柱状图 (diverging)
# ====================================================================


def _gen_diverging(cfg: dict) -> str:
    title = cfg.get("title", "对比柱状图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [])
    if len(series) < 2 or not labels:
        return None
    left_vals = series[0].get("values", [])
    right_vals = series[1].get("values", [])
    left_name = series[0].get("name", "左")
    right_name = series[1].get("name", "右")
    n = len(labels)
    cx = 250
    label_x = 58
    top_y, bar_h = 62, min(26, 200 // n)
    gap = max(8, bar_h * 0.5)
    max_w = 190
    all_v = left_vals + right_vals
    max_v = _safe_max(all_v)

    s = _head(title)
    s += f'<line x1="{cx}" y1="45" x2="{cx}" y2="265" ' f'stroke="#CBD5E1" stroke-width="1"/>\n'
    for i in range(n):
        y = top_y + i * (bar_h + gap)
        lv = left_vals[i] if i < len(left_vals) else 0
        rv = right_vals[i] if i < len(right_vals) else 0
        lw = (lv / max_v) * max_w
        rw = (rv / max_v) * max_w
        lb = labels[i] if i < len(labels) else ""
        s += (
            f'<text x="{label_x}" y="{y + bar_h/2 + 4:.0f}" '
            f'text-anchor="end" font-size="12" fill="#334155" {DEFAULT_FONT_STYLE}>'
            f"{_esc(lb)}</text>\n"
        )
        s += (
            f'<rect x="{cx - lw:.0f}" y="{y}" width="{lw:.0f}" '
            f'height="{bar_h}" rx="4" fill="#E74C3C" opacity="0.8"/>\n'
        )
        s += (
            f'<rect x="{cx}" y="{y}" width="{rw:.0f}" '
            f'height="{bar_h}" rx="4" fill="#4A90D9" opacity="0.8"/>\n'
        )
        # 百分比
        if lw > 30:
            s += (
                f'<text x="{cx - lw/2:.0f}" y="{y + bar_h/2 + 4:.0f}" '
                f'text-anchor="middle" font-size="11" fill="white" '
                f'font-weight="bold">{lv}%</text>\n'
            )
        if rw > 30:
            s += (
                f'<text x="{cx + rw/2:.0f}" y="{y + bar_h/2 + 4:.0f}" '
                f'text-anchor="middle" font-size="11" fill="white" '
                f'font-weight="bold">{rv}%</text>\n'
            )
    # 标注
    s += (
        f'<text x="130" y="285" text-anchor="middle" font-size="10" '
        f'fill="#E74C3C">← {_esc(left_name)}</text>\n'
    )
    s += (
        f'<text x="370" y="285" text-anchor="middle" font-size="10" '
        f'fill="#4A90D9">{_esc(right_name)} →</text>\n'
    )
    s += _TAIL
    return s


# ====================================================================
# 矩形树图 (treemap)
# ====================================================================


def _gen_treemap(cfg: dict) -> str:
    title = cfg.get("title", "矩形树图")
    labels = cfg.get("labels", [])
    series = cfg.get("series", [{}])
    values = series[0].get("values", []) if series else []
    if not values:
        return None
    total = sum(values) if values else 1
    n = len(values)
    pad = 15
    area_x, area_y = pad, 42
    area_w, area_h = CHART_WIDTH - 2 * pad, CHART_HEIGHT - area_y - pad

    # 简单的从上到下、从左到右排布
    rects = []
    cx_, cy_ = area_x, area_y
    row_w = area_w
    half = max(n // 2, 1)
    top_sum = sum(values[j] for j in range(half))
    bot_sum = sum(values[j] for j in range(half, n))
    for i, v in enumerate(values):
        if i < half:
            w = row_w * (v / top_sum) if top_sum > 0 else row_w / half
            rects.append((cx_, cy_, max(w - 3, 4), area_h * 0.55 - 3))
            cx_ += w
        else:
            if i == half:
                cx_ = area_x
                cy_ = area_y + area_h * 0.55 + 3
            w = row_w * (v / bot_sum) if bot_sum > 0 else row_w / max(n - half, 1)
            rects.append((cx_, cy_, max(w - 3, 4), area_h * 0.45 - 3))
            cx_ += w

    s = _head(title)
    for i, (rx, ry, rw, rh) in enumerate(rects):
        c = CHART_COLORS[i % len(CHART_COLORS)]
        lb = labels[i] if i < len(labels) else f"类{i+1}"
        pct = f"{values[i] / total * 100:.0f}%" if total > 0 else ""
        s += (
            f'<rect x="{rx:.0f}" y="{ry:.0f}" width="{rw:.0f}" '
            f'height="{rh:.0f}" rx="6" fill="{c}"/>\n'
        )
        font_sz = 16 if rw > 120 and rh > 60 else 12
        s += (
            f'<text x="{rx + rw/2:.0f}" y="{ry + rh/2:.0f}" '
            f'text-anchor="middle" font-size="{font_sz}" font-weight="bold" '
            f'fill="white">{_esc(lb)}</text>\n'
        )
        s += (
            f'<text x="{rx + rw/2:.0f}" y="{ry + rh/2 + font_sz:.0f}" '
            f'text-anchor="middle" font-size="{font_sz - 3}" '
            f'fill="rgba(255,255,255,0.8)">{pct}</text>\n'
        )
    s += _TAIL
    return s


# ====================================================================
# 注册表
# ====================================================================

_GENERATORS: dict[str, callable] = {
    "bar": _gen_bar,
    "grouped": _gen_grouped,
    "stacked": _gen_stacked,
    "h_bar": _gen_h_bar,
    "line": _gen_line,
    "area": _gen_area,
    "pie": _gen_pie,
    "donut": _gen_donut,
    "scatter": _gen_scatter,
    "bubble": _gen_bubble,
    "radar": _gen_radar,
    "funnel": _gen_funnel,
    "gauge": _gen_gauge,
    "waterfall": _gen_waterfall,
    "progress": _gen_progress,
    "heatmap": _gen_heatmap,
    "gantt": _gen_gantt,
    "boxplot": _gen_boxplot,
    "dual_axis": _gen_dual_axis,
    "diverging": _gen_diverging,
    "treemap": _gen_treemap,
}
