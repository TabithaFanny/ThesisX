"""Mock data for workspace home page."""

from __future__ import annotations

# Progress cards — aligned with page_01_workspace_home.svg
MOCK_PROGRESS_CARDS = [
    {"title": "大纲完成度", "percent": 54},
    {"title": "文献整理进度", "percent": 78},
    {"title": "基于深度学习的摘要生成", "percent": 100},
]

# Legacy projects (kept for compatibility, no longer used in home page)
MOCK_PROJECTS = [
    {
        "title": "数字化转型背景下基层治理创新研究",
        "subtitle": "硕士学位论文 · 第三稿",
        "status": "写作中",
        "status_type": "primary",
        "meta": "最后编辑: 2 小时前 · 12,340 字",
    },
    {
        "title": "社区网格化管理效能评估",
        "subtitle": "期刊论文 · 投稿准备",
        "status": "审稿中",
        "status_type": "warning",
        "meta": "最后编辑: 1 天前 · 8,200 字",
    },
    {
        "title": "人工智能赋能公共服务的路径分析",
        "subtitle": "课程论文 · 初稿",
        "status": "已完成",
        "status_type": "success",
        "meta": "最后编辑: 3 天前 · 6,800 字",
    },
]

MOCK_RECENT_FILES = [
    {"name": "论文初稿.md", "modified": "今天 14:30"},
    {"name": "文献综述.md", "modified": "昨天 09:15"},
    {"name": "rebuttal草案.md", "modified": "3 天前"},
]

MOCK_TODO_ITEMS = [
    {"text": "补充研究背景"},
    {"text": "检查引用一致性"},
    {"text": "提交 Conference 模板"},
]

# Literature categories — aligned with page_04_literature_management.svg
MOCK_LIT_CATEGORIES = [
    {"name": "全部文献", "count": 512, "active": True},
    {"name": "我的收藏", "count": 126, "active": False},
    {"name": "回收站", "count": 32, "active": False},
]
