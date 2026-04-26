"""SVG 图标管理器

提供统一的 SVG 图标管理，支持动态颜色替换。
设计风格参考 Google Drive / Microsoft Office / WPS Office。
"""

import logging
from typing import Dict

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

logger = logging.getLogger(__name__)


class SvgIcons:
    """SVG 图标管理器"""

    ICONS: Dict[str, str] = {
        # ========== 操作图标 ==========
        "add": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
        </svg>''',

        "delete": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
        </svg>''',

        "check": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
        </svg>''',

        "close": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>''',

        "refresh": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
        </svg>''',

        "folder": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="#FFC107" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/>
            <path fill="#FFD54F" d="M20 8H4v10h16V8z" opacity="0.3"/>
        </svg>''',

        "skill": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
        </svg>''',

        "warning": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
        </svg>''',

        "info": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path fill="{color}" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
        </svg>''',

        # ========== PDF 文件 - Adobe/WPS 红色风格 ==========
        "file_pdf": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="pdf_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#FF5252"/>
                    <stop offset="100%" style="stop-color:#D32F2F"/>
                </linearGradient>
            </defs>
            <path fill="url(#pdf_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#FFCDD2" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#B71C1C" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <rect x="7" y="16" width="18" height="10" rx="1" fill="#B71C1C"/>
            <text x="16" y="23.5" font-family="Arial,sans-serif" font-size="6" font-weight="bold" fill="white" text-anchor="middle">PDF</text>
        </svg>''',

        # ========== Word 文件 - Microsoft 蓝色风格 ==========
        "file_word": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="word_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#42A5F5"/>
                    <stop offset="100%" style="stop-color:#1565C0"/>
                </linearGradient>
            </defs>
            <path fill="url(#word_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#BBDEFB" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#0D47A1" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <rect x="7" y="16" width="18" height="10" rx="1" fill="#0D47A1"/>
            <text x="16" y="23.5" font-family="Arial,sans-serif" font-size="5.5" font-weight="bold" fill="white" text-anchor="middle">DOCX</text>
        </svg>''',

        # ========== PPT 文件 - Microsoft 橙色风格 ==========
        "file_ppt": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="ppt_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#FF7043"/>
                    <stop offset="100%" style="stop-color:#E64A19"/>
                </linearGradient>
            </defs>
            <path fill="url(#ppt_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#FFCCBC" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#BF360C" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <rect x="7" y="16" width="18" height="10" rx="1" fill="#BF360C"/>
            <text x="16" y="23.5" font-family="Arial,sans-serif" font-size="5.5" font-weight="bold" fill="white" text-anchor="middle">PPTX</text>
        </svg>''',

        # ========== Excel 文件 - Microsoft 绿色风格 ==========
        "file_excel": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="excel_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#66BB6A"/>
                    <stop offset="100%" style="stop-color:#2E7D32"/>
                </linearGradient>
            </defs>
            <path fill="url(#excel_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#C8E6C9" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#1B5E20" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <rect x="7" y="16" width="18" height="10" rx="1" fill="#1B5E20"/>
            <text x="16" y="23.5" font-family="Arial,sans-serif" font-size="5.5" font-weight="bold" fill="white" text-anchor="middle">XLSX</text>
        </svg>''',

        # ========== 文本文件 - 灰色简约风格 ==========
        "file_text": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="txt_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#78909C"/>
                    <stop offset="100%" style="stop-color:#546E7A"/>
                </linearGradient>
            </defs>
            <path fill="url(#txt_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#CFD8DC" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#37474F" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <path fill="white" d="M8 15h16v1.5H8zM8 18h16v1.5H8zM8 21h12v1.5H8z" opacity="0.9"/>
        </svg>''',

        # ========== Markdown 文件 - 深蓝简约风格 ==========
        "file_md": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="md_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#5C6BC0"/>
                    <stop offset="100%" style="stop-color:#3949AB"/>
                </linearGradient>
            </defs>
            <path fill="url(#md_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#C5CAE9" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#1A237E" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <rect x="7" y="16" width="18" height="10" rx="1" fill="#1A237E"/>
            <text x="16" y="23.5" font-family="Arial,sans-serif" font-size="6" font-weight="bold" fill="white" text-anchor="middle">MD</text>
        </svg>''',

        # ========== 代码文件 - 紫色风格 ==========
        "file_code": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="code_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#AB47BC"/>
                    <stop offset="100%" style="stop-color:#7B1FA2"/>
                </linearGradient>
            </defs>
            <path fill="url(#code_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#E1BEE7" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#4A148C" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <path fill="white" d="M11 16l-4 5 4 5 1.5-1.5L9 21l3.5-3.5zM21 16l4 5-4 5-1.5-1.5L23 21l-3.5-3.5z"/>
            <rect x="14.5" y="15" width="3" height="12" rx="1" fill="white" transform="rotate(15 16 21)"/>
        </svg>''',

        # ========== Python 文件 - 蓝黄风格 ==========
        "file_python": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="py_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#5C6BC0"/>
                    <stop offset="100%" style="stop-color:#3949AB"/>
                </linearGradient>
            </defs>
            <path fill="url(#py_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#C5CAE9" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#1A237E" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <rect x="7" y="16" width="18" height="10" rx="1" fill="#1A237E"/>
            <text x="16" y="23.5" font-family="Arial,sans-serif" font-size="6" font-weight="bold" fill="#FFD54F" text-anchor="middle">PY</text>
        </svg>''',

        # ========== JSON 文件 - 黄色风格 ==========
        "file_json": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="json_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#FFD54F"/>
                    <stop offset="100%" style="stop-color:#FFA000"/>
                </linearGradient>
            </defs>
            <path fill="url(#json_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#FFF8E1" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#FF6F00" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <rect x="7" y="16" width="18" height="10" rx="1" fill="#E65100"/>
            <text x="16" y="23.5" font-family="Arial,sans-serif" font-size="5" font-weight="bold" fill="white" text-anchor="middle">JSON</text>
        </svg>''',

        # ========== 图片文件 - 青色风格 ==========
        "file_image": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="img_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#26C6DA"/>
                    <stop offset="100%" style="stop-color:#00ACC1"/>
                </linearGradient>
            </defs>
            <path fill="url(#img_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#B2EBF2" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#006064" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
            <rect x="8" y="15" width="16" height="11" rx="1" fill="white" opacity="0.9"/>
            <circle cx="12" cy="19" r="2" fill="#26C6DA"/>
            <path fill="#00ACC1" d="M8 24l4-4 3 3 5-5 4 4v2c0 .5-.5 1-1 1H9c-.5 0-1-.5-1-1v-0z"/>
        </svg>''',

        # ========== 通用文件 - 灰色 ==========
        "file_generic": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <defs>
                <linearGradient id="gen_grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#90A4AE"/>
                    <stop offset="100%" style="stop-color:#607D8B"/>
                </linearGradient>
            </defs>
            <path fill="url(#gen_grad)" d="M6 2C4.9 2 4 2.9 4 4v24c0 1.1.9 2 2 2h20c1.1 0 2-.9 2-2V10l-8-8H6z"/>
            <path fill="#ECEFF1" d="M20 2v6c0 1.1.9 2 2 2h6l-8-8z"/>
            <path fill="#455A64" d="M20 2l8 8h-6c-1.1 0-2-.9-2-2V2z" opacity="0.2"/>
        </svg>''',
    }

    _cache: Dict[str, QIcon] = {}

    @classmethod
    def get_icon(cls, name: str, color: str = "#5f6368", size: int = 24) -> QIcon:
        """获取指定颜色的图标"""
        # 使用 2x 分辨率渲染，提高清晰度
        render_size = size * 2
        cache_key = f"{name}_{color}_{size}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        svg_template = cls.ICONS.get(name)
        if not svg_template:
            logger.warning(f"未找到图标: {name}")
            return QIcon()

        try:
            svg_content = svg_template.format(color=color)
            renderer = QSvgRenderer(svg_content.encode())

            # 高分辨率渲染
            pixmap = QPixmap(render_size, render_size)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            renderer.render(painter)
            painter.end()

            # 缩放到目标大小，保持高质量
            pixmap = pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            icon = QIcon(pixmap)
            cls._cache[cache_key] = icon
            return icon

        except Exception as e:
            logger.warning(f"创建图标失败 {name}: {e}")
            return QIcon()

    @classmethod
    def get_file_icon(cls, extension: str, color: str = "#5f6368", size: int = 24) -> QIcon:
        """根据文件扩展名获取图标"""
        ext = extension.lower().lstrip('.')

        icon_map = {
            # Office 文档
            "pdf": "file_pdf",
            "docx": "file_word",
            "doc": "file_word",
            "pptx": "file_ppt",
            "ppt": "file_ppt",
            "xlsx": "file_excel",
            "xls": "file_excel",
            # 代码文件
            "py": "file_python",
            "js": "file_code",
            "ts": "file_code",
            "java": "file_code",
            "cpp": "file_code",
            "c": "file_code",
            "h": "file_code",
            "css": "file_code",
            "html": "file_code",
            # 数据文件
            "json": "file_json",
            "xml": "file_json",
            "yaml": "file_json",
            "yml": "file_json",
            # 文本文件
            "txt": "file_text",
            "md": "file_md",
            "markdown": "file_md",
            # 图片文件
            "png": "file_image",
            "jpg": "file_image",
            "jpeg": "file_image",
            "gif": "file_image",
            "svg": "file_image",
            "webp": "file_image",
        }

        icon_name = icon_map.get(ext, "file_generic")
        return cls.get_icon(icon_name, color, size)

    @classmethod
    def clear_cache(cls):
        """清空图标缓存"""
        cls._cache.clear()
