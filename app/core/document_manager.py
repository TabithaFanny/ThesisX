"""文档管理模块

提供文档的创建、打开、保存等文件操作功能。
支持普通 Markdown 文件（.md/.txt）和 WTZ 归档格式（.wtz）。
"""

import json
import logging
import os
from typing import List, Optional

from app.constants import MAX_RECENT_FILES
from app.core.document import Document
from app.core.exceptions import DocumentError
from app.core.wtz_handler import (
    WtzDocument,
    WtzMeta,
    read_wtz,
    write_wtz,
)

logger = logging.getLogger(__name__)


def _is_wtz(path: str) -> bool:
    return path.lower().endswith(".wtz")


class DocumentManager:
    """Handles file operations: new, open, save, recent files.

    Supports both plain .md/.txt files and .wtz archives.
    """

    def __init__(self):
        self.current_document = Document()
        self.current_wtz_meta: Optional[WtzMeta] = None  # non-None when working with .wtz
        self.current_wtz_images: dict = {}  # embedded images
        self._recent_files: List[str] = []
        self._config_dir = os.path.join(os.path.expanduser("~"), ".wenbiao")
        self._config_file = os.path.join(self._config_dir, "recent.json")
        self._load_recent_files()

    def new_document(self) -> Document:
        self.current_document = Document()
        self.current_wtz_meta = None
        self.current_wtz_images = {}
        return self.current_document

    def open_document(self, file_path: str) -> Document:
        """打开文档文件

        Args:
            file_path: 文件路径，支持 .md/.txt 或 .wtz 格式

        Returns:
            打开的文档对象

        Raises:
            DocumentError: 文件不存在或读取失败
        """
        if _is_wtz(file_path):
            return self._open_wtz(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError as e:
            logger.error("文件不存在: %s", file_path)
            raise DocumentError(f"文件不存在: {file_path}") from e
        except (OSError, UnicodeDecodeError) as e:
            logger.error("读取文件失败: %s - %s", file_path, e)
            raise DocumentError(f"读取文件失败: {file_path}") from e

        self.current_document = Document(content=content, file_path=file_path)
        self.current_wtz_meta = None
        self.current_wtz_images = {}
        self._add_recent_file(file_path)
        return self.current_document

    def _open_wtz(self, file_path: str) -> Document:
        wtz_doc = read_wtz(file_path)
        self.current_document = Document(content=wtz_doc.content, file_path=file_path)
        self.current_wtz_meta = wtz_doc.meta
        self.current_wtz_images = wtz_doc.images
        self._add_recent_file(file_path)
        logger.info("打开 .wtz: %s (preset=%s)", file_path, wtz_doc.meta.style_preset)
        return self.current_document

    def save_document(self, file_path: Optional[str] = None) -> bool:
        """保存文档到文件

        Args:
            file_path: 保存路径，如果为 None 则使用当前文档路径

        Returns:
            保存成功返回 True，失败返回 False

        Raises:
            DocumentError: 保存失败时抛出
        """
        path = file_path or self.current_document.file_path
        if not path:
            logger.warning("保存文档失败: 未指定文件路径")
            raise DocumentError("未指定文件路径")

        try:
            if _is_wtz(path):
                return self._save_wtz(path)

            with open(path, "w", encoding="utf-8") as f:
                f.write(self.current_document.content)

            self.current_document.file_path = path
            self.current_document.mark_saved()
            self._add_recent_file(path)
            logger.info("文档已保存: %s", path)
            return True

        except (OSError, UnicodeEncodeError) as e:
            logger.error("保存文档失败: %s - %s", path, e)
            raise DocumentError(f"保存文档失败: {path}") from e

    def _save_wtz(self, path: str) -> bool:
        """保存为 WTZ 格式

        Args:
            path: WTZ 文件路径

        Returns:
            保存成功返回 True

        Raises:
            DocumentError: 保存失败时抛出
        """
        meta = self.current_wtz_meta or WtzMeta()
        source_dir = ""
        if self.current_document.file_path:
            source_dir = os.path.dirname(self.current_document.file_path)

        try:
            write_wtz(
                path,
                self.current_document.content,
                meta=meta,
                images=self.current_wtz_images or None,
                source_dir=source_dir,
            )
            self.current_document.file_path = path
            self.current_document.mark_saved()
            self._add_recent_file(path)
            logger.info("WTZ 文档已保存: %s", path)
            return True

        except (OSError, ValueError) as e:
            logger.error("保存 WTZ 失败: %s - %s", path, e)
            raise DocumentError(f"保存 WTZ 失败: {path}") from e

    def save_as_wtz(self, path: str, meta: Optional[WtzMeta] = None) -> bool:
        """Save current document as .wtz with optional metadata override."""
        if meta:
            self.current_wtz_meta = meta
        return self._save_wtz(path)

    def _add_recent_file(self, file_path: str):
        abs_path = os.path.abspath(file_path)
        if abs_path in self._recent_files:
            self._recent_files.remove(abs_path)
        self._recent_files.insert(0, abs_path)
        self._recent_files = self._recent_files[:MAX_RECENT_FILES]
        self._save_recent_files()

    def get_recent_files(self) -> List[str]:
        return [f for f in self._recent_files if os.path.exists(f)]

    def _load_recent_files(self):
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, "r", encoding="utf-8") as f:
                    self._recent_files = json.load(f)
        except (json.JSONDecodeError, OSError):
            self._recent_files = []

    def _save_recent_files(self):
        """保存最近文件列表到配置文件"""
        try:
            os.makedirs(self._config_dir, exist_ok=True)
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._recent_files, f, ensure_ascii=False)
        except OSError as e:
            logger.warning("保存最近文件列表失败: %s", e)
