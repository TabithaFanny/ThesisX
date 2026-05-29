from __future__ import annotations

from app.core.literature.models import Reference
from app.core.literature.structuring import LiteratureStructuringService


def test_build_items_from_reference_with_abstract():
    ref = Reference.new(
        title="Interactive Systems for Research Workflows",
        authors=["Alice Smith", "Bob Lee"],
        year="2025",
        journal="CHI",
        doi="10.1000/test",
        abstract=(
            "This paper studies interactive systems for research workflows. "
            "It introduces a mixed-initiative method for structuring literature notes. "
            "Results show improved traceability and synthesis speed."
        ),
        zotero_key="ABCD1234",
    )

    svc = LiteratureStructuringService()
    items = svc.build_items(ref, project_id="proj-1")

    assert len(items) == 5
    assert {item.item_type for item in items} == {"note", "theory", "evidence"}
    assert all(item.project_id == "proj-1" for item in items)
    assert any("Overview" in item.title for item in items)
    assert any("Evidence Snippet" in item.title for item in items)
    evidence_item = next(item for item in items if item.item_type == "evidence")
    assert "zotero_key=ABCD1234" in evidence_item.content


def test_build_items_handles_missing_abstract():
    ref = Reference.new(
        title="Untitled Imported Paper",
        authors=[],
        year="",
        abstract=None,
    )

    svc = LiteratureStructuringService()
    items = svc.build_items(ref)

    assert len(items) == 5
    assert any("lacks an abstract" in item.content for item in items if "Background" in item.title)
