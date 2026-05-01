#!/usr/bin/env python3
"""ThesisX CLI — unified local diagnostics and mock execution.

Usage:
    .venv/bin/python cli/thesisx.py diagnose runs
    .venv/bin/python cli/thesisx.py diagnose latest
    .venv/bin/python cli/thesisx.py verify contracts
    .venv/bin/python cli/thesisx.py verify providers
    .venv/bin/python cli/thesisx.py health
    .venv/bin/python cli/thesisx.py run mock <topic>
    .venv/bin/python cli/thesisx.py migrate

All commands are read-only or mock-only. No real API calls. No UI.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

DEFAULT_BASE_DIR = Path.home() / ".wenbiao"
OUTPUT_DIR_NAME = "_diagnostics"


# ── Shared helpers ────────────────────────────────────────────────────────────


def _banner(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _load_deps():
    """Lazy-import shared modules (no side effects on import failure)."""
    from app.core.pipeline.run_diagnostics import RunDiagnostics
    from app.core.pipeline.run_history import RunHistoryReader
    from app.core.pipeline.agent_team_compat_adapter import AgentTeamCompatAdapter
    from app.core.providers.detector import (
        discover_local_clis,
        detect_remote_api_config,
        detect_agent_team_paths,
        generate_provider_health_report,
    )
    return {
        "RunDiagnostics": RunDiagnostics,
        "RunHistoryReader": RunHistoryReader,
        "AgentTeamCompatAdapter": AgentTeamCompatAdapter,
        "discover_local_clis": discover_local_clis,
        "detect_remote_api_config": detect_remote_api_config,
        "detect_agent_team_paths": detect_agent_team_paths,
        "generate_provider_health_report": generate_provider_health_report,
    }


# ── diagnose runs ─────────────────────────────────────────────────────────────


def _cmd_diagnose_runs(base_dir: Path) -> None:
    deps = _load_deps()
    reader = deps["RunHistoryReader"](base_dir=base_dir)
    diagnostics = deps["RunDiagnostics"](reader=reader)
    sessions = reader.list_runs()
    if not sessions:
        print("No runs found.")
        return
    print(f"Found {len(sessions)} run(s):\n")
    for s in sessions:
        topic = (s.topic or "?")[:40]
        mode = s.run_mode or "?"
        paper = "Y" if s.has_paper else "N"
        events = "Y" if s.has_events else "N"
        print(f"  {s.session_id[:14]:<16} {topic:<42} {s.status:<12} {mode:<6} paper={paper} events={events}")


def _cmd_diagnose_latest(base_dir: Path, output_dir: Path, limit: int) -> None:
    deps = _load_deps()
    diagnostics = deps["RunDiagnostics"](base_dir=base_dir)
    markdown = diagnostics.render_latest_markdown(limit=limit)
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "latest.md"
    out.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"\n  Written to: {out}")


# ── verify ────────────────────────────────────────────────────────────────────


def _cmd_verify_contracts() -> None:
    deps = _load_deps()
    adapter = deps["AgentTeamCompatAdapter"]
    candidates = [
        ("candidate-1", "/Volumes/E/agent team 2/academic-agent-team/"),
        ("candidate-2", "/Volumes/E/agent team 2/academic-agent-team-work/"),
        ("candidate-3", "/Users/magnus/.codex_work/agent-team-2/academic-agent-team/"),
        ("candidate-4", "/Volumes/E/agent team 2/wt-1488343317639991428/"),
    ]
    print()
    for name, path in candidates:
        check = adapter.validate_agent_team_contract(path)
        icon = "✓" if check.supported else "✗"
        mode = {
            "tui_runner": "real",
            "pipeline_v2": "dry-run",
            "pipeline_function": "dry-run",
            "unsupported": "broken",
        }.get(check.contract_type, "?")
        print(f"  [{icon}] {name:<20} {check.contract_type:<20} mode={mode}")
        if not check.supported:
            print(f"       → {check.reason}")


def _cmd_verify_providers() -> None:
    deps = _load_deps()
    clis = deps["discover_local_clis"]()
    apis = deps["detect_remote_api_config"]()
    teams = deps["detect_agent_team_paths"]()

    print("\n  ── Local CLIs ──")
    for p in clis:
        icon = "✓" if p.available else "✗"
        path = p.executable_path if p.available else "not found"
        ver = f", v{p.version}" if p.version else ""
        print(f"  [{icon}] {p.display_name:<20} {path}{ver}")

    print("\n  ── Remote APIs ──")
    for p in apis:
        key = "key ✓" if p.api_key_configured else "key ✗"
        print(f"  [{p.health_status[0]:>1}] {p.display_name:<20} {p.model:<20} {key}  {p.base_url}")

    print("\n  ── Agent Teams ──")
    for p in teams:
        mode_icon = {"real": "✓", "dry-run": "~", "broken": "✗"}.get(p.execution_mode, "?")
        print(f"  [{mode_icon}] {p.display_name}")
        print(f"       contract={p.contract_type}  mode={p.execution_mode}  path={p.root_path}")


# ── health ────────────────────────────────────────────────────────────────────


def _cmd_health(output_dir: Path) -> None:
    deps = _load_deps()
    report = deps["generate_provider_health_report"]()

    print()
    print(f"  Overall: {'✓ OK' if report.overall_ok else '✗ Issues found'}")
    print()

    for title, items in [
        ("Local CLIs", report.local_clis),
        ("Remote APIs", report.remote_apis),
        ("Agent Teams", report.agent_teams),
    ]:
        print(f"  {title}:")
        for h in items:
            icon = "✓" if h.ok else "✗"
            print(f"    [{icon}] {h.provider_name}")
            for issue in h.issues:
                print(f"        ❌ {issue}")
            for warn in h.warnings:
                print(f"        ⚠ {warn}")
            if h.dry_run_only:
                print(f"        ℹ dry-run only")
        print()

    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / "provider_health.md"
    json_path = output_dir / "provider_health.json"
    _write_health_files(report, md_path, json_path)
    print(f"  Reports: {md_path}\n           {json_path}")


def _write_health_files(report, md_path: Path, json_path: Path) -> None:
    lines = ["# ThesisX Provider Health Report", "",
             f"- Overall: {'OK' if report.overall_ok else 'Issues'}", ""]
    for title, items in [("Local CLI", report.local_clis), ("Remote API", report.remote_apis),
                          ("Agent Team", report.agent_teams)]:
        lines.append(f"## {title}")
        for h in items:
            icon = "✓" if h.ok else "✗"
            lines.append(f"- [{icon}] {h.provider_name}")
            for issue in h.issues:
                lines.append(f"  - ❌ {issue}")
            for warn in h.warnings:
                lines.append(f"  - ⚠ {warn}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "timestamp": report.timestamp, "overall_ok": report.overall_ok,
        "local_clis": [{"name": h.provider_name, "ok": h.ok, "issues": h.issues} for h in report.local_clis],
        "remote_apis": [{"name": h.provider_name, "ok": h.ok, "issues": h.issues} for h in report.remote_apis],
        "agent_teams": [{"name": h.provider_name, "ok": h.ok, "issues": h.issues,
                         "dry_run_only": h.dry_run_only} for h in report.agent_teams],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ── run mock ──────────────────────────────────────────────────────────────────


def _cmd_run_mock(topic: str, journal: str, base_dir: Path) -> None:
    from app.core.pipeline.agent_team_runner import AgentTeamRunner
    from app.core.pipeline.models import PaperRequest

    _banner(f"Mock Run: {topic[:60]}")
    request = PaperRequest(
        topic=topic,
        journal=journal,
        run_mode="mock",
        budget_cap_cny=10.0,
        base_dir=base_dir,
    )

    async def _run():
        runner = AgentTeamRunner()
        count = 0
        async for evt in runner.run(request):
            count += 1
            stage = evt.stage or ""
            msg = evt.message[:80] if evt.message else ""
            prefix = {"state": "◆", "token": "·", "cost": "$", "message": " ",
                      "completion": "✓", "error": "✗", "artifact": "📄"}.get(evt.type, "?")
            print(f"  {prefix} [{evt.type:<10}] {stage:<22} {msg}")
        return count

    count = asyncio.run(_run())
    print(f"\n  Done: {count} events")

    # Show where the session was written
    runs_dir = base_dir / "runs"
    if runs_dir.exists():
        sessions = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if sessions:
            sid = sessions[0].name
            paper = sessions[0] / "output" / "paper.md"
            print(f"  Session: {sid}")
            if paper.exists():
                print(f"  Paper:   {paper} ({paper.stat().st_size}B)")


# ── migrate ───────────────────────────────────────────────────────────────────


def _cmd_migrate(base_dir: Path, dry_run: bool) -> None:
    output_root = base_dir / "output"
    runs_root = base_dir / "runs"
    if not output_root.exists():
        print(f"No legacy output/ at {output_root}")
        return
    session_dirs = sorted([p for p in output_root.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not session_dirs:
        print("No sessions in output/")
        return
    mode = "DRY RUN" if dry_run else "MIGRATE"
    print(f"\n  {mode}: {len(session_dirs)} sessions\n")
    for src in session_dirs:
        sid = src.name
        dest = runs_root / sid
        if dest.exists() and any(dest.iterdir()):
            print(f"  SKIP {sid} (already exists)")
            continue
        has_paper = (src / "paper.md").exists()
        has_outline = (src / "outline.json").exists()
        action = "would create" if dry_run else "migrated"
        paper_str = " +paper.md" if has_paper else ""
        outline_str = " +outline" if has_outline else ""
        print(f"  {action} {sid}{paper_str}{outline_str}")
    if dry_run:
        print("\n  (dry run — no files created)")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="ThesisX CLI — local diagnostics and mock execution")
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # diagnose
    diag = sub.add_parser("diagnose", help="Run diagnostics")
    diag_sub = diag.add_subparsers(dest="diag_cmd")
    diag_runs = diag_sub.add_parser("runs", help="List all runs")
    diag_runs.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    diag_latest = diag_sub.add_parser("latest", help="Latest N runs aggregated")
    diag_latest.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    diag_latest.add_argument("--output-dir", default=None)
    diag_latest.add_argument("--limit", type=int, default=5)

    # verify
    verify = sub.add_parser("verify", help="Verify configuration")
    verify_sub = verify.add_subparsers(dest="verify_cmd")
    verify_sub.add_parser("contracts", help="Verify Agent Team contracts")
    verify_sub.add_parser("providers", help="Verify all providers")

    # health
    health = sub.add_parser("health", help="Full health check")
    health.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    health.add_argument("--output-dir", default=None)

    # run
    run = sub.add_parser("run", help="Run a pipeline (mock only)")
    run_sub = run.add_subparsers(dest="run_cmd")
    run_mock = run_sub.add_parser("mock", help="Run a mock pipeline")
    run_mock.add_argument("topic", help="Research topic")
    run_mock.add_argument("--journal", default="中文核心")
    run_mock.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))

    # migrate
    migrate = sub.add_parser("migrate", help="Migrate legacy output/ to runs/")
    migrate.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    migrate.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    base_dir = Path(getattr(args, "base_dir", str(DEFAULT_BASE_DIR))).expanduser()
    output_dir = Path(getattr(args, "output_dir", None) or (base_dir / "runs" / OUTPUT_DIR_NAME))

    _banner("ThesisX CLI")

    if args.command == "diagnose":
        if args.diag_cmd == "runs":
            _cmd_diagnose_runs(base_dir)
        elif args.diag_cmd == "latest":
            _cmd_diagnose_latest(base_dir, output_dir, args.limit)
        else:
            diag.print_help()

    elif args.command == "verify":
        if args.verify_cmd == "contracts":
            _cmd_verify_contracts()
        elif args.verify_cmd == "providers":
            _cmd_verify_providers()
        else:
            verify.print_help()

    elif args.command == "health":
        _cmd_health(output_dir)

    elif args.command == "run":
        if args.run_cmd == "mock":
            _cmd_run_mock(args.topic, args.journal, base_dir)
        else:
            run.print_help()

    elif args.command == "migrate":
        _cmd_migrate(base_dir, args.dry_run)


if __name__ == "__main__":
    main()
