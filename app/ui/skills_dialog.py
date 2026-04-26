"""Skills 集群记忆对话框"""

import json
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QLabel, QTextBrowser,
    QWidget, QFrame, QSplitter,
)

from app.ui.svg_icons import SvgIcons

logger = logging.getLogger(__name__)


class FileParserThread(QThread):
    """文件解析线程"""
    finished = pyqtSignal(str, str, str)  # path, content, error

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        try:
            from app.core.document_parser import DocumentParser
            content = DocumentParser.parse_file(self.file_path)
            if content is None:
                self.finished.emit(self.file_path, "", "无法解析文件")
            else:
                if len(content) > 50000:
                    content = content[:50000] + "\n\n... (内容过长，已截断)"
                self.finished.emit(self.file_path, content, "")
        except Exception as e:
            self.finished.emit(self.file_path, "", str(e))


def _markdown_to_html(text: str) -> str:
    """Markdown 转 HTML，WPS 风格渲染"""
    if not text:
        return ""

    # 转义 HTML 特殊字符
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    lines = text.split('\n')
    html_lines = []
    in_code_block = False
    in_table = False
    table_rows = []

    for line in lines:
        # 代码块
        if line.strip().startswith('```'):
            if in_code_block:
                html_lines.append('</pre>')
                in_code_block = False
            else:
                html_lines.append('<pre style="background:#f5f7fa;padding:12px 16px;border-radius:6px;font-family:Consolas,\'Courier New\',monospace;font-size:13px;border:1px solid #e4e7ed;margin:8px 0;overflow-x:auto;line-height:1.6;">')
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(line)
            continue

        # 页面/幻灯片分隔符 (PDF)
        page_match = re.match(r'^===\s*(.+?)\s*===$', line.strip())
        if page_match:
            if in_table:
                html_lines.append(_render_table(table_rows))
                table_rows = []
                in_table = False
            title = page_match.group(1)
            html_lines.append(f'<div style="background:linear-gradient(135deg,#409eff,#66b1ff);color:#fff;padding:8px 16px;margin:16px 0 10px 0;border-radius:6px;font-weight:600;font-size:13px;box-shadow:0 2px 4px rgba(64,158,255,0.3);">{title}</div>')
            continue

        # 页眉页脚标记 (DOCX)
        if line.strip().startswith('[页眉]') or line.strip().startswith('[页脚]'):
            if in_table:
                html_lines.append(_render_table(table_rows))
                table_rows = []
                in_table = False
            label = '页眉' if '[页眉]' in line else '页脚'
            content = line.replace('[页眉]', '').replace('[页脚]', '').strip()
            color = '#909399' if label == '页脚' else '#606266'
            html_lines.append(f'<div style="color:{color};font-size:11px;padding:4px 12px;margin:4px 0;border-left:3px solid #dcdfe6;background:#fafafa;">{content}</div>')
            continue

        # 表格标记 (DOCX) - 开始表格模式
        if line.strip().startswith('[表格'):
            if in_table:
                html_lines.append(_render_table(table_rows))
                table_rows = []
            table_match = re.match(r'\[表格\s*(\d+)\]', line.strip())
            if table_match:
                html_lines.append(f'<div style="color:#409eff;font-size:12px;font-weight:600;margin:12px 0 6px 0;">表格 {table_match.group(1)}</div>')
            in_table = True
            continue

        # 表格行（制表符分隔，以两个空格开头）
        if in_table and line.startswith('  ') and '\t' in line:
            cells = [c.strip() for c in line.strip().split('\t')]
            cells = [c for c in cells if c]
            if cells:
                table_rows.append(cells)
            continue

        # 遇到非表格内容，结束表格
        if in_table and not line.startswith('  '):
            html_lines.append(_render_table(table_rows))
            table_rows = []
            in_table = False

        # 分隔线 (独立的 ---)
        if line.strip() == '---':
            html_lines.append('<hr style="border:none;border-top:1px solid #e4e7ed;margin:16px 0;">')
            continue

        # 标题
        if line.startswith('#'):
            level = len(re.match(r'^#+', line).group())
            title_text = line[level:].strip()
            # WPS 风格标题样式
            styles = {
                1: 'font-size:20px;font-weight:700;color:#303133;margin:20px 0 12px 0;padding-bottom:8px;border-bottom:2px solid #409eff;',
                2: 'font-size:17px;font-weight:600;color:#303133;margin:16px 0 10px 0;',
                3: 'font-size:15px;font-weight:600;color:#606266;margin:14px 0 8px 0;',
                4: 'font-size:14px;font-weight:600;color:#606266;margin:12px 0 6px 0;',
                5: 'font-size:13px;font-weight:600;color:#909399;margin:10px 0 6px 0;',
                6: 'font-size:12px;font-weight:600;color:#909399;margin:8px 0 4px 0;',
            }
            style = styles.get(level, styles[4])
            html_lines.append(f'<div style="{style}">{title_text}</div>')
            continue

        # 普通段落
        stripped = line.strip()
        if stripped:
            # 粗体
            stripped = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight:600;">\1</strong>', stripped)
            # 斜体 (单个 * 包围，但不匹配 **)
            stripped = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em style="font-style:italic;">\1</em>', stripped)
            # 行内代码
            stripped = re.sub(r'`(.+?)`', r'<code style="background:#f5f7fa;padding:2px 6px;border-radius:4px;font-family:Consolas,monospace;font-size:12px;color:#c7254e;">\1</code>', stripped)
            html_lines.append(f'<p style="margin:6px 0;line-height:1.8;color:#303133;font-size:14px;text-align:justify;">{stripped}</p>')

    # 结束未关闭的块
    if in_code_block:
        html_lines.append('</pre>')
    if in_table:
        html_lines.append(_render_table(table_rows))

    return '\n'.join(html_lines)


def _render_table(rows: list) -> str:
    """渲染表格为 HTML - WPS 风格"""
    if not rows:
        return ""

    html = ['<table style="border-collapse:collapse;width:100%;margin:10px 0;font-size:13px;border:1px solid #ebeef5;border-radius:4px;overflow:hidden;">']

    for i, row in enumerate(rows):
        if i == 0:
            # 表头样式 - WPS 蓝色风格
            bg = '#f5f7fa'
            weight = 'font-weight:600;color:#303133;'
        else:
            # 斑马纹
            bg = '#ffffff' if i % 2 == 1 else '#fafafa'
            weight = 'color:#606266;'

        html.append('<tr>')
        for cell in row:
            border_style = 'border:1px solid #ebeef5;'
            padding = 'padding:10px 14px;'
            html.append(f'<td style="{border_style}{padding}background:{bg};{weight}line-height:1.6;">{cell}</td>')
        html.append('</tr>')

    html.append('</table>')
    return ''.join(html)


class Colors:
    PRIMARY = "#1a73e8"
    PRIMARY_HOVER = "#1557b0"
    BACKGROUND = "#ffffff"
    SURFACE = "#f8f9fa"
    BORDER = "#e0e0e0"
    TEXT_PRIMARY = "#202124"
    TEXT_SECONDARY = "#5f6368"
    TEXT_DISABLED = "#9aa0a6"
    ERROR = "#d93025"
    SUCCESS = "#1e8e3e"


class SkillsDialog(QDialog):
    skills_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Skills 集群记忆")
        self.resize(1000, 650)
        self.setMinimumSize(800, 500)
        self.config_dir = Path.home() / ".wenbiao"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "skills.json"
        self.skills: List[Dict] = []
        self._current_preview_path = ""
        self._parser_thread: Optional[FileParserThread] = None
        self._init_ui()
        self._apply_styles()
        self._load_skills()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._create_header())

        # 使用 QSplitter 实现可调整大小的面板
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background: #e0e0e0; }")
        splitter.addWidget(self._create_list_panel())
        splitter.addWidget(self._create_preview_panel())
        splitter.setSizes([350, 650])

        content = QWidget()
        cl = QHBoxLayout(content)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.addWidget(splitter)

        layout.addWidget(content, 1)
        layout.addWidget(self._create_footer())

    def _create_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)

        # 左侧标题
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("Skills 集群记忆")
        title.setObjectName("title")
        title_layout.addWidget(title)
        desc = QLabel("添加需求文档、规范文件，AI 会读取这些内容作为上下文参考")
        desc.setObjectName("description")
        title_layout.addWidget(desc)
        layout.addLayout(title_layout)
        layout.addStretch()

        return header

    def _create_list_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("listPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(12)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        label = QLabel("技能文件")
        label.setStyleSheet("font-weight: 600; color: #202124; font-size: 14px;")
        toolbar.addWidget(label)
        toolbar.addStretch()

        add_btn = QPushButton("添加")
        add_btn.setObjectName("primaryButton")
        add_btn.setIcon(SvgIcons.get_icon("add", "#ffffff", 16))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_skill)
        toolbar.addWidget(add_btn)

        rm_btn = QPushButton("删除")
        rm_btn.setObjectName("secondaryButton")
        rm_btn.setIcon(SvgIcons.get_icon("delete", "#5f6368", 16))
        rm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rm_btn.clicked.connect(self._remove_skill)
        toolbar.addWidget(rm_btn)

        layout.addLayout(toolbar)

        # 文件列表
        self.skill_list = QListWidget()
        self.skill_list.setObjectName("skillList")
        self.skill_list.setIconSize(QSize(28, 28))
        self.skill_list.setSpacing(2)
        self.skill_list.itemClicked.connect(self._on_skill_selected)
        self.skill_list.itemDoubleClicked.connect(self._toggle_skill_enabled)
        layout.addWidget(self.skill_list)

        hint = QLabel("双击切换启用/禁用状态")
        hint.setObjectName("hint")
        layout.addWidget(hint)

        return panel

    def _create_preview_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("previewPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(12)

        self.preview_label = QLabel("文件预览")
        self.preview_label.setStyleSheet("font-weight: 600; color: #202124; font-size: 14px;")
        layout.addWidget(self.preview_label)

        # 使用 QTextBrowser 支持 HTML 渲染
        self.preview_text = QTextBrowser()
        self.preview_text.setObjectName("previewText")
        self.preview_text.setOpenExternalLinks(True)
        self.preview_text.setPlaceholderText("选择一个技能文件查看内容...")
        layout.addWidget(self.preview_text)

        return panel

    def _create_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("footer")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 12, 24, 12)

        self.stats_label = QLabel("共 0 个技能文件")
        self.stats_label.setObjectName("stats")
        layout.addWidget(self.stats_label)
        layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primaryButton")
        close_btn.setMinimumWidth(80)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        return footer

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BACKGROUND};
            }}
            #header {{
                background-color: {Colors.BACKGROUND};
                border-bottom: 1px solid {Colors.BORDER};
            }}
            #title {{
                font-size: 20px;
                font-weight: 600;
                color: {Colors.TEXT_PRIMARY};
            }}
            #description {{
                font-size: 13px;
                color: {Colors.TEXT_SECONDARY};
            }}
            #skillList {{
                background-color: {Colors.BACKGROUND};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
                outline: none;
            }}
            #skillList::item {{
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px 0;
            }}
            #skillList::item:hover {{
                background-color: #f5f5f5;
            }}
            #skillList::item:selected {{
                background-color: #e8f0fe;
                color: {Colors.PRIMARY};
            }}
            #previewText {{
                background-color: {Colors.BACKGROUND};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 10px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
                font-size: 13px;
                line-height: 1.5;
            }}
            #hint {{
                font-size: 11px;
                color: {Colors.TEXT_SECONDARY};
                font-style: italic;
            }}
            #footer {{
                background-color: {Colors.SURFACE};
                border-top: 1px solid {Colors.BORDER};
            }}
            #stats {{
                font-size: 12px;
                color: {Colors.TEXT_SECONDARY};
            }}
            #primaryButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            #primaryButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            #secondaryButton {{
                background-color: {Colors.BACKGROUND};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            #secondaryButton:hover {{
                background-color: {Colors.SURFACE};
                border-color: #bdbdbd;
            }}
        """)

    def _load_skills(self):
        if not self.config_file.exists():
            return
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.skills = json.load(f).get("skills", [])
            self._refresh_list()
        except Exception as e:
            logger.error(f"加载技能配置失败: {e}")

    def _save_skills(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"skills": self.skills}, f, ensure_ascii=False, indent=2)
            self.skills_changed.emit()
            try:
                from app.core.skills_cache import invalidate_skills_cache
                invalidate_skills_cache()
            except:
                pass
        except Exception as e:
            logger.error(f"保存技能配置失败: {e}")

    def _refresh_list(self):
        self.skill_list.clear()
        enabled_count = 0

        for skill in self.skills:
            name = skill.get("name", "未命名")
            enabled = skill.get("enabled", True)
            path = skill.get("path", "")
            exists = os.path.exists(path)
            file_ext = Path(path).suffix.lower()

            # 状态标记
            if not exists:
                status_icon = "  [不存在]"
                color = Colors.ERROR
            elif not enabled:
                status_icon = "  [已禁用]"
                color = Colors.TEXT_DISABLED
            else:
                status_icon = ""
                color = Colors.TEXT_PRIMARY
                enabled_count += 1

            item = QListWidgetItem(f"{name}{status_icon}")
            item.setData(Qt.ItemDataRole.UserRole, skill)
            item.setIcon(SvgIcons.get_file_icon(file_ext, color, 28))
            item.setForeground(QColor(color))

            # 设置字体
            font = item.font()
            if not enabled:
                font.setItalic(True)
            item.setFont(font)

            self.skill_list.addItem(item)

        self.stats_label.setText(f"共 {len(self.skills)} 个技能文件，{enabled_count} 个已启用")

    def _add_skill(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择技能文件", "",
            "所有支持的文件 (*.txt *.md *.json *.py *.docx *.pdf *.pptx);;所有文件 (*.*)"
        )
        if not paths:
            return
        for p in paths:
            if not any(s["path"] == p for s in self.skills):
                self.skills.append({"path": p, "enabled": True, "name": os.path.basename(p)})
        self._save_skills()
        self._refresh_list()

    def _remove_skill(self):
        item = self.skill_list.currentItem()
        if not item:
            return
        skill = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除技能文件 \"{skill['name']}\" 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.skills.remove(skill)
            self._save_skills()
            self._refresh_list()
            self.preview_text.clear()

    def _toggle_skill_enabled(self, item: QListWidgetItem):
        skill = item.data(Qt.ItemDataRole.UserRole)
        skill["enabled"] = not skill.get("enabled", True)
        self._save_skills()
        self._refresh_list()

    def _on_skill_selected(self, item: QListWidgetItem):
        skill = item.data(Qt.ItemDataRole.UserRole)
        path = skill.get("path", "")
        name = skill.get("name", "")

        self.preview_label.setText(f"文件预览: {name}")

        if not os.path.exists(path):
            self.preview_text.setHtml(
                '<div style="color:#d93025;padding:20px;text-align:center;">'
                '<p style="font-size:16px;">文件不存在</p>'
                f'<p style="font-size:12px;color:#5f6368;">{path}</p>'
                '</div>'
            )
            return

        self._current_preview_path = path
        self.preview_text.setHtml(
            '<div style="color:#5f6368;padding:40px;text-align:center;">'
            '<p style="font-size:14px;">正在加载...</p>'
            '</div>'
        )

        # 停止之前的线程
        if self._parser_thread is not None and self._parser_thread.isRunning():
            self._parser_thread.quit()
            self._parser_thread.wait(1000)

        # 启动新的解析线程
        self._parser_thread = FileParserThread(path, self)
        self._parser_thread.finished.connect(self._on_parse_finished)
        self._parser_thread.start()

    def _on_parse_finished(self, path: str, content: str, error: str):
        """解析完成回调"""
        if path != self._current_preview_path:
            return

        if error:
            self.preview_text.setHtml(
                f'<div style="color:#d93025;padding:20px;">'
                f'<p style="font-weight:600;">解析失败</p>'
                f'<p style="font-size:12px;">{error}</p>'
                f'</div>'
            )
        elif content:
            html = _markdown_to_html(content)
            self.preview_text.setHtml(f'<div style="padding:2px;">{html}</div>')
        else:
            self.preview_text.setHtml(
                '<div style="color:#5f6368;padding:20px;text-align:center;">'
                '<p>文件内容为空</p>'
                '</div>'
            )

    def get_enabled_skills(self) -> List[Dict]:
        return [s for s in self.skills if s.get("enabled", True) and os.path.exists(s.get("path", ""))]

    @staticmethod
    def load_skills_content() -> str:
        try:
            from app.core.skills_cache import get_skills_content
            return get_skills_content()
        except:
            return ""
