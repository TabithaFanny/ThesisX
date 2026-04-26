from typing import Callable, Dict

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget


class ShortcutManager:
    """Central registry for keyboard shortcuts."""

    def __init__(self, parent: QWidget):
        self._parent = parent
        self._shortcuts: Dict[str, QShortcut] = {}

    def register(self, key_sequence: str, callback: Callable, description: str = ""):
        shortcut = QShortcut(QKeySequence(key_sequence), self._parent)
        shortcut.activated.connect(callback)
        self._shortcuts[key_sequence] = shortcut

    def unregister(self, key_sequence: str):
        if key_sequence in self._shortcuts:
            shortcut = self._shortcuts.pop(key_sequence)
            shortcut.setEnabled(False)
            shortcut.deleteLater()
