<!--
ThesisX Final Product Documentation Pack
Generated for agent handoff and development execution
Date: 2026-05-03
Scope: Final product blueprint, PRD, technical roadmap, frontend-interface mapping, API contracts, and agent execution rules.
-->


# Agent Execution Rules

## 1. Global Hard Rules

The agent must obey these rules:

1. Do not continue SVG visual polishing.
2. Do not call Runtime-only success “final product.”
3. Do not break Main Editor.
4. Do not break AgentTeamDialog.
5. Do not remove Mock mode.
6. Do not delete `~/.wenbiao/output/`.
7. Do not modify external Agent Team repositories.
8. Do not send real API requests without explicit user confirmation.
9. Do not pretend dry-run is Real.
10. Do not pretend preview pages are real.
11. Do not store API keys in project content.
12. Do not skip tests.

## 2. Before Every Implementation

Run:

```bash
cd /Volumes/E/ThesisX
git status --short
git diff --stat
.venv/bin/python -m pytest tests/ -x -q --override-ini="addopts="
```

If tests fail:
- Stop.
- Report failure.
- Do not start new feature implementation.

## 3. Plan Before Code

For every Vision, output:

```text
1. Target Vision
2. Scope
3. Files to read
4. Files allowed to modify
5. Files forbidden to modify
6. Implementation steps
7. Tests
8. Stop conditions
```

## 4. Implementation Style

Prefer:
- Small modules.
- Unit tests first or alongside.
- Local-only default.
- Typed dataclasses.
- Clear error codes.
- Atomic writes.
- No hidden network calls.
- No UI direct SQL.
- No provider logic in UI.

## 5. Testing Rules

### 5.1 Required

After any code change:

```bash
.venv/bin/python -m pytest tests/ -x -q --override-ini="addopts="
```

### 5.2 Targeted Tests

Run relevant tests first.

Examples:

```bash
pytest tests/unit/test_knowledge_store.py -q
pytest tests/unit/test_run_diagnostics.py -q
pytest tests/unit/test_provider_detector.py -q
```

## 6. Data Safety Rules

### 6.1 Never Delete Without Confirmation

Forbidden without user confirmation:
- rm
- unlink
- shutil.rmtree
- deleting DB
- deleting output
- deleting runs
- deleting imported files
- overwriting external vault files

### 6.2 Migration Rules

When migrating:
- Read old data.
- Create new data.
- Never modify old data.
- Write migration report.
- Make operation idempotent.

## 7. API Safety Rules

Never call real API unless:
1. User explicitly confirms.
2. API key source is known.
3. base_url is known.
4. model is known.
5. budget is known.
6. prompt content is shown or summarized.
7. task is one-shot, not looped.

## 8. UI Rules

Allowed:
- Functional UI needed for real feature.
- Clear empty states.
- Clear error states.
- Read-only views.

Forbidden:
- SVG pixel polishing.
- Decorative redesign.
- Misleading active buttons.
- Fake toggles.
- Fake success.

## 9. Provider Rules

Provider states must be explicit:

```text
not_configured
detected
dry_run_supported
real_supported
error
```

Do not merge them.

## 10. Mock / Dry-run / Real Labels

The agent must maintain strict terminology:

| Term | Meaning |
|---|---|
| Mock | Internal fake output, no external agent/API. |
| Dry-run | Tests contract shape, no real API. |
| Real | Actually calls configured provider/API/agent. |

## 11. Documentation Rules

When implementing a major module, update or create:
- PRD document if product behavior changes.
- API document if service interface changes.
- Technical document if architecture changes.
- User guide if user-facing behavior changes.

## 12. Completion Report

Every run must output:

```text
1. Summary
2. Modified files
3. New files
4. Tests run
5. Result
6. What is real
7. What is preview
8. Remaining gaps
9. Next step
```

## 13. Stop Conditions

Stop immediately if:
- Tests fail.
- Data deletion needed.
- Real API needed.
- External repo modification needed.
- User privacy risk appears.
- Main Editor breakage risk appears.
- Scope drifts into UI polishing.
- New dependency is heavy or uncertain.

## 14. Agent Self-Review Checklist

Before final answer, ask:

```text
Did I call mock real?
Did I modify forbidden files?
Did I run tests?
Did I preserve old data?
Did I create misleading UI?
Did I update docs?
Did I produce a useful report?
```
