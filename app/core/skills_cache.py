"""Skills 内容缓存模块

提供 Skills 文件内容的缓存机制，避免每次 AI 请求都重新解析文件。
使用文件修改时间检测缓存有效性。
支持异步加载，避免阻塞主线程。
"""

import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# 全局线程池，用于异步解析文件
_executor: Optional[ThreadPoolExecutor] = None


def _get_executor() -> ThreadPoolExecutor:
    """获取全局线程池"""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="skills_parser")
    return _executor


def _parse_file_with_timeout(path: str, timeout: float = 10.0) -> Optional[str]:
    """带超时的文件解析

    Args:
        path: 文件路径
        timeout: 超时时间（秒）

    Returns:
        文件内容，超时或失败返回 None
    """
    from app.core.document_parser import DocumentParser

    try:
        future = _get_executor().submit(DocumentParser.parse_file, path)
        return future.result(timeout=timeout)
    except FuturesTimeoutError:
        logger.warning(f"解析文件超时 ({timeout}s): {path}")
        return None
    except Exception as e:
        logger.warning(f"解析文件失败: {path}, 错误: {e}")
        return None


class SkillsCache:
    """Skills 内容缓存 (线程安全单例)

    缓存所有启用的技能文件内容，通过文件修改时间检测是否需要更新。

    Example:
        >>> cache = SkillsCache.get_instance()
        >>> content = cache.get_skills_content()
        >>> # 修改技能后使缓存失效
        >>> cache.invalidate()
    """

    _instance: Optional["SkillsCache"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._cache: Dict[str, str] = {}  # path -> content
        self._mtimes: Dict[str, float] = {}  # path -> mtime
        self._combined_cache: Optional[str] = None
        self._config_mtime: float = 0
        self._cache_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "SkillsCache":
        """获取单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_skills_content(self) -> str:
        """获取合并后的 Skills 内容

        如果缓存有效则直接返回，否则重新构建缓存。

        Returns:
            合并后的技能内容字符串
        """
        with self._cache_lock:
            if self._is_cache_valid():
                return self._combined_cache or ""
            return self._rebuild_cache()

    def invalidate(self):
        """使缓存失效

        当用户修改技能列表时调用此方法。
        """
        with self._cache_lock:
            self._combined_cache = None
            self._cache.clear()
            self._mtimes.clear()
            self._config_mtime = 0
            logger.debug("Skills 缓存已失效")

    def preload(self):
        """预加载缓存

        应用启动时调用，提前加载所有技能文件。
        """
        with self._cache_lock:
            self._rebuild_cache()
            logger.info("Skills 缓存预加载完成")

    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        return Path.home() / ".wenbiao" / "skills.json"

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._combined_cache is None:
            return False

        config_path = self._get_config_path()
        if not config_path.exists():
            return self._combined_cache == ""

        # 检查配置文件是否修改
        try:
            current_mtime = config_path.stat().st_mtime
            if current_mtime != self._config_mtime:
                return False
        except OSError:
            return False

        # 检查各个技能文件是否修改
        for path, cached_mtime in self._mtimes.items():
            try:
                if os.path.getmtime(path) != cached_mtime:
                    return False
            except OSError:
                return False

        return True

    def _rebuild_cache(self) -> str:
        """重新构建缓存"""
        config_path = self._get_config_path()

        if not config_path.exists():
            self._combined_cache = ""
            return ""

        try:
            # 记录配置文件修改时间
            self._config_mtime = config_path.stat().st_mtime

            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                skills = data.get("skills", [])

            # 清空旧缓存
            self._cache.clear()
            self._mtimes.clear()

            # 读取所有启用的技能文件
            contents = []
            for skill in skills:
                if not skill.get("enabled", True):
                    continue

                path = skill.get("path", "")
                if not os.path.exists(path):
                    continue

                try:
                    # 记录文件修改时间
                    self._mtimes[path] = os.path.getmtime(path)

                    # 检查是否已缓存
                    if path in self._cache:
                        content = self._cache[path]
                    else:
                        # 使用带超时的解析，避免卡死
                        content = _parse_file_with_timeout(path, timeout=15.0)
                        if content:
                            self._cache[path] = content

                    if content:
                        name = skill.get("name", os.path.basename(path))
                        contents.append(f"# Skill: {name}\n\n{content}")

                except Exception as e:
                    logger.warning(f"无法读取技能文件 {path}: {e}")

            if contents:
                self._combined_cache = "\n\n---\n\n".join(contents)
            else:
                self._combined_cache = ""

            logger.debug(f"Skills 缓存已重建，共 {len(contents)} 个文件")
            return self._combined_cache

        except Exception as e:
            logger.error(f"重建 Skills 缓存失败: {e}")
            self._combined_cache = ""
            return ""


def get_skills_content() -> str:
    """便捷函数：获取 Skills 内容

    Returns:
        合并后的技能内容
    """
    return SkillsCache.get_instance().get_skills_content()


def invalidate_skills_cache():
    """便捷函数：使 Skills 缓存失效"""
    SkillsCache.get_instance().invalidate()


def preload_skills_cache():
    """便捷函数：预加载 Skills 缓存"""
    SkillsCache.get_instance().preload()
