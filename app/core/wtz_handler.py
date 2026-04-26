"""
wtz_handler.py — 文表智联专属 .wtz 格式读写

.wtz 是一个 ZIP 压缩包，内部结构:

    content.md          — Markdown 正文
    meta.json           — 元数据（标题、作者、样式预设等）
    images/             — 内嵌图片（可选）

元数据示例:
{
    "title": "论文标题",
    "author": "作者",
    "style_preset": "academic",
    "created": "2026-01-01T00:00:00",
    "modified": "2026-01-02T12:00:00",
    "app_version": "2.0.0"
}
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
import shutil
import zipfile
from dataclasses import dataclass, field
from typing import Dict, Optional

from app.constants import APP_VERSION, PREVIEW_STYLE_ACADEMIC

logger = logging.getLogger(__name__)

CONTENT_ENTRY = "content.md"
META_ENTRY = "meta.json"
IMAGES_DIR = "images/"


@dataclass
class WtzMeta:
    """Metadata stored inside a .wtz archive."""

    title: str = ""
    author: str = ""
    style_preset: str = PREVIEW_STYLE_ACADEMIC
    created: str = ""
    modified: str = ""
    app_version: str = APP_VERSION
    extra: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "title": self.title,
            "author": self.author,
            "style_preset": self.style_preset,
            "created": self.created,
            "modified": self.modified,
            "app_version": self.app_version,
        }
        d.update(self.extra)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "WtzMeta":
        known = {"title", "author", "style_preset", "created", "modified", "app_version"}
        extra = {k: v for k, v in d.items() if k not in known}
        return cls(
            title=d.get("title", ""),
            author=d.get("author", ""),
            style_preset=d.get("style_preset", PREVIEW_STYLE_ACADEMIC),
            created=d.get("created", ""),
            modified=d.get("modified", ""),
            app_version=d.get("app_version", ""),
            extra=extra,
        )


@dataclass
class WtzDocument:
    """Represents the full content of a .wtz file."""

    content: str = ""
    meta: WtzMeta = field(default_factory=WtzMeta)
    images: Dict[str, bytes] = field(default_factory=dict)  # relative_name → data


def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def read_wtz(file_path: str) -> WtzDocument:
    """Read a .wtz archive and return a WtzDocument."""
    doc = WtzDocument()
    with zipfile.ZipFile(file_path, "r") as zf:
        # Content
        if CONTENT_ENTRY in zf.namelist():
            doc.content = zf.read(CONTENT_ENTRY).decode("utf-8")

        # Meta
        if META_ENTRY in zf.namelist():
            raw = zf.read(META_ENTRY).decode("utf-8")
            try:
                doc.meta = WtzMeta.from_dict(json.loads(raw))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("meta.json 解析失败: %s", e)

        # Images
        for name in zf.namelist():
            if name.startswith(IMAGES_DIR) and name != IMAGES_DIR:
                doc.images[name[len(IMAGES_DIR) :]] = zf.read(name)

    logger.info("读取 .wtz: %s (images=%d)", file_path, len(doc.images))
    return doc


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------


def write_wtz(
    file_path: str,
    content: str,
    meta: Optional[WtzMeta] = None,
    images: Optional[Dict[str, bytes]] = None,
    source_dir: str = "",
) -> None:
    """
    Save a .wtz archive.

    Parameters
    ----------
    file_path : str
        Output .wtz path.
    content : str
        Markdown content.
    meta : WtzMeta, optional
        Metadata; if None, a default is created.
    images : dict, optional
        Explicit image map (name → bytes). If empty, images are
        collected from the Markdown content by scanning for local
        file references relative to *source_dir*.
    source_dir : str
        Directory of the original .md file, used to resolve image paths.
    """
    if meta is None:
        meta = WtzMeta()
    meta.modified = _now_iso()
    if not meta.created:
        meta.created = meta.modified
    meta.app_version = APP_VERSION

    if images is None:
        images = {}

    # Auto-collect images referenced in Markdown
    if source_dir and not images:
        images = _collect_images(content, source_dir)

    with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(CONTENT_ENTRY, content.encode("utf-8"))
        zf.writestr(
            META_ENTRY, json.dumps(meta.to_dict(), ensure_ascii=False, indent=2).encode("utf-8")
        )
        for name, data in images.items():
            zf.writestr(IMAGES_DIR + name, data)

    logger.info("保存 .wtz: %s (images=%d)", file_path, len(images))


# ---------------------------------------------------------------------------
# Image collection
# ---------------------------------------------------------------------------

_IMG_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _collect_images(content: str, source_dir: str) -> Dict[str, bytes]:
    """Scan Markdown for local image references and collect them."""
    images: Dict[str, bytes] = {}
    for m in _IMG_PATTERN.finditer(content):
        src = m.group(2).strip()
        # Skip URLs
        if src.startswith(("http://", "https://", "data:")):
            continue
        # Resolve relative path
        abs_path = src if os.path.isabs(src) else os.path.join(source_dir, src)
        abs_path = os.path.normpath(abs_path)
        if os.path.isfile(abs_path):
            name = os.path.basename(abs_path)
            # Avoid duplicates
            if name not in images:
                try:
                    with open(abs_path, "rb") as f:
                        images[name] = f.read()
                except OSError as e:
                    logger.warning("图片读取失败 %s: %s", abs_path, e)
    return images


# ---------------------------------------------------------------------------
# Extract images to temp dir (for preview / export)
# ---------------------------------------------------------------------------


def extract_images_to_dir(doc: WtzDocument, target_dir: str) -> None:
    """Write embedded images to a directory on disk."""
    os.makedirs(target_dir, exist_ok=True)
    for name, data in doc.images.items():
        out_path = os.path.join(target_dir, name)
        with open(out_path, "wb") as f:
            f.write(data)


def rewrite_image_paths(content: str, images: Dict[str, bytes], target_dir: str) -> str:
    """
    Rewrite image references in Markdown so they point to
    extracted files in *target_dir*.
    """

    def replace(m):
        alt = m.group(1)
        src = m.group(2).strip()
        name = os.path.basename(src)
        if name in images:
            new_path = os.path.join(target_dir, name).replace("\\", "/")
            return f"![{alt}]({new_path})"
        return m.group(0)

    return _IMG_PATTERN.sub(replace, content)
