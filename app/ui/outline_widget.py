from typing import List, Tuple

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHeaderView, QTreeWidget, QTreeWidgetItem


class OutlineWidget(QTreeWidget):
    """Sidebar showing document outline / TOC."""

    heading_clicked = pyqtSignal(int)  # emits line number

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("大纲")
        self.setMinimumWidth(220)
        self.setMaximumWidth(320)
        self.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setIndentation(16)
        self.setRootIsDecorated(True)
        self.itemClicked.connect(self._on_item_clicked)

    def update_outline(self, headings: List[Tuple[int, str, int]]):
        self.clear()
        stack = []  # (level, QTreeWidgetItem)

        for level, title, line_num in headings:
            item = QTreeWidgetItem()
            item.setText(0, title)
            item.setData(0, 256, line_num)  # Qt.UserRole = 256

            # Find parent
            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack:
                stack[-1][1].addChild(item)
            else:
                self.addTopLevelItem(item)

            stack.append((level, item))

        self.expandAll()

    def _on_item_clicked(self, item, column):
        line_num = item.data(0, 256)
        if line_num is not None:
            self.heading_clicked.emit(line_num)
