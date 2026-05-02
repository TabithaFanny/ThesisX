"""Knowledge Base module — local file import, parsing, and chunking."""

from __future__ import annotations

from .models import KnowledgeSource, KnowledgeChunk
from .service import KnowledgeService

__all__ = ["KnowledgeSource", "KnowledgeChunk", "KnowledgeService"]
