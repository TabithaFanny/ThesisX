"""测试配置文件

本文件包含 pytest 的全局配置和 fixtures。
"""
import os
import sys
from pathlib import Path

import pytest

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_markdown():
    """提供示例 Markdown 文本"""
    return """# 测试文档

这是一个测试文档。

## 第一章

这是第一章的内容。

### 1.1 小节

这是小节内容。

## 第二章

这是第二章的内容。
"""


@pytest.fixture
def sample_config():
    """提供示例配置"""
    return {
        "title": "测试图表",
        "labels": ["A", "B", "C", "D"],
        "series": [
            {"name": "系列1", "values": [10, 20, 30, 40]},
            {"name": "系列2", "values": [15, 25, 35, 45]}
        ]
    }


@pytest.fixture
def temp_file(tmp_path):
    """提供临时文件路径"""
    def _create_temp_file(content: str, suffix: str = ".md"):
        file_path = tmp_path / f"test{suffix}"
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)
    return _create_temp_file
