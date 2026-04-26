"""
docx_exporter_v2.py — 文表智联 强化版 DOCX 导出器
===================================================
特性：
  · 三线表 / 全边框表
  · 嵌入本地图片
  · 页码页脚 (PAGE / NUMPAGES)
  · Word 目录字段 (TOC)
  · 脚注收集附录
  · 封面页
  · 三种预设样式：学术 / 现代 / 经典
  · 嵌套有序/无序列表
  · 代码块语言标签 + 灰底
  · 完整内联格式：粗/斜/下划线/删除线/行内代码/上下标
"""

from __future__ import annotations

import datetime
import os
import re
from html.parser import HTMLParser

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from app.core.markdown_renderer import MarkdownRenderer

# ---------------------------------------------------------------------------
# Style presets
# ---------------------------------------------------------------------------

PRESETS: dict[str, dict] = {
    "academic": {
        "label": "学术",
        "font_body": "宋体",
        "font_heading": "黑体",
        "font_mono": "Courier New",
        "size_body": 12,
        "size_h1": 18,
        "size_h2": 15,
        "size_h3": 13,
        "line_spacing": 1.5,
        "h1_align": WD_ALIGN_PARAGRAPH.CENTER,
        "color_heading": RGBColor(0, 0, 0),
        "margins": (2.54, 2.54, 3.17, 3.17),  # top bottom left right cm
    },
    "modern": {
        "label": "现代",
        "font_body": "Microsoft YaHei",
        "font_heading": "Microsoft YaHei",
        "font_mono": "Cascadia Code",
        "size_body": 11,
        "size_h1": 20,
        "size_h2": 15,
        "size_h3": 13,
        "line_spacing": 1.15,
        "h1_align": WD_ALIGN_PARAGRAPH.LEFT,
        "color_heading": RGBColor(26, 91, 180),
        "margins": (2.0, 2.0, 2.5, 2.5),
    },
    "classic": {
        "label": "经典",
        "font_body": "仿宋",
        "font_heading": "黑体",
        "font_mono": "Courier New",
        "size_body": 12,
        "size_h1": 18,
        "size_h2": 15,
        "size_h3": 13,
        "line_spacing": 2.0,
        "h1_align": WD_ALIGN_PARAGRAPH.CENTER,
        "color_heading": RGBColor(50, 50, 50),
        "margins": (3.0, 2.54, 3.17, 3.17),
    },
}

TABLE_STYLE_THREELINE = "threeline"
TABLE_STYLE_FULL = "full"


# ---------------------------------------------------------------------------
# Low-level XML helpers
# ---------------------------------------------------------------------------


def _set_para_spacing(para, ls: float) -> None:
    """Set paragraph line spacing (multiple) and zero before/after."""
    pPr = para._p.get_or_add_pPr()
    for old in pPr.findall(qn("w:spacing")):
        pPr.remove(old)
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:line"), str(int(ls * 240)))
    sp.set(qn("w:lineRule"), "auto")
    sp.set(qn("w:before"), "0")
    sp.set(qn("w:after"), "80")
    pPr.append(sp)


def _set_run_font(run, name: str, size_pt: float, color: RGBColor | None = None) -> None:
    """Apply font name (including East-Asian), size, and optional color to a run."""
    run.font.name = name
    run.font.size = Pt(size_pt)
    if color:
        run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), name)


def _para_shade(para, fill: str) -> None:
    """Shade a paragraph background with a hex colour (no '#')."""
    pPr = para._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def _run_shade(run, fill: str) -> None:
    """Shade a run's character background."""
    rPr = run._r.get_or_add_rPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    rPr.append(shd)


def _para_indent(para, left: int, right: int = 0, hanging: int = 0) -> None:
    pPr = para._p.get_or_add_pPr()
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), str(left))
    if right:
        ind.set(qn("w:right"), str(right))
    if hanging:
        ind.set(qn("w:hanging"), str(hanging))
    pPr.append(ind)


def _set_table_no_borders(table) -> None:
    """Remove all borders from a table (base for three-line table)."""
    tbl = table._tbl
    tblPr = tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    tblBorders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "none")
        tblBorders.append(e)
    tblPr.append(tblBorders)


def _set_cell_borders(cell, **sides) -> None:
    """
    Set explicit borders on one table cell.
    sides: top={"sz":12,"val":"single","color":"000000"}, ...
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("w:tcBorders")):
        tcPr.remove(old)
    tcBorders = OxmlElement("w:tcBorders")
    for side, props in sides.items():
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), props.get("val", "single"))
        e.set(qn("w:sz"), str(props.get("sz", 6)))
        e.set(qn("w:color"), props.get("color", "000000"))
        e.set(qn("w:space"), "0")
        tcBorders.append(e)
    tcPr.append(tcBorders)


def _add_page_number_footer(section) -> None:
    """Insert 'PAGE / NUMPAGES' field into section footer, centred."""
    footer = section.footer
    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.clear()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _field(instr: str):
        r = OxmlElement("w:r")
        fc1 = OxmlElement("w:fldChar")
        fc1.set(qn("w:fldCharType"), "begin")
        it = OxmlElement("w:instrText")
        it.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        it.text = instr
        fc2 = OxmlElement("w:fldChar")
        fc2.set(qn("w:fldCharType"), "end")
        r.extend([fc1, it, fc2])
        return r

    para._p.append(_field(" PAGE "))
    sep = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = " / "
    sep.append(t)
    para._p.append(sep)
    para._p.append(_field(" NUMPAGES "))


def _insert_toc_field(doc: Document) -> None:
    """Prepend a '目录' heading + TOC field at the very start of the document."""
    body = doc.element.body

    # --- TOC field paragraph ---
    p_toc = OxmlElement("w:p")
    r1 = OxmlElement("w:r")
    fc1 = OxmlElement("w:fldChar")
    fc1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText")
    it.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    it.text = ' TOC \\o "1-3" \\h \\z \\u '
    fc_s = OxmlElement("w:fldChar")
    fc_s.set(qn("w:fldCharType"), "separate")
    r_ph = OxmlElement("w:r")
    t_ph = OxmlElement("w:t")
    t_ph.text = "[在 Word 中按 Ctrl+A 后按 F9 更新目录]"
    r_ph.append(t_ph)
    fc2 = OxmlElement("w:fldChar")
    fc2.set(qn("w:fldCharType"), "end")
    r2 = OxmlElement("w:r")
    r2.append(fc2)
    r1.extend([fc1, it, fc_s])
    p_toc.extend([r1, r_ph, r2])

    # --- '目录' heading paragraph ---
    p_h = OxmlElement("w:p")
    pPr_h = OxmlElement("w:pPr")
    pSt = OxmlElement("w:pStyle")
    pSt.set(qn("w:val"), "Heading1")
    pPr_h.append(pSt)
    p_h.append(pPr_h)
    r_h = OxmlElement("w:r")
    t_h = OxmlElement("w:t")
    t_h.text = "目录"
    r_h.append(t_h)
    p_h.append(r_h)

    # --- Page break to separate TOC from content ---
    p_br = OxmlElement("w:p")
    r_br = OxmlElement("w:r")
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    r_br.append(br)
    p_br.append(r_br)

    # Insert at position 0 (before all existing content)
    body.insert(0, p_br)
    body.insert(0, p_toc)
    body.insert(0, p_h)


# ---------------------------------------------------------------------------
# HTML → DOCX state-machine parser
# ---------------------------------------------------------------------------


class _DocxHTMLParser(HTMLParser):
    """
    Walk rendered Markdown HTML and populate a python-docx Document.

    Block-level tags open new paragraphs.
    Inline tags modify the _fmt dict that drives run attributes.
    Table cells are buffered then committed.
    Footnote div content is collected and returned via .fn_items.
    """

    def __init__(
        self,
        doc: Document,
        preset: dict,
        table_style: str = TABLE_STYLE_THREELINE,
        file_dir: str = "",
    ) -> None:
        super().__init__(convert_charrefs=True)
        self._doc = doc
        self._p = preset
        self._ts = table_style
        self._file_dir = file_dir

        # Current paragraph
        self._para = None

        # Inline formatting  { flag: count_or_True }
        self._fmt: dict = {}

        # Tag tracking
        self._stack: list[str] = []

        # PRE state
        self._in_pre = False

        # BLOCKQUOTE depth
        self._bq_depth = 0

        # LIST stack  ["ul" | "ol"]
        self._list_stack: list[str] = []
        self._in_li = False

        # TABLE accumulation
        self._in_table = False
        self._tbl_rows: list[list[dict]] = []
        self._tbl_row: list[dict] = []
        self._cell_buf = ""
        self._cell_is_hdr = False
        self._in_cell = False

        # HIGHLIGHT div (codehilite wrapper)
        self._in_highlight = False
        self._highlight_lang = ""

        # FOOTNOTE div
        self._in_fn_div = False
        self._fn_id_buf = ""
        self._fn_txt_buf = ""
        self.fn_items: dict[str, str] = {}  # public: id → text

    # -----------------------------------------------------------------------
    # Paragraph helpers
    # -----------------------------------------------------------------------

    def _open_para(self, style: str | None = None) -> None:
        try:
            self._para = (
                self._doc.add_paragraph(style=style) if style else self._doc.add_paragraph()
            )
        except Exception:
            self._para = self._doc.add_paragraph()
        _set_para_spacing(self._para, self._p.get("line_spacing", 1.5))

    def _ensure_para(self) -> None:
        if self._para is None:
            self._open_para()

    def _emit(self, text: str) -> None:
        """Emit a formatted run, honouring all current inline flags."""
        if self._in_cell:
            self._cell_buf += text
            return
        if self._in_fn_div:
            self._fn_txt_buf += text
            return
        self._ensure_para()
        run = self._para.add_run(text)
        is_code = bool(self._fmt.get("code")) or self._in_pre
        fn = self._p["font_mono"] if is_code else self._p["font_body"]
        sz = self._p["size_body"] * (0.9 if is_code else 1.0)
        _set_run_font(run, fn, sz)
        run.bold = bool(self._fmt.get("bold"))
        run.italic = bool(self._fmt.get("italic"))
        run.underline = bool(self._fmt.get("underline"))
        if self._fmt.get("strike"):
            run.font.strike = True
        if self._fmt.get("sup"):
            run.font.superscript = True
        if self._fmt.get("sub"):
            run.font.subscript = True
        if is_code and not self._in_pre:
            _run_shade(run, "F0F4F8")

    def _dec_fmt(self, key: str) -> None:
        """Decrement a reference-counted inline-format flag."""
        v = self._fmt.get(key, 1) - 1
        if v <= 0:
            self._fmt.pop(key, None)
        else:
            self._fmt[key] = v

    # -----------------------------------------------------------------------
    # Start-tag dispatcher
    # -----------------------------------------------------------------------

    def handle_starttag(self, tag: str, attrs):
        a = dict(attrs)
        self._stack.append(tag)

        # ---------- headings ----------
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            lvl = int(tag[1])
            self._open_para(f"Heading {lvl}")
            if lvl == 1:
                self._para.alignment = self._p.get("h1_align", WD_ALIGN_PARAGRAPH.LEFT)
            return

        # ---------- paragraph ----------
        if tag == "p":
            if self._in_cell or self._in_li or self._in_fn_div:
                # inside a cell/li/footnote: treat as line-break separator
                if self._in_cell and self._cell_buf:
                    self._cell_buf += "\n"
                return
            self._open_para()
            return

        # ---------- line break ----------
        if tag == "br":
            if self._para:
                self._para.add_run().add_break()
            return

        # ---------- horizontal rule ----------
        if tag == "hr":
            if self._in_fn_div:
                return
            p = self._doc.add_paragraph()
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement("w:pBdr")
            b = OxmlElement("w:bottom")
            b.set(qn("w:val"), "single")
            b.set(qn("w:sz"), "6")
            b.set(qn("w:color"), "999999")
            pBdr.append(b)
            pPr.append(pBdr)
            return

        # ---------- preformatted ----------
        if tag == "pre":
            self._in_pre = True
            self._open_para()
            _para_indent(self._para, 360)
            _para_shade(self._para, "F5F5F5")
            return

        if tag == "code":
            if not self._in_pre:
                self._fmt["code"] = self._fmt.get("code", 0) + 1
            return

        # ---------- blockquote ----------
        if tag == "blockquote":
            self._bq_depth += 1
            self._open_para()
            _para_indent(self._para, 720 * self._bq_depth, 360)
            _para_shade(self._para, "F8F9FF")
            return

        # ---------- lists ----------
        if tag == "ul":
            self._list_stack.append("ul")
            return
        if tag == "ol":
            self._list_stack.append("ol")
            return

        if tag == "li":
            if self._in_fn_div:
                # footnote item
                fn_id = re.sub(r"^fn:", "", a.get("id", ""))
                self._fn_id_buf = fn_id
                self._fn_txt_buf = ""
                return
            self._in_li = True
            depth = max(0, len(self._list_stack) - 1)
            ltype = self._list_stack[-1] if self._list_stack else "ul"
            sty = "List Bullet" if ltype == "ul" else "List Number"
            try:
                self._para = self._doc.add_paragraph(style=sty)
            except Exception:
                self._para = self._doc.add_paragraph()
            _set_para_spacing(self._para, self._p["line_spacing"])
            if depth > 0:
                _para_indent(self._para, 720 + depth * 360, hanging=360)
            return

        # ---------- table structure ----------
        if tag == "table":
            self._in_table = True
            self._tbl_rows = []
            return
        if tag in ("thead", "tbody", "tfoot"):
            return
        if tag == "tr":
            self._tbl_row = []
            return
        if tag in ("th", "td"):
            self._in_cell = True
            self._cell_buf = ""
            self._cell_is_hdr = tag == "th"
            return

        # ---------- image ----------
        if tag == "img":
            self._insert_image(a.get("src", ""), a.get("alt", ""))
            return

        # ---------- div containers ----------
        if tag == "div":
            cls = a.get("class", "")
            if "highlight" in cls:
                self._in_highlight = True
                m = re.search(r"language-(\w+)", cls)
                self._highlight_lang = m.group(1) if m else ""
            elif "footnote" in cls:
                self._in_fn_div = True
            return

        # ---------- inline formatting ----------
        if tag in ("strong", "b"):
            self._fmt["bold"] = self._fmt.get("bold", 0) + 1
        elif tag in ("em", "i"):
            self._fmt["italic"] = self._fmt.get("italic", 0) + 1
        elif tag == "u":
            self._fmt["underline"] = self._fmt.get("underline", 0) + 1
        elif tag in ("del", "s"):
            self._fmt["strike"] = self._fmt.get("strike", 0) + 1
        elif tag == "sup":
            self._fmt["sup"] = self._fmt.get("sup", 0) + 1
        elif tag == "sub":
            self._fmt["sub"] = self._fmt.get("sub", 0) + 1
        elif tag == "a":
            self._fmt["link_href"] = a.get("href", "")
        elif tag == "mark":
            self._fmt["highlight"] = True
        elif tag == "span":
            m = re.search(r"color:\s*([#\w]+)", a.get("style", ""))
            if m:
                self._fmt["color"] = m.group(1)

    # -----------------------------------------------------------------------
    # End-tag dispatcher
    # -----------------------------------------------------------------------

    def handle_endtag(self, tag: str):
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return

        if tag == "pre":
            self._in_pre = False
            return

        if tag == "code":
            self._dec_fmt("code")
            return

        if tag == "blockquote":
            self._bq_depth = max(0, self._bq_depth - 1)
            return

        if tag == "ul":
            if self._list_stack:
                self._list_stack.pop()
            return
        if tag == "ol":
            if self._list_stack:
                self._list_stack.pop()
            return

        if tag == "li":
            if self._in_fn_div and self._fn_id_buf:
                self.fn_items[self._fn_id_buf] = self._fn_txt_buf
                self._fn_id_buf = self._fn_txt_buf = ""
            self._in_li = False
            return

        if tag in ("th", "td"):
            self._tbl_row.append(
                {
                    "text": self._cell_buf,
                    "is_header": self._cell_is_hdr,
                }
            )
            self._in_cell = False
            self._cell_buf = ""
            return

        if tag == "tr":
            if self._tbl_row:
                self._tbl_rows.append(self._tbl_row)
            self._tbl_row = []
            return

        if tag == "table":
            self._build_table()
            self._in_table = False
            return

        if tag == "div":
            if self._in_highlight:
                self._in_highlight = False
            if self._in_fn_div:
                self._in_fn_div = False
            return

        # inline
        if tag in ("strong", "b"):
            self._dec_fmt("bold")
        elif tag in ("em", "i"):
            self._dec_fmt("italic")
        elif tag == "u":
            self._dec_fmt("underline")
        elif tag in ("del", "s"):
            self._dec_fmt("strike")
        elif tag == "sup":
            self._dec_fmt("sup")
        elif tag == "sub":
            self._dec_fmt("sub")
        elif tag == "a":
            self._fmt.pop("link_href", None)
        elif tag == "mark":
            self._fmt.pop("highlight", None)
        elif tag == "span":
            self._fmt.pop("color", None)

    # -----------------------------------------------------------------------
    # Character data
    # -----------------------------------------------------------------------

    def handle_data(self, data: str):
        if not data:
            return

        if self._in_cell:
            self._cell_buf += data
            return

        if self._in_fn_div:
            self._fn_txt_buf += data
            return

        if self._in_pre:
            self._ensure_para()
            lines = data.split("\n")
            for i, line in enumerate(lines):
                if i > 0:
                    r_br = OxmlElement("w:r")
                    br = OxmlElement("w:br")
                    r_br.append(br)
                    self._para._p.append(r_br)
                run = self._para.add_run(line)
                _set_run_font(run, self._p["font_mono"], self._p["size_body"] * 0.9)
            return

        self._emit(data)

    # -----------------------------------------------------------------------
    # Table renderer
    # -----------------------------------------------------------------------

    def _build_table(self) -> None:
        if not self._tbl_rows:
            return
        num_rows = len(self._tbl_rows)
        num_cols = max(len(r) for r in self._tbl_rows)

        # Header row indices
        hdr_rows = {i for i, row in enumerate(self._tbl_rows) if row and row[0].get("is_header")}
        last_hdr = max(hdr_rows) if hdr_rows else -1

        table = self._doc.add_table(rows=num_rows, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        if self._ts == TABLE_STYLE_THREELINE:
            _set_table_no_borders(table)

        for r_idx, row_data in enumerate(self._tbl_rows):
            is_first = r_idx == 0
            is_last = r_idx == num_rows - 1
            is_hdr_row = r_idx in hdr_rows

            for c_idx in range(min(len(row_data), num_cols)):
                cd = row_data[c_idx]
                cell = table.rows[r_idx].cells[c_idx]
                cell.text = ""
                para = cell.paragraphs[0]
                _set_para_spacing(para, self._p["line_spacing"])
                run = para.add_run(cd["text"])
                run.bold = cd.get("is_header", False)
                _set_run_font(run, self._p["font_body"], self._p["size_body"])

                if self._ts == TABLE_STYLE_THREELINE:
                    borders: dict = {}
                    if is_first:
                        borders["top"] = {"sz": 12}
                    if is_last:
                        borders["bottom"] = {"sz": 12}
                    if r_idx == last_hdr and last_hdr >= 0:
                        # thin separator between header and body
                        borders["bottom"] = {"sz": 6}
                    if borders:
                        _set_cell_borders(cell, **borders)

    # -----------------------------------------------------------------------
    # Image insertion
    # -----------------------------------------------------------------------

    def _insert_image(self, src: str, alt: str) -> None:
        if not os.path.isabs(src) and self._file_dir:
            candidate = os.path.join(self._file_dir, src)
            if os.path.isfile(candidate):
                src = candidate

        if os.path.isfile(src):
            try:
                p_img = self._doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.add_run().add_picture(src, width=Inches(5.0))
                if alt:
                    p_cap = self._doc.add_paragraph()
                    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    r = p_cap.add_run(f"▲ {alt}")
                    r.italic = True
                    _set_run_font(r, self._p["font_body"], 10)
                return
            except Exception:
                pass

        self._ensure_para()
        self._emit(f"[图片: {alt or src}]")


# ---------------------------------------------------------------------------
# Public exporter class
# ---------------------------------------------------------------------------


class EnhancedDocxExporter:
    """
    强化版 DOCX 导出器。

    用法::

        exporter = EnhancedDocxExporter()
        exporter.export(
            markdown_text = "# 标题\\n正文...",
            output_path   = "output.docx",
            style         = "academic",   # academic / modern / classic
            title         = "我的论文",
            author        = "张三",
            add_cover     = True,
            add_toc       = True,
            add_page_numbers = True,
            table_style   = "threeline",  # threeline / full
            file_dir      = "/path/to/markdown/file",
        )
    """

    def __init__(self) -> None:
        self._renderer = MarkdownRenderer()

    def export(
        self,
        markdown_text: str,
        output_path: str,
        *,
        style: str = "academic",
        title: str = "",
        author: str = "",
        add_cover: bool = False,
        add_toc: bool = False,
        add_page_numbers: bool = True,
        table_style: str = TABLE_STYLE_THREELINE,
        file_dir: str = "",
    ) -> None:
        preset = PRESETS.get(style, PRESETS["academic"])
        doc = Document()

        self._setup_margins(doc, preset)

        if add_page_numbers:
            _add_page_number_footer(doc.sections[0])

        if add_cover and (title or author):
            self._build_cover(doc, title, author, preset)

        # Render Markdown → HTML (reuses the same pipeline as the preview)
        html = self._renderer.render(markdown_text)

        # Walk HTML → DOCX
        parser = _DocxHTMLParser(
            doc,
            preset,
            table_style=table_style,
            file_dir=file_dir,
        )
        parser.feed(html)

        # Append footnotes section if any were collected
        if parser.fn_items:
            self._build_footnotes(doc, parser.fn_items, preset)

        # Prepend TOC (must be done last so it sits before body content)
        if add_toc:
            _insert_toc_field(doc)

        doc.save(output_path)

    # -----------------------------------------------------------------------

    def _setup_margins(self, doc: Document, preset: dict) -> None:
        sec = doc.sections[0]
        t, b, l, r = preset.get("margins", (2.54, 2.54, 3.17, 3.17))
        sec.top_margin = Cm(t)
        sec.bottom_margin = Cm(b)
        sec.left_margin = Cm(l)
        sec.right_margin = Cm(r)

    def _build_cover(self, doc: Document, title: str, author: str, preset: dict) -> None:
        # Vertical padding (~one-third down the page)
        for _ in range(8):
            p = doc.add_paragraph()
            _set_para_spacing(p, 1.0)

        if title:
            p_t = doc.add_paragraph()
            p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p_t.add_run(title)
            r.bold = True
            _set_run_font(
                r, preset["font_heading"], 26, preset.get("color_heading", RGBColor(0, 0, 0))
            )

        doc.add_paragraph()  # spacer

        if author:
            p_a = doc.add_paragraph()
            p_a.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p_a.add_run(author)
            _set_run_font(r, preset["font_body"], 14)

        p_d = doc.add_paragraph()
        p_d.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p_d.add_run(datetime.date.today().strftime("%Y 年 %m 月"))
        _set_run_font(r, preset["font_body"], 12)

        doc.add_page_break()

    def _build_footnotes(self, doc: Document, fn_items: dict[str, str], preset: dict) -> None:
        doc.add_paragraph()

        # Divider line
        p_div = doc.add_paragraph()
        pPr = p_div._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        top = OxmlElement("w:top")
        top.set(qn("w:val"), "single")
        top.set(qn("w:sz"), "6")
        top.set(qn("w:color"), "999999")
        pBdr.append(top)
        pPr.append(pBdr)

        # "注释" heading
        p_h = doc.add_paragraph()
        r = p_h.add_run("注释")
        r.bold = True
        _set_run_font(r, preset["font_heading"], 13)

        for fn_id, fn_text in fn_items.items():
            # Strip the backref arrow character if present
            clean = re.sub(r"\s*↩\s*$", "", fn_text).strip()
            p = doc.add_paragraph()
            _set_para_spacing(p, preset["line_spacing"])
            r1 = p.add_run(f"[{fn_id}]  ")
            r1.bold = True
            _set_run_font(r1, preset["font_body"], preset["size_body"] * 0.9)
            r2 = p.add_run(clean)
            _set_run_font(r2, preset["font_body"], preset["size_body"] * 0.9)
