"""WorkerManager — 集中管理 QThread worker 的生命周期。

替代 MainWindow 中 7 个独立 worker 引用 + 8 处重复 cancel 模式。

用法：
    self._workers = WorkerManager()

    # 启动 worker（自动 cancel 同槽位旧 worker）
    self._workers.start("ai", worker)

    # 取消特定槽位
    self._workers.cancel("ai")

    # 取消所有
    self._workers.cancel_all()

    # 检查状态
    if self._workers.is_running("ai"):
        ...
"""

import logging
from typing import Dict, Optional

from PyQt6.QtCore import QThread

logger = logging.getLogger(__name__)

# 默认 cancel 后 wait 超时（毫秒）
DEFAULT_CANCEL_TIMEOUT_MS = 2000


class WorkerManager:
    """管理多个命名 QThread worker 槽位的生命周期。"""

    def __init__(self) -> None:
        self._workers: Dict[str, QThread] = {}

    def start(self, slot: str, worker: QThread) -> None:
        """启动 worker 到指定槽位。

        如果同槽位已有 running worker，先 cancel 并等待其结束。

        Args:
            slot: 槽位名称（如 "ai", "plag", "img"）
            worker: QThread 实例
        """
        self.cancel(slot)
        self._workers[slot] = worker
        worker.start()

    def cancel(self, slot: str, timeout_ms: int = DEFAULT_CANCEL_TIMEOUT_MS) -> None:
        """取消指定槽位的 worker。

        如果该槽位有 running worker，调用 cancel() + wait()。

        Args:
            slot: 槽位名称
            timeout_ms: wait 超时（毫秒）
        """
        worker = self._workers.get(slot)
        if worker is not None and worker.isRunning():
            worker.cancel()
            worker.wait(timeout_ms)

    def cancel_all(self, timeout_ms: int = DEFAULT_CANCEL_TIMEOUT_MS) -> None:
        """取消所有 running workers。"""
        for slot in list(self._workers):
            self.cancel(slot, timeout_ms)

    def is_running(self, slot: str) -> bool:
        """检查指定槽位是否有 running worker。"""
        worker = self._workers.get(slot)
        return worker is not None and worker.isRunning()
