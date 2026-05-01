#!/usr/bin/env python3
"""Migrate old ~/.wenbiao/output/ sessions to new ~/.wenbiao/runs/ layout.

Read-only on old output/ — never modifies or deletes old files.
Creates new runs/<session_id>/ directories with canonical structure.

Usage:
    .venv/bin/python scripts/migrate_sessions.py           # migrate all
    .venv/bin/python scripts/migrate_sessions.py --dry-run # show plan only
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

DEFAULT_BASE_DIR = Path.home() / ".wenbiao"

CONTEXT_PAPER_REQUEST_TMPL = """# Paper Request

- Session ID: `{session_id}`
- Topic: {topic}
- Journal: {journal}
- Generation Type: paper_draft
"""

CONTEXT_RUNTIME_INSTRUCTIONS = """# Runtime Instructions

- This session was migrated from the legacy `output/` directory.
- 当前的运行目录采用 ThesisX 本地 run 契约。
- 本轮目标是论文初稿生成与静态质量检查。
- 本地历史需保留 request / context / logs / output / artifacts。
- 当前阶段不得把 Mock 页面、Mock 链路伪装成真实外部 Agent Team 已接通。
"""

CONTEXT_USER_CONSTRAINTS_TMPL = """# User Constraints

- Run Mode: `{run_mode}`
- Runner Kind: `sequential`
- Auto Polish: `false`
- Budget Cap (CNY): `10.0`
- Agent Team Path: `{agent_team_path}`
- Model: `未指定`

- 当前阶段不接真实 API，不接 CLI，不接 Skill Registry，不接 RAG / Zotero / Git。
"""

CONTEXT_SELECTED_SKILLS = """# Selected Skills

- 当前未接入真实 Skill Registry。
- 本次运行未选择可执行技能列表。
- 该文件为后续 Runtime / CLI / Skill 接通预留。
"""


def _read_json(path: Path) -> dict:
    """Read a JSON file, returning empty dict on any error."""
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _read_text(path: Path) -> str:
    try:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def migrate_session(session_id: str, src_dir: Path, runs_root: Path, dry_run: bool = False) -> dict:
    """Migrate one old session to the new runs/ layout.

    Returns a status dict with 'action', 'session_id', 'files_copied', 'warnings'.
    """
    result = {"session_id": session_id, "files_created": [], "warnings": []}

    request = _read_json(src_dir / "request.json")
    metadata = _read_json(src_dir / "metadata.json")
    outline = _read_json(src_dir / "outline.json")
    paper_text = _read_text(src_dir / "paper.md")

    has_paper = bool(paper_text)
    has_outline = bool(outline)
    has_metadata = bool(metadata)
    has_request = bool(request)

    if not has_request and not has_outline:
        result["warnings"].append("No request.json or outline.json — minimal stub only")

    # Derive metadata fields
    topic = str(request.get("topic") or metadata.get("topic") or "?")
    journal = str(request.get("journal") or metadata.get("journal") or "?")
    run_mode = str(request.get("run_mode") or metadata.get("run_mode") or "mock")
    agent_team_path = str(request.get("agent_team_path") or "未提供")

    dest_dir = runs_root / session_id

    if dry_run:
        files_planned = [
            "request.json", "metadata.json",
            "output/outline.json" if has_outline else None,
            "output/paper.md" if has_paper else None,
            "context/paper_request.md",
            "context/runtime_instructions.md",
            "context/user_constraints.md",
            "context/selected_skills.md",
        ]
        result["files_created"] = [f for f in files_planned if f]
        result["action"] = "would_migrate"
        return result

    # 1. request.json — copy as-is if possible, else build minimal stub
    if has_request:
        _write_json(dest_dir / "request.json", request)
    else:
        minimal_request = {
            "topic": topic,
            "journal": journal,
            "run_mode": run_mode,
            "generation_type": "paper_draft",
            "runner_kind": "sequential",
            "auto_polish": False,
            "budget_cap_cny": 10.0,
            "agent_team_path": agent_team_path,
            "session_id": session_id,
        }
        _write_json(dest_dir / "request.json", minimal_request)
        result["warnings"].append("request.json was minimal stub (no original)")
    result["files_created"].append("request.json")

    # 2. metadata.json — copy if exists, else generate from available data
    if has_metadata:
        _write_json(dest_dir / "metadata.json", metadata)
    else:
        now = datetime.now().isoformat()
        generated_metadata = {
            "session_id": session_id,
            "run_dir": str(dest_dir),
            "legacy_output_dir": str(src_dir),
            "status": "completed" if has_paper else ("partial" if has_outline else "unknown"),
            "created_at": now,
            "updated_at": now,
            "migrated_from": str(src_dir),
            "migrated_at": now,
            "run_mode": run_mode,
            "topic": topic,
            "journal": journal,
            "output_files": {},
            "event_count": 0,
            "message_count": 0,
            "has_errors": False,
            "note": "Metadata auto-generated during migration from legacy output/ directory.",
        }
        if has_paper:
            generated_metadata["output_files"]["paper_md"] = str(dest_dir / "output" / "paper.md")
        if has_outline:
            generated_metadata["output_files"]["outline_json"] = str(dest_dir / "output" / "outline.json")
        _write_json(dest_dir / "metadata.json", generated_metadata)
        result["warnings"].append("metadata.json was auto-generated (no original)")
    result["files_created"].append("metadata.json")

    # 3. output/outline.json
    if has_outline:
        _write_json(dest_dir / "output" / "outline.json", outline)
        result["files_created"].append("output/outline.json")

    # 4. output/paper.md
    if has_paper:
        _write_text(dest_dir / "output" / "paper.md", paper_text)
        result["files_created"].append("output/paper.md")

    # 5. context/*.md
    _write_text(dest_dir / "context" / "paper_request.md",
                CONTEXT_PAPER_REQUEST_TMPL.format(session_id=session_id, topic=topic, journal=journal))
    _write_text(dest_dir / "context" / "runtime_instructions.md", CONTEXT_RUNTIME_INSTRUCTIONS)
    _write_text(dest_dir / "context" / "user_constraints.md",
                CONTEXT_USER_CONSTRAINTS_TMPL.format(run_mode=run_mode, agent_team_path=agent_team_path))
    _write_text(dest_dir / "context" / "selected_skills.md", CONTEXT_SELECTED_SKILLS)
    result["files_created"].extend([
        "context/paper_request.md",
        "context/runtime_instructions.md",
        "context/user_constraints.md",
        "context/selected_skills.md",
    ])

    # 6. artifacts/ empty dirs
    (dest_dir / "artifacts" / "imported_files").mkdir(parents=True, exist_ok=True)
    (dest_dir / "artifacts" / "generated").mkdir(parents=True, exist_ok=True)
    result["files_created"].append("artifacts/ (empty dirs)")

    result["action"] = "migrated"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy output/ → runs/")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR),
                        help=f"Base directory (default: {DEFAULT_BASE_DIR})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show migration plan without creating files")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser()
    output_root = base_dir / "output"
    runs_root = base_dir / "runs"

    if not output_root.exists():
        print(f"Legacy output/ not found at {output_root}")
        return

    session_dirs = sorted(
        [p for p in output_root.iterdir() if p.is_dir()],
        key=lambda p: p.name,
    )

    if not session_dirs:
        print("No session directories found in output/")
        return

    mode = "DRY RUN" if args.dry_run else "MIGRATE"
    print(f"\n{'='*60}")
    print(f"  Legacy Session Migration — {mode}")
    print(f"{'='*60}")
    print(f"  Source:      {output_root}")
    print(f"  Destination: {runs_root}")
    print(f"  Sessions:    {len(session_dirs)}")
    print()

    created = skipped = warned = 0
    for src_dir in session_dirs:
        sid = src_dir.name
        dest_dir = runs_root / sid

        if dest_dir.exists() and any(dest_dir.iterdir()):
            print(f"  SKIP  {sid} — runs/ dir already exists with content")
            skipped += 1
            continue

        result = migrate_session(sid, src_dir, runs_root, dry_run=args.dry_run)
        status = "PLAN " if args.dry_run else "OK   "
        print(f"  {status} {sid}  ({len(result['files_created'])} files)"
              f"{'  paper.md' if any('paper.md' in f for f in result['files_created']) else ''}")
        for w in result.get("warnings", []):
            print(f"         ⚠ {w}")
            warned += 1
        created += 1

    print(f"\n  Summary: {created} migrated, {skipped} skipped, {warned} warnings")
    if args.dry_run:
        print("  (Dry run — no files were created)")
    print()


if __name__ == "__main__":
    main()
