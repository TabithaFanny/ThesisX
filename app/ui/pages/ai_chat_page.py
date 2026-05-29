"""AI Chat page — multi-agent chat interface mock.

Aligned with page_03_ai_chat.svg + component_agent_chat_panel.svg.
Left: conversation history list.
Center: chat flow with user/AI bubbles.
Right: project context + Agent list.
User bubbles: #EEF5FF (light blue) + dark text.
AI bubbles: #2563EB (deep blue) + white text.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QVBoxLayout, QWidget, QScrollArea, QFrame,
)

from app.ui.design_tokens import get_theme, ThemeManager, FontSize, Radius, Spacing
from app.ui.components.base import (
    PageHeader, StatusBadge, ComingSoonBadge, AgentCard, _card_style,
)
from app.ui.mock.pages_data import (
    MOCK_AGENTS, MOCK_CHAT_MESSAGES, MOCK_CHAT_CONTEXT, MOCK_CHAT_HISTORY,
)


class AIChatPage(QWidget):
    """AI Chat mock page — conversation history + chat flow + context panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        L = get_theme()
        self.setStyleSheet(f"background-color: {L.CANVAS};")
        self._init_ui()
        ThemeManager.instance().theme_changed.connect(self.apply_theme)

    def apply_theme(self) -> None:
        """Re-apply theme by rebuilding UI."""
        old = self.layout()
        if old is not None:
            QWidget().setLayout(old)
        self._init_ui()

    def _init_ui(self):
        L = get_theme()
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.MD, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Header with coming soon badge
        header_row = QHBoxLayout()
        header_row.addWidget(PageHeader("AI 助手", "多 Agent 协作写作，智能问答与论文辅助。"))
        header_row.addWidget(ComingSoonBadge("V2 计划"))
        header_row.addStretch()
        root.addLayout(header_row)

        # 3-column layout
        cols = QHBoxLayout()
        cols.setSpacing(Spacing.MD)

        # --- Left: conversation history (SVG: 对话历史) ---
        history_panel = QFrame()
        history_panel.setStyleSheet(_card_style())
        history_panel.setFixedWidth(200)
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(Spacing.SM, Spacing.MD, Spacing.SM, Spacing.MD)
        history_layout.setSpacing(Spacing.SM)

        history_title = QLabel("对话历史")
        history_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        history_layout.addWidget(history_title)

        for item in MOCK_CHAT_HISTORY:
            row = QVBoxLayout()
            row.setSpacing(Spacing.XS)

            title = QLabel(item["title"])
            if item["active"]:
                title.setStyleSheet(
                    f"font-size: {FontSize.BODY}px; color: {L.PRIMARY}; font-weight: bold;"
                )
            else:
                title.setStyleSheet(
                    f"font-size: {FontSize.BODY}px; color: {L.TEXT_SECONDARY};"
                )
            row.addWidget(title)

            time = QLabel(item["time"])
            time.setStyleSheet(
                f"font-size: {FontSize.MICRO}px; color: {L.TEXT_MUTED};"
            )
            row.addWidget(time)

            history_layout.addLayout(row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {L.BORDER_SUBTLE};")
        history_layout.addWidget(sep)

        # Agent list (compact, below history)
        agent_section_title = QLabel("AI 助手")
        agent_section_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold; "
            f"margin-top: {Spacing.SM}px;"
        )
        history_layout.addWidget(agent_section_title)

        for agent in MOCK_AGENTS:
            row = QHBoxLayout()
            row.setSpacing(Spacing.SM)

            dot = QLabel("●" if agent["status"] == "在线" else "○")
            dot.setFixedWidth(12)
            if agent["status"] == "在线":
                dot.setStyleSheet(f"color: {L.SUCCESS}; font-size: 8px;")
            else:
                dot.setStyleSheet(f"color: {L.TEXT_MUTED}; font-size: 8px;")
            row.addWidget(dot)

            name = QLabel(agent["name"])
            name.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_PRIMARY};"
            )
            row.addWidget(name, 1)

            history_layout.addLayout(row)

        history_layout.addStretch()
        cols.addWidget(history_panel)

        # --- Center: Chat flow ---
        chat_panel = QFrame()
        chat_panel.setStyleSheet(_card_style())
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        chat_layout.setSpacing(Spacing.SM)

        for msg in MOCK_CHAT_MESSAGES:
            bubble = self._create_bubble(msg)
            chat_layout.addWidget(bubble)

        chat_layout.addStretch()

        # Input bar mock — SVG: "输入指令，或 @引用 / #章节 / skill"
        input_bar = QFrame()
        input_bar.setStyleSheet(
            f"QFrame {{ background-color: {L.SURFACE}; border: 1px solid {L.BORDER}; "
            f"border-radius: {Radius.INPUT}px; padding: {Spacing.SM}px; }}"
        )
        input_bar.setFixedHeight(40)
        input_row = QHBoxLayout(input_bar)
        input_row.setContentsMargins(Spacing.SM, 0, Spacing.SM, 0)
        input_lbl = QLabel("输入指令，或 @引用 / #章节 / skill")
        input_lbl.setStyleSheet(f"color: {L.TEXT_MUTED}; font-size: {FontSize.BODY}px;")
        input_row.addWidget(input_lbl)
        preview_badge = QLabel("仅预览")
        preview_badge.setStyleSheet(
            f"color: {L.WARNING}; font-size: {FontSize.MICRO}px; font-weight: bold;"
        )
        preview_badge.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        input_row.addWidget(preview_badge)
        chat_layout.addWidget(input_bar)

        cols.addWidget(chat_panel, 1)

        # --- Right: Context panel ---
        ctx_panel = QFrame()
        ctx_panel.setStyleSheet(_card_style())
        ctx_panel.setFixedWidth(200)
        ctx_layout = QVBoxLayout(ctx_panel)
        ctx_layout.setContentsMargins(Spacing.SM, Spacing.MD, Spacing.SM, Spacing.MD)
        ctx_layout.setSpacing(Spacing.SM)

        ctx_title = QLabel("上下文")
        ctx_title.setStyleSheet(
            f"font-size: {FontSize.CARD_TITLE}px; font-weight: bold; color: {L.TEXT_PRIMARY};"
        )
        ctx_layout.addWidget(ctx_title)

        for key, val in MOCK_CHAT_CONTEXT.items():
            k = QLabel(key.replace("_", " ").title())
            k.setStyleSheet(f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_SECONDARY};")
            ctx_layout.addWidget(k)
            v = QLabel(str(val))
            v.setStyleSheet(
                f"font-size: {FontSize.BODY}px; color: {L.TEXT_PRIMARY}; font-weight: bold; "
                f"margin-bottom: {Spacing.XS}px;"
            )
            ctx_layout.addWidget(v)

        # Skills section
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {L.BORDER_SUBTLE};")
        ctx_layout.addWidget(sep2)

        skills_title = QLabel("可用 Skills")
        skills_title.setStyleSheet(
            f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_MUTED}; font-weight: bold; "
            f"margin-top: {Spacing.SM}px;"
        )
        ctx_layout.addWidget(skills_title)

        for skill_name in ["论文结构规划", "文献综述生成", "AI 去痕润色"]:
            s = QLabel(f"▸ {skill_name}")
            s.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.PRIMARY};"
            )
            ctx_layout.addWidget(s)

        ctx_layout.addStretch()
        cols.addWidget(ctx_panel)

        root.addLayout(cols, 1)

    def _create_bubble(self, msg: dict) -> QFrame:
        """Create a chat bubble aligned with SVG color scheme.

        SVG: user = #EEF5FF (light blue) + dark text
             AI   = #2563EB (deep blue) + white text
        """
        L = get_theme()
        bubble = QFrame()
        is_user = msg["sender"] == "user"

        if is_user:
            bg = L.PRIMARY_LIGHT  # #EEF5FF
            text_color = L.TEXT_PRIMARY  # #1E293B
            time_color = L.TEXT_SECONDARY
        else:
            bg = L.PRIMARY  # #2563EB
            text_color = L.TEXT_ON_PRIMARY  # #FFFFFF
            time_color = L.PRIMARY_LIGHT

        bubble.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border-radius: {Radius.BUBBLE}px; "
            f"padding: {Spacing.SM}px; margin: {Spacing.XS}px {Spacing.SM}px; }}"
        )
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        layout.setSpacing(Spacing.XS)

        if not is_user:
            agent_lbl = QLabel(msg.get("agent", "Agent"))
            agent_lbl.setStyleSheet(
                f"font-size: {FontSize.SECONDARY}px; color: {L.TEXT_ON_PRIMARY}; font-weight: bold;"
            )
            layout.addWidget(agent_lbl)

        content = QLabel(msg["content"])
        content.setWordWrap(True)
        content.setStyleSheet(f"font-size: {FontSize.BODY}px; color: {text_color};")
        layout.addWidget(content)

        time_lbl = QLabel(msg["time"])
        time_lbl.setStyleSheet(f"font-size: {FontSize.MICRO}px; color: {time_color};")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(time_lbl)

        return bubble
