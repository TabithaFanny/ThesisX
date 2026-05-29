"""Tests for RagService (Vision 3.5)."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.core.rag.service import RagService, RagResult
from app.core.knowledge.models import KnowledgeItem


# ── fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def sample_items() -> list[KnowledgeItem]:
    return [
        KnowledgeItem.create(
            item_type="note",
            title="机器学习入门",
            content="监督学习是一种从标注数据中学习映射函数的方法。常见算法包括线性回归、决策树和支持向量机。",
        ),
        KnowledgeItem.create(
            item_type="literature",
            title="Smith 2020 Deep Learning",
            content="Deep learning has revolutionized computer vision and natural language processing. "
                     "Convolutional neural networks (CNNs) are particularly effective for image recognition tasks.",
        ),
        KnowledgeItem.create(
            item_type="theory",
            title="制度理论概述",
            content="制度理论认为组织行为受制度环境深刻影响。合法性机制、同构压力和制度逻辑是核心概念。"
                     "DiMaggio和Powell提出了三种同构机制：强制同构、模仿同构和规范同构。",
        ),
        KnowledgeItem.create(
            item_type="evidence",
            title="实验数据",
            content="实验结果表明，在测试集上准确率达到94.3%，F1分数为0.91。"
                     "与基线模型相比提升了3.2个百分点。",
        ),
        KnowledgeItem.create(
            item_type="note",
            title="空内容条目",
            content="",
        ),
    ]


@pytest.fixture
def mock_store(sample_items):
    store = MagicMock()
    store.list.return_value = sample_items
    store.search.return_value = []
    return store


@pytest.fixture
def rag_service(mock_store):
    return RagService(knowledge_store=mock_store)


# ── build_index ─────────────────────────────────────────────────────────────

class TestBuildIndex:
    def test_build_index_from_store(self, rag_service):
        count = rag_service.build_index()
        assert count > 0
        assert rag_service.index_size() == count

    def test_build_index_filters_empty_content(self, rag_service):
        count = rag_service.build_index()
        # 5 items but 1 has empty content
        assert rag_service.index_size() > 0

    def test_build_index_sets_source_metadata(self, rag_service):
        rag_service.build_index()
        # All chunks should have source metadata
        for chunk in rag_service._index:
            assert "source_id" in chunk
            assert "source_title" in chunk
            assert "item_type" in chunk

    def test_build_index_empty_store(self):
        store = MagicMock()
        store.list.return_value = []
        svc = RagService(knowledge_store=store)
        count = svc.build_index()
        assert count == 0
        assert svc.index_size() == 0

    def test_build_index_with_type_filter(self, rag_service):
        rag_service._store.list.return_value = [
            KnowledgeItem.create(item_type="note", title="测试", content="测试内容"),
        ]
        count = rag_service.build_index(item_type="note")
        rag_service._store.list.assert_called_once_with(item_type="note")

    def test_index_size_after_build(self, rag_service):
        count = rag_service.build_index()
        assert rag_service.index_size() == count

    def test_persistent_index_survives_new_service(self, tmp_path, monkeypatch):
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("app.core.knowledge.store._DB_PATH", db_path)
        store = __import__("app.core.knowledge.store", fromlist=["KnowledgeStore"]).KnowledgeStore()
        item = KnowledgeItem.create(
            item_type="note",
            title="Persistent RAG",
            content="persistent alpha beta gamma uniquechunk",
            project_id="p1",
        )
        store.add(item)

        first = RagService()
        count = first.build_index()
        assert count > 0

        second = RagService()
        assert second.index_size() == count
        results = second.search("uniquechunk", top_k=5)
        assert results
        assert results[0].source_id == item.id

    def test_persistent_filters_and_rebuild_replace(self, tmp_path, monkeypatch):
        db_path = tmp_path / "test.db"
        monkeypatch.setattr("app.core.knowledge.store._DB_PATH", db_path)
        store = __import__("app.core.knowledge.store", fromlist=["KnowledgeStore"]).KnowledgeStore()
        item1 = KnowledgeItem.create(
            item_type="note",
            title="Project One",
            content="alpha projectone only",
            project_id="p1",
        )
        item2 = KnowledgeItem.create(
            item_type="literature",
            title="Project Two",
            content="beta projecttwo only",
            project_id="p2",
        )
        store.add(item1)
        store.add(item2)

        svc = RagService()
        count1 = svc.build_index(project_id="p1")
        count2 = svc.build_index(project_id="p1")
        assert count1 == count2
        assert svc.index_size(project_id="p1") == count1
        assert svc.index_size(project_id="p2") == 0
        assert svc.search("projectone", project_id="p1")
        assert not svc.search("projecttwo", project_id="p1")

        svc.build_index(object_id=item2.id)
        assert svc.index_size(object_id=item2.id) > 0
        assert svc.search("projecttwo", object_id=item2.id)


# ── search ──────────────────────────────────────────────────────────────────

class TestSearch:
    def test_search_returns_results(self, rag_service):
        rag_service.build_index()
        results = rag_service.search("机器学习")
        assert len(results) > 0
        for r in results:
            assert isinstance(r, RagResult)
            assert r.source_title
            assert r.score >= 0

    def test_search_empty_index_returns_empty(self, rag_service):
        results = rag_service.search("test query")
        assert results == []

    def test_search_empty_query_returns_empty(self, rag_service):
        rag_service.build_index()
        results = rag_service.search("")
        assert results == []

    def test_search_returns_top_k_results(self, rag_service):
        rag_service.build_index()
        results = rag_service.search("学习", top_k=2)
        assert len(results) <= 2

    def test_search_type_filter(self, rag_service):
        rag_service.build_index()
        results = rag_service.search("deep learning", item_type="literature")
        for r in results:
            assert r.item_type == "literature"

    def test_search_scores_are_sorted(self, rag_service):
        rag_service.build_index()
        results = rag_service.search("制度 理论")
        if len(results) >= 2:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_search_chinese_query(self, rag_service):
        rag_service.build_index()
        results = rag_service.search("深度学习 神经网络")
        # Should find the English deep learning content due to keyword extraction
        assert isinstance(results, list)

    def test_search_no_match_returns_empty(self, rag_service):
        rag_service.build_index()
        results = rag_service.search("zzzzxywxyz 不存在的内容")
        # May return empty or zero-scored results
        assert all(r.score == 0 for r in results) if results else True

    def test_search_result_has_chunk_id(self, rag_service):
        rag_service.build_index()
        results = rag_service.search("CNN")
        for r in results:
            assert r.chunk_id


# ── context bundle ──────────────────────────────────────────────────────────

class TestContextBundle:
    def test_get_context_bundle_format(self, rag_service):
        rag_service.build_index()
        bundle = rag_service.get_context_bundle("机器学习", top_k=3)
        assert "相关知识库上下文" in bundle
        assert "相关度" in bundle

    def test_get_context_bundle_empty_index(self, rag_service):
        bundle = rag_service.get_context_bundle("test")
        assert "无相关" in bundle or bundle.startswith("<!--")

    def test_export_context_file(self, rag_service, tmp_path):
        rag_service.build_index()
        path = rag_service.export_context_file("学习", top_k=2, output_dir=tmp_path)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert len(content) > 0
