# Agent Gap Analysis

> Last updated: 2026-05-16

## Why This Exists

ThesisX already exposes many AI entry points across web workspaces, but until now
each page assembled its own thin prompt context. That made the system good at
showing AI buttons and weak at preserving task continuity, project memory, and
output discipline.

This document compares ThesisX against strong open-source agent patterns and
records the design moves needed to close the biggest gaps.

## External Reference Points

### LangGraph

Reference: [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)

Useful pattern:
- explicit state carried across node boundaries
- durable execution / resumability
- workflow nodes that consume structured state, not raw ad hoc prompt text

Gap in ThesisX:
- many web actions still inject context as one-off strings
- no single state object spans project -> quality -> writing -> export

### Aider

Reference: [Aider-AI/aider](https://github.com/Aider-AI/aider)

Useful pattern:
- inject only the most relevant context
- keep editing targets explicit
- make outputs operational rather than conversational

Gap in ThesisX:
- pages often pass raw local context without prioritization
- AI results can still be "helpful text" instead of task-ready artifacts

### OpenHands

Reference: [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands)

Useful pattern:
- environment awareness
- durable action traces
- strong separation between planning context and execution context

Gap in ThesisX:
- execution history exists in sessions, but is not yet consistently injected
- context from prior runs is weakly surfaced outside pipeline/history

## Current ThesisX Weaknesses

### 1. Context Injection Was Fragmented

Before this pass, pages like quality and writing built context manually:
- `title=...`
- `project_id=...`
- or direct metric strings

This made behavior drift by page and prevented improvements from propagating
system-wide.

### 2. Output Contracts Were Implicit

Many actions asked the model to "rewrite" or "expand" without encoding
task-specific output expectations such as:
- writing -> directly usable Markdown
- quality -> prioritized revision plan
- evidence -> support-oriented draft

### 3. Memory Was Underused

ThesisX already had valuable memory sources:
- project metadata
- knowledge store
- quality signals
- enabled skills
- run history
- latest RAG context

But these were not assembled into one reusable bundle.

## What We Added

### Unified Agent Context Assembler

Code:
- [app/core/agent/context_assembler.py](/Volumes/E/ThesisX/app/core/agent/context_assembler.py)
- [thesisx_api/routes/agent.py](/Volumes/E/ThesisX/thesisx_api/routes/agent.py)
- [thesisx_api/schemas/agent.py](/Volumes/E/ThesisX/thesisx_api/schemas/agent.py)

The assembler now creates layered context bundles with:
- project context
- working context
- memory context
- output contract

Inputs:
- `task_type`
- `project_id`
- `session_id`
- `query`

Sources currently included:
- ProjectService
- KnowledgeStore
- QualityService
- RunHistoryReader
- latest RAG context file
- EnabledSkillsStore

The assembler now also:
- trims context with explicit budgets
- ranks project knowledge by task type + query relevance
- selects more relevant run-history paper paragraphs instead of raw prefix dumps

### Feedback Memory

Code:
- [app/core/agent/feedback_memory.py](/Volumes/E/ThesisX/app/core/agent/feedback_memory.py)
- [thesisx_api/routes/agent.py](/Volumes/E/ThesisX/thesisx_api/routes/agent.py)

ThesisX now persists lightweight user feedback:
- accepted / rejected
- task type
- project id
- short free-form signal

This feedback is injected back into future context bundles for the same task type
and project, so the system can start avoiding repeated failure modes.

### Unified Agent Execution Surface

Code:
- `POST /api/agent/context`
- `POST /api/agent/rewrite`
- `POST /api/agent/artifact`
- `POST /api/agent/feedback`

The important shift is architectural:
- pages no longer need to assemble context themselves
- pages no longer need to know whether a result should be free-form text or typed artifact
- feedback can now flow back into future executions

### Typed Artifacts

Code:
- [app/core/agent/artifact_builder.py](/Volumes/E/ThesisX/app/core/agent/artifact_builder.py)
- [app/core/agent/output_contracts.py](/Volumes/E/ThesisX/app/core/agent/output_contracts.py)

Typed artifacts now exist for:
- quality
- writing
- theory
- knowledge
- evidence

Each artifact now has at least:
- `summary`
- `sections`
- `markdown`
- `steps`
- `actions`
- `metadata`
- `output_contract`
- `sources`

### Initial Live Adoption

The agent layer is now used by:
- [writing-workspace.tsx](/Volumes/E/ThesisX/thesisx-web/components/writing-workspace.tsx)
- [quality-workspace.tsx](/Volumes/E/ThesisX/thesisx-web/components/quality-workspace.tsx)
- [theory-workspace.tsx](/Volumes/E/ThesisX/thesisx-web/components/theory-workspace.tsx)
- [literature-workspace.tsx](/Volumes/E/ThesisX/thesisx-web/components/literature-workspace.tsx)
- [knowledge-workspace.tsx](/Volumes/E/ThesisX/thesisx-web/components/knowledge-workspace.tsx)
- [evidence-workspace.tsx](/Volumes/E/ThesisX/thesisx-web/components/evidence-workspace.tsx)

This means the main web AI surfaces now consume standardized layered context
instead of page-local string assembly, and several of them now render typed
artifacts instead of only raw rewrite text.

### Shared Rendering

Code:
- [agent-artifact-panel.tsx](/Volumes/E/ThesisX/thesisx-web/components/agent-artifact-panel.tsx)

Major web surfaces now use one shared rendering pattern for agent outputs, which
reduces page-specific drift in how artifacts, next-step actions, and feedback
controls are presented.

## What Still Needs Work

### Near-Term

1. Improve context ranking:
- current relevance scoring is lightweight lexical overlap
- no source weighting, freshness, or acceptance-history weighting yet

2. Deepen feedback memory:
- current memory stores short acceptance / rejection signals only
- no artifact-level diff memory or per-surface preference policies yet

3. Stabilize artifact protocol further:
- sections / steps / actions are now standardized, but not yet versioned
- no formal schema evolution policy exists yet

### Later

1. Move from context bundle strings to typed workflow state
2. Add source-level provenance tags inside assembled agent context
3. Weight memory by acceptance strength / recency / project stage
4. Introduce richer browser-level workflow tests around agent-assisted tasks

## Design Rule Going Forward

No new AI workflow should hand-roll its own prompt context if it can use the
shared context assembler.

If a page needs extra context, that extra context should be appended on top of
the standardized bundle, not replace it.
