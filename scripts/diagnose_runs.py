#!/usr/bin/env python3
"""ThesisX Runtime Diagnostics CLI — read-only scanner for local runs.

Usage:
    .venv/bin/python scripts/diagnose_runs.py              # full scan + export
    .venv/bin/python scripts/diagnose_runs.py --latest 10  # last N runs only
    .venv/bin/python scripts/diagnose_runs.py --contracts  # contract check only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `app` imports work
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.core.pipeline.run_diagnostics import RunDiagnostics  # noqa: E402
from app.core.pipeline.run_history import RunHistoryReader  # noqa: E402
from app.core.pipeline.agent_team_compat_adapter import AgentTeamCompatAdapter  # noqa: E402
from app.core.providers.detector import (  # noqa: E402
    discover_local_clis,
    detect_remote_api_config,
    detect_agent_team_paths,
    generate_provider_health_report,
)
from app.core.providers.models import (  # noqa: E402
    LocalCLIProvider,
    RemoteAPIProvider,
    AgentTeamProvider,
    ProviderHealthStatus,
    ProviderKind,
)

DEFAULT_BASE_DIR = Path.home() / ".wenbiao"
OUTPUT_DIR_NAME = "_diagnostics"

AGENT_TEAM_CANDIDATES = [
    "/Volumes/E/agent team 2/academic-agent-team/",
    "/Volumes/E/agent team 2/academic-agent-team-work/",
    "/Users/magnus/.codex_work/agent-team-2/academic-agent-team/",
    "/Volumes/E/agent team 2/wt-1488343317639991428/",
]


def _banner(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def diagnose_all(base_dir: Path, output_dir: Path) -> None:
    """Scan all sessions and export individual + aggregate reports."""
    reader = RunHistoryReader(base_dir=base_dir)
    diagnostics = RunDiagnostics(reader=reader)

    sessions = reader.list_runs()
    if not sessions:
        print("No sessions found in", str(base_dir))
        return

    print(f"Found {len(sessions)} session(s)")
    output_dir.mkdir(parents=True, exist_ok=True)

    ok = warning = broken = 0
    for summary in sessions:
        report = diagnostics.diagnose_run(summary.session_id)
        dest = output_dir / f"{summary.session_id}.md"
        diagnostics.export_report(summary.session_id, dest, format="markdown")
        dest_json = output_dir / f"{summary.session_id}.json"
        diagnostics.export_report(summary.session_id, dest_json, format="json")
        if report.health_status == "ok":
            ok += 1
        elif report.health_status == "warning":
            warning += 1
        else:
            broken += 1

    # Aggregate report
    latest_md = output_dir / "latest.md"
    latest_json = output_dir / "latest.json"
    diagnostics.export_latest(latest_md, limit=50, format="markdown")
    diagnostics.export_latest(latest_json, limit=50, format="json")

    print()
    print(f"  Health summary:  OK={ok}  WARNING={warning}  BROKEN={broken}")
    print(f"  Reports written to: {output_dir}/")
    _print_session_table(sessions)


def _print_session_table(sessions) -> None:
    """Print a compact table of all sessions."""
    print()
    header = f"  {'SESSION ID':<16} {'TOPIC':<24} {'STATUS':<12} {'MODE':<8} {'PAPER':<6} {'EVENTS':<7}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for s in sessions:
        topic = (s.topic or "?")[:22]
        print(
            f"  {s.session_id:<16} {topic:<24} {s.status:<12} "
            f"{s.run_mode or '?':<8} {'Y' if s.has_paper else 'N':<6} "
            f"{'Y' if s.has_events else 'N':<7}"
        )


def verify_contracts() -> None:
    """Dry-run contract detection on candidate Agent Team paths."""
    print()
    header = f"  {'PATH':<55} {'CONTRACT':<20} {'SUPPORTED':<10}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for raw_path in AGENT_TEAM_CANDIDATES:
        result = AgentTeamCompatAdapter.validate_agent_team_contract(raw_path)
        label = str(raw_path)[:53]
        print(
            f"  {label:<55} {result.contract_type:<20} "
            f"{'YES' if result.supported else 'NO':<10}"
        )
        if result.reason:
            print(f"    → {result.reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ThesisX Runtime Diagnostics")
    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help=f"Base directory (default: {DEFAULT_BASE_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for reports (default: <base_dir>/runs/_diagnostics/)",
    )
    parser.add_argument(
        "--latest",
        type=int,
        default=0,
        help="Show only the N most recent runs",
    )
    parser.add_argument(
        "--contracts",
        action="store_true",
        help="Only verify external Agent Team contracts",
    )
    # Provider detection commands
    parser.add_argument(
        "--providers",
        action="store_true",
        help="Scan all providers (local CLI + remote API + agent team)",
    )
    parser.add_argument(
        "--discover-local",
        action="store_true",
        help="Discover local AI CLI tools on PATH",
    )
    parser.add_argument(
        "--check-api",
        action="store_true",
        help="Check remote API provider configuration (no API calls)",
    )
    parser.add_argument(
        "--detect-agent-teams",
        action="store_true",
        help="Detect Agent Team installations at candidate paths",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Generate unified provider health report",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser()
    output_dir = Path(args.output_dir) if args.output_dir else (base_dir / "runs" / OUTPUT_DIR_NAME)

    # ── Provider commands (priority over session scan) ──
    if args.providers or args.discover_local or args.check_api or args.detect_agent_teams or args.health:
        if args.discover_local:
            _banner("Local CLI Discovery")
            _print_local_clis(discover_local_clis())
        if args.check_api:
            _banner("Remote API Configuration")
            _print_remote_apis(detect_remote_api_config())
        if args.detect_agent_teams:
            _banner("Agent Team Detection")
            _print_agent_teams(detect_agent_team_paths())
        if args.providers:
            _banner("All Providers")
            _print_local_clis(discover_local_clis())
            _print_remote_apis(detect_remote_api_config())
            _print_agent_teams(detect_agent_team_paths())
        if args.health:
            _banner("Provider Health Report")
            report = generate_provider_health_report()
            _print_health_report(report)
            output_dir.mkdir(parents=True, exist_ok=True)
            _write_health_markdown(report, output_dir / "provider_health.md")
            import json
            health_json = {
                "timestamp": report.timestamp,
                "overall_ok": report.overall_ok,
                "summary": report.summary,
                "local_clis": [
                    {"name": h.provider_name, "ok": h.ok, "issues": h.issues, "checks": h.checks}
                    for h in report.local_clis
                ],
                "remote_apis": [
                    {"name": h.provider_name, "ok": h.ok, "issues": h.issues, "checks": h.checks}
                    for h in report.remote_apis
                ],
                "agent_teams": [
                    {"name": h.provider_name, "ok": h.ok, "issues": h.issues,
                     "checks": h.checks, "dry_run_only": h.dry_run_only}
                    for h in report.agent_teams
                ],
            }
            (output_dir / "provider_health.json").write_text(
                json.dumps(health_json, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"\n  Health reports: {output_dir}/provider_health.md, provider_health.json")
        _banner("Done")
        print()
        return

    # ── Session scan (default behaviour) ──
    if args.contracts:
        _banner("External Agent Team Contract Detection")
        verify_contracts()
        return

    _banner("Scanning sessions")
    diagnose_all(base_dir, output_dir)

    _banner("External Agent Team Contract Detection")
    verify_contracts()

    _banner("Done")
    print(f"  Base dir:    {base_dir}")
    print(f"  Output dir:  {output_dir}")
    print()


# ── Provider output helpers ──

def _print_local_clis(providers: list[LocalCLIProvider]) -> None:
    print()
    if not providers:
        print("  No local CLIs found.")
        return
    for p in providers:
        status = "✓" if p.available else "✗"
        path_info = p.executable_path if p.available else "not found"
        ver_info = f", v{p.version}" if p.version else ""
        print(f"  [{status}] {p.display_name:<20} {path_info}{ver_info}")
        if not p.available:
            print(f"       install: {p.name} CLI 未在 PATH 中找到")


def _print_remote_apis(providers: list[RemoteAPIProvider]) -> None:
    print()
    if not providers:
        print("  No remote API providers configured.")
        return
    for p in providers:
        key_status = "key ✓" if p.api_key_configured else "key ✗"
        health_icon = {"unknown": "?", "ok": "✓", "unavailable": "✗"}.get(p.health_status, "?")
        print(f"  [{health_icon}] {p.display_name:<20} {p.model:<20} {key_status}  {p.base_url}")
        print(f"       source: {p.api_key_source}, health: {p.health_status}")


def _print_agent_teams(providers: list[AgentTeamProvider]) -> None:
    print()
    if not providers:
        print("  No Agent Team installations found.")
        return
    for p in providers:
        mode_icon = {"real": "✓", "dry-run": "~", "broken": "✗"}.get(p.execution_mode, "?")
        print(f"  [{mode_icon}] {p.display_name}")
        print(f"       path:   {p.root_path}")
        print(f"       contract: {p.contract_type}  mode: {p.execution_mode}  health: {p.health_status}")


def _print_health_report(report) -> None:
    print()
    print(f"  Overall: {'✓ OK' if report.overall_ok else '✗ Issues found'}")
    print()

    def _print_section(title: str, items: list[ProviderHealthStatus]) -> None:
        print(f"  {title}:")
        if not items:
            print("    (none)")
            return
        for h in items:
            icon = "✓" if h.ok else "✗"
            print(f"    [{icon}] {h.provider_name}")
            for issue in h.issues:
                print(f"        ISSUE: {issue}")
            for warn in h.warnings:
                print(f"        WARN:  {warn}")
            if h.dry_run_only:
                print(f"        NOTE:  dry-run only, 不支持真实执行")

    _print_section("Local CLIs", report.local_clis)
    print()
    _print_section("Remote APIs", report.remote_apis)
    print()
    _print_section("Agent Teams", report.agent_teams)
    print()
    if report.summary:
        print(report.summary)


def _write_health_markdown(report, path) -> None:
    lines = [
        "# ThesisX Provider Health Report",
        "",
        f"- Generated: {report.timestamp}",
        f"- Overall: {'✓ OK' if report.overall_ok else '✗ Issues found'}",
        "",
    ]
    for title, items in [
        ("Local CLI Providers", report.local_clis),
        ("Remote API Providers", report.remote_apis),
        ("Agent Team Providers", report.agent_teams),
    ]:
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("(none)")
        for h in items:
            icon = "✓" if h.ok else "✗"
            lines.append(f"- **[{icon}] {h.provider_name}**")
            for issue in h.issues:
                lines.append(f"  - ❌ {issue}")
            for warn in h.warnings:
                lines.append(f"  - ⚠️ {warn}")
            if h.dry_run_only:
                lines.append(f"  - ℹ️ dry-run only")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
