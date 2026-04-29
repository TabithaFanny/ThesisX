"""WorkerManager 单元测试

覆盖：start, cancel, cancel_all, is_running 方法。
"""
import pytest
from unittest.mock import MagicMock

from app.core.worker_manager import WorkerManager


class TestWorkerManager:
    """WorkerManager 核心功能测试"""

    def setup_method(self):
        """每个测试前创建新实例"""
        self.mgr = WorkerManager()

    def _make_mock_worker(self, running: bool = False):
        """创建 mock QThread worker"""
        worker = MagicMock()
        worker.isRunning.return_value = running
        worker.wait.return_value = True
        return worker

    # ── start ──

    def test_start_registers_worker(self):
        """start 注册 worker 并启动"""
        worker = self._make_mock_worker()
        self.mgr.start("ai", worker)
        worker.start.assert_called_once()
        assert self.mgr.is_running("ai") is False  # mock 不会真正 running

    def test_start_cancels_existing_worker(self):
        """start 同槽位已有 running worker 时先 cancel"""
        old_worker = self._make_mock_worker(running=True)
        new_worker = self._make_mock_worker()

        self.mgr.start("ai", old_worker)
        self.mgr.start("ai", new_worker)

        old_worker.cancel.assert_called_once()
        old_worker.wait.assert_called_once()
        new_worker.start.assert_called_once()

    def test_start_replaces_stopped_worker(self):
        """start 同槽位已有 stopped worker 时直接替换"""
        old_worker = self._make_mock_worker(running=False)
        new_worker = self._make_mock_worker()

        self.mgr.start("ai", old_worker)
        self.mgr.start("ai", new_worker)

        old_worker.cancel.assert_not_called()
        new_worker.start.assert_called_once()

    # ── is_running ──

    def test_is_running_unknown_slot(self):
        """未知槽位返回 False"""
        assert self.mgr.is_running("nonexistent") is False

    def test_is_running_with_running_worker(self):
        """running worker 返回 True"""
        worker = self._make_mock_worker(running=True)
        self.mgr.start("ai", worker)
        assert self.mgr.is_running("ai") is True

    def test_is_running_with_stopped_worker(self):
        """stopped worker 返回 False"""
        worker = self._make_mock_worker(running=False)
        self.mgr.start("ai", worker)
        assert self.mgr.is_running("ai") is False

    # ── cancel ──

    def test_cancel_running_worker(self):
        """cancel 正在运行的 worker"""
        worker = self._make_mock_worker(running=True)
        self.mgr.start("ai", worker)
        self.mgr.cancel("ai")

        worker.cancel.assert_called_once()
        worker.wait.assert_called_once()

    def test_cancel_stopped_worker(self):
        """cancel 已停止的 worker 不调用 cancel/wait"""
        worker = self._make_mock_worker(running=False)
        self.mgr.start("ai", worker)
        self.mgr.cancel("ai")

        worker.cancel.assert_not_called()

    def test_cancel_unknown_slot(self):
        """cancel 未知槽位不崩溃"""
        self.mgr.cancel("nonexistent")  # 应无异常

    def test_cancel_custom_timeout(self):
        """cancel 使用自定义超时"""
        worker = self._make_mock_worker(running=True)
        self.mgr.start("ai", worker)
        self.mgr.cancel("ai", timeout_ms=5000)

        worker.wait.assert_called_once_with(5000)

    # ── cancel_all ──

    def test_cancel_all_multiple_workers(self):
        """cancel_all 取消所有 running workers"""
        w1 = self._make_mock_worker(running=True)
        w2 = self._make_mock_worker(running=True)
        w3 = self._make_mock_worker(running=False)

        self.mgr.start("ai", w1)
        self.mgr.start("plag", w2)
        self.mgr.start("img", w3)

        self.mgr.cancel_all()

        w1.cancel.assert_called_once()
        w2.cancel.assert_called_once()
        w3.cancel.assert_not_called()  # 已停止

    def test_cancel_all_empty(self):
        """cancel_all 空管理器不崩溃"""
        self.mgr.cancel_all()

    def test_cancel_all_custom_timeout(self):
        """cancel_all 使用自定义超时"""
        w1 = self._make_mock_worker(running=True)
        self.mgr.start("ai", w1)
        self.mgr.cancel_all(timeout_ms=1000)

        w1.wait.assert_called_once_with(1000)

    # ── 多槽位独立性 ──

    def test_independent_slots(self):
        """不同槽位独立管理"""
        w1 = self._make_mock_worker(running=True)
        w2 = self._make_mock_worker(running=True)

        self.mgr.start("ai", w1)
        self.mgr.start("plag", w2)

        assert self.mgr.is_running("ai") is True
        assert self.mgr.is_running("plag") is True

        self.mgr.cancel("ai")
        w1.cancel.assert_called_once()
        w2.cancel.assert_not_called()
