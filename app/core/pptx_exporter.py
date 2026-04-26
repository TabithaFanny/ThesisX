"""
pptx_exporter.py — 文表智联 PPTX 导出器
=========================================
将 Markdown 内容自动转换为 PowerPoint 演示文稿。

规则：
  · H1 → 封面/章节标题页（大字居中）
  · H2 → 内容页（标题 + 正文区）
  · H3 → 正文中的加粗小标题
  · 段落 / 列表 / 代码 / 引用 → 正文文本
  · 表格 → PPT 表格（嵌入内容页或独占页面）
  · 图片 → 嵌入幻灯片（本地路径）
  · --- 分隔线 → 强制换页
  · 无标题文档 → 按段落自动分组

三种主题：academic（学术）/ modern（现代）/ classic（经典）
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm, Pt

# ---------------------------------------------------------------------------
# 主题预设
# ---------------------------------------------------------------------------

PRESETS: dict[str, dict] = {
    "academic": {
        "bg": (255, 255, 255),
        "accent": (16, 80, 159),
        "title_color": (26, 26, 26),
        "body_color": (51, 51, 51),
        "title_font": "黑体",
        "body_font": "宋体",
    },
    "modern": {
        "bg": (247, 249, 252),
        "accent": (26, 91, 180),
        "title_color": (26, 91, 180),
        "body_color": (51, 51, 51),
        "title_font": "微软雅黑",
        "body_font": "微软雅黑",
    },
    "classic": {
        "bg": (255, 251, 240),
        "accent": (139, 69, 19),
        "title_color": (50, 50, 50),
        "body_color": (68, 68, 68),
        "title_font": "仿宋",
        "body_font": "仿宋",
    },
}


def _rgb(t) -> RGBColor:
    return RGBColor(*t)


def _shade(color, delta: int = -40):
    """让颜色变深（delta<0）或变浅（delta>0）。"""
    return tuple(max(0, min(255, c + delta)) for c in color)


# ---------------------------------------------------------------------------
# 行内 Markdown 解析
# ---------------------------------------------------------------------------


def _parse_inline(text: str) -> List[Dict]:
    """解析 **bold** / *italic* / `code` 行内标记，返回 run 列表。"""
    runs: List[Dict] = []
    pat = re.compile(
        r"\*\*\*(.+?)\*\*\*"  # bold+italic
        r"|\*\*(.+?)\*\*"  # bold
        r"|__(.+?)__"  # bold alt
        r"|`([^`]+)`"  # code
        r"|\*(.+?)\*"  # italic
        r"|_(.+?)_"  # italic alt
    )
    last = 0
    for m in pat.finditer(text):
        if m.start() > last:
            runs.append(
                {"text": text[last : m.start()], "bold": False, "italic": False, "code": False}
            )
        g = m.groups()
        if g[0]:
            runs.append({"text": g[0], "bold": True, "italic": True, "code": False})
        elif g[1] or g[2]:
            runs.append({"text": g[1] or g[2], "bold": True, "italic": False, "code": False})
        elif g[3]:
            runs.append({"text": g[3], "bold": False, "italic": False, "code": True})
        elif g[4] or g[5]:
            runs.append({"text": g[4] or g[5], "bold": False, "italic": True, "code": False})
        last = m.end()
    if last < len(text):
        runs.append({"text": text[last:], "bold": False, "italic": False, "code": False})
    return runs or [{"text": text, "bold": False, "italic": False, "code": False}]


# ---------------------------------------------------------------------------
# Markdown 块解析
# ---------------------------------------------------------------------------


class _Block:
    __slots__ = ("type", "level", "content", "items", "header", "rows", "lang", "src", "alt")

    def __init__(self, type_: str, **kw):
        self.type = type_
        self.level = 0
        self.content = ""
        self.items = []
        self.header = []
        self.rows = []
        self.lang = ""
        self.src = ""
        self.alt = ""
        for k, v in kw.items():
            setattr(self, k, v)


def _parse_md(text: str) -> List[_Block]:
    blocks: List[_Block] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if not s:
            i += 1
            continue

        # Heading
        m = re.match(r"^(#{1,6})\s+(.+)$", s)
        if m:
            blocks.append(_Block("heading", level=len(m.group(1)), content=m.group(2).strip()))
            i += 1
            continue

        # HR
        if re.match(r"^[-*_]{3,}$", s):
            blocks.append(_Block("hr"))
            i += 1
            continue

        # Code fence
        if s.startswith("```"):
            lang = s[3:].strip()
            code_lines: List[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            blocks.append(_Block("code", lang=lang, content="\n".join(code_lines)))
            continue

        # Table
        if s.startswith("|"):
            tbl: List[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl.append(lines[i].strip())
                i += 1
            if len(tbl) >= 2 and re.match(r"^\|[-: |]+\|$", tbl[1]):
                header = [c.strip() for c in tbl[0].strip("|").split("|")]
                rows = [[c.strip() for c in l.strip("|").split("|")] for l in tbl[2:]]
                blocks.append(_Block("table", header=header, rows=rows))
            continue

        # List (unordered / ordered)
        if re.match(r"^\s*([-*+]|\d+\.)\s", raw):
            items: List[Dict] = []
            while i < len(lines):
                l = lines[i]
                um = re.match(r"^(\s*)([-*+])\s+(.+)$", l)
                om = re.match(r"^(\s*)(\d+)\.\s+(.+)$", l)
                if um:
                    items.append(
                        {"level": len(um.group(1)) // 2, "content": um.group(3), "ordered": False}
                    )
                    i += 1
                elif om:
                    items.append(
                        {"level": len(om.group(1)) // 2, "content": om.group(3), "ordered": True}
                    )
                    i += 1
                elif not l.strip():
                    i += 1
                    k = i
                    while k < len(lines) and not lines[k].strip():
                        k += 1
                    if k < len(lines) and re.match(r"^\s*([-*+]|\d+\.)\s", lines[k]):
                        continue
                    break
                else:
                    break
            if items:
                blocks.append(_Block("list", items=items))
            continue

        # Blockquote
        if s.startswith(">"):
            q: List[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip().lstrip(">").strip())
                i += 1
            blocks.append(_Block("quote", content=" ".join(q)))
            continue

        # Standalone image
        m_img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", s)
        if m_img:
            blocks.append(_Block("image", alt=m_img.group(1), src=m_img.group(2)))
            i += 1
            continue

        # Paragraph
        para: List[str] = []
        while i < len(lines):
            l = lines[i].strip()
            if not l:
                break
            if re.match(r"^#{1,6}\s", l):
                break
            if l.startswith("```") or l.startswith("|") or l.startswith(">"):
                break
            if re.match(r"^[-*_]{3,}$", l):
                break
            if re.match(r"^\s*([-*+]|\d+\.)\s", lines[i]):
                break
            para.append(l)
            i += 1
        if para:
            blocks.append(_Block("paragraph", content=" ".join(para)))
    return blocks


# ---------------------------------------------------------------------------
# 幻灯片分组
# ---------------------------------------------------------------------------


def _group_slides(blocks: List[_Block]) -> List[Dict]:
    slides: List[Dict] = []
    cur: Optional[Dict] = None

    def flush():
        nonlocal cur
        if cur is not None:
            slides.append(cur)
            cur = None

    for b in blocks:
        if b.type == "heading":
            if b.level == 1:
                flush()
                cur = {"layout": "section", "title": b.content, "body": []}
            elif b.level == 2:
                flush()
                cur = {"layout": "content", "title": b.content, "body": []}
            else:  # H3–H6: sub-heading in body
                if cur is None:
                    cur = {"layout": "content", "title": b.content, "body": []}
                else:
                    cur["body"].append(b)
        elif b.type == "hr":
            if cur and cur["body"]:
                flush()
                cur = {"layout": "content", "title": "", "body": []}
        else:
            if cur is None:
                cur = {"layout": "content", "title": "", "body": []}
            cur["body"].append(b)

    flush()

    if not slides:
        return [{"layout": "content", "title": "演示文稿", "body": []}]

    # First H1 slide becomes cover
    if slides[0]["layout"] == "section":
        slides[0]["layout"] = "cover"

    return slides


# ---------------------------------------------------------------------------
# PptxExporter
# ---------------------------------------------------------------------------


class PptxExporter:
    """将 Markdown 导出为 PPTX 演示文稿。"""

    SLIDE_W = Cm(33.867)  # 16:9  宽
    SLIDE_H = Cm(19.05)  # 16:9  高
    MARGIN = Cm(1.27)

    def export(
        self,
        markdown_text: str,
        output_path: str,
        style: str = "academic",
        title: str = "",
        author: str = "",
    ) -> None:
        preset = PRESETS.get(style, PRESETS["academic"])
        blocks = _parse_md(markdown_text)
        slides = _group_slides(blocks)

        prs = Presentation()
        prs.slide_width = self.SLIDE_W
        prs.slide_height = self.SLIDE_H

        for sd in slides:
            layout = sd["layout"]
            if layout == "cover":
                self._cover(prs, sd, preset, author)
            elif layout == "section":
                self._section(prs, sd, preset)
            else:
                self._content(prs, sd, preset)

        prs.save(output_path)

    # ── 内部辅助 ──

    def _blank(self, prs: Presentation):
        """返回空白布局幻灯片。"""
        blank_idx = min(6, len(prs.slide_layouts) - 1)
        for idx, lay in enumerate(prs.slide_layouts):
            if lay.name.lower() in ("blank", "空白"):
                blank_idx = idx
                break
        return prs.slides.add_slide(prs.slide_layouts[blank_idx])

    def _bg(self, slide, color):
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = _rgb(color)

    def _bar(self, slide, left, top, w, h, color):
        s = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, left, top, w, h)
        s.fill.solid()
        s.fill.fore_color.rgb = _rgb(color)
        s.line.color.rgb = _rgb(color)
        return s

    # ── 幻灯片类型 ──

    def _cover(self, prs, sd, preset, author):
        """封面页：上 62% 为 accent 大色块，下 38% 为白色，白色主标题。"""
        slide = self._blank(prs)
        self._bg(slide, (255, 255, 255))
        W, H, M = self.SLIDE_W, self.SLIDE_H, self.MARGIN

        split_y = int(H * 0.62)

        # 上半段大色块
        self._bar(slide, 0, 0, W, split_y, preset["accent"])
        # 色块下边缘加深细条，增加层次感
        self._bar(slide, 0, split_y, W, int(Cm(0.20)), _shade(preset["accent"], -45))

        # 主标题（白色，居中于色块内）
        tb = slide.shapes.add_textbox(
            int(M * 1.5), int(H * 0.08), int(W - M * 3), int(split_y - H * 0.10)
        )
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = sd["title"]
        r.font.name = preset["title_font"]
        r.font.size = Pt(40)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        # 副标题 / 作者（下方白色区，深色文字）
        sub = author
        if not sub:
            for b in sd.get("body", []):
                if b.type == "paragraph" and b.content:
                    sub = b.content[:120]
                    break
        if sub:
            tb2 = slide.shapes.add_textbox(
                int(M * 1.5), int(split_y + Cm(0.65)), int(W - M * 3), int(H - split_y - Cm(0.9))
            )
            tf2 = tb2.text_frame
            tf2.word_wrap = True
            p2 = tf2.paragraphs[0]
            p2.alignment = PP_ALIGN.CENTER
            r2 = p2.add_run()
            r2.text = sub
            r2.font.name = preset["body_font"]
            r2.font.size = Pt(18)
            r2.font.color.rgb = _rgb(preset["title_color"])

    def _section(self, prs, sd, preset):
        """章节页：全 accent 背景 + 右 68% 白色面板，标题写在面板内。"""
        slide = self._blank(prs)
        self._bg(slide, preset["accent"])
        W, H, M = self.SLIDE_W, self.SLIDE_H, self.MARGIN

        panel_x = int(W * 0.30)
        # 右侧白色面板
        self._bar(slide, panel_x, 0, W - panel_x, H, (255, 255, 255))

        # 标题文字
        tb = slide.shapes.add_textbox(
            panel_x + int(M), int(H * 0.26), W - panel_x - int(M * 1.5), int(H * 0.48)
        )
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = sd["title"]
        r.font.name = preset["title_font"]
        r.font.size = Pt(32)
        r.font.bold = True
        r.font.color.rgb = _rgb(preset["title_color"])

        # 装饰线（accent 色，在白色面板内标题下方）
        line_top = int(H * 0.26) + int(H * 0.48) + int(Cm(0.25))
        self._bar(
            slide,
            panel_x + int(M),
            line_top,
            int((W - panel_x) * 0.62),
            int(Cm(0.09)),
            preset["accent"],
        )

    def _content(self, prs, sd, preset):
        """内容页：全宽 accent 色标题栏（白字）+ 白色正文区。"""
        slide = self._blank(prs)
        self._bg(slide, preset["bg"])
        W, H, M = self.SLIDE_W, self.SLIDE_H, self.MARGIN

        # 彩色标题栏（全宽）
        title_bar_h = Cm(2.3)
        self._bar(slide, 0, 0, W, title_bar_h, preset["accent"])

        # 标题栏底边加深细条
        self._bar(slide, 0, title_bar_h, W, int(Cm(0.14)), _shade(preset["accent"], -35))

        # 标题文字（白色）
        tb = slide.shapes.add_textbox(M, int(Cm(0.32)), W - 2 * M, title_bar_h - int(Cm(0.18)))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        r = p.add_run()
        r.text = sd.get("title", "")
        r.font.name = preset["title_font"]
        r.font.size = Pt(22)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        # 正文区
        body_top = title_bar_h + int(Cm(0.14)) + Cm(0.35)
        body_h = H - body_top - Cm(0.4)
        body = sd.get("body", [])

        tables = [b for b in body if b.type == "table"]
        images = [b for b in body if b.type == "image"]
        text_blks = [b for b in body if b.type not in ("table", "image")]

        if tables:
            text_h = Cm(3.0) if text_blks else Cm(0)
            tbl_top = body_top + text_h + (Cm(0.3) if text_blks else 0)
            tbl_h = body_h - text_h - (Cm(0.3) if text_blks else 0)
            if text_blks:
                self._render_text(slide, text_blks, preset, M, body_top, W - 2 * M, text_h)
            for tbl in tables:
                self._render_table(slide, tbl, preset, M, tbl_top, W - 2 * M, tbl_h)
        elif images:
            self._render_image(slide, images[0], M, body_top, W - 2 * M, body_h)
            if text_blks:
                self._render_text(slide, text_blks, preset, M, body_top, W - 2 * M, Cm(2.5))
        else:
            self._render_text(slide, text_blks, preset, M, body_top, W - 2 * M, body_h)

    # ── 内容渲染器 ──

    def _render_text(self, slide, blocks, preset, left, top, width, height):
        if not blocks:
            return
        tb = slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.word_wrap = True
        first = True

        for b in blocks:
            if b.type == "paragraph":
                self._fmt_para(
                    tf, b.content, preset["body_font"], 16, preset["body_color"], first=first
                )
                first = False
            elif b.type == "heading":
                sz = {3: 18, 4: 16, 5: 15, 6: 14}.get(b.level, 16)
                self._plain_para(
                    tf,
                    b.content,
                    preset["title_font"],
                    sz,
                    preset["accent"],
                    bold=True,
                    first=first,
                )
                first = False
            elif b.type == "list":
                for it in b.items:
                    prefix = "  " * it.get("level", 0) + ("▸ " if it.get("ordered") else "• ")
                    self._fmt_para(
                        tf,
                        prefix + it["content"],
                        preset["body_font"],
                        15,
                        preset["body_color"],
                        first=first,
                    )
                    first = False
            elif b.type == "code":
                for line in (b.content or "").split("\n")[:14]:
                    self._plain_para(tf, line, "Courier New", 11, (0xD6, 0x33, 0x84), first=first)
                    first = False
            elif b.type == "quote":
                self._plain_para(
                    tf,
                    "❝ " + b.content,
                    preset["body_font"],
                    15,
                    preset["accent"],
                    italic=True,
                    first=first,
                )
                first = False

    def _fmt_para(
        self, tf, text: str, font: str, size: float, color, bold=False, italic=False, first=False
    ):
        """带行内 Markdown 格式的段落。"""
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        for rd in _parse_inline(text):
            run = p.add_run()
            run.text = rd["text"]
            if rd["code"]:
                run.font.name = "Courier New"
                run.font.size = Pt(max(10, size - 2))
                run.font.color.rgb = RGBColor(0xD6, 0x33, 0x84)
            else:
                run.font.name = font
                run.font.size = Pt(size)
                run.font.bold = rd["bold"] or bold
                run.font.italic = rd["italic"] or italic
                run.font.color.rgb = _rgb(color)

    def _plain_para(
        self, tf, text: str, font: str, size: float, color, bold=False, italic=False, first=False
    ):
        """纯文本段落（不解析行内 Markdown）。"""
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        run = p.add_run()
        run.text = text
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = _rgb(color)

    def _render_table(self, slide, blk, preset, left, top, width, height):
        header = blk.header or []
        rows = blk.rows or []
        n_cols = len(header) or (len(rows[0]) if rows else 0)
        if n_cols == 0:
            return
        rows = rows[:15]  # 最多显示 15 行
        n_rows = 1 + len(rows)
        actual_h = min(height, Cm(0.75) * n_rows + Cm(0.4))

        tbl_shp = slide.shapes.add_table(n_rows, n_cols, left, top, width, actual_h)
        tbl = tbl_shp.table
        col_w = width // n_cols
        for col in tbl.columns:
            col.width = col_w

        # 表头
        for c, h in enumerate(header[:n_cols]):
            cell = tbl.cell(0, c)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            run = p.add_run()
            run.text = h
            run.font.name = preset["title_font"]
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            cell.fill.solid()
            cell.fill.fore_color.rgb = _rgb(preset["accent"])

        # 数据行
        for r_i, row in enumerate(rows):
            for c_i in range(n_cols):
                cell = tbl.cell(r_i + 1, c_i)
                cell.text = ""
                val = row[c_i] if c_i < len(row) else ""
                p = cell.text_frame.paragraphs[0]
                run = p.add_run()
                run.text = val
                run.font.name = preset["body_font"]
                run.font.size = Pt(11)
                run.font.color.rgb = _rgb(preset["body_color"])
                if r_i % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(0xF2, 0xF4, 0xF8)

    def _render_image(self, slide, blk, left, top, width, height):
        src = blk.src or ""
        if src.startswith("data:"):
            return
        path = src if os.path.isabs(src) else os.path.abspath(src)
        if not os.path.isfile(path):
            return
        try:
            slide.shapes.add_picture(path, left, top, width, height)
        except Exception:
            pass
