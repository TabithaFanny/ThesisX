"""
chart_dialog.py — 数据图选择对话框

弹出一个美观的选择界面，展示各种数据图（柱状图、折线图、饼图等）的预览缩略图。
用户选择一种图表后点击「插入」，将对应的 HTML 表格+内联 SVG 插入编辑器。
"""

import html as _html_mod
import json as _json

from PyQt6.QtCore import QByteArray, QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# ======================================================================
# Chart definitions: each chart has an SVG preview and insertable HTML
# ======================================================================

_CHART_DEFS = []


def _register(key, label, desc, svg_func, html_func, default_config=None):
    _CHART_DEFS.append(
        {
            "key": key,
            "label": label,
            "desc": desc,
            "svg_func": svg_func,
            "html_func": html_func,
            "default_config": default_config or {},
        }
    )


def wrap_chart_with_config(chart_type: str, html: str, config: dict) -> str:
    """给图表 HTML 注入 data-chart-type 和 data-chart-config 属性。"""
    if not config:
        return html
    config_json = _json.dumps(config, ensure_ascii=False)
    escaped = _html_mod.escape(config_json, quote=True)
    return html.replace(
        'class="chart-container"',
        f'class="chart-container" data-chart-type="{chart_type}" ' f'data-chart-config="{escaped}"',
        1,
    )


# ── Color palette ──
_COLORS = ["#4A90D9", "#27AE60", "#F39C12", "#E74C3C", "#9B59B6", "#1ABC9C"]


# ------------------------------------------------------------------
# SVG preview generators (return SVG bytes for thumbnail)
# ------------------------------------------------------------------


def _svg_bar_chart():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="150" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="15" x2="25" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<rect x="35" y="60" width="18" height="40" rx="2" fill="#4A90D9"/>'
        b'<rect x="60" y="35" width="18" height="65" rx="2" fill="#27AE60"/>'
        b'<rect x="85" y="50" width="18" height="50" rx="2" fill="#F39C12"/>'
        b'<rect x="110" y="25" width="18" height="75" rx="2" fill="#E74C3C"/>'
        b'<rect x="135" y="45" width="18" height="55" rx="2" fill="#9B59B6"/>'
        b"</svg>"
    )


def _svg_line_chart():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="150" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="15" x2="25" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<polyline points="35,75 60,50 85,60 110,30 135,45" fill="none" stroke="#4A90D9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
        b'<circle cx="35" cy="75" r="3.5" fill="#4A90D9"/>'
        b'<circle cx="60" cy="50" r="3.5" fill="#4A90D9"/>'
        b'<circle cx="85" cy="60" r="3.5" fill="#4A90D9"/>'
        b'<circle cx="110" cy="30" r="3.5" fill="#4A90D9"/>'
        b'<circle cx="135" cy="45" r="3.5" fill="#4A90D9"/>'
        b'<polyline points="35,85 60,65 85,70 110,55 135,60" fill="none" stroke="#27AE60" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4,3"/>'
        b"</svg>"
    )


def _svg_pie_chart():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<circle cx="75" cy="60" r="42" fill="#4A90D9"/>'
        b'<path d="M75,60 L75,18 A42,42 0 0,1 111.3,39 Z" fill="#27AE60"/>'
        b'<path d="M75,60 L111.3,39 A42,42 0 0,1 108.7,87 Z" fill="#F39C12"/>'
        b'<path d="M75,60 L108.7,87 A42,42 0 0,1 75,102 Z" fill="#E74C3C"/>'
        b'<circle cx="134" cy="30" r="4" fill="#4A90D9"/><text x="141" y="34" font-size="9" fill="#64748B">A</text>'
        b'<circle cx="134" cy="48" r="4" fill="#27AE60"/><text x="141" y="52" font-size="9" fill="#64748B">B</text>'
        b'<circle cx="134" cy="66" r="4" fill="#F39C12"/><text x="141" y="70" font-size="9" fill="#64748B">C</text>'
        b'<circle cx="134" cy="84" r="4" fill="#E74C3C"/><text x="141" y="88" font-size="9" fill="#64748B">D</text>'
        b"</svg>"
    )


def _svg_area_chart():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="150" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="15" x2="25" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<path d="M35,80 L60,55 L85,65 L110,35 L135,50 L135,100 L35,100 Z" fill="#4A90D9" opacity="0.25"/>'
        b'<polyline points="35,80 60,55 85,65 110,35 135,50" fill="none" stroke="#4A90D9" stroke-width="2" stroke-linecap="round"/>'
        b'<path d="M35,90 L60,75 L85,80 L110,60 L135,70 L135,100 L35,100 Z" fill="#27AE60" opacity="0.2"/>'
        b'<polyline points="35,90 60,75 85,80 110,60 135,70" fill="none" stroke="#27AE60" stroke-width="2" stroke-linecap="round"/>'
        b"</svg>"
    )


def _svg_scatter_chart():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="150" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="15" x2="25" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<circle cx="40" cy="75" r="4.5" fill="#4A90D9" opacity="0.8"/>'
        b'<circle cx="55" cy="60" r="4.5" fill="#4A90D9" opacity="0.8"/>'
        b'<circle cx="70" cy="68" r="4.5" fill="#4A90D9" opacity="0.8"/>'
        b'<circle cx="85" cy="45" r="4.5" fill="#4A90D9" opacity="0.8"/>'
        b'<circle cx="100" cy="38" r="4.5" fill="#4A90D9" opacity="0.8"/>'
        b'<circle cx="115" cy="50" r="4.5" fill="#4A90D9" opacity="0.8"/>'
        b'<circle cx="130" cy="30" r="4.5" fill="#4A90D9" opacity="0.8"/>'
        b'<circle cx="48" cy="85" r="4" fill="#E74C3C" opacity="0.7"/>'
        b'<circle cx="72" cy="55" r="4" fill="#E74C3C" opacity="0.7"/>'
        b'<circle cx="95" cy="52" r="4" fill="#E74C3C" opacity="0.7"/>'
        b'<circle cx="120" cy="40" r="4" fill="#E74C3C" opacity="0.7"/>'
        b'<line x1="35" y1="85" x2="140" y2="28" stroke="#94A3B8" stroke-width="1" stroke-dasharray="4,3"/>'
        b"</svg>"
    )


def _svg_radar_chart():
    import math

    cx, cy, r = 80, 60, 38
    pts5 = []
    for i in range(5):
        angle = math.radians(-90 + i * 72)
        pts5.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    # Pentagon outline
    outline = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts5)
    # Data polygon (inner)
    ratios = [0.8, 0.6, 0.9, 0.5, 0.7]
    data_pts = []
    for i, ratio in enumerate(ratios):
        angle = math.radians(-90 + i * 72)
        data_pts.append((cx + r * ratio * math.cos(angle), cy + r * ratio * math.sin(angle)))
    data_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_pts)
    # Axis lines
    axes = ""
    for x, y in pts5:
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#CBD5E1" stroke-width="0.8"/>'
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        f'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        f"{axes}"
        f'<polygon points="{outline}" fill="none" stroke="#CBD5E1" stroke-width="1"/>'
        f'<polygon points="{data_str}" fill="#4A90D9" fill-opacity="0.3" stroke="#4A90D9" stroke-width="2"/>'
        f"</svg>"
    )
    return svg.encode()


def _svg_horizontal_bar():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="15" x2="25" y2="105" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="105" x2="150" y2="105" stroke="#CBD5E1" stroke-width="1"/>'
        b'<rect x="25" y="18" width="95" height="14" rx="2" fill="#4A90D9"/>'
        b'<rect x="25" y="38" width="120" height="14" rx="2" fill="#27AE60"/>'
        b'<rect x="25" y="58" width="70" height="14" rx="2" fill="#F39C12"/>'
        b'<rect x="25" y="78" width="105" height="14" rx="2" fill="#E74C3C"/>'
        b"</svg>"
    )


def _svg_stacked_bar():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="150" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="15" x2="25" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<rect x="35" y="65" width="22" height="35" rx="1" fill="#4A90D9"/>'
        b'<rect x="35" y="40" width="22" height="25" rx="1" fill="#27AE60"/>'
        b'<rect x="35" y="25" width="22" height="15" rx="1" fill="#F39C12"/>'
        b'<rect x="70" y="55" width="22" height="45" rx="1" fill="#4A90D9"/>'
        b'<rect x="70" y="30" width="22" height="25" rx="1" fill="#27AE60"/>'
        b'<rect x="70" y="20" width="22" height="10" rx="1" fill="#F39C12"/>'
        b'<rect x="105" y="60" width="22" height="40" rx="1" fill="#4A90D9"/>'
        b'<rect x="105" y="38" width="22" height="22" rx="1" fill="#27AE60"/>'
        b'<rect x="105" y="28" width="22" height="10" rx="1" fill="#F39C12"/>'
        b"</svg>"
    )


def _svg_donut_chart():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<circle cx="75" cy="60" r="42" fill="#4A90D9"/>'
        b'<path d="M75,60 L75,18 A42,42 0 0,1 111.3,39 Z" fill="#27AE60"/>'
        b'<path d="M75,60 L111.3,39 A42,42 0 0,1 108.7,87 Z" fill="#F39C12"/>'
        b'<path d="M75,60 L108.7,87 A42,42 0 0,1 75,102 Z" fill="#E74C3C"/>'
        b'<circle cx="75" cy="60" r="22" fill="#F8FAFC"/>'
        b'<text x="75" y="64" text-anchor="middle" font-size="11" font-weight="bold" fill="#334155">65%</text>'
        b"</svg>"
    )


# ------------------------------------------------------------------
# Insertable HTML generators (produce an inline SVG chart for the doc)
# ------------------------------------------------------------------


def _html_bar_chart():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">柱状图标题</text>
<line x1="60" y1="260" x2="470" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<text x="55" y="265" text-anchor="end" font-size="10" fill="#94A3B8">0</text>
<text x="55" y="210" text-anchor="end" font-size="10" fill="#94A3B8">25</text>
<text x="55" y="155" text-anchor="end" font-size="10" fill="#94A3B8">50</text>
<text x="55" y="100" text-anchor="end" font-size="10" fill="#94A3B8">75</text>
<line x1="60" y1="207" x2="470" y2="207" stroke="#F1F5F9" stroke-width="0.5"/>
<line x1="60" y1="155" x2="470" y2="155" stroke="#F1F5F9" stroke-width="0.5"/>
<line x1="60" y1="102" x2="470" y2="102" stroke="#F1F5F9" stroke-width="0.5"/>
<rect x="90" y="155" width="55" height="105" rx="3" fill="#4A90D9"/>
<rect x="175" y="100" width="55" height="160" rx="3" fill="#27AE60"/>
<rect x="260" y="130" width="55" height="130" rx="3" fill="#F39C12"/>
<rect x="345" y="75" width="55" height="185" rx="3" fill="#E74C3C"/>
<text x="117" y="278" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif">类目A</text>
<text x="202" y="278" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif">类目B</text>
<text x="287" y="278" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif">类目C</text>
<text x="372" y="278" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif">类目D</text>
<text x="117" y="150" text-anchor="middle" font-size="11" font-weight="bold" fill="#4A90D9">50</text>
<text x="202" y="95" text-anchor="middle" font-size="11" font-weight="bold" fill="#27AE60">76</text>
<text x="287" y="125" text-anchor="middle" font-size="11" font-weight="bold" fill="#F39C12">62</text>
<text x="372" y="70" text-anchor="middle" font-size="11" font-weight="bold" fill="#E74C3C">88</text>
</svg>
</div>"""


def _html_line_chart():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">折线图标题</text>
<line x1="60" y1="260" x2="470" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="207" x2="470" y2="207" stroke="#F1F5F9" stroke-width="0.5"/>
<line x1="60" y1="155" x2="470" y2="155" stroke="#F1F5F9" stroke-width="0.5"/>
<line x1="60" y1="102" x2="470" y2="102" stroke="#F1F5F9" stroke-width="0.5"/>
<polyline points="90,190 172,130 254,155 336,85 418,120" fill="none" stroke="#4A90D9" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="90" cy="190" r="4" fill="#fff" stroke="#4A90D9" stroke-width="2"/>
<circle cx="172" cy="130" r="4" fill="#fff" stroke="#4A90D9" stroke-width="2"/>
<circle cx="254" cy="155" r="4" fill="#fff" stroke="#4A90D9" stroke-width="2"/>
<circle cx="336" cy="85" r="4" fill="#fff" stroke="#4A90D9" stroke-width="2"/>
<circle cx="418" cy="120" r="4" fill="#fff" stroke="#4A90D9" stroke-width="2"/>
<polyline points="90,220 172,180 254,195 336,150 418,170" fill="none" stroke="#27AE60" stroke-width="2" stroke-dasharray="6,3" stroke-linecap="round"/>
<text x="90" y="278" text-anchor="middle" font-size="11" fill="#64748B">1月</text>
<text x="172" y="278" text-anchor="middle" font-size="11" fill="#64748B">2月</text>
<text x="254" y="278" text-anchor="middle" font-size="11" fill="#64748B">3月</text>
<text x="336" y="278" text-anchor="middle" font-size="11" fill="#64748B">4月</text>
<text x="418" y="278" text-anchor="middle" font-size="11" fill="#64748B">5月</text>
<circle cx="400" cy="48" r="4" fill="#4A90D9"/><text x="410" y="52" font-size="10" fill="#64748B">系列1</text>
<circle cx="400" cy="64" r="4" fill="#27AE60"/><text x="410" y="68" font-size="10" fill="#64748B">系列2</text>
</svg>
</div>"""


def _html_pie_chart():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">饼图标题</text>
<circle cx="210" cy="165" r="105" fill="#4A90D9"/>
<path d="M210,165 L210,60 A105,105 0 0,1 300,95 Z" fill="#27AE60"/>
<path d="M210,165 L300,95 A105,105 0 0,1 293,248 Z" fill="#F39C12"/>
<path d="M210,165 L293,248 A105,105 0 0,1 210,270 Z" fill="#E74C3C"/>
<circle cx="390" cy="100" r="6" fill="#4A90D9"/><text x="402" y="104" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目A 35%</text>
<circle cx="390" cy="130" r="6" fill="#27AE60"/><text x="402" y="134" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目B 25%</text>
<circle cx="390" cy="160" r="6" fill="#F39C12"/><text x="402" y="164" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目C 25%</text>
<circle cx="390" cy="190" r="6" fill="#E74C3C"/><text x="402" y="194" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目D 15%</text>
</svg>
</div>"""


def _html_area_chart():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">面积图标题</text>
<line x1="60" y1="260" x2="470" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<path d="M90,200 L172,140 L254,160 L336,90 L418,130 L418,260 L90,260 Z" fill="#4A90D9" opacity="0.25"/>
<polyline points="90,200 172,140 254,160 336,90 418,130" fill="none" stroke="#4A90D9" stroke-width="2.5" stroke-linecap="round"/>
<path d="M90,230 L172,190 L254,200 L336,155 L418,175 L418,260 L90,260 Z" fill="#27AE60" opacity="0.2"/>
<polyline points="90,230 172,190 254,200 336,155 418,175" fill="none" stroke="#27AE60" stroke-width="2" stroke-linecap="round"/>
<text x="90" y="278" text-anchor="middle" font-size="11" fill="#64748B">Q1</text>
<text x="172" y="278" text-anchor="middle" font-size="11" fill="#64748B">Q2</text>
<text x="254" y="278" text-anchor="middle" font-size="11" fill="#64748B">Q3</text>
<text x="336" y="278" text-anchor="middle" font-size="11" fill="#64748B">Q4</text>
<text x="418" y="278" text-anchor="middle" font-size="11" fill="#64748B">Q5</text>
</svg>
</div>"""


def _html_scatter_chart():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">散点图标题</text>
<line x1="60" y1="260" x2="470" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<circle cx="100" cy="200" r="6" fill="#4A90D9" opacity="0.75"/>
<circle cx="140" cy="170" r="6" fill="#4A90D9" opacity="0.75"/>
<circle cx="190" cy="180" r="6" fill="#4A90D9" opacity="0.75"/>
<circle cx="240" cy="130" r="6" fill="#4A90D9" opacity="0.75"/>
<circle cx="290" cy="110" r="6" fill="#4A90D9" opacity="0.75"/>
<circle cx="350" cy="140" r="6" fill="#4A90D9" opacity="0.75"/>
<circle cx="410" cy="80" r="6" fill="#4A90D9" opacity="0.75"/>
<circle cx="120" cy="220" r="5" fill="#E74C3C" opacity="0.65"/>
<circle cx="200" cy="155" r="5" fill="#E74C3C" opacity="0.65"/>
<circle cx="270" cy="145" r="5" fill="#E74C3C" opacity="0.65"/>
<circle cx="370" cy="105" r="5" fill="#E74C3C" opacity="0.65"/>
<line x1="80" y1="225" x2="440" y2="70" stroke="#94A3B8" stroke-width="1" stroke-dasharray="6,3"/>
<text x="250" y="290" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif">X 轴</text>
<text x="35" y="155" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif" transform="rotate(-90,35,155)">Y 轴</text>
</svg>
</div>"""


def _html_radar_chart():
    import math

    cx, cy, r = 250, 170, 100
    pts = []
    labels = ["指标A", "指标B", "指标C", "指标D", "指标E"]
    for i in range(5):
        angle = math.radians(-90 + i * 72)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    outline = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    ratios = [0.8, 0.6, 0.9, 0.5, 0.7]
    data_pts = []
    for i, ratio in enumerate(ratios):
        angle = math.radians(-90 + i * 72)
        data_pts.append((cx + r * ratio * math.cos(angle), cy + r * ratio * math.sin(angle)))
    data_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_pts)
    axes = ""
    label_els = ""
    for i, (x, y) in enumerate(pts):
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#CBD5E1" stroke-width="0.8"/>'
        lx = cx + (r + 18) * math.cos(math.radians(-90 + i * 72))
        ly = cy + (r + 18) * math.sin(math.radians(-90 + i * 72))
        label_els += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">{labels[i]}</text>'
    return f"""<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">雷达图标题</text>
{axes}
<polygon points="{outline}" fill="none" stroke="#CBD5E1" stroke-width="1"/>
<polygon points="{data_str}" fill="#4A90D9" fill-opacity="0.3" stroke="#4A90D9" stroke-width="2.5"/>
{label_els}
</svg>
</div>"""


def _html_horizontal_bar():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">条形图标题</text>
<line x1="100" y1="50" x2="100" y2="265" stroke="#CBD5E1" stroke-width="1"/>
<line x1="100" y1="265" x2="470" y2="265" stroke="#CBD5E1" stroke-width="1"/>
<text x="90" y="85" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目A</text>
<text x="90" y="135" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目B</text>
<text x="90" y="185" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目C</text>
<text x="90" y="235" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目D</text>
<rect x="100" y="65" width="280" height="30" rx="3" fill="#4A90D9"/>
<rect x="100" y="115" width="350" height="30" rx="3" fill="#27AE60"/>
<rect x="100" y="165" width="200" height="30" rx="3" fill="#F39C12"/>
<rect x="100" y="215" width="310" height="30" rx="3" fill="#E74C3C"/>
<text x="390" y="85" font-size="12" font-weight="bold" fill="#4A90D9">75</text>
<text x="460" y="135" font-size="12" font-weight="bold" fill="#27AE60">95</text>
<text x="310" y="185" font-size="12" font-weight="bold" fill="#F39C12">55</text>
<text x="420" y="235" font-size="12" font-weight="bold" fill="#E74C3C">82</text>
</svg>
</div>"""


def _html_stacked_bar():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">堆叠柱状图标题</text>
<line x1="60" y1="260" x2="470" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<rect x="90" y="160" width="65" height="100" rx="2" fill="#4A90D9"/>
<rect x="90" y="100" width="65" height="60" rx="2" fill="#27AE60"/>
<rect x="90" y="65" width="65" height="35" rx="2" fill="#F39C12"/>
<rect x="220" y="140" width="65" height="120" rx="2" fill="#4A90D9"/>
<rect x="220" y="80" width="65" height="60" rx="2" fill="#27AE60"/>
<rect x="220" y="55" width="65" height="25" rx="2" fill="#F39C12"/>
<rect x="350" y="150" width="65" height="110" rx="2" fill="#4A90D9"/>
<rect x="350" y="95" width="65" height="55" rx="2" fill="#27AE60"/>
<rect x="350" y="70" width="65" height="25" rx="2" fill="#F39C12"/>
<text x="122" y="278" text-anchor="middle" font-size="12" fill="#64748B" font-family="Microsoft YaHei,sans-serif">Q1</text>
<text x="252" y="278" text-anchor="middle" font-size="12" fill="#64748B" font-family="Microsoft YaHei,sans-serif">Q2</text>
<text x="382" y="278" text-anchor="middle" font-size="12" fill="#64748B" font-family="Microsoft YaHei,sans-serif">Q3</text>
<circle cx="380" cy="46" r="5" fill="#4A90D9"/><text x="390" y="50" font-size="10" fill="#334155">系列A</text>
<circle cx="420" cy="46" r="5" fill="#27AE60"/><text x="430" y="50" font-size="10" fill="#334155">系列B</text>
<circle cx="460" cy="46" r="5" fill="#F39C12"/><text x="470" y="50" font-size="10" fill="#334155">系列C</text>
</svg>
</div>"""


def _html_donut_chart():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">环形图标题</text>
<circle cx="210" cy="165" r="105" fill="#4A90D9"/>
<path d="M210,165 L210,60 A105,105 0 0,1 300,95 Z" fill="#27AE60"/>
<path d="M210,165 L300,95 A105,105 0 0,1 293,248 Z" fill="#F39C12"/>
<path d="M210,165 L293,248 A105,105 0 0,1 210,270 Z" fill="#E74C3C"/>
<circle cx="210" cy="165" r="55" fill="#FAFBFC"/>
<text x="210" y="160" text-anchor="middle" font-size="22" font-weight="bold" fill="#1E293B">65%</text>
<text x="210" y="180" text-anchor="middle" font-size="12" fill="#64748B" font-family="Microsoft YaHei,sans-serif">核心指标</text>
<circle cx="390" cy="110" r="6" fill="#4A90D9"/><text x="402" y="114" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目A 35%</text>
<circle cx="390" cy="140" r="6" fill="#27AE60"/><text x="402" y="144" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目B 25%</text>
<circle cx="390" cy="170" r="6" fill="#F39C12"/><text x="402" y="174" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目C 25%</text>
<circle cx="390" cy="200" r="6" fill="#E74C3C"/><text x="402" y="204" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目D 15%</text>
</svg>
</div>"""


# ------------------------------------------------------------------
# Additional chart types
# ------------------------------------------------------------------


def _svg_grouped_bar():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="150" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="15" x2="25" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<rect x="32" y="55" width="12" height="45" rx="1" fill="#4A90D9"/>'
        b'<rect x="46" y="40" width="12" height="60" rx="1" fill="#27AE60"/>'
        b'<rect x="70" y="35" width="12" height="65" rx="1" fill="#4A90D9"/>'
        b'<rect x="84" y="50" width="12" height="50" rx="1" fill="#27AE60"/>'
        b'<rect x="108" y="25" width="12" height="75" rx="1" fill="#4A90D9"/>'
        b'<rect x="122" y="45" width="12" height="55" rx="1" fill="#27AE60"/>'
        b"</svg>"
    )


def _html_grouped_bar():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">分组柱状图标题</text>
<line x1="60" y1="260" x2="470" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<rect x="80" y="150" width="35" height="110" rx="2" fill="#4A90D9"/>
<rect x="118" y="120" width="35" height="140" rx="2" fill="#27AE60"/>
<rect x="200" y="100" width="35" height="160" rx="2" fill="#4A90D9"/>
<rect x="238" y="140" width="35" height="120" rx="2" fill="#27AE60"/>
<rect x="320" y="80" width="35" height="180" rx="2" fill="#4A90D9"/>
<rect x="358" y="130" width="35" height="130" rx="2" fill="#27AE60"/>
<text x="117" y="278" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif">组别 A</text>
<text x="237" y="278" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif">组别 B</text>
<text x="357" y="278" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif">组别 C</text>
<circle cx="400" cy="46" r="5" fill="#4A90D9"/><text x="410" y="50" font-size="10" fill="#334155">系列 1</text>
<circle cx="440" cy="46" r="5" fill="#27AE60"/><text x="450" y="50" font-size="10" fill="#334155">系列 2</text>
</svg>
</div>"""


def _svg_bubble():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="150" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="15" x2="25" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<circle cx="50" cy="70" r="12" fill="#4A90D9" opacity="0.55"/>'
        b'<circle cx="80" cy="45" r="18" fill="#27AE60" opacity="0.5"/>'
        b'<circle cx="115" cy="55" r="10" fill="#F39C12" opacity="0.6"/>'
        b'<circle cx="135" cy="30" r="14" fill="#E74C3C" opacity="0.5"/>'
        b'<circle cx="60" cy="88" r="8" fill="#9B59B6" opacity="0.55"/>'
        b"</svg>"
    )


def _html_bubble():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">气泡图标题</text>
<line x1="60" y1="260" x2="470" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<circle cx="130" cy="180" r="30" fill="#4A90D9" opacity="0.5"/>
<circle cx="220" cy="120" r="45" fill="#27AE60" opacity="0.45"/>
<circle cx="320" cy="150" r="25" fill="#F39C12" opacity="0.55"/>
<circle cx="400" cy="90" r="35" fill="#E74C3C" opacity="0.45"/>
<circle cx="150" cy="230" r="18" fill="#9B59B6" opacity="0.5"/>
<circle cx="350" cy="210" r="22" fill="#1ABC9C" opacity="0.5"/>
<text x="250" y="290" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif">X 轴</text>
<text x="35" y="155" text-anchor="middle" font-size="11" fill="#64748B" font-family="Microsoft YaHei,sans-serif" transform="rotate(-90,35,155)">Y 轴</text>
</svg>
</div>"""


def _svg_funnel():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<polygon points="20,20 140,20 125,42 35,42" fill="#4A90D9"/>'
        b'<polygon points="35,44 125,44 115,66 45,66" fill="#27AE60"/>'
        b'<polygon points="45,68 115,68 105,90 55,90" fill="#F39C12"/>'
        b'<polygon points="55,92 105,92 95,110 65,110" fill="#E74C3C"/>'
        b"</svg>"
    )


def _html_funnel():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">漏斗图标题</text>
<polygon points="50,50 450,50 410,105 90,105" fill="#4A90D9"/>
<text x="250" y="84" text-anchor="middle" font-size="13" fill="white" font-weight="bold">访问 1000</text>
<polygon points="90,110 410,110 380,165 120,165" fill="#27AE60"/>
<text x="250" y="144" text-anchor="middle" font-size="13" fill="white" font-weight="bold">注册 650</text>
<polygon points="120,170 380,170 350,225 150,225" fill="#F39C12"/>
<text x="250" y="204" text-anchor="middle" font-size="13" fill="white" font-weight="bold">活跃 380</text>
<polygon points="150,230 350,230 320,280 180,280" fill="#E74C3C"/>
<text x="250" y="262" text-anchor="middle" font-size="13" fill="white" font-weight="bold">付费 120</text>
</svg>
</div>"""


def _svg_gauge():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<path d="M30,85 A50,50 0 0,1 130,85" fill="none" stroke="#E2E8F0" stroke-width="12" stroke-linecap="round"/>'
        b'<path d="M30,85 A50,50 0 0,1 110,45" fill="none" stroke="#4A90D9" stroke-width="12" stroke-linecap="round"/>'
        b'<text x="80" y="80" text-anchor="middle" font-size="18" font-weight="bold" fill="#1E293B">75</text>'
        b'<text x="80" y="95" text-anchor="middle" font-size="9" fill="#94A3B8">%</text>'
        b"</svg>"
    )


def _html_gauge():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">仪表盘标题</text>
<path d="M100,230 A150,150 0 0,1 400,230" fill="none" stroke="#E2E8F0" stroke-width="28" stroke-linecap="round"/>
<path d="M100,230 A150,150 0 0,1 370,110" fill="none" stroke="#4A90D9" stroke-width="28" stroke-linecap="round"/>
<text x="250" y="200" text-anchor="middle" font-size="48" font-weight="bold" fill="#1E293B">75</text>
<text x="250" y="230" text-anchor="middle" font-size="16" fill="#64748B" font-family="Microsoft YaHei,sans-serif">完成率 %</text>
<text x="110" y="260" text-anchor="middle" font-size="11" fill="#94A3B8">0</text>
<text x="250" y="80" text-anchor="middle" font-size="11" fill="#94A3B8">50</text>
<text x="390" y="260" text-anchor="middle" font-size="11" fill="#94A3B8">100</text>
</svg>
</div>"""


def _svg_waterfall():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="150" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<rect x="30" y="30" width="16" height="70" rx="1" fill="#4A90D9"/>'
        b'<rect x="52" y="30" width="16" height="25" rx="1" fill="#27AE60"/>'
        b'<rect x="74" y="55" width="16" height="20" rx="1" fill="#E74C3C"/>'
        b'<rect x="96" y="40" width="16" height="35" rx="1" fill="#27AE60"/>'
        b'<rect x="118" y="30" width="16" height="70" rx="1" fill="#9B59B6"/>'
        b'<line x1="46" y1="30" x2="52" y2="30" stroke="#94A3B8" stroke-width="0.8" stroke-dasharray="2,1"/>'
        b'<line x1="68" y1="55" x2="74" y2="55" stroke="#94A3B8" stroke-width="0.8" stroke-dasharray="2,1"/>'
        b'<line x1="90" y1="75" x2="96" y2="75" stroke="#94A3B8" stroke-width="0.8" stroke-dasharray="2,1"/>'
        b'<line x1="112" y1="40" x2="118" y2="40" stroke="#94A3B8" stroke-width="0.8" stroke-dasharray="2,1"/>'
        b"</svg>"
    )


def _html_waterfall():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">瀑布图标题</text>
<line x1="60" y1="260" x2="470" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<rect x="80" y="80" width="50" height="180" rx="2" fill="#4A90D9"/>
<text x="105" y="75" text-anchor="middle" font-size="11" fill="#4A90D9" font-weight="bold">100</text>
<rect x="155" y="80" width="50" height="60" rx="2" fill="#27AE60"/>
<text x="180" y="75" text-anchor="middle" font-size="11" fill="#27AE60" font-weight="bold">+30</text>
<line x1="130" y1="80" x2="155" y2="80" stroke="#94A3B8" stroke-width="1" stroke-dasharray="3,2"/>
<rect x="230" y="140" width="50" height="40" rx="2" fill="#E74C3C"/>
<text x="255" y="135" text-anchor="middle" font-size="11" fill="#E74C3C" font-weight="bold">-20</text>
<line x1="205" y1="140" x2="230" y2="140" stroke="#94A3B8" stroke-width="1" stroke-dasharray="3,2"/>
<rect x="305" y="100" width="50" height="80" rx="2" fill="#27AE60"/>
<text x="330" y="95" text-anchor="middle" font-size="11" fill="#27AE60" font-weight="bold">+40</text>
<line x1="280" y1="180" x2="305" y2="180" stroke="#94A3B8" stroke-width="1" stroke-dasharray="3,2"/>
<rect x="380" y="100" width="50" height="160" rx="2" fill="#9B59B6"/>
<text x="405" y="95" text-anchor="middle" font-size="11" fill="#9B59B6" font-weight="bold">150</text>
<text x="105" y="278" text-anchor="middle" font-size="10" fill="#64748B">起始</text>
<text x="180" y="278" text-anchor="middle" font-size="10" fill="#64748B">增加</text>
<text x="255" y="278" text-anchor="middle" font-size="10" fill="#64748B">减少</text>
<text x="330" y="278" text-anchor="middle" font-size="10" fill="#64748B">增加</text>
<text x="405" y="278" text-anchor="middle" font-size="10" fill="#64748B">合计</text>
</svg>
</div>"""


def _svg_progress():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<rect x="15" y="25" width="130" height="12" rx="6" fill="#E2E8F0"/>'
        b'<rect x="15" y="25" width="100" height="12" rx="6" fill="#4A90D9"/>'
        b'<rect x="15" y="48" width="130" height="12" rx="6" fill="#E2E8F0"/>'
        b'<rect x="15" y="48" width="80" height="12" rx="6" fill="#27AE60"/>'
        b'<rect x="15" y="71" width="130" height="12" rx="6" fill="#E2E8F0"/>'
        b'<rect x="15" y="71" width="110" height="12" rx="6" fill="#F39C12"/>'
        b'<rect x="15" y="94" width="130" height="12" rx="6" fill="#E2E8F0"/>'
        b'<rect x="15" y="94" width="55" height="12" rx="6" fill="#E74C3C"/>'
        b"</svg>"
    )


def _html_progress():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 220" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="220" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">进度条标题</text>
<text x="60" y="62" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">项目 A</text>
<rect x="130" y="50" width="300" height="18" rx="9" fill="#E2E8F0"/>
<rect x="130" y="50" width="230" height="18" rx="9" fill="#4A90D9"/>
<text x="445" y="63" font-size="12" font-weight="bold" fill="#4A90D9">77%</text>
<text x="60" y="102" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">项目 B</text>
<rect x="130" y="90" width="300" height="18" rx="9" fill="#E2E8F0"/>
<rect x="130" y="90" width="185" height="18" rx="9" fill="#27AE60"/>
<text x="445" y="103" font-size="12" font-weight="bold" fill="#27AE60">62%</text>
<text x="60" y="142" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">项目 C</text>
<rect x="130" y="130" width="300" height="18" rx="9" fill="#E2E8F0"/>
<rect x="130" y="130" width="270" height="18" rx="9" fill="#F39C12"/>
<text x="445" y="143" font-size="12" font-weight="bold" fill="#F39C12">90%</text>
<text x="60" y="182" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">项目 D</text>
<rect x="130" y="170" width="300" height="18" rx="9" fill="#E2E8F0"/>
<rect x="130" y="170" width="126" height="18" rx="9" fill="#E74C3C"/>
<text x="445" y="183" font-size="12" font-weight="bold" fill="#E74C3C">42%</text>
</svg>
</div>"""


# ------------------------------------------------------------------
# Additional chart types (batch 2)
# ------------------------------------------------------------------


def _svg_heatmap():
    colors = [
        "#DBEAFE",
        "#93C5FD",
        "#60A5FA",
        "#3B82F6",
        "#2563EB",
        "#1D4ED8",
        "#60A5FA",
        "#93C5FD",
        "#DBEAFE",
        "#3B82F6",
        "#1D4ED8",
        "#2563EB",
        "#93C5FD",
        "#DBEAFE",
        "#60A5FA",
        "#1D4ED8",
        "#3B82F6",
        "#60A5FA",
        "#DBEAFE",
        "#60A5FA",
        "#2563EB",
        "#93C5FD",
        "#3B82F6",
        "#1D4ED8",
        "#3B82F6",
        "#1D4ED8",
        "#93C5FD",
        "#60A5FA",
        "#DBEAFE",
        "#2563EB",
    ]
    cells = []
    idx = 0
    for r in range(5):
        for c in range(6):
            x = 25 + c * 21
            y = 15 + r * 18
            cells.append(
                f'<rect x="{x}" y="{y}" width="19" height="16" rx="2" fill="{colors[idx]}"/>'.encode()
            )
            idx += 1
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        + b"".join(cells)
        + b"</svg>"
    )


def _html_heatmap():
    colors_data = [
        ["#DBEAFE", "#93C5FD", "#60A5FA", "#3B82F6", "#2563EB"],
        ["#60A5FA", "#3B82F6", "#1D4ED8", "#2563EB", "#93C5FD"],
        ["#93C5FD", "#DBEAFE", "#60A5FA", "#1D4ED8", "#3B82F6"],
        ["#3B82F6", "#1D4ED8", "#93C5FD", "#60A5FA", "#DBEAFE"],
        ["#DBEAFE", "#60A5FA", "#2563EB", "#3B82F6", "#1D4ED8"],
    ]
    vals = [
        [12, 35, 58, 76, 92],
        [55, 72, 95, 88, 40],
        [38, 15, 60, 90, 70],
        [68, 92, 42, 56, 18],
        [14, 55, 85, 65, 96],
    ]
    rows = ["指标A", "指标B", "指标C", "指标D", "指标E"]
    cols = ["维度1", "维度2", "维度3", "维度4", "维度5"]
    cells = ""
    for r in range(5):
        for c in range(5):
            x = 110 + c * 68
            y = 58 + r * 42
            cells += (
                f'<rect x="{x}" y="{y}" width="64" height="38" rx="4" fill="{colors_data[r][c]}"/>'
            )
            tx = "#fff" if colors_data[r][c] in ("#1D4ED8", "#2563EB", "#3B82F6") else "#1E293B"
            cells += f'<text x="{x+32}" y="{y+23}" text-anchor="middle" font-size="12" fill="{tx}">{vals[r][c]}</text>'
    row_labels = ""
    for i, lb in enumerate(rows):
        row_labels += f'<text x="100" y="{82+i*42}" text-anchor="end" font-size="11" fill="#334155" font-family="Microsoft YaHei,sans-serif">{lb}</text>'
    col_labels = ""
    for i, lb in enumerate(cols):
        col_labels += f'<text x="{142+i*68}" y="52" text-anchor="middle" font-size="11" fill="#334155" font-family="Microsoft YaHei,sans-serif">{lb}</text>'
    return f"""<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">热力图标题</text>
{col_labels}{row_labels}{cells}
</svg>
</div>"""


def _svg_gantt():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="40" y1="15" x2="40" y2="105" stroke="#CBD5E1" stroke-width="0.5"/>'
        b'<line x1="70" y1="15" x2="70" y2="105" stroke="#CBD5E1" stroke-width="0.5"/>'
        b'<line x1="100" y1="15" x2="100" y2="105" stroke="#CBD5E1" stroke-width="0.5"/>'
        b'<line x1="130" y1="15" x2="130" y2="105" stroke="#CBD5E1" stroke-width="0.5"/>'
        b'<rect x="30" y="22" width="55" height="12" rx="6" fill="#4A90D9"/>'
        b'<rect x="50" y="42" width="40" height="12" rx="6" fill="#27AE60"/>'
        b'<rect x="75" y="62" width="50" height="12" rx="6" fill="#F39C12"/>'
        b'<rect x="100" y="82" width="45" height="12" rx="6" fill="#E74C3C"/>'
        b"</svg>"
    )


def _html_gantt():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 280" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="280" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">甘特图标题</text>
<line x1="120" y1="40" x2="120" y2="255" stroke="#CBD5E1" stroke-width="0.5"/>
<line x1="195" y1="40" x2="195" y2="255" stroke="#E2E8F0" stroke-width="0.5"/>
<line x1="270" y1="40" x2="270" y2="255" stroke="#E2E8F0" stroke-width="0.5"/>
<line x1="345" y1="40" x2="345" y2="255" stroke="#E2E8F0" stroke-width="0.5"/>
<line x1="420" y1="40" x2="420" y2="255" stroke="#E2E8F0" stroke-width="0.5"/>
<text x="157" y="52" text-anchor="middle" font-size="10" fill="#94A3B8">1月</text>
<text x="232" y="52" text-anchor="middle" font-size="10" fill="#94A3B8">2月</text>
<text x="307" y="52" text-anchor="middle" font-size="10" fill="#94A3B8">3月</text>
<text x="382" y="52" text-anchor="middle" font-size="10" fill="#94A3B8">4月</text>
<text x="457" y="52" text-anchor="middle" font-size="10" fill="#94A3B8">5月</text>
<text x="110" y="82" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">需求分析</text>
<rect x="120" y="68" width="130" height="22" rx="11" fill="#4A90D9"/>
<text x="110" y="122" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">系统设计</text>
<rect x="175" y="108" width="110" height="22" rx="11" fill="#27AE60"/>
<text x="110" y="162" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">开发实现</text>
<rect x="250" y="148" width="150" height="22" rx="11" fill="#F39C12"/>
<text x="110" y="202" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">测试验收</text>
<rect x="340" y="188" width="100" height="22" rx="11" fill="#E74C3C"/>
<text x="110" y="242" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">上线部署</text>
<rect x="400" y="228" width="70" height="22" rx="11" fill="#9B59B6"/>
</svg>
</div>"""


def _svg_boxplot():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="150" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="15" x2="25" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        # box 1
        b'<line x1="50" y1="25" x2="50" y2="38" stroke="#4A90D9" stroke-width="1.5"/>'
        b'<rect x="38" y="38" width="24" height="35" rx="2" fill="#4A90D9" opacity="0.3" stroke="#4A90D9" stroke-width="1.5"/>'
        b'<line x1="38" y1="52" x2="62" y2="52" stroke="#4A90D9" stroke-width="2"/>'
        b'<line x1="50" y1="73" x2="50" y2="88" stroke="#4A90D9" stroke-width="1.5"/>'
        # box 2
        b'<line x1="95" y1="32" x2="95" y2="45" stroke="#27AE60" stroke-width="1.5"/>'
        b'<rect x="83" y="45" width="24" height="30" rx="2" fill="#27AE60" opacity="0.3" stroke="#27AE60" stroke-width="1.5"/>'
        b'<line x1="83" y1="58" x2="107" y2="58" stroke="#27AE60" stroke-width="2"/>'
        b'<line x1="95" y1="75" x2="95" y2="92" stroke="#27AE60" stroke-width="1.5"/>'
        # box 3
        b'<line x1="135" y1="20" x2="135" y2="35" stroke="#F39C12" stroke-width="1.5"/>'
        b'<rect x="123" y="35" width="24" height="40" rx="2" fill="#F39C12" opacity="0.3" stroke="#F39C12" stroke-width="1.5"/>'
        b'<line x1="123" y1="50" x2="147" y2="50" stroke="#F39C12" stroke-width="2"/>'
        b'<line x1="135" y1="75" x2="135" y2="95" stroke="#F39C12" stroke-width="1.5"/>'
        b"</svg>"
    )


def _html_boxplot():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">箱线图标题</text>
<line x1="60" y1="260" x2="470" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="50" x2="60" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="60" y1="155" x2="470" y2="155" stroke="#F1F5F9" stroke-width="0.5"/>
<line x1="60" y1="102" x2="470" y2="102" stroke="#F1F5F9" stroke-width="0.5"/>
<line x1="60" y1="207" x2="470" y2="207" stroke="#F1F5F9" stroke-width="0.5"/>
<line x1="130" y1="75" x2="130" y2="105" stroke="#4A90D9" stroke-width="2"/>
<rect x="100" y="105" width="60" height="85" rx="4" fill="#4A90D9" opacity="0.2" stroke="#4A90D9" stroke-width="2"/>
<line x1="100" y1="145" x2="160" y2="145" stroke="#4A90D9" stroke-width="3"/>
<line x1="130" y1="190" x2="130" y2="230" stroke="#4A90D9" stroke-width="2"/>
<line x1="115" y1="75" x2="145" y2="75" stroke="#4A90D9" stroke-width="2"/>
<line x1="115" y1="230" x2="145" y2="230" stroke="#4A90D9" stroke-width="2"/>
<line x1="265" y1="85" x2="265" y2="115" stroke="#27AE60" stroke-width="2"/>
<rect x="235" y="115" width="60" height="75" rx="4" fill="#27AE60" opacity="0.2" stroke="#27AE60" stroke-width="2"/>
<line x1="235" y1="150" x2="295" y2="150" stroke="#27AE60" stroke-width="3"/>
<line x1="265" y1="190" x2="265" y2="240" stroke="#27AE60" stroke-width="2"/>
<line x1="250" y1="85" x2="280" y2="85" stroke="#27AE60" stroke-width="2"/>
<line x1="250" y1="240" x2="280" y2="240" stroke="#27AE60" stroke-width="2"/>
<line x1="400" y1="65" x2="400" y2="95" stroke="#F39C12" stroke-width="2"/>
<rect x="370" y="95" width="60" height="95" rx="4" fill="#F39C12" opacity="0.2" stroke="#F39C12" stroke-width="2"/>
<line x1="370" y1="135" x2="430" y2="135" stroke="#F39C12" stroke-width="3"/>
<line x1="400" y1="190" x2="400" y2="245" stroke="#F39C12" stroke-width="2"/>
<line x1="385" y1="65" x2="415" y2="65" stroke="#F39C12" stroke-width="2"/>
<line x1="385" y1="245" x2="415" y2="245" stroke="#F39C12" stroke-width="2"/>
<text x="130" y="278" text-anchor="middle" font-size="12" fill="#64748B" font-family="Microsoft YaHei,sans-serif">组别 A</text>
<text x="265" y="278" text-anchor="middle" font-size="12" fill="#64748B" font-family="Microsoft YaHei,sans-serif">组别 B</text>
<text x="400" y="278" text-anchor="middle" font-size="12" fill="#64748B" font-family="Microsoft YaHei,sans-serif">组别 C</text>
</svg>
</div>"""


def _svg_dual_axis():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="25" y1="100" x2="140" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="25" y1="15" x2="25" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<line x1="140" y1="15" x2="140" y2="100" stroke="#CBD5E1" stroke-width="1"/>'
        b'<rect x="35" y="55" width="16" height="45" rx="1" fill="#4A90D9" opacity="0.6"/>'
        b'<rect x="60" y="35" width="16" height="65" rx="1" fill="#4A90D9" opacity="0.6"/>'
        b'<rect x="85" y="45" width="16" height="55" rx="1" fill="#4A90D9" opacity="0.6"/>'
        b'<rect x="110" y="28" width="16" height="72" rx="1" fill="#4A90D9" opacity="0.6"/>'
        b'<polyline points="43,60 68,38 93,48 118,30" fill="none" stroke="#E74C3C" stroke-width="2.5" stroke-linecap="round"/>'
        b'<circle cx="43" cy="60" r="3" fill="#E74C3C"/>'
        b'<circle cx="68" cy="38" r="3" fill="#E74C3C"/>'
        b'<circle cx="93" cy="48" r="3" fill="#E74C3C"/>'
        b'<circle cx="118" cy="30" r="3" fill="#E74C3C"/>'
        b"</svg>"
    )


def _html_dual_axis():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">双轴图标题</text>
<line x1="65" y1="260" x2="435" y2="260" stroke="#CBD5E1" stroke-width="1"/>
<line x1="65" y1="50" x2="65" y2="260" stroke="#4A90D9" stroke-width="1"/>
<line x1="435" y1="50" x2="435" y2="260" stroke="#E74C3C" stroke-width="1"/>
<text x="55" y="265" text-anchor="end" font-size="10" fill="#4A90D9">0</text>
<text x="55" y="155" text-anchor="end" font-size="10" fill="#4A90D9">50</text>
<text x="55" y="55" text-anchor="end" font-size="10" fill="#4A90D9">100</text>
<text x="445" y="265" font-size="10" fill="#E74C3C">0%</text>
<text x="445" y="155" font-size="10" fill="#E74C3C">50%</text>
<text x="445" y="55" font-size="10" fill="#E74C3C">100%</text>
<rect x="90" y="150" width="50" height="110" rx="3" fill="#4A90D9" opacity="0.55"/>
<rect x="175" y="100" width="50" height="160" rx="3" fill="#4A90D9" opacity="0.55"/>
<rect x="260" y="120" width="50" height="140" rx="3" fill="#4A90D9" opacity="0.55"/>
<rect x="345" y="80" width="50" height="180" rx="3" fill="#4A90D9" opacity="0.55"/>
<polyline points="115,165 200,110 285,130 370,85" fill="none" stroke="#E74C3C" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="115" cy="165" r="5" fill="#fff" stroke="#E74C3C" stroke-width="2.5"/>
<circle cx="200" cy="110" r="5" fill="#fff" stroke="#E74C3C" stroke-width="2.5"/>
<circle cx="285" cy="130" r="5" fill="#fff" stroke="#E74C3C" stroke-width="2.5"/>
<circle cx="370" cy="85" r="5" fill="#fff" stroke="#E74C3C" stroke-width="2.5"/>
<text x="115" y="278" text-anchor="middle" font-size="11" fill="#64748B">Q1</text>
<text x="200" y="278" text-anchor="middle" font-size="11" fill="#64748B">Q2</text>
<text x="285" y="278" text-anchor="middle" font-size="11" fill="#64748B">Q3</text>
<text x="370" y="278" text-anchor="middle" font-size="11" fill="#64748B">Q4</text>
<rect x="140" y="42" width="10" height="10" rx="2" fill="#4A90D9" opacity="0.55"/><text x="155" y="51" font-size="10" fill="#334155">销售额</text>
<line x1="220" y1="47" x2="240" y2="47" stroke="#E74C3C" stroke-width="2.5"/><text x="245" y="51" font-size="10" fill="#334155">增长率</text>
</svg>
</div>"""


def _svg_diverging():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<line x1="80" y1="15" x2="80" y2="105" stroke="#CBD5E1" stroke-width="1"/>'
        b'<rect x="35" y="20" width="45" height="14" rx="2" fill="#E74C3C"/>'
        b'<rect x="80" y="20" width="55" height="14" rx="2" fill="#4A90D9"/>'
        b'<rect x="50" y="42" width="30" height="14" rx="2" fill="#E74C3C"/>'
        b'<rect x="80" y="42" width="40" height="14" rx="2" fill="#4A90D9"/>'
        b'<rect x="25" y="64" width="55" height="14" rx="2" fill="#E74C3C"/>'
        b'<rect x="80" y="64" width="30" height="14" rx="2" fill="#4A90D9"/>'
        b'<rect x="60" y="86" width="20" height="14" rx="2" fill="#E74C3C"/>'
        b'<rect x="80" y="86" width="65" height="14" rx="2" fill="#4A90D9"/>'
        b"</svg>"
    )


def _html_diverging():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">对比柱状图标题</text>
<line x1="250" y1="45" x2="250" y2="265" stroke="#CBD5E1" stroke-width="1"/>
<text x="250" y="285" text-anchor="middle" font-size="10" fill="#94A3B8">0</text>
<text x="130" y="285" text-anchor="middle" font-size="10" fill="#E74C3C">← 反对</text>
<text x="370" y="285" text-anchor="middle" font-size="10" fill="#4A90D9">赞同 →</text>
<text x="58" y="78" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目 A</text>
<rect x="130" y="62" width="120" height="26" rx="4" fill="#E74C3C" opacity="0.8"/>
<rect x="250" y="62" width="155" height="26" rx="4" fill="#4A90D9" opacity="0.8"/>
<text x="185" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">32%</text>
<text x="322" y="80" text-anchor="middle" font-size="11" fill="white" font-weight="bold">68%</text>
<text x="58" y="128" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目 B</text>
<rect x="165" y="112" width="85" height="26" rx="4" fill="#E74C3C" opacity="0.8"/>
<rect x="250" y="112" width="115" height="26" rx="4" fill="#4A90D9" opacity="0.8"/>
<text x="205" y="130" text-anchor="middle" font-size="11" fill="white" font-weight="bold">23%</text>
<text x="305" y="130" text-anchor="middle" font-size="11" fill="white" font-weight="bold">45%</text>
<text x="58" y="178" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目 C</text>
<rect x="100" y="162" width="150" height="26" rx="4" fill="#E74C3C" opacity="0.8"/>
<rect x="250" y="162" width="80" height="26" rx="4" fill="#4A90D9" opacity="0.8"/>
<text x="170" y="180" text-anchor="middle" font-size="11" fill="white" font-weight="bold">55%</text>
<text x="288" y="180" text-anchor="middle" font-size="11" fill="white" font-weight="bold">28%</text>
<text x="58" y="228" text-anchor="end" font-size="12" fill="#334155" font-family="Microsoft YaHei,sans-serif">类目 D</text>
<rect x="195" y="212" width="55" height="26" rx="4" fill="#E74C3C" opacity="0.8"/>
<rect x="250" y="212" width="175" height="26" rx="4" fill="#4A90D9" opacity="0.8"/>
<text x="220" y="230" text-anchor="middle" font-size="11" fill="white" font-weight="bold">15%</text>
<text x="335" y="230" text-anchor="middle" font-size="11" fill="white" font-weight="bold">85%</text>
</svg>
</div>"""


def _svg_treemap():
    return (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">'
        b'<rect x="0" y="0" width="160" height="120" rx="6" fill="#F8FAFC"/>'
        b'<rect x="8" y="10" width="80" height="62" rx="3" fill="#4A90D9"/>'
        b'<rect x="92" y="10" width="60" height="35" rx="3" fill="#27AE60"/>'
        b'<rect x="92" y="49" width="60" height="23" rx="3" fill="#F39C12"/>'
        b'<rect x="8" y="76" width="50" height="35" rx="3" fill="#E74C3C"/>'
        b'<rect x="62" y="76" width="45" height="35" rx="3" fill="#9B59B6"/>'
        b'<rect x="111" y="76" width="41" height="35" rx="3" fill="#1ABC9C"/>'
        b"</svg>"
    )


def _html_treemap():
    return """<div class="chart-container" style="text-align:center;margin:16px 0;page-break-inside:avoid;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 300" style="max-width:480px;width:100%;height:auto;">
<rect x="0" y="0" width="500" height="300" rx="8" fill="#FAFBFC" stroke="#E2E8F0" stroke-width="1"/>
<text x="250" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1E293B" font-family="Microsoft YaHei,sans-serif">矩形树图标题</text>
<rect x="15" y="42" width="240" height="150" rx="6" fill="#4A90D9"/>
<text x="135" y="110" text-anchor="middle" font-size="18" font-weight="bold" fill="white">类目 A</text>
<text x="135" y="130" text-anchor="middle" font-size="13" fill="rgba(255,255,255,0.8)">35%</text>
<rect x="260" y="42" width="225" height="85" rx="6" fill="#27AE60"/>
<text x="372" y="82" text-anchor="middle" font-size="16" font-weight="bold" fill="white">类目 B</text>
<text x="372" y="100" text-anchor="middle" font-size="12" fill="rgba(255,255,255,0.8)">25%</text>
<rect x="260" y="132" width="225" height="60" rx="6" fill="#F39C12"/>
<text x="372" y="168" text-anchor="middle" font-size="14" font-weight="bold" fill="white">类目 C  18%</text>
<rect x="15" y="197" width="155" height="90" rx="6" fill="#E74C3C"/>
<text x="92" y="245" text-anchor="middle" font-size="14" font-weight="bold" fill="white">类目 D  12%</text>
<rect x="175" y="197" width="150" height="90" rx="6" fill="#9B59B6"/>
<text x="250" y="245" text-anchor="middle" font-size="13" font-weight="bold" fill="white">类目 E  7%</text>
<rect x="330" y="197" width="155" height="90" rx="6" fill="#1ABC9C"/>
<text x="407" y="245" text-anchor="middle" font-size="13" font-weight="bold" fill="white">类目 F  3%</text>
</svg>
</div>"""


# ------------------------------------------------------------------
# Register all charts
# ------------------------------------------------------------------

_register(
    "bar",
    "柱状图",
    "适合对比不同类目的数值",
    _svg_bar_chart,
    _html_bar_chart,
    {
        "title": "柱状图标题",
        "labels": ["类目A", "类目B", "类目C", "类目D"],
        "series": [{"name": "系列1", "values": [50, 76, 62, 88]}],
    },
)
_register(
    "grouped",
    "分组柱状图",
    "多系列并排对比",
    _svg_grouped_bar,
    _html_grouped_bar,
    {
        "title": "分组柱状图标题",
        "labels": ["组别A", "组别B", "组别C"],
        "series": [
            {"name": "系列1", "values": [52, 76, 86]},
            {"name": "系列2", "values": [67, 57, 62]},
        ],
    },
)
_register(
    "stacked",
    "堆叠柱状图",
    "展示各部分的组成占比",
    _svg_stacked_bar,
    _html_stacked_bar,
    {
        "title": "堆叠柱状图标题",
        "labels": ["Q1", "Q2", "Q3"],
        "series": [
            {"name": "系列A", "values": [48, 57, 52]},
            {"name": "系列B", "values": [29, 29, 26]},
            {"name": "系列C", "values": [17, 12, 12]},
        ],
    },
)
_register(
    "h_bar",
    "条形图",
    "横向柱状图，适合长标签",
    _svg_horizontal_bar,
    _html_horizontal_bar,
    {
        "title": "条形图标题",
        "labels": ["类目A", "类目B", "类目C", "类目D"],
        "series": [{"name": "系列1", "values": [75, 95, 55, 82]}],
    },
)
_register(
    "line",
    "折线图",
    "适合展示趋势变化",
    _svg_line_chart,
    _html_line_chart,
    {
        "title": "折线图标题",
        "labels": ["1月", "2月", "3月", "4月", "5月"],
        "series": [
            {"name": "系列1", "values": [33, 62, 50, 83, 67]},
            {"name": "系列2", "values": [19, 38, 31, 52, 43]},
        ],
    },
)
_register(
    "area",
    "面积图",
    "折线图+面积填充，强调趋势量感",
    _svg_area_chart,
    _html_area_chart,
    {
        "title": "面积图标题",
        "labels": ["Q1", "Q2", "Q3", "Q4", "Q5"],
        "series": [
            {"name": "系列1", "values": [29, 57, 48, 81, 62]},
            {"name": "系列2", "values": [14, 33, 29, 50, 40]},
        ],
    },
)
_register(
    "pie",
    "饼图",
    "适合展示占比分布",
    _svg_pie_chart,
    _html_pie_chart,
    {
        "title": "饼图标题",
        "labels": ["类目A", "类目B", "类目C", "类目D"],
        "series": [{"name": "占比", "values": [35, 25, 25, 15]}],
    },
)
_register(
    "donut",
    "环形图",
    "饼图变体，突出核心指标",
    _svg_donut_chart,
    _html_donut_chart,
    {
        "title": "环形图标题",
        "labels": ["类目A", "类目B", "类目C", "类目D"],
        "series": [{"name": "占比", "values": [35, 25, 25, 15]}],
        "centerText": "65%",
        "centerLabel": "核心指标",
    },
)
_register(
    "scatter",
    "散点图",
    "适合展示两变量相关性",
    _svg_scatter_chart,
    _html_scatter_chart,
    {
        "title": "散点图标题",
        "xLabel": "X 轴",
        "yLabel": "Y 轴",
        "labels": ["A", "B", "C", "D", "E", "F", "G"],
        "series": [
            {"name": "系列1", "values": [30, 55, 45, 75, 85, 60, 95]},
            {"name": "系列2", "values": [20, 50, 48, 65, 70, 55, 80]},
        ],
    },
)
_register(
    "bubble",
    "气泡图",
    "散点图变体，第三维用圆大小表示",
    _svg_bubble,
    _html_bubble,
    {
        "title": "气泡图标题",
        "xLabel": "X 轴",
        "yLabel": "Y 轴",
        "labels": ["A", "B", "C", "D", "E", "F"],
        "series": [
            {"name": "数值", "values": [38, 70, 50, 82, 20, 45]},
            {"name": "大小", "values": [30, 45, 25, 35, 18, 22]},
        ],
    },
)
_register(
    "radar",
    "雷达图",
    "多维度综合能力评估",
    _svg_radar_chart,
    _html_radar_chart,
    {
        "title": "雷达图标题",
        "labels": ["指标A", "指标B", "指标C", "指标D", "指标E"],
        "series": [{"name": "系列1", "values": [80, 60, 90, 50, 70]}],
    },
)
_register(
    "funnel",
    "漏斗图",
    "展示转化率和流失过程",
    _svg_funnel,
    _html_funnel,
    {
        "title": "漏斗图标题",
        "labels": ["访问", "注册", "活跃", "付费"],
        "series": [{"name": "数量", "values": [1000, 650, 380, 120]}],
    },
)
_register(
    "gauge",
    "仪表盘",
    "单一指标完成率/达成率",
    _svg_gauge,
    _html_gauge,
    {
        "title": "仪表盘标题",
        "labels": ["完成率"],
        "series": [{"name": "值", "values": [75]}],
        "max": 100,
        "unit": "%",
    },
)
_register(
    "waterfall",
    "瀑布图",
    "展示增减变化过程",
    _svg_waterfall,
    _html_waterfall,
    {
        "title": "瀑布图标题",
        "labels": ["起始", "增加", "减少", "增加", "合计"],
        "series": [{"name": "值", "values": [100, 30, -20, 40, 150]}],
    },
)
_register(
    "progress",
    "进度条",
    "多项目完成进度对比",
    _svg_progress,
    _html_progress,
    {
        "title": "进度条标题",
        "labels": ["项目A", "项目B", "项目C", "项目D"],
        "series": [{"name": "完成率", "values": [77, 62, 90, 42]}],
    },
)
_register(
    "heatmap",
    "热力图",
    "相关矩阵/数据密度可视化",
    _svg_heatmap,
    _html_heatmap,
    {
        "title": "热力图标题",
        "labels": ["指标A", "指标B", "指标C", "指标D", "指标E"],
        "colLabels": ["维度1", "维度2", "维度3", "维度4", "维度5"],
        "series": [
            {
                "name": "值",
                "values": [
                    12,
                    35,
                    58,
                    76,
                    92,
                    55,
                    72,
                    95,
                    88,
                    40,
                    38,
                    15,
                    60,
                    90,
                    70,
                    68,
                    92,
                    42,
                    56,
                    18,
                    14,
                    55,
                    85,
                    65,
                    96,
                ],
            }
        ],
    },
)
_register(
    "gantt",
    "甘特图",
    "项目时间线与任务规划",
    _svg_gantt,
    _html_gantt,
    {
        "title": "甘特图标题",
        "labels": ["需求分析", "系统设计", "开发实现", "测试验收", "上线部署"],
        "series": [
            {"name": "开始", "values": [0, 1, 2, 3.5, 4.5]},
            {"name": "时长", "values": [1.7, 1.5, 2.0, 1.3, 0.9]},
        ],
    },
)
_register(
    "boxplot",
    "箱线图",
    "统计分布：中位数/四分位/极值",
    _svg_boxplot,
    _html_boxplot,
    {
        "title": "箱线图标题",
        "labels": ["组别A", "组别B", "组别C"],
        "series": [
            {"name": "min", "values": [23, 24, 18]},
            {"name": "q1", "values": [50, 55, 45]},
            {"name": "median", "values": [68, 64, 60]},
            {"name": "q3", "values": [90, 86, 90]},
            {"name": "max", "values": [107, 107, 112]},
        ],
    },
)
_register(
    "dual_axis",
    "双轴图",
    "柱状+折线组合，双指标对比",
    _svg_dual_axis,
    _html_dual_axis,
    {
        "title": "双轴图标题",
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "series": [
            {"name": "销售额", "values": [52, 76, 67, 86]},
            {"name": "增长率", "values": [45, 71, 62, 83]},
        ],
    },
)
_register(
    "diverging",
    "对比柱状图",
    "正反/左右对比分析",
    _svg_diverging,
    _html_diverging,
    {
        "title": "对比柱状图标题",
        "labels": ["类目A", "类目B", "类目C", "类目D"],
        "series": [
            {"name": "反对", "values": [32, 23, 55, 15]},
            {"name": "赞同", "values": [68, 45, 28, 85]},
        ],
    },
)
_register(
    "treemap",
    "矩形树图",
    "层次结构占比可视化",
    _svg_treemap,
    _html_treemap,
    {
        "title": "矩形树图标题",
        "labels": ["类目A", "类目B", "类目C", "类目D", "类目E", "类目F"],
        "series": [{"name": "占比", "values": [35, 25, 18, 12, 7, 3]}],
    },
)


# ======================================================================
# ChartCard — 单个图表预览卡片
# ======================================================================


class _ChartCard(QFrame):
    """可点击的图表预览卡片。"""

    def __init__(self, chart_def: dict, parent=None):
        super().__init__(parent)
        self._chart_def = chart_def
        self._selected = False
        self.setFixedSize(195, 168)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 6)
        layout.setSpacing(4)

        # SVG preview
        preview = QLabel()
        preview.setFixedSize(178, 110)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        svg_bytes = self._chart_def["svg_func"]()
        pixmap = QPixmap(178, 110)
        pixmap.fill(QColor(Qt.GlobalColor.transparent))
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        if renderer.isValid():
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            renderer.render(painter)
            painter.end()
        preview.setPixmap(pixmap)
        layout.addWidget(preview)

        # Label
        name_label = QLabel(self._chart_def["label"])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #334155; background: transparent;")
        layout.addWidget(name_label)

        # Description
        desc_label = QLabel(self._chart_def["desc"])
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setFont(QFont("Microsoft YaHei", 8))
        desc_label.setStyleSheet("color: #94A3B8; background: transparent;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

    def _update_style(self):
        if self._selected:
            self.setStyleSheet("""
                _ChartCard {
                    background: #EFF6FF;
                    border: 2px solid #4A90D9;
                    border-radius: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                _ChartCard {
                    background: #FFFFFF;
                    border: 1px solid #E2E8F0;
                    border-radius: 10px;
                }
                _ChartCard:hover {
                    border: 1.5px solid #93C5FD;
                    background: #F8FAFF;
                }
            """)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()

    def is_selected(self) -> bool:
        return self._selected

    def get_chart_def(self) -> dict:
        return self._chart_def

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Notify parent to update selection
            parent = self.parent()
            while parent and not isinstance(parent, ChartDialog):
                parent = parent.parent()
            if parent:
                parent._select_card(self)
        super().mousePressEvent(event)


# ======================================================================
# ChartDialog — 数据图选择对话框
# ======================================================================


class ChartDialog(QDialog):
    """美观的数据图选择对话框，包含各种图表预览卡片。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("插入数据图")
        self.setMinimumSize(680, 520)
        self.resize(700, 540)
        self._selected_card = None
        self._result_html = ""
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background: #F8FAFC;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("选择数据图类型")
        header.setFont(QFont("Microsoft YaHei", 15, QFont.Weight.Bold))
        header.setStyleSheet("color: #1E293B; background: transparent;")
        layout.addWidget(header)

        subtitle = QLabel(
            "点击选择一种图表，然后点击「插入」将其添加到文档中。插入后可直接编辑数据。"
        )
        subtitle.setFont(QFont("Microsoft YaHei", 9))
        subtitle.setStyleSheet("color: #64748B; background: transparent;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)

        container = QWidget()
        self._grid = QGridLayout(container)
        self._grid.setContentsMargins(0, 4, 0, 4)
        self._grid.setSpacing(14)

        self._cards = []
        cols = 3
        for i, chart_def in enumerate(_CHART_DEFS):
            card = _ChartCard(chart_def)
            self._cards.append(card)
            row, col = divmod(i, cols)
            self._grid.addWidget(card, row, col)

        # Fill remaining cells with spacers if needed
        remaining = cols - (len(_CHART_DEFS) % cols)
        if remaining < cols:
            last_row = len(_CHART_DEFS) // cols
            for j in range(len(_CHART_DEFS) % cols, cols):
                spacer = QWidget()
                spacer.setFixedSize(195, 168)
                self._grid.addWidget(spacer, last_row, j)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setFixedSize(90, 36)
        self._cancel_btn.setFont(QFont("Microsoft YaHei", 10))
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                color: #475569;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #F1F5F9;
                border-color: #94A3B8;
            }
        """)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._insert_btn = QPushButton("插入图表")
        self._insert_btn.setFixedSize(110, 36)
        self._insert_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self._insert_btn.setEnabled(False)
        self._insert_btn.setStyleSheet("""
            QPushButton {
                background: #4A90D9;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #3A7BC8;
            }
            QPushButton:disabled {
                background: #CBD5E1;
                color: #94A3B8;
            }
        """)
        self._insert_btn.clicked.connect(self._on_insert)
        btn_layout.addWidget(self._insert_btn)

        layout.addLayout(btn_layout)

    def _select_card(self, card: _ChartCard):
        """选中某张卡片，取消其它选中。"""
        for c in self._cards:
            c.set_selected(c is card)
        self._selected_card = card
        self._insert_btn.setEnabled(True)

    def _on_insert(self):
        if self._selected_card:
            chart_def = self._selected_card.get_chart_def()
            raw_html = chart_def["html_func"]()
            cfg = chart_def.get("default_config", {})
            self._result_html = wrap_chart_with_config(chart_def["key"], raw_html, cfg)
            self.accept()

    def get_chart_html(self) -> str:
        """返回选中图表的 HTML。"""
        return self._result_html
