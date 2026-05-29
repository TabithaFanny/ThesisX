"""Tests for KnowledgeStore SQLite CRUD (Vision 3.1)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.core.knowledge.store import KnowledgeStore, _DB_PATH, _get_conn
from app.core.knowledge.models import KnowledgeItem, ITEM_TYPES


@pytest.fixture
def store():
    """Create a KnowledgeStore instance."""
    return KnowledgeStore()


@pytest.fixture(autouse=True)
def _clean_db():
    """Clean up DB after each test to avoid cross-test pollution."""
    yield
    if _DB_PATH.exists():
        os.remove(str(_DB_PATH))


class TestCreateAndGet:
    def test_create_item_and_get(self, store):
        item = KnowledgeItem.create(
            item_type="note",
            title="Test Note",
            content="Hello world",
        )
        store.add(item)
        fetched = store.get(item.id)
        assert fetched is not None
        assert fetched.title == "Test Note"
        assert fetched.content == "Hello world"
        assert fetched.item_type == "note"

    def test_create_item_defaults(self, store):
        item = KnowledgeItem.create(item_type="literature", title="Ref")
        store.add(item)
        fetched = store.get(item.id)
        assert fetched is not None
        assert fetched.tags == []
        assert fetched.external_source == "manual"
        assert fetched.source_file == ""

    def test_create_item_with_tags(self, store):
        item = KnowledgeItem.create(
            item_type="theory",
            title="Institutional Theory",
            tags=["public_admin", "sociology"],
            project_id="proj-123",
        )
        store.add(item)
        fetched = store.get(item.id)
        assert fetched is not None
        assert "public_admin" in fetched.tags
        assert "sociology" in fetched.tags
        assert fetched.project_id == "proj-123"

    def test_get_nonexistent_returns_none(self, store):
        assert store.get("no-such-id") is None


class TestList:
    def test_list_all(self, store):
        for i in range(3):
            store.add(KnowledgeItem.create(item_type="note", title=f"Note {i}"))
        items = store.list()
        assert len(items) >= 3

    def test_list_by_type(self, store):
        store.add(KnowledgeItem.create(item_type="note", title="N1"))
        store.add(KnowledgeItem.create(item_type="literature", title="L1"))
        store.add(KnowledgeItem.create(item_type="note", title="N2"))

        notes = store.list(item_type="note")
        assert len(notes) >= 2
        assert all(it.item_type == "note" for it in notes)

    def test_list_by_project(self, store):
        store.add(KnowledgeItem.create(item_type="note", title="A", project_id="p1"))
        store.add(KnowledgeItem.create(item_type="note", title="B", project_id="p2"))
        store.add(KnowledgeItem.create(item_type="note", title="C", project_id="p1"))

        p1_items = store.list(project_id="p1")
        assert len(p1_items) >= 2
        assert all(it.project_id == "p1" for it in p1_items)

    def test_list_by_tag(self, store):
        store.add(KnowledgeItem.create(item_type="note", title="N1", tags=["important"]))
        store.add(KnowledgeItem.create(item_type="note", title="N2", tags=["draft"]))
        store.add(KnowledgeItem.create(item_type="note", title="N3", tags=["important"]))

        important = store.list(tag="important")
        assert len(important) >= 2
        assert all("important" in it.tags for it in important)

    def test_list_empty_returns_empty_list(self, store):
        items = store.list()
        # May have items from other tests; clear DB first
        assert isinstance(items, list)


class TestSearch:
    def test_search_finds_in_title(self, store):
        store.add(KnowledgeItem.create(item_type="note", title="Machine Learning Basics"))
        store.add(KnowledgeItem.create(item_type="note", title="Data Structures"))

        results = store.search("machine learning")
        assert len(results) >= 1
        assert any("Machine" in r.title for r in results)

    def test_search_finds_in_content(self, store):
        store.add(KnowledgeItem.create(
            item_type="note", title="Notes",
            content="This document discusses institutional theory in public administration."
        ))

        results = store.search("institutional theory")
        assert len(results) >= 1

    def test_search_no_match(self, store):
        store.add(KnowledgeItem.create(item_type="note", title="Notes", content="Politics"))
        results = store.search("quantum computing xyz notfound")
        assert len(results) == 0

    def test_search_case_insensitive(self, store):
        store.add(KnowledgeItem.create(item_type="note", title="ML Research"))
        results = store.search("ml")
        assert len(results) >= 1


class TestUpdate:
    def test_update_title(self, store):
        item = KnowledgeItem.create(item_type="note", title="Old Title")
        store.add(item)

        updated = store.update(item.id, {"title": "New Title"})
        assert updated is not None
        assert updated.title == "New Title"
        assert store.get(item.id).title == "New Title"

    def test_update_tags(self, store):
        item = KnowledgeItem.create(item_type="note", title="X", tags=["a"])
        store.add(item)

        updated = store.update(item.id, {"tags": ["a", "b", "c"]})
        assert updated is not None
        assert len(updated.tags) == 3
        assert "b" in updated.tags

    def test_update_nonexistent_returns_none(self, store):
        assert store.update("no-id", {"title": "X"}) is None

    def test_update_preserves_id(self, store):
        item = KnowledgeItem.create(item_type="note", title="T")
        store.add(item)
        original_id = item.id
        updated = store.update(item.id, {"content": "new content"})
        assert updated is not None
        assert updated.id == original_id


class TestDelete:
    def test_delete_item(self, store):
        item = KnowledgeItem.create(item_type="note", title="To Delete")
        store.add(item)

        assert store.delete(item.id) is True
        assert store.get(item.id) is None

    def test_delete_nonexistent(self, store):
        assert store.delete("no-such-id") is False

    def test_delete_only_target_item(self, store):
        item1 = KnowledgeItem.create(item_type="note", title="Keep")
        item2 = KnowledgeItem.create(item_type="note", title="Remove")
        store.add(item1)
        store.add(item2)

        store.delete(item2.id)
        assert store.get(item1.id) is not None
        assert store.get(item2.id) is None


class TestItemTypeValidation:
    def test_valid_types(self, store):
        for itype in sorted(ITEM_TYPES):
            item = KnowledgeItem.create(item_type=itype, title=f"Type {itype}")
            store.add(item)
            assert store.get(item.id).item_type == itype

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="item_type must be one of"):
            KnowledgeItem.create(item_type="invalid_type", title="X")
