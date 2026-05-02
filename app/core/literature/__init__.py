"""Literature management — import, parse, and manage academic references."""

from .models import Reference
from .service import LiteratureService

__all__ = ["Reference", "LiteratureService"]
