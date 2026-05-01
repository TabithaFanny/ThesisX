"""Design tokens derived from ThesisX SVG component system.

Color palette: Blue-600 monochrome accent, slate-800/500 text, blue-gray borders.
Typography: Inter + PingFang SC (macOS) + Microsoft YaHei (Windows).
"""

from __future__ import annotations

import sys

# ---------------------------------------------------------------------------
# Font family (platform-aware)
# ---------------------------------------------------------------------------

if sys.platform == "darwin":
    FONT_FAMILY = '"PingFang SC", "Hiragino Sans GB", "Helvetica Neue", sans-serif'
elif sys.platform == "win32":
    FONT_FAMILY = '"Microsoft YaHei", "Segoe UI", sans-serif'
else:
    FONT_FAMILY = '"Noto Sans CJK SC", "WenQuanYi Micro Hei", sans-serif'

# ---------------------------------------------------------------------------
# Color tokens — light theme
# ---------------------------------------------------------------------------

class Light:
    """Light theme tokens from SVG design system."""
    # Surfaces
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#F9FBFF"
    CANVAS = "#F7FAFF"

    # Primary accent (Blue-600)
    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    PRIMARY_LIGHT = "#EEF5FF"
    PRIMARY_BORDER = "#BFDBFE"
    PRIMARY_SOFT = "#60A5FA"

    # Text
    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#64748B"
    TEXT_MUTED = "#94A3B8"
    TEXT_ON_PRIMARY = "#FFFFFF"

    # Borders
    BORDER = "#D7E3F5"
    BORDER_SUBTLE = "#E6EEF9"

    # Status
    SUCCESS = "#16A34A"
    SUCCESS_BG = "#F0FDF4"
    WARNING = "#D97706"
    WARNING_BG = "#FFFBEB"
    ERROR = "#DC2626"
    ERROR_BG = "#FEF2F2"

    # Shadows
    SHADOW_SM = "0 1px 2px rgba(0, 0, 0, 0.05)"
    SHADOW_MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1)"

    # Scrollbar
    SCROLLBAR = "#CBD5E1"
    SCROLLBAR_HOVER = "#94A3B8"


class Dark:
    """Dark theme tokens (Catppuccin Mocha inspired, adjusted for SVG system)."""
    # Surfaces
    SURFACE = "#1E1E2E"
    SURFACE_ALT = "#181825"
    CANVAS = "#11111B"

    # Primary accent
    PRIMARY = "#89B4FA"
    PRIMARY_HOVER = "#74C7EC"
    PRIMARY_LIGHT = "#1E2A3F"
    PRIMARY_BORDER = "#2A3F5F"
    PRIMARY_SOFT = "#74C7EC"

    # Text
    TEXT_PRIMARY = "#CDD6F4"
    TEXT_SECONDARY = "#A6ADC8"
    TEXT_MUTED = "#585B70"
    TEXT_ON_PRIMARY = "#1E1E2E"

    # Borders
    BORDER = "#313244"
    BORDER_SUBTLE = "#45475A"

    # Status
    SUCCESS = "#A6E3A1"
    SUCCESS_BG = "#1A2E1A"
    WARNING = "#F9E2AF"
    WARNING_BG = "#2E2A1A"
    ERROR = "#F38BA8"
    ERROR_BG = "#2E1A1A"

    # Shadows
    SHADOW_SM = "0 1px 2px rgba(0, 0, 0, 0.3)"
    SHADOW_MD = "0 4px 6px -1px rgba(0, 0, 0, 0.4)"

    # Scrollbar
    SCROLLBAR = "#45475A"
    SCROLLBAR_HOVER = "#585B70"


# ---------------------------------------------------------------------------
# Typography scale
# ---------------------------------------------------------------------------

class FontSize:
    """Font size scale in pixels."""
    HERO = 28
    PAGE_TITLE = 18
    PANEL_TITLE = 16
    CARD_TITLE = 14
    BODY = 13
    SECONDARY = 12
    CAPTION = 11
    SMALL = 10
    MICRO = 9


class FontWeight:
    """Font weight scale."""
    EXTRABOLD = 800
    BOLD = 700
    SEMIBOLD = 600
    MEDIUM = 500
    REGULAR = 400


# ---------------------------------------------------------------------------
# Border radius
# ---------------------------------------------------------------------------

class Radius:
    """Border radius scale in pixels."""
    PAGE = 8
    PANEL = 6
    BUBBLE = 10
    INPUT = 5
    PILL = 12
    BAR = 3
    BUTTON = 6


# ---------------------------------------------------------------------------
# Spacing
# ---------------------------------------------------------------------------

class Spacing:
    """Spacing scale in pixels."""
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24
