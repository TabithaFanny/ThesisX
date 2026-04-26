"""DOCX 文件解析器

全面提取 Word 文档内容：
- 段落文本
- 表格内容
- 页眉页脚
- 文本框
- 批注
- 样式信息
"""

import logging
from pathlib import Path
from typing import Optional, List
from zipfile import ZipFile
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# Word XML 命名空间
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}


class DOCXParser:
    """DOCX 解析器"""

    @staticmethod
    def parse(file_path: str) -> Optional[str]:
        """解析 DOCX 文件

        Args:
            file_path: DOCX 文件路径

        Returns:
            提取的文本内容，失败返回 None
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"DOCX 文件不存在: {file_path}")
            return None

        # 优先使用 python-docx
        try:
            result = DOCXParser._parse_with_docx(path)
            if result:
                logger.info(f"DOCX 解析成功 (python-docx): {path.name}")
                return result
        except ImportError:
            logger.debug("python-docx 未安装，使用原生解析")
        except Exception as e:
            logger.debug(f"python-docx 解析失败: {e}")

        # 回退到原生 XML 解析
        try:
            result = DOCXParser._parse_native(path)
            if result:
                logger.info(f"DOCX 解析成功 (原生): {path.name}")
                return result
        except Exception as e:
            logger.error(f"DOCX 原生解析失败: {e}")

        return None

    @staticmethod
    def _parse_with_docx(path: Path) -> Optional[str]:
        """使用 python-docx 解析 - 按文档顺序提取"""
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph

        doc = Document(str(path))
        content_parts = []

        # 1. 提取页眉页脚（放在最前面）
        headers_footers = []
        for section in doc.sections:
            if section.header and section.header.paragraphs:
                header_text = " ".join(p.text.strip() for p in section.header.paragraphs if p.text.strip())
                if header_text:
                    headers_footers.append(f"[页眉] {header_text}")

            if section.footer and section.footer.paragraphs:
                footer_text = " ".join(p.text.strip() for p in section.footer.paragraphs if p.text.strip())
                if footer_text:
                    headers_footers.append(f"[页脚] {footer_text}")

        if headers_footers:
            content_parts.append("\n".join(headers_footers))

        # 2. 按文档顺序遍历 body 中的所有元素
        body = doc.element.body
        table_idx = 0

        for child in body:
            tag = child.tag.split('}')[-1]

            if tag == 'p':
                # 段落
                para = Paragraph(child, doc)
                text = para.text.strip()
                if text:
                    # 检查是否是标题
                    if para.style and para.style.name.startswith('Heading'):
                        level = para.style.name.replace('Heading ', '')
                        prefix = '#' * int(level) if level.isdigit() else '##'
                        content_parts.append(f"{prefix} {text}")
                    else:
                        content_parts.append(text)

            elif tag == 'tbl':
                # 表格
                table_idx += 1
                table = Table(child, doc)
                table_lines = [f"[表格 {table_idx}]"]

                for row in table.rows:
                    # 去重：合并单元格会导致相同内容重复
                    seen_texts = []
                    for cell in row.cells:
                        cell_text = cell.text.strip().replace('\n', ' ')
                        # 跳过空单元格和重复内容
                        if cell_text and cell_text not in seen_texts:
                            seen_texts.append(cell_text)

                    if seen_texts:
                        table_lines.append("  " + "\t".join(seen_texts))

                if len(table_lines) > 1:
                    content_parts.append("\n".join(table_lines))

        return "\n\n".join(content_parts) if content_parts else None

    @staticmethod
    def _parse_native(path: Path) -> Optional[str]:
        """原生 XML 解析 (不依赖 python-docx)"""
        texts = []

        with ZipFile(path, 'r') as zf:
            # 解析主文档
            if 'word/document.xml' in zf.namelist():
                content = zf.read('word/document.xml')
                root = ET.fromstring(content)

                # 提取所有文本
                for elem in root.iter():
                    if elem.tag.endswith('}t'):  # w:t 标签
                        if elem.text:
                            texts.append(elem.text)
                    elif elem.tag.endswith('}p'):  # w:p 段落结束
                        texts.append('\n')

        # 清理文本
        result = ''.join(texts)
        # 合并多余空行
        lines = [line.strip() for line in result.split('\n')]
        lines = [line for line in lines if line]

        return '\n\n'.join(lines) if lines else None

    @staticmethod
    def get_metadata(file_path: str) -> dict:
        """获取文档元数据"""
        metadata = {}

        try:
            with ZipFile(file_path, 'r') as zf:
                if 'docProps/core.xml' in zf.namelist():
                    content = zf.read('docProps/core.xml')
                    root = ET.fromstring(content)

                    # 常见元数据字段
                    for elem in root:
                        tag = elem.tag.split('}')[-1]
                        if elem.text:
                            metadata[tag] = elem.text
        except Exception as e:
            logger.debug(f"获取元数据失败: {e}")

        return metadata
