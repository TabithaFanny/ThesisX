"""性能监控工具

提供性能监控、计时和分析功能。
"""
import time
import logging
from functools import wraps
from typing import Callable, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器

    记录和分析函数执行时间。
    """

    def __init__(self):
        self._metrics = {}

    def record(self, operation: str, duration_ms: float):
        """记录操作耗时

        Args:
            operation: 操作名称
            duration_ms: 耗时（毫秒）
        """
        if operation not in self._metrics:
            self._metrics[operation] = {
                "count": 0,
                "total_ms": 0.0,
                "min_ms": float("inf"),
                "max_ms": 0.0,
            }

        metrics = self._metrics[operation]
        metrics["count"] += 1
        metrics["total_ms"] += duration_ms
        metrics["min_ms"] = min(metrics["min_ms"], duration_ms)
        metrics["max_ms"] = max(metrics["max_ms"], duration_ms)

    def get_stats(self, operation: str) -> dict:
        """获取操作统计信息

        Args:
            operation: 操作名称

        Returns:
            包含统计信息的字典
        """
        if operation not in self._metrics:
            return {}

        metrics = self._metrics[operation]
        avg_ms = metrics["total_ms"] / metrics["count"] if metrics["count"] > 0 else 0

        return {
            "count": metrics["count"],
            "total_ms": metrics["total_ms"],
            "avg_ms": avg_ms,
            "min_ms": metrics["min_ms"],
            "max_ms": metrics["max_ms"],
        }

    def get_all_stats(self) -> dict:
        """获取所有操作的统计信息"""
        return {op: self.get_stats(op) for op in self._metrics.keys()}

    def print_report(self):
        """打印性能报告"""
        logger.info("=" * 60)
        logger.info("性能监控报告")
        logger.info("=" * 60)

        for operation, stats in self.get_all_stats().items():
            logger.info(
                f"{operation}:\n"
                f"  调用次数: {stats['count']}\n"
                f"  总耗时: {stats['total_ms']:.2f}ms\n"
                f"  平均耗时: {stats['avg_ms']:.2f}ms\n"
                f"  最小耗时: {stats['min_ms']:.2f}ms\n"
                f"  最大耗时: {stats['max_ms']:.2f}ms"
            )

        logger.info("=" * 60)

    def clear(self):
        """清空所有统计数据"""
        self._metrics.clear()


# 全局性能监控器实例
_global_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    return _global_monitor


@contextmanager
def measure_time(operation: str, log_threshold_ms: float = 100.0):
    """测量代码块执行时间的上下文管理器

    Args:
        operation: 操作名称
        log_threshold_ms: 日志记录阈值（毫秒），超过此值才记录日志

    Example:
        >>> with measure_time("load_document"):
        ...     document = load_large_file()
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        _global_monitor.record(operation, duration_ms)

        if duration_ms >= log_threshold_ms:
            logger.info(f"{operation} 耗时: {duration_ms:.2f}ms")


def timed(operation: str = None, log_threshold_ms: float = 100.0):
    """函数计时装饰器

    Args:
        operation: 操作名称，默认使用函数名
        log_threshold_ms: 日志记录阈值（毫秒）

    Example:
        >>> @timed("render_markdown")
        ... def render(text: str) -> str:
        ...     return markdown.render(text)
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                _global_monitor.record(op_name, duration_ms)

                if duration_ms >= log_threshold_ms:
                    logger.info(f"{op_name} 耗时: {duration_ms:.2f}ms")

        return wrapper

    return decorator


class PerformanceWarning:
    """性能警告检查器

    检测性能问题并发出警告。
    """

    # 性能阈值（毫秒）
    THRESHOLDS = {
        "document_open": 500,
        "document_save": 500,
        "markdown_render": 1000,
        "chart_generate": 200,
        "export_docx": 5000,
        "export_pptx": 5000,
        "ai_request": 10000,
    }

    @classmethod
    def check(cls, operation: str, duration_ms: float):
        """检查操作是否超过性能阈值

        Args:
            operation: 操作名称
            duration_ms: 实际耗时（毫秒）
        """
        threshold = cls.THRESHOLDS.get(operation)
        if threshold and duration_ms > threshold:
            logger.warning(
                f"性能警告: {operation} 耗时 {duration_ms:.2f}ms "
                f"(阈值: {threshold}ms, 超出 {duration_ms - threshold:.2f}ms)"
            )
