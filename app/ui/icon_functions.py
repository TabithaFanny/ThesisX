"""
Unified geometric line icons — 2px strokes, RoundCap, no font dependency.
All icons are rendered as vector paths via QPainter.
"""

import os
import tempfile

from PyQt6.QtCore import QByteArray, QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def _make_pixmap(size, draw_func):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_func(painter, size)
    painter.end()
    return QIcon(pixmap)


def _pen(color="#444444", width=2.0):
    p = QPen(QColor(color))
    p.setWidthF(width)
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


# ─── Bold: thick vertical bar + two bumps ───
def icon_bold(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        m = s * 0.25
        # Left vertical bar
        p.drawLine(QPointF(m, s * 0.15), QPointF(m, s * 0.85))
        # Top bump
        path = QPainterPath()
        path.moveTo(m, s * 0.15)
        path.lineTo(s * 0.55, s * 0.15)
        path.cubicTo(s * 0.78, s * 0.15, s * 0.78, s * 0.50, s * 0.55, s * 0.50)
        path.lineTo(m, s * 0.50)
        p.drawPath(path)
        # Bottom bump (slightly wider)
        path2 = QPainterPath()
        path2.moveTo(m, s * 0.50)
        path2.lineTo(s * 0.60, s * 0.50)
        path2.cubicTo(s * 0.82, s * 0.50, s * 0.82, s * 0.85, s * 0.60, s * 0.85)
        path2.lineTo(m, s * 0.85)
        p.drawPath(path2)

    return _make_pixmap(size, draw)


# ─── Italic: slanted line with top/bottom bars ───
def icon_italic(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.58, s * 0.15), QPointF(s * 0.42, s * 0.85))
        p.drawLine(QPointF(s * 0.40, s * 0.15), QPointF(s * 0.72, s * 0.15))
        p.drawLine(QPointF(s * 0.28, s * 0.85), QPointF(s * 0.60, s * 0.85))

    return _make_pixmap(size, draw)


# ─── Underline: U-arc + bottom bar ───
def icon_underline(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.25, s * 0.15)
        path.lineTo(s * 0.25, s * 0.55)
        path.cubicTo(s * 0.25, s * 0.78, s * 0.75, s * 0.78, s * 0.75, s * 0.55)
        path.lineTo(s * 0.75, s * 0.15)
        p.drawPath(path)
        p.drawLine(QPointF(s * 0.18, s * 0.88), QPointF(s * 0.82, s * 0.88))

    return _make_pixmap(size, draw)


# ─── Strikethrough: S-curve + horizontal line ───
def icon_strikethrough(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.70, s * 0.22)
        path.cubicTo(s * 0.55, s * 0.12, s * 0.25, s * 0.15, s * 0.25, s * 0.35)
        path.cubicTo(s * 0.25, s * 0.50, s * 0.75, s * 0.50, s * 0.75, s * 0.65)
        path.cubicTo(s * 0.75, s * 0.85, s * 0.45, s * 0.88, s * 0.30, s * 0.78)
        p.drawPath(path)
        p.setPen(_pen("#444444", 1.8))
        p.drawLine(QPointF(s * 0.12, s * 0.50), QPointF(s * 0.88, s * 0.50))

    return _make_pixmap(size, draw)


# ─── Heading: H + dropdown arrow ───
def icon_heading(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.18, s * 0.18), QPointF(s * 0.18, s * 0.72))
        p.drawLine(QPointF(s * 0.52, s * 0.18), QPointF(s * 0.52, s * 0.72))
        p.drawLine(QPointF(s * 0.18, s * 0.45), QPointF(s * 0.52, s * 0.45))
        p.setPen(_pen("#444444", 1.6))
        p.drawLine(QPointF(s * 0.64, s * 0.40), QPointF(s * 0.78, s * 0.55))
        p.drawLine(QPointF(s * 0.78, s * 0.55), QPointF(s * 0.92, s * 0.40))

    return _make_pixmap(size, draw)


# ─── Link: two chain links ───
def icon_link(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(s * 0.08, s * 0.35, s * 0.38, s * 0.30), s * 0.15, s * 0.15)
        p.drawRoundedRect(QRectF(s * 0.54, s * 0.35, s * 0.38, s * 0.30), s * 0.15, s * 0.15)
        p.drawLine(QPointF(s * 0.38, s * 0.50), QPointF(s * 0.62, s * 0.50))

    return _make_pixmap(size, draw)


# ─── Image: frame + mountain + sun ───
def icon_image(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        m = s * 0.12
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), 2, 2)
        path = QPainterPath()
        path.moveTo(m + 1, s - m - 1)
        path.lineTo(s * 0.35, s * 0.50)
        path.lineTo(s * 0.50, s * 0.62)
        path.lineTo(s * 0.65, s * 0.42)
        path.lineTo(s - m - 1, s - m - 1)
        p.drawPath(path)
        p.setBrush(QBrush(QColor("#444444")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(s * 0.68, s * 0.30), s * 0.07, s * 0.07)

    return _make_pixmap(size, draw)


# ─── Code: angle brackets < > with slash ───
def icon_code(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.35, s * 0.25), QPointF(s * 0.12, s * 0.50))
        p.drawLine(QPointF(s * 0.12, s * 0.50), QPointF(s * 0.35, s * 0.75))
        p.drawLine(QPointF(s * 0.65, s * 0.25), QPointF(s * 0.88, s * 0.50))
        p.drawLine(QPointF(s * 0.88, s * 0.50), QPointF(s * 0.65, s * 0.75))
        p.setPen(_pen("#444444", 1.5))
        p.drawLine(QPointF(s * 0.56, s * 0.20), QPointF(s * 0.44, s * 0.80))

    return _make_pixmap(size, draw)


# ─── Table: grid ───
def icon_table(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        m = s * 0.12
        w, h = s - 2 * m, s - 2 * m
        p.drawRoundedRect(QRectF(m, m, w, h), 2, 2)
        p.drawLine(QPointF(m, m + h / 3), QPointF(m + w, m + h / 3))
        p.drawLine(QPointF(m, m + 2 * h / 3), QPointF(m + w, m + 2 * h / 3))
        p.drawLine(QPointF(m + w / 2, m), QPointF(m + w / 2, m + h))

    return _make_pixmap(size, draw)


# ─── Quote: left bar + lines ───
def icon_quote(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.5))
        p.drawLine(QPointF(s * 0.14, s * 0.20), QPointF(s * 0.14, s * 0.80))
        p.setPen(_pen("#444444", 1.8))
        p.drawLine(QPointF(s * 0.28, s * 0.30), QPointF(s * 0.85, s * 0.30))
        p.drawLine(QPointF(s * 0.28, s * 0.50), QPointF(s * 0.75, s * 0.50))
        p.drawLine(QPointF(s * 0.28, s * 0.70), QPointF(s * 0.65, s * 0.70))

    return _make_pixmap(size, draw)


# ─── Bullet list: dots + lines ───
def icon_bullet_list(size=20):
    def draw(p, s):
        for yf in [0.25, 0.50, 0.75]:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor("#444444")))
            p.drawEllipse(QPointF(s * 0.18, s * yf), s * 0.045, s * 0.045)
            p.setPen(_pen("#444444", 1.8))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(QPointF(s * 0.30, s * yf), QPointF(s * 0.88, s * yf))

    return _make_pixmap(size, draw)


# ─── Ordered list: number strokes + lines ───
def icon_ordered_list(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.5))
        p.drawLine(QPointF(s * 0.15, s * 0.17), QPointF(s * 0.15, s * 0.32))
        path2 = QPainterPath()
        path2.moveTo(s * 0.08, s * 0.42)
        path2.cubicTo(s * 0.08, s * 0.38, s * 0.22, s * 0.38, s * 0.22, s * 0.46)
        path2.lineTo(s * 0.08, s * 0.56)
        path2.lineTo(s * 0.22, s * 0.56)
        p.drawPath(path2)
        path3 = QPainterPath()
        path3.moveTo(s * 0.08, s * 0.65)
        path3.cubicTo(s * 0.22, s * 0.62, s * 0.22, s * 0.72, s * 0.15, s * 0.73)
        path3.cubicTo(s * 0.22, s * 0.74, s * 0.22, s * 0.84, s * 0.08, s * 0.82)
        p.drawPath(path3)
        p.setPen(_pen("#444444", 1.8))
        for yf in [0.25, 0.50, 0.75]:
            p.drawLine(QPointF(s * 0.30, s * yf), QPointF(s * 0.88, s * yf))

    return _make_pixmap(size, draw)


# ─── Horizontal rule ───
def icon_hr(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        y = s * 0.50
        p.drawLine(QPointF(s * 0.10, y), QPointF(s * 0.90, y))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#444444")))
        for xf in [0.30, 0.50, 0.70]:
            p.drawEllipse(QPointF(s * xf, y), 1.8, 1.8)

    return _make_pixmap(size, draw)


# ─── Font color: A triangle + color bar ───
def icon_font_color(size=20, color="#e74c3c"):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.50, s * 0.10), QPointF(s * 0.25, s * 0.68))
        p.drawLine(QPointF(s * 0.50, s * 0.10), QPointF(s * 0.75, s * 0.68))
        p.drawLine(QPointF(s * 0.33, s * 0.48), QPointF(s * 0.67, s * 0.48))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(color)))
        p.drawRoundedRect(QRectF(s * 0.10, s * 0.78, s * 0.80, s * 0.14), 1.5, 1.5)

    return _make_pixmap(size, draw)


# ─── Highlight ───
def icon_highlight(size=20, color="#ffc107"):
    def draw(p, s):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(color)))
        p.drawRoundedRect(QRectF(s * 0.08, s * 0.10, s * 0.84, s * 0.58), 3, 3)
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.50, s * 0.12), QPointF(s * 0.28, s * 0.62))
        p.drawLine(QPointF(s * 0.50, s * 0.12), QPointF(s * 0.72, s * 0.62))
        p.drawLine(QPointF(s * 0.35, s * 0.44), QPointF(s * 0.65, s * 0.44))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(color)))
        p.drawRoundedRect(QRectF(s * 0.10, s * 0.78, s * 0.80, s * 0.14), 1.5, 1.5)

    return _make_pixmap(size, draw)


# ─── Font size: big A + small a ───
def icon_font_size(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.35, s * 0.12), QPointF(s * 0.12, s * 0.72))
        p.drawLine(QPointF(s * 0.35, s * 0.12), QPointF(s * 0.58, s * 0.72))
        p.drawLine(QPointF(s * 0.20, s * 0.50), QPointF(s * 0.50, s * 0.50))
        p.setPen(_pen("#444444", 1.5))
        p.drawLine(QPointF(s * 0.72, s * 0.40), QPointF(s * 0.60, s * 0.72))
        p.drawLine(QPointF(s * 0.72, s * 0.40), QPointF(s * 0.84, s * 0.72))
        p.drawLine(QPointF(s * 0.64, s * 0.58), QPointF(s * 0.80, s * 0.58))

    return _make_pixmap(size, draw)


# ─── Superscript: X + raised 2 ───
def icon_superscript(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.10, s * 0.30), QPointF(s * 0.48, s * 0.82))
        p.drawLine(QPointF(s * 0.48, s * 0.30), QPointF(s * 0.10, s * 0.82))
        p.setPen(_pen("#444444", 1.5))
        path = QPainterPath()
        path.moveTo(s * 0.58, s * 0.25)
        path.cubicTo(s * 0.58, s * 0.12, s * 0.88, s * 0.12, s * 0.88, s * 0.25)
        path.lineTo(s * 0.58, s * 0.42)
        path.lineTo(s * 0.88, s * 0.42)
        p.drawPath(path)

    return _make_pixmap(size, draw)


# ─── Align left: left-aligned lines ───
def icon_align_left(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.drawLine(QPointF(s * 0.12, s * 0.20), QPointF(s * 0.88, s * 0.20))
        p.drawLine(QPointF(s * 0.12, s * 0.40), QPointF(s * 0.65, s * 0.40))
        p.drawLine(QPointF(s * 0.12, s * 0.60), QPointF(s * 0.78, s * 0.60))
        p.drawLine(QPointF(s * 0.12, s * 0.80), QPointF(s * 0.55, s * 0.80))

    return _make_pixmap(size, draw)


# ─── Align center: center-aligned lines ───
def icon_align_center(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.drawLine(QPointF(s * 0.12, s * 0.20), QPointF(s * 0.88, s * 0.20))
        p.drawLine(QPointF(s * 0.22, s * 0.40), QPointF(s * 0.78, s * 0.40))
        p.drawLine(QPointF(s * 0.15, s * 0.60), QPointF(s * 0.85, s * 0.60))
        p.drawLine(QPointF(s * 0.28, s * 0.80), QPointF(s * 0.72, s * 0.80))

    return _make_pixmap(size, draw)


# ─── Align right: right-aligned lines ───
def icon_align_right(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.drawLine(QPointF(s * 0.12, s * 0.20), QPointF(s * 0.88, s * 0.20))
        p.drawLine(QPointF(s * 0.35, s * 0.40), QPointF(s * 0.88, s * 0.40))
        p.drawLine(QPointF(s * 0.22, s * 0.60), QPointF(s * 0.88, s * 0.60))
        p.drawLine(QPointF(s * 0.45, s * 0.80), QPointF(s * 0.88, s * 0.80))

    return _make_pixmap(size, draw)


# ─── Align justify: fully justified lines ───
def icon_align_justify(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.drawLine(QPointF(s * 0.12, s * 0.20), QPointF(s * 0.88, s * 0.20))
        p.drawLine(QPointF(s * 0.12, s * 0.40), QPointF(s * 0.88, s * 0.40))
        p.drawLine(QPointF(s * 0.12, s * 0.60), QPointF(s * 0.88, s * 0.60))
        p.drawLine(QPointF(s * 0.12, s * 0.80), QPointF(s * 0.88, s * 0.80))

    return _make_pixmap(size, draw)


# ─── ChatGPT / OpenAI logo (SVG) ───
_CHATGPT_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    b'<path fill="#10A37F" d="'
    b"M22.282 9.821a5.985 5.985 0 0 0-.516-4.911 6.046 6.046 0 0 0-6.51-2.9"
    b"A6.065 6.065 0 0 0 4.981 4.182a5.985 5.985 0 0 0-3.998 2.9"
    b" 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .511 4.911"
    b" 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24"
    b"a6.056 6.056 0 0 0 5.772-4.206 5.989 5.989 0 0 0 3.998-2.9"
    b" 6.056 6.056 0 0 0-.748-7.073z"
    b"m-9.022 12.608a4.476 4.476 0 0 1-2.876-1.041l.142-.08"
    b" 4.778-2.758a.795.795 0 0 0 .393-.681v-6.737l2.02 1.169"
    b"a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.495 4.494z"
    b"m-9.661-4.125a4.471 4.471 0 0 1-.535-3.014l.142.085"
    b" 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332"
    b"a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646z"
    b"M2.341 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6"
    b"a.766.766 0 0 0 .388.677l5.814 3.354-2.02 1.169"
    b"a.076.076 0 0 1-.071 0l-4.83-2.787"
    b"A4.504 4.504 0 0 1 2.34 7.896z"
    b"m16.597 3.856L13.104 8.364l2.02-1.164"
    b"a.076.076 0 0 1 .071 0l4.83 2.791"
    b"a4.494 4.494 0 0 1-.676 8.105v-5.678"
    b"a.79.79 0 0 0-.41-.676z"
    b"m2.01-3.023l-.141-.085-4.774-2.782"
    b"a.776.776 0 0 0-.785 0L9.409 9.23V6.897"
    b"a.066.066 0 0 1 .028-.061l4.83-2.787"
    b"a4.5 4.5 0 0 1 6.68 4.66z"
    b"M8.307 12.863l-2.02-1.164"
    b"a.08.08 0 0 1-.038-.057V6.074"
    b"a4.5 4.5 0 0 1 7.376-3.454l-.142.081"
    b"L8.704 5.46a.795.795 0 0 0-.393.681z"
    b"m1.097-2.362l2.603-1.5 2.603 1.5v3.001"
    b"l-2.603 1.5-2.603-1.5z"
    b'"/></svg>'
)


def icon_chatgpt(size=24, color="#10A37F"):
    """ChatGPT/OpenAI 官方 logo 图标，使用 SVG 渲染。"""
    try:
        from PyQt6.QtSvg import QSvgRenderer

        svg = _CHATGPT_SVG.replace(b'fill="#10A37F"', f'fill="{color}"'.encode())
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        renderer = QSvgRenderer(QByteArray(svg))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    except Exception:
        # Fallback: simple sparkle drawn with QPainter
        return _icon_ai_fallback(size)


def _icon_ai_fallback(size=20):
    def draw(p, s):
        p.setPen(_pen("#10A37F", 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        cx, cy = s * 0.42, s * 0.38
        path.moveTo(cx, cy - s * 0.28)
        path.cubicTo(cx + s * 0.04, cy - s * 0.08, cx + s * 0.08, cy - s * 0.04, cx + s * 0.28, cy)
        path.cubicTo(cx + s * 0.08, cy + s * 0.04, cx + s * 0.04, cy + s * 0.08, cx, cy + s * 0.28)
        path.cubicTo(cx - s * 0.04, cy + s * 0.08, cx - s * 0.08, cy + s * 0.04, cx - s * 0.28, cy)
        path.cubicTo(cx - s * 0.08, cy - s * 0.04, cx - s * 0.04, cy - s * 0.08, cx, cy - s * 0.28)
        p.drawPath(path)
        p.setPen(_pen("#10A37F", 1.5))
        sx2, sy2 = s * 0.78, s * 0.22
        r2 = s * 0.12
        p.drawLine(QPointF(sx2, sy2 - r2), QPointF(sx2, sy2 + r2))
        p.drawLine(QPointF(sx2 - r2, sy2), QPointF(sx2 + r2, sy2))

    return _make_pixmap(size, draw)


# ─── Claude / Anthropic logo (SVG, no background) ───
_CLAUDE_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    b'<path fill="#D97757" d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275'
    b"h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214"
    b"-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608"
    b" 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886"
    b"l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879"
    b"-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225"
    b".8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336"
    b".3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467"
    b"-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674"
    b"-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642"
    b".6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318"
    b".091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957"
    b".0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433"
    b"-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429"
    b".9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311"
    b"h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414"
    b"-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607"
    b" 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075"
    b"-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607"
    b" 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376"
    b"-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279"
    b"h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314"
    b".1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468"
    b"-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807"
    b"-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959"
    b"l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793"
    b"-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53"
    b".2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672"
    b"-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618"
    b".4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579"
    b"h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467"
    b'.2307-.2429 1.9064-1.3114Z"/>'
    b"</svg>"
)


def icon_claude(size=24, color="#D97757"):
    """Claude/Anthropic 官方 starburst 图标，使用 SVG 渲染。"""
    try:
        from PyQt6.QtSvg import QSvgRenderer

        svg = _CLAUDE_SVG.replace(b'fill="#D97757"', f'fill="{color}"'.encode())
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        renderer = QSvgRenderer(QByteArray(svg))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    except Exception:
        return _icon_ai_fallback(size)


# ─── Gemini / Google logo (SVG, no background) ───
_GEMINI_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    b'<path fill="#4285F4" d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68'
    b".96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93"
    b"a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81"
    b"Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81"
    b"a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96"
    b' 2.19.93 3.81 2.55t2.55 3.81"/>'
    b"</svg>"
)


def icon_gemini(size=24, color="#4285F4"):
    """Gemini/Google 官方 sparkle 图标，使用 SVG 渲染。"""
    try:
        from PyQt6.QtSvg import QSvgRenderer

        svg = _GEMINI_SVG.replace(b'fill="#4285F4"', f'fill="{color}"'.encode())
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        renderer = QSvgRenderer(QByteArray(svg))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    except Exception:
        return _icon_ai_fallback(size)


# Keep old name as alias
def icon_ai(size=20):
    return icon_chatgpt(size)


# ─── Dropdown chevron (saved as temp PNG for QComboBox stylesheet) ───
_DROPDOWN_ARROW_CACHE = None


def dropdown_arrow_path():
    """Return filesystem path to a chevron‑down PNG for QComboBox styling."""
    global _DROPDOWN_ARROW_CACHE
    if _DROPDOWN_ARROW_CACHE and os.path.exists(_DROPDOWN_ARROW_CACHE):
        return _DROPDOWN_ARROW_CACHE
    size = 16
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor("#666666"))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    # Chevron: V shape
    painter.drawLine(QPointF(3, 5.5), QPointF(8, 11))
    painter.drawLine(QPointF(8, 11), QPointF(13, 5.5))
    painter.end()
    path = os.path.join(tempfile.gettempdir(), "wenbiao_dropdown_arrow.png")
    pixmap.save(path)
    _DROPDOWN_ARROW_CACHE = path
    return path


# ─── More: two horizontal lines + chevron-down (pure QPainter) ───
def icon_more(size=20):
    """展开/收起扩展工具栏 — 两横线 + 向下箭头。"""

    def draw(p, s):
        p.setPen(_pen("#333333", 2.0))
        # Top line
        p.drawLine(QPointF(s * 0.15, s * 0.26), QPointF(s * 0.85, s * 0.26))
        # Middle line
        p.drawLine(QPointF(s * 0.15, s * 0.48), QPointF(s * 0.85, s * 0.48))
        # Chevron down
        p.setPen(_pen("#333333", 2.2))
        p.drawLine(QPointF(s * 0.32, s * 0.65), QPointF(s * 0.50, s * 0.82))
        p.drawLine(QPointF(s * 0.50, s * 0.82), QPointF(s * 0.68, s * 0.65))

    return _make_pixmap(size, draw)


# ─── Clear formatting: crossed-out T ───
def icon_clear_format(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.20, s * 0.20), QPointF(s * 0.65, s * 0.20))
        p.drawLine(QPointF(s * 0.42, s * 0.20), QPointF(s * 0.42, s * 0.70))
        p.setPen(_pen("#e74c3c", 1.8))
        p.drawLine(QPointF(s * 0.15, s * 0.80), QPointF(s * 0.85, s * 0.20))

    return _make_pixmap(size, draw)


# ─── Indent: lines + right arrow ───
def icon_indent(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.drawLine(QPointF(s * 0.40, s * 0.25), QPointF(s * 0.88, s * 0.25))
        p.drawLine(QPointF(s * 0.40, s * 0.50), QPointF(s * 0.88, s * 0.50))
        p.drawLine(QPointF(s * 0.40, s * 0.75), QPointF(s * 0.88, s * 0.75))
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.10, s * 0.50), QPointF(s * 0.28, s * 0.50))
        p.drawLine(QPointF(s * 0.20, s * 0.38), QPointF(s * 0.28, s * 0.50))
        p.drawLine(QPointF(s * 0.20, s * 0.62), QPointF(s * 0.28, s * 0.50))

    return _make_pixmap(size, draw)


# ─── Outdent: lines + left arrow ───
def icon_outdent(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.drawLine(QPointF(s * 0.40, s * 0.25), QPointF(s * 0.88, s * 0.25))
        p.drawLine(QPointF(s * 0.40, s * 0.50), QPointF(s * 0.88, s * 0.50))
        p.drawLine(QPointF(s * 0.40, s * 0.75), QPointF(s * 0.88, s * 0.75))
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.28, s * 0.50), QPointF(s * 0.10, s * 0.50))
        p.drawLine(QPointF(s * 0.18, s * 0.38), QPointF(s * 0.10, s * 0.50))
        p.drawLine(QPointF(s * 0.18, s * 0.62), QPointF(s * 0.10, s * 0.50))

    return _make_pixmap(size, draw)


# ─── GPT 菜单项图标（SVG + QPainter fallback）───

_GPT_OPTIMIZE_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
    b'<line x1="8" y1="1.5" x2="8" y2="14.5" stroke="#10A37F" stroke-width="2" stroke-linecap="round"/>'
    b'<line x1="1.5" y1="8" x2="14.5" y2="8" stroke="#10A37F" stroke-width="2" stroke-linecap="round"/>'
    b'<line x1="4" y1="4" x2="12" y2="12" stroke="#10A37F" stroke-width="1" stroke-linecap="round" opacity="0.45"/>'
    b'<line x1="12" y1="4" x2="4" y2="12" stroke="#10A37F" stroke-width="1" stroke-linecap="round" opacity="0.45"/>'
    b'<circle cx="8" cy="8" r="2.2" fill="#10A37F"/>'
    b"</svg>"
)

_GPT_CONTINUE_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none">'
    b'<path d="M9.5 2L14 6.5L5.5 15H2V11.5Z" fill="#6366F1"/>'
    b'<line x1="7.5" y1="4" x2="12" y2="8.5" stroke="#4338CA" stroke-width="0.8"/>'
    b"</svg>"
)

_GPT_REWRITE_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none">'
    b'<path d="M8 2.5C5 2.5 2.5 5 2.5 8C2.5 11 5 13.5 8 13.5'
    b'C11 13.5 13.5 11 13.5 8C13.5 6.1 12.6 4.4 11.2 3.3"'
    b' stroke="#F59E0B" stroke-width="1.6" stroke-linecap="round"/>'
    b'<polyline points="9,1.5 11.5,3.2 9.8,5.8" fill="none"'
    b' stroke="#F59E0B" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    b"</svg>"
)

_GPT_CUSTOM_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none">'
    b'<circle cx="8" cy="8" r="2.5" stroke="#6B7280" stroke-width="1.5"/>'
    b'<line x1="8" y1="1" x2="8" y2="3.2" stroke="#6B7280" stroke-width="1.5" stroke-linecap="round"/>'
    b'<line x1="8" y1="12.8" x2="8" y2="15" stroke="#6B7280" stroke-width="1.5" stroke-linecap="round"/>'
    b'<line x1="1" y1="8" x2="3.2" y2="8" stroke="#6B7280" stroke-width="1.5" stroke-linecap="round"/>'
    b'<line x1="12.8" y1="8" x2="15" y2="8" stroke="#6B7280" stroke-width="1.5" stroke-linecap="round"/>'
    b'<line x1="3.05" y1="3.05" x2="4.61" y2="4.61" stroke="#6B7280" stroke-width="1.5" stroke-linecap="round"/>'
    b'<line x1="11.39" y1="11.39" x2="12.95" y2="12.95" stroke="#6B7280" stroke-width="1.5" stroke-linecap="round"/>'
    b'<line x1="12.95" y1="3.05" x2="11.39" y2="4.61" stroke="#6B7280" stroke-width="1.5" stroke-linecap="round"/>'
    b'<line x1="4.61" y1="11.39" x2="3.05" y2="12.95" stroke="#6B7280" stroke-width="1.5" stroke-linecap="round"/>'
    b"</svg>"
)

# Pre-computed cos/sin for gear teeth at 0°,45°,...,315°
_GEAR_DIRS = [
    (1.0, 0.0),
    (0.707, 0.707),
    (0.0, 1.0),
    (-0.707, 0.707),
    (-1.0, 0.0),
    (-0.707, -0.707),
    (0.0, -1.0),
    (0.707, -0.707),
]


def _render_svg_icon(svg_bytes, size):
    """Render SVG bytes to QIcon. Returns None on failure."""
    try:
        from PyQt6.QtSvg import QSvgRenderer

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        if not renderer.isValid():
            return None
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)
    except Exception:
        return None


def icon_gpt_optimize(size=16):
    """优化选中内容 — 4点小星，GPT 绿。"""
    icon = _render_svg_icon(_GPT_OPTIMIZE_SVG, size)
    if icon is not None:
        return icon

    def draw(p, s):
        cx, cy = s / 2, s / 2
        p.setPen(_pen("#10A37F", 1.8))
        p.drawLine(QPointF(cx, cy - s * 0.42), QPointF(cx, cy + s * 0.42))
        p.drawLine(QPointF(cx - s * 0.42, cy), QPointF(cx + s * 0.42, cy))
        p.setPen(_pen("#10A37F", 0.9))
        d = s * 0.26
        p.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
        p.drawLine(QPointF(cx + d, cy - d), QPointF(cx - d, cy + d))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#10A37F")))
        p.drawEllipse(QPointF(cx, cy), s * 0.15, s * 0.15)

    return _make_pixmap(size, draw)


def icon_gpt_continue(size=16):
    """续写论文 — 铅笔形，蒜紫色。"""
    icon = _render_svg_icon(_GPT_CONTINUE_SVG, size)
    if icon is not None:
        return icon

    def draw(p, s):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#6366F1")))
        path = QPainterPath()
        path.moveTo(s * 0.60, s * 0.12)
        path.lineTo(s * 0.88, s * 0.40)
        path.lineTo(s * 0.35, s * 0.94)
        path.lineTo(s * 0.12, s * 0.94)
        path.lineTo(s * 0.12, s * 0.72)
        path.closeSubpath()
        p.drawPath(path)
        p.setPen(_pen("#4338CA", 0.8))
        p.drawLine(QPointF(s * 0.48, s * 0.26), QPointF(s * 0.76, s * 0.54))

    return _make_pixmap(size, draw)


def icon_gpt_rewrite(size=16):
    """降重改写 — 循环箭头，琐珀色。"""
    icon = _render_svg_icon(_GPT_REWRITE_SVG, size)
    if icon is not None:
        return icon

    def draw(p, s):
        p.setPen(_pen("#F59E0B", 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.50, s * 0.16)
        path.cubicTo(s * 0.78, s * 0.16, s * 0.84, s * 0.44, s * 0.70, s * 0.72)
        path.cubicTo(s * 0.55, s * 0.90, s * 0.22, s * 0.90, s * 0.14, s * 0.60)
        p.drawPath(path)
        p.setPen(_pen("#F59E0B", 1.5))
        p.drawLine(QPointF(s * 0.56, s * 0.06), QPointF(s * 0.72, s * 0.20))
        p.drawLine(QPointF(s * 0.72, s * 0.20), QPointF(s * 0.60, s * 0.36))

    return _make_pixmap(size, draw)


def icon_gpt_custom(size=16):
    """自定义指令 — 齿轮，灰色。"""
    icon = _render_svg_icon(_GPT_CUSTOM_SVG, size)
    if icon is not None:
        return icon

    def draw(p, s):
        cx, cy = s / 2, s / 2
        p.setPen(_pen("#6B7280", 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), s * 0.25, s * 0.25)
        for dx, dy in _GEAR_DIRS:
            p.drawLine(
                QPointF(cx + dx * s * 0.30, cy + dy * s * 0.30),
                QPointF(cx + dx * s * 0.46, cy + dy * s * 0.46),
            )

    return _make_pixmap(size, draw)


# ─── Switch Model: double arrows + circle ───

_SWITCH_MODEL_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none">'
    b'<rect x="2" y="2" width="12" height="12" rx="3" fill="none" stroke="#8B5CF6" stroke-width="1.2"/>'
    b'<path d="M5.5 6.5L8 4L10.5 6.5" stroke="#8B5CF6" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>'
    b'<path d="M10.5 9.5L8 12L5.5 9.5" stroke="#8B5CF6" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>'
    b'<line x1="8" y1="4" x2="8" y2="12" stroke="#8B5CF6" stroke-width="1.2" stroke-linecap="round"/>'
    b"</svg>"
)


def icon_switch_model(size=16):
    """切换模型 — 上下箭头+竖线，紫色。"""
    icon = _render_svg_icon(_SWITCH_MODEL_SVG, size)
    if icon is not None:
        return icon

    def draw(p, s):
        p.setPen(_pen("#8B5CF6", 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Up arrow
        p.drawLine(QPointF(s * 0.35, s * 0.40), QPointF(s * 0.50, s * 0.25))
        p.drawLine(QPointF(s * 0.50, s * 0.25), QPointF(s * 0.65, s * 0.40))
        # Down arrow
        p.drawLine(QPointF(s * 0.35, s * 0.60), QPointF(s * 0.50, s * 0.75))
        p.drawLine(QPointF(s * 0.50, s * 0.75), QPointF(s * 0.65, s * 0.60))
        # Vertical line
        p.drawLine(QPointF(s * 0.50, s * 0.25), QPointF(s * 0.50, s * 0.75))

    return _make_pixmap(size, draw)


# ─── Model brand icons (for model switch dialog) ───

# Claude / Anthropic — official starburst logo (source: Simple Icons)
_MODEL_CLAUDE_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
    b'<rect width="48" height="48" rx="12" fill="#D97757"/>'
    b'<g transform="translate(8,8) scale(1.333)" fill="white">'
    b'<path d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275'
    b"h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214"
    b"-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608"
    b" 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886"
    b"l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879"
    b"-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225"
    b".8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336"
    b".3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467"
    b"-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674"
    b"-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642"
    b".6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318"
    b".091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957"
    b".0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433"
    b"-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429"
    b".9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311"
    b"h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414"
    b"-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607"
    b" 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075"
    b"-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607"
    b" 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376"
    b"-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279"
    b"h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314"
    b".1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468"
    b"-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807"
    b"-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959"
    b"l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793"
    b"-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53"
    b".2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672"
    b"-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618"
    b".4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579"
    b"h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467"
    b'.2307-.2429 1.9064-1.3114Z"/>'
    b"</g></svg>"
)

# OpenAI / GPT — official hexagonal knot logo (same path as _CHATGPT_SVG)
_MODEL_GPT_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
    b'<rect width="48" height="48" rx="12" fill="#10A37F"/>'
    b'<g transform="translate(8,8) scale(1.333)" fill="white">'
    b'<path d="'
    b"M22.282 9.821a5.985 5.985 0 0 0-.516-4.911 6.046 6.046 0 0 0-6.51-2.9"
    b"A6.065 6.065 0 0 0 4.981 4.182a5.985 5.985 0 0 0-3.998 2.9"
    b" 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .511 4.911"
    b" 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24"
    b"a6.056 6.056 0 0 0 5.772-4.206 5.989 5.989 0 0 0 3.998-2.9"
    b" 6.056 6.056 0 0 0-.748-7.073z"
    b"m-9.022 12.608a4.476 4.476 0 0 1-2.876-1.041l.142-.08"
    b" 4.778-2.758a.795.795 0 0 0 .393-.681v-6.737l2.02 1.169"
    b"a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.495 4.494z"
    b"m-9.661-4.125a4.471 4.471 0 0 1-.535-3.014l.142.085"
    b" 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332"
    b"a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646z"
    b"M2.341 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6"
    b"a.766.766 0 0 0 .388.677l5.814 3.354-2.02 1.169"
    b"a.076.076 0 0 1-.071 0l-4.83-2.787"
    b"A4.504 4.504 0 0 1 2.34 7.896z"
    b"m16.597 3.856L13.104 8.364l2.02-1.164"
    b"a.076.076 0 0 1 .071 0l4.83 2.791"
    b"a4.494 4.494 0 0 1-.676 8.105v-5.678"
    b"a.79.79 0 0 0-.41-.676z"
    b"m2.01-3.023l-.141-.085-4.774-2.782"
    b"a.776.776 0 0 0-.785 0L9.409 9.23V6.897"
    b"a.066.066 0 0 1 .028-.061l4.83-2.787"
    b"a4.5 4.5 0 0 1 6.68 4.66z"
    b"M8.307 12.863l-2.02-1.164"
    b"a.08.08 0 0 1-.038-.057V6.074"
    b"a4.5 4.5 0 0 1 7.376-3.454l-.142.081"
    b"L8.704 5.46a.795.795 0 0 0-.393.681z"
    b"m1.097-2.362l2.603-1.5 2.603 1.5v3.001"
    b"l-2.603 1.5-2.603-1.5z"
    b'"/>'
    b"</g></svg>"
)

# Gemini / Google — official sparkle logo (source: Simple Icons)
_MODEL_GEMINI_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
    b'<defs><linearGradient id="gem" x1="0" y1="0" x2="1" y2="1">'
    b'<stop offset="0%" stop-color="#4285F4"/>'
    b'<stop offset="100%" stop-color="#886FBF"/>'
    b"</linearGradient></defs>"
    b'<rect width="48" height="48" rx="12" fill="url(#gem)"/>'
    b'<g transform="translate(8,8) scale(1.333)" fill="white">'
    b'<path d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68'
    b".96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93"
    b"a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81"
    b"Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81"
    b"a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96"
    b' 2.19.93 3.81 2.55t2.55 3.81"/>'
    b"</g></svg>"
)


def icon_model_claude(size=48):
    """Claude 模型图标 — Anthropic 风格，暖棕色五瓣星。"""
    icon = _render_svg_icon(_MODEL_CLAUDE_SVG, size)
    if icon is not None:
        return icon

    def draw(p, s):
        import math

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#D97757")))
        p.drawRoundedRect(QRectF(0, 0, s, s), s * 0.25, s * 0.25)
        p.setBrush(QBrush(QColor("#FFFFFF")))
        cx, cy = s / 2, s / 2
        # Center circle
        p.drawEllipse(QPointF(cx, cy), s * 0.10, s * 0.10)
        # 5 organic petals
        for angle_deg in range(0, 360, 72):
            p.save()
            p.translate(cx, cy)
            p.rotate(angle_deg)
            p.drawEllipse(QPointF(0, -s * 0.23), s * 0.065, s * 0.18)
            p.restore()

    return _make_pixmap(size, draw)


def icon_model_gpt(size=48):
    """GPT 模型图标 — OpenAI 风格，绿色六瓣结。"""
    icon = _render_svg_icon(_MODEL_GPT_SVG, size)
    if icon is not None:
        return icon

    def draw(p, s):
        import math

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#10A37F")))
        p.drawRoundedRect(QRectF(0, 0, s, s), s * 0.25, s * 0.25)
        cx, cy = s / 2, s / 2
        r = s * 0.27
        p.setPen(_pen("#FFFFFF", s * 0.050))
        p.setBrush(Qt.BrushStyle.NoBrush)
        # 6 curved segments forming hexagonal knot
        for i in range(6):
            a1 = math.radians(i * 60 - 90)
            a2 = math.radians((i + 2) * 60 - 90)
            x1 = cx + r * math.cos(a1)
            y1 = cy + r * math.sin(a1)
            x2 = cx + r * math.cos(a2)
            y2 = cy + r * math.sin(a2)
            mid_a = math.radians((i + 1) * 60 - 90)
            cpx = cx + r * 0.42 * math.cos(mid_a + 0.35)
            cpy = cy + r * 0.42 * math.sin(mid_a + 0.35)
            path = QPainterPath()
            path.moveTo(x1, y1)
            path.quadTo(cpx, cpy, x2, y2)
            p.drawPath(path)
        # Center dot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.drawEllipse(QPointF(cx, cy), s * 0.06, s * 0.06)

    return _make_pixmap(size, draw)


def icon_model_gemini(size=48):
    """Gemini 模型图标 — Google 风格，蓝紫渐变四角星。"""
    icon = _render_svg_icon(_MODEL_GEMINI_SVG, size)
    if icon is not None:
        return icon

    def draw(p, s):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#1A73E8")))
        p.drawRoundedRect(QRectF(0, 0, s, s), s * 0.25, s * 0.25)
        cx, cy = s / 2, s / 2
        ro, ri = s * 0.35, s * 0.06
        p.setBrush(QBrush(QColor("#FFFFFF")))
        star = QPainterPath()
        star.moveTo(cx, cy - ro)
        star.cubicTo(cx + ri, cy - ri, cx + ri, cy - ri, cx + ro, cy)
        star.cubicTo(cx + ri, cy + ri, cx + ri, cy + ri, cx, cy + ro)
        star.cubicTo(cx - ri, cy + ri, cx - ri, cy + ri, cx - ro, cy)
        star.cubicTo(cx - ri, cy - ri, cx - ri, cy - ri, cx, cy - ro)
        p.drawPath(star)

    return _make_pixmap(size, draw)


# ─── Plagiarism check: shield + checkmark ───
def icon_plagiarism_check(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Shield outline
        path = QPainterPath()
        path.moveTo(s * 0.50, s * 0.08)
        path.lineTo(s * 0.15, s * 0.22)
        path.lineTo(s * 0.15, s * 0.55)
        path.cubicTo(s * 0.15, s * 0.78, s * 0.50, s * 0.92, s * 0.50, s * 0.92)
        path.cubicTo(s * 0.50, s * 0.92, s * 0.85, s * 0.78, s * 0.85, s * 0.55)
        path.lineTo(s * 0.85, s * 0.22)
        path.closeSubpath()
        p.drawPath(path)
        # Checkmark inside
        p.setPen(_pen("#10A37F", 2.2))
        p.drawLine(QPointF(s * 0.32, s * 0.50), QPointF(s * 0.45, s * 0.64))
        p.drawLine(QPointF(s * 0.45, s * 0.64), QPointF(s * 0.68, s * 0.36))

    return _make_pixmap(size, draw)


# ─── Rewrite: circular arrows ───
def icon_rewrite(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Circular arc (top half)
        path1 = QPainterPath()
        path1.moveTo(s * 0.72, s * 0.25)
        path1.cubicTo(s * 0.88, s * 0.38, s * 0.88, s * 0.62, s * 0.72, s * 0.75)
        p.drawPath(path1)
        # Circular arc (bottom half)
        path2 = QPainterPath()
        path2.moveTo(s * 0.28, s * 0.75)
        path2.cubicTo(s * 0.12, s * 0.62, s * 0.12, s * 0.38, s * 0.28, s * 0.25)
        p.drawPath(path2)
        # Arrow head top-right
        p.drawLine(QPointF(s * 0.72, s * 0.25), QPointF(s * 0.60, s * 0.20))
        p.drawLine(QPointF(s * 0.72, s * 0.25), QPointF(s * 0.72, s * 0.38))
        # Arrow head bottom-left
        p.drawLine(QPointF(s * 0.28, s * 0.75), QPointF(s * 0.40, s * 0.80))
        p.drawLine(QPointF(s * 0.28, s * 0.75), QPointF(s * 0.28, s * 0.62))

    return _make_pixmap(size, draw)


# ─── Chart: bar chart icon ───
def icon_chart(size=20):
    """数据图 — 柱状图图标。"""

    def draw(p, s):
        p.setPen(_pen("#444444", 1.8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Bottom axis line
        p.drawLine(QPointF(s * 0.12, s * 0.85), QPointF(s * 0.88, s * 0.85))
        # Left axis line
        p.drawLine(QPointF(s * 0.12, s * 0.12), QPointF(s * 0.12, s * 0.85))
        # Bars (filled)
        p.setPen(Qt.PenStyle.NoPen)
        # Bar 1 (short, blue)
        p.setBrush(QBrush(QColor("#4A90D9")))
        p.drawRoundedRect(QRectF(s * 0.20, s * 0.58, s * 0.13, s * 0.27), 1.5, 1.5)
        # Bar 2 (tall, green)
        p.setBrush(QBrush(QColor("#27AE60")))
        p.drawRoundedRect(QRectF(s * 0.38, s * 0.30, s * 0.13, s * 0.55), 1.5, 1.5)
        # Bar 3 (medium, orange)
        p.setBrush(QBrush(QColor("#F39C12")))
        p.drawRoundedRect(QRectF(s * 0.56, s * 0.45, s * 0.13, s * 0.40), 1.5, 1.5)
        # Bar 4 (tallest, red)
        p.setBrush(QBrush(QColor("#E74C3C")))
        p.drawRoundedRect(QRectF(s * 0.74, s * 0.20, s * 0.13, s * 0.65), 1.5, 1.5)

    return _make_pixmap(size, draw)


# ─── Formula: Σ sigma symbol ───
def icon_formula(size=20):
    """公式 — Σ 求和符号图标。"""

    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        # Σ shape
        path = QPainterPath()
        path.moveTo(s * 0.78, s * 0.15)
        path.lineTo(s * 0.22, s * 0.15)
        path.lineTo(s * 0.50, s * 0.50)
        path.lineTo(s * 0.22, s * 0.85)
        path.lineTo(s * 0.78, s * 0.85)
        p.drawPath(path)
        # small decorative dots
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#4A90D9")))
        p.drawEllipse(QPointF(s * 0.82, s * 0.15), s * 0.04, s * 0.04)
        p.drawEllipse(QPointF(s * 0.82, s * 0.85), s * 0.04, s * 0.04)

    return _make_pixmap(size, draw)


# ─── Subscript: X + lowered 2 ───
def icon_subscript(size=20):
    def draw(p, s):
        p.setPen(_pen("#444444", 2.0))
        p.drawLine(QPointF(s * 0.10, s * 0.18), QPointF(s * 0.48, s * 0.70))
        p.drawLine(QPointF(s * 0.48, s * 0.18), QPointF(s * 0.10, s * 0.70))
        p.setPen(_pen("#444444", 1.5))
        path = QPainterPath()
        path.moveTo(s * 0.58, s * 0.62)
        path.cubicTo(s * 0.58, s * 0.50, s * 0.88, s * 0.50, s * 0.88, s * 0.62)
        path.lineTo(s * 0.58, s * 0.82)
        path.lineTo(s * 0.88, s * 0.82)
        p.drawPath(path)

    return _make_pixmap(size, draw)
