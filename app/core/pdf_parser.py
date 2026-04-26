"""PDF 文件解析器

支持多种 PDF 解析策略，自动选择最佳方案：
1. pdfplumber - 处理复杂布局、表格
2. pypdf - 轻量快速
3. pdfminer - 精确文本提取
4. PyMuPDF (fitz) - 最快最强
"""

import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class PDFParser:
    """PDF 解析器"""

    @staticmethod
    def parse(file_path: str) -> Optional[str]:
        """解析 PDF 文件

        自动尝试多种解析方案，返回最佳结果。

        Args:
            file_path: PDF 文件路径

        Returns:
            提取的文本内容，失败返回 None
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"PDF 文件不存在: {file_path}")
            return None

        # 按优先级尝试不同的解析器
        parsers = [
            ("PyMuPDF", PDFParser._parse_with_fitz),
            ("pdfplumber", PDFParser._parse_with_pdfplumber),
            ("pdfminer", PDFParser._parse_with_pdfminer),
            ("pypdf", PDFParser._parse_with_pypdf),
        ]

        for name, parser_func in parsers:
            try:
                result = parser_func(path)
                if result and result.strip():
                    logger.info(f"PDF 解析成功 ({name}): {path.name}")
                    return result
            except ImportError:
                logger.debug(f"{name} 未安装，跳过")
            except Exception as e:
                logger.debug(f"{name} 解析失败: {e}")

        logger.error(f"所有 PDF 解析器都失败: {file_path}")
        return None

    @staticmethod
    def _parse_with_fitz(path: Path) -> Optional[str]:
        """使用 PyMuPDF (fitz) 解析 - 最快最强"""
        import fitz  # PyMuPDF

        doc = fitz.open(str(path))
        pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages.append(f"=== 第 {page_num + 1} 页 ===\n{text.strip()}")

        doc.close()
        return "\n\n".join(pages) if pages else None

    @staticmethod
    def _parse_with_pdfplumber(path: Path) -> Optional[str]:
        """使用 pdfplumber 解析 - 擅长表格"""
        import pdfplumber

        pages = []
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # 提取文本
                text = page.extract_text() or ""

                # 提取表格
                tables = page.extract_tables()
                table_text = ""
                if tables:
                    for table in tables:
                        if table:
                            rows = []
                            for row in table:
                                cells = [str(cell or "").strip() for cell in row]
                                rows.append(" | ".join(cells))
                            table_text += "\n" + "\n".join(rows)

                combined = text.strip()
                if table_text:
                    combined += "\n\n[表格内容]" + table_text

                if combined.strip():
                    pages.append(f"=== 第 {page_num} 页 ===\n{combined}")

        return "\n\n".join(pages) if pages else None

    @staticmethod
    def _parse_with_pdfminer(path: Path) -> Optional[str]:
        """使用 pdfminer 解析 - 精确提取"""
        from pdfminer.high_level import extract_text

        text = extract_text(str(path))
        return text.strip() if text else None

    @staticmethod
    def _parse_with_pypdf(path: Path) -> Optional[str]:
        """使用 pypdf 解析 - 轻量快速"""
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = []

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"=== 第 {page_num} 页 ===\n{text.strip()}")

        return "\n\n".join(pages) if pages else None

    @staticmethod
    def get_page_count(file_path: str) -> int:
        """获取 PDF 页数"""
        try:
            import fitz
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except:
            pass

        try:
            from pypdf import PdfReader
            return len(PdfReader(file_path).pages)
        except:
            pass

        return 0
