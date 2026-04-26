"""缓存机制

提供 LRU 缓存和内存缓存功能，提升性能。
"""
import hashlib
import logging
from functools import lru_cache, wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class MemoryCache:
    """内存缓存

    简单的键值对缓存，支持最大容量限制。
    """

    def __init__(self, max_size: int = 100):
        """初始化缓存

        Args:
            max_size: 最大缓存条目数
        """
        self._cache = {}
        self._max_size = max_size
        self._access_order = []  # 用于 LRU 淘汰

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在返回 None
        """
        if key in self._cache:
            # 更新访问顺序
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: Any):
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果已存在，先删除旧的
        if key in self._cache:
            self._access_order.remove(key)

        # 如果超过最大容量，淘汰最久未使用的
        if len(self._cache) >= self._max_size:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
            logger.debug(f"缓存淘汰: {oldest_key}")

        self._cache[key] = value
        self._access_order.append(key)

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
        logger.debug("缓存已清空")

    def size(self) -> int:
        """获取当前缓存大小"""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._cache


class HashableDict(dict):
    """可哈希的字典

    用于将字典作为缓存键。
    """

    def __hash__(self):
        return hash(frozenset(self.items()))


def make_cache_key(*args, **kwargs) -> str:
    """生成缓存键

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        缓存键字符串
    """
    # 将参数转换为字符串并哈希
    key_parts = []

    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, dict):
            key_parts.append(str(sorted(arg.items())))
        else:
            key_parts.append(str(arg))

    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")

    key_str = "|".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(cache: MemoryCache, key_func: Optional[Callable] = None):
    """缓存装饰器

    Args:
        cache: 缓存实例
        key_func: 自定义键生成函数，默认使用 make_cache_key

    Example:
        >>> chart_cache = MemoryCache(max_size=50)
        >>>
        >>> @cached(chart_cache)
        ... def generate_chart(chart_type: str, config: dict) -> str:
        ...     # 耗时的图表生成逻辑
        ...     return html
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = make_cache_key(*args, **kwargs)

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {func.__name__} ({cache_key[:8]}...)")
                return cached_value

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            logger.debug(f"缓存设置: {func.__name__} ({cache_key[:8]}...)")

            return result

        # 添加清空缓存的方法
        wrapper.clear_cache = cache.clear

        return wrapper

    return decorator


# 全局缓存实例
_markdown_cache = MemoryCache(max_size=100)
_chart_cache = MemoryCache(max_size=50)
_image_cache = MemoryCache(max_size=200)


def get_markdown_cache() -> MemoryCache:
    """获取 Markdown 渲染缓存"""
    return _markdown_cache


def get_chart_cache() -> MemoryCache:
    """获取图表生成缓存"""
    return _chart_cache


def get_image_cache() -> MemoryCache:
    """获取图片缓存"""
    return _image_cache


def clear_all_caches():
    """清空所有全局缓存"""
    _markdown_cache.clear()
    _chart_cache.clear()
    _image_cache.clear()
    logger.info("所有缓存已清空")


# 使用示例
if __name__ == "__main__":
    # 创建缓存
    cache = MemoryCache(max_size=3)

    # 使用装饰器
    @cached(cache)
    def expensive_function(x: int, y: int) -> int:
        print(f"计算 {x} + {y}")
        return x + y

    # 第一次调用，会执行函数
    result1 = expensive_function(1, 2)  # 输出: 计算 1 + 2
    print(f"结果: {result1}")

    # 第二次调用相同参数，从缓存获取
    result2 = expensive_function(1, 2)  # 不输出，从缓存获取
    print(f"结果: {result2}")

    # 不同参数，会执行函数
    result3 = expensive_function(3, 4)  # 输出: 计算 3 + 4
    print(f"结果: {result3}")
