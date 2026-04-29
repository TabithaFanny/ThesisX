"""PaperPipelineRunner — thin async protocol for paper generation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from .events import PaperEvent
from .models import PaperRequest


@runtime_checkable
class PaperPipelineRunner(Protocol):
    """Async pipeline runner that yields PaperEvent objects.

    Implementations must:
    - Accept a PaperRequest in run()
    - Yield PaperEvent objects as the pipeline progresses
    - Support cancellation via cancel()
    """

    async def run(self, request: PaperRequest) -> AsyncIterator[PaperEvent]:
        """Execute the pipeline, yielding events as they occur."""
        ...  # pragma: no cover

    def cancel(self) -> None:
        """Request cancellation of the running pipeline."""
        ...  # pragma: no cover
