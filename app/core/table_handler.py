"""表格处理模块

提供表格的创建、导入和转换功能。
支持从 CSV、TSV、Excel、剪贴板等多种来源导入表格数据。
"""

import csv
import io
import logging
from typing import List, Optional

from app.core.exceptions import TableError

logger = logging.getLogger(__name__)


class TableHandler:
    """Handle table creation and import from various sources."""

    @staticmethod
    def create_empty_table(rows: int, cols: int) -> str:
        header = "| " + " | ".join(f"列{i+1}" for i in range(cols)) + " |"
        separator = "| " + " | ".join("---" for _ in range(cols)) + " |"
        data_rows = []
        for _ in range(rows):
            data_rows.append("| " + " | ".join("   " for _ in range(cols)) + " |")
        return "\n".join([header, separator] + data_rows)

    @staticmethod
    def from_csv_text(text: str) -> str:
        """从 CSV 文本创建 Markdown 表格

        Args:
            text: CSV 格式的文本

        Returns:
            Markdown 格式的表格字符串

        Raises:
            TableError: CSV 解析失败时抛出
        """
        try:
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
            if not rows:
                return ""
            return TableHandler._rows_to_markdown(rows)
        except csv.Error as e:
            logger.error("CSV 解析失败: %s", e)
            raise TableError(f"CSV 解析失败: {e}") from e

    @staticmethod
    def from_tsv_text(text: str) -> str:
        """从 TSV 文本创建 Markdown 表格

        Args:
            text: TSV 格式的文本（制表符分隔）

        Returns:
            Markdown 格式的表格字符串

        Raises:
            TableError: TSV 解析失败时抛出
        """
        try:
            reader = csv.reader(io.StringIO(text), delimiter="\t")
            rows = list(reader)
            if not rows:
                return ""
            return TableHandler._rows_to_markdown(rows)
        except csv.Error as e:
            logger.error("TSV 解析失败: %s", e)
            raise TableError(f"TSV 解析失败: {e}") from e

    @staticmethod
    def from_clipboard_text(text: str) -> str:
        if "\t" in text:
            return TableHandler.from_tsv_text(text)
        elif "," in text:
            return TableHandler.from_csv_text(text)
        else:
            lines = text.strip().split("\n")
            rows = [line.split() for line in lines if line.strip()]
            if rows:
                return TableHandler._rows_to_markdown(rows)
        return ""

    @staticmethod
    def from_excel(file_path: str) -> str:
        """从 Excel 文件导入表格

        Args:
            file_path: Excel 文件路径（.xlsx 或 .xls）

        Returns:
            Markdown 格式的表格字符串，失败时返回空字符串

        Raises:
            TableError: Excel 文件读取失败时抛出
        """
        try:
            from openpyxl import load_workbook
        except ImportError as e:
            logger.error("openpyxl 模块未安装")
            raise TableError("openpyxl 模块未安装，无法读取 Excel 文件") from e

        try:
            wb = load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
            rows = []
            for row in ws.iter_rows(values_only=True):
                rows.append([str(cell) if cell is not None else "" for cell in row])
            wb.close()

            if rows:
                return TableHandler._rows_to_markdown(rows)
            return ""

        except FileNotFoundError as e:
            logger.error("Excel 文件不存在: %s", file_path)
            raise TableError(f"Excel 文件不存在: {file_path}") from e
        except Exception as e:
            logger.error("读取 Excel 文件失败: %s - %s", file_path, e)
            raise TableError(f"读取 Excel 文件失败: {file_path}") from e

    @staticmethod
    def _rows_to_markdown(rows: List[List[str]]) -> str:
        if not rows:
            return ""
        max_cols = max(len(row) for row in rows)
        for row in rows:
            while len(row) < max_cols:
                row.append("")

        header = "| " + " | ".join(rows[0]) + " |"
        separator = "| " + " | ".join("---" for _ in range(max_cols)) + " |"
        data_rows = []
        for row in rows[1:]:
            data_rows.append("| " + " | ".join(row) + " |")
        return "\n".join([header, separator] + data_rows)

    @staticmethod
    def parse_markdown_table(text: str) -> Optional[List[List[str]]]:
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        if len(lines) < 2:
            return None
        rows = []
        for i, line in enumerate(lines):
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if i == 1 and all(set(c.strip()) <= set("-: ") for c in cells):
                continue
            rows.append(cells)
        return rows if rows else None
