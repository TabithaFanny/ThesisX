"""SessionExporter — archive a run session to ZIP (Vision 3.9)."""

from __future__ import annotations

import zipfile
from pathlib import Path
from datetime import datetime, timezone


class SessionExporter:
    """Pack a session's run directory into a ZIP archive."""

    SESSIONS_DIR = Path.home() / ".wenbiao" / "runs"

    @classmethod
    def archive(cls, session_id: str, output_path: Path | None = None) -> Path:
        """Archive run directory to ZIP. Returns the ZIP path."""
        session_dir = cls.SESSIONS_DIR / session_id
        if not session_dir.is_dir():
            raise FileNotFoundError(f"Session directory not found: {session_dir}")

        if output_path is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_path = Path.home() / "Desktop" / f"thesisx_session_{session_id}_{ts}.zip"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(str(output_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(session_dir.rglob("*")):
                if f.is_file():
                    arcname = str(f.relative_to(session_dir))
                    zf.write(f, arcname)

        return output_path

    @classmethod
    def list_sessions(cls) -> list[str]:
        """List available session IDs."""
        if not cls.SESSIONS_DIR.is_dir():
            return []
        return sorted(
            d.name for d in cls.SESSIONS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        )
