"""文档解析器

支持解析多种文档格式：
- DOCX: Microsoft Word 文档
- PDF: PDF 文档
- PPTX: Microsoft PowerPoint 演示文稿
- TXT/MD/JSON 等文本文件
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentParser:
    """文档解析器"""

    @staticmethod
    def parse_file(file_path: str) -> Optional[str]:
        """解析文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容文本，如果解析失败返回 None
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None

        suffix = path.suffix.lower()

        try:
            if suffix == ".docx":
                return DocumentParser._parse_docx(path)
            elif suffix == ".pdf":
                return DocumentParser._parse_pdf(path)
            elif suffix in [".pptx", ".ppt"]:
                return DocumentParser._parse_pptx(path)
            else:
                # 文本文件
                return DocumentParser._parse_text(path)
        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {e}")
            return None

    @staticmethod
    def _parse_text(path: Path) -> Optional[str]:
        """解析文本文件"""
        try:
            # 尝试多种编码
            for encoding in ["utf-8", "gbk", "gb2312", "utf-16"]:
                try:
                    with open(path, "r", encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"成功解析文本文件 (编码: {encoding}): {path.name}")
                    return content
                except UnicodeDecodeError:
                    continue

            logger.error(f"无法解析文本文件 (编码不支持): {path.name}")
            return None
        except Exception as e:
            logger.error(f"解析文本文件失败: {e}")
            return None

    @staticmethod
    def _parse_docx(path: Path) -> Optional[str]:
        """解析 DOCX 文件 - 使用专用解析器"""
        from app.core.docx_parser import DOCXParser
        return DOCXParser.parse(str(path))

    @staticmethod
    def _parse_pdf(path: Path) -> Optional[str]:
        """解析 PDF 文件 - 使用专用解析器"""
        from app.core.pdf_parser import PDFParser
        return PDFParser.parse(str(path))

    @staticmethod
    def _parse_pptx(path: Path) -> Optional[str]:
        """解析 PPTX 文件"""
        try:
            from pptx import Presentation

            prs = Presentation(str(path))
            slides_text = []

            for slide_num, slide in enumerate(prs.slides, 1):
                slide_content = [f"=== 幻灯片 {slide_num} ==="]

                # 提取所有文本框内容
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_content.append(shape.text.strip())

                    # 提取表格内容
                    if shape.has_table:
                        table = shape.table
                        for row in table.rows:
                            row_text = " | ".join(
                                cell.text.strip() for cell in row.cells
                            )
                            if row_text.strip():
                                slide_content.append(row_text)

                if len(slide_content) > 1:  # 有内容才添加
                    slides_text.append("\n".join(slide_content))

            content = "\n\n".join(slides_text)
            logger.info(f"成功解析 PPTX 文件 ({len(prs.slides)} 页): {path.name}")
            return content
        except ImportError:
            logger.error("缺少 python-pptx 库，请安装: pip install python-pptx")
            return None
        except Exception as e:
            logger.error(f"解析 PPTX 文件失败: {e}")
            return None

    @staticmethod
    def is_supported(file_path: str) -> bool:
        """检查文件格式是否支持"""
        suffix = Path(file_path).suffix.lower()
        supported_formats = [
            ".txt", ".md", ".json", ".py", ".js", ".java", ".cpp", ".c",
            ".h", ".css", ".html", ".xml", ".yaml", ".yml",
            ".docx", ".pdf", ".pptx", ".ppt",
        ]
        return suffix in supported_formats
