import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Document:
    """Represents a single document."""

    content: str = ""
    file_path: Optional[str] = None
    modified: bool = False
    _saved_content: str = ""

    def __post_init__(self):
        self._saved_content = self.content

    @property
    def filename(self) -> str:
        if self.file_path:
            return os.path.basename(self.file_path)
        return "未命名文档"

    @property
    def is_modified(self) -> bool:
        return self.content != self._saved_content

    def mark_saved(self):
        self._saved_content = self.content
        self.modified = False

    def update_content(self, text: str):
        self.content = text
        self.modified = self.is_modified
