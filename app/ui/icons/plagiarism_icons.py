"""
plagiarism_icons.py — 论文查重模块 SVG 图标管理

提供统一的图标加载和缓存机制。
"""

import os
from functools import lru_cache

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QLabel

# 图标目录
_ICONS_DIR = os.path.join(os.path.dirname(__file__), "plagiarism")


class PlagiarismIcons:
    """论文查重图标管理器。"""

    # 图标名称映射
    CHECK = "check"
    REWRITE = "rewrite"
    SMART_REWRITE = "smart_rewrite"
    QUICK_REWRITE = "quick_rewrite"
    REFRESH = "refresh"
    HIGH_RISK = "high_risk"
    MEDIUM_RISK = "medium_risk"
    LOW_RISK = "low_risk"
    SUGGESTION = "suggestion"
    SOURCE = "source"
    DATABASE = "database"
    TARGET = "target"
    ITERATION = "iteration"
    VERIFY = "verify"
    SETTINGS = "settings"
    SUCCESS = "success"
    INFO = "info"
    MODE_STANDARD = "mode_standard"
    MODE_AGGRESSIVE = "mode_aggressive"
    MODE_CONSERVATIVE = "mode_conservative"

    @staticmethod
    @lru_cache(maxsize=32)
    def get_icon(name: str, size: int = 24) -> QIcon:
        """获取指定名称的图标。

        Args:
            name: 图标名称
            size: 图标尺寸

        Returns:
            QIcon 对象
        """
        svg_path = os.path.join(_ICONS_DIR, f"{name}.svg")
        if not os.path.exists(svg_path):
            return QIcon()

        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    @staticmethod
    @lru_cache(maxsize=32)
    def get_pixmap(name: str, size: int = 24) -> QPixmap:
        """获取指定名称的 Pixmap。

        Args:
            name: 图标名称
            size: 图标尺寸

        Returns:
            QPixmap 对象
        """
        svg_path = os.path.join(_ICONS_DIR, f"{name}.svg")
        if not os.path.exists(svg_path):
            return QPixmap()

        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)

        from PyQt6.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return pixmap

    @staticmethod
    def create_icon_label(name: str, size: int = 16) -> QLabel:
        """创建带图标的 QLabel。

        Args:
            name: 图标名称
            size: 图标尺寸

        Returns:
            QLabel 对象
        """
        label = QLabel()
        pixmap = PlagiarismIcons.get_pixmap(name, size)
        label.setPixmap(pixmap)
        label.setFixedSize(size, size)
        return label


# 风险等级对应的图标
RISK_ICONS = {
    "high": PlagiarismIcons.HIGH_RISK,
    "medium": PlagiarismIcons.MEDIUM_RISK,
    "low": PlagiarismIcons.LOW_RISK,
}
