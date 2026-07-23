---
name: stack-eval
description: >
  End-to-end stack evaluation and production gap-closure orchestrator.
  Discovers current codebase state, plans the path to a production end-state
  (asks first; defaults to Vercel-oriented production), gates on human approval,
  commits/pushes, then executes via swarm with hard completion gates.
  Use when the user invokes /stack-eval, asks for stack evaluation, production
  readiness, gap analysis to prod/Vercel, or plan-then-swarm execution.
disable-model-invocation: true
---

# /stack-eval

Portable orchestrator: architecture → gap plan → human approval → commit/push → swarm execution with hard completion gates.

**This skill does not auto-invoke.** Only run when the user explicitly calls `/stack-eval` (or equivalent).

## Hard STOPs (verbatim — never violate)

1. **Do not skip the end-state ask.** Default only when the user gives no guidance.
2. **Do not execute implementation** until the user says **plan is set to go** (or equivalent explicit approval).
3. **Do not start Phase 14** until plan docs are committed and pushed (or push failure is explicitly acknowledged by the user).
4. **Do not mark a subtask complete** until the orchestrator re-runs verification-before-completion and all gate items pass.

## Every run — start here

1. Read this file, then [references/00-end-state.md](references/00-end-state.md).
2. Ask the user for the production end-state (once).
3. If unanswered → load [references/vercel-default-endstate.md](references/vercel-default-endstate.md) and record `end_state: vercel-default`.
4. Proceed through phases P1→P14 in order. Load the matching reference before each phase.
5. Artifacts live under `.agent/` (tasks, progress, state). Do not invent ad-hoc root folders.

## Phase table

| Phase | Name | Reference | STOP / CONTINUE |
|-------|------|-----------|-----------------|
| P0 | Ask end-state | [00-end-state.md](references/00-end-state.md) | STOP until asked (or default applied) |
| P1 | Architecture analyze | [01-architecture-analyze.md](references/01-architecture-analyze.md) | CONTINUE after arch note written |
| P2 | GitHub code review | [02-github-code-review.md](references/02-github-code-review.md) | CONTINUE (skip OK with reason) |
| P3 | Swarm bootstrap | [03-swarm-bootstrap.md](references/03-swarm-bootstrap.md) | CONTINUE after swarm init |
| P4 | Agents inventory | [04-agents-inventory.md](references/04-agents-inventory.md) | CONTINUE after inventory |
| P5 | Planner gap | [05-planner-gap.md](references/05-planner-gap.md) | CONTINUE after gap doc |
| P6 | Remote backup cascade | [06-remote-backup-cascade.md](references/06-remote-backup-cascade.md) | CONTINUE after cascade (declines OK) |
| P7 | Git bootstrap | [07-git-bootstrap.md](references/07-git-bootstrap.md) | CONTINUE after branch/ledger ready |
| P8 | Research / workflow / CI-CD | [08-research-parallel.md](references/08-research-parallel.md) | CONTINUE after research notes |
| P9 | Task decomposition (SDD) | [09-task-decomposition.md](references/09-task-decomposition.md) | CONTINUE after `.agent/tasks.json` |
| P10 | Docs / rules / system / STRATEGY | [10-docs-contract.md](references/10-docs-contract.md) | CONTINUE after docs contract |
| P11 | Clarification loop | [11-clarification-loop.md](references/11-clarification-loop.md) | STOP until questions empty or deferred |
| P12 | Master plan | [12-master-plan.md](references/12-master-plan.md) | **HARD STOP** until "plan is set to go" |
| P13 | Commit + push plan | [13-pre-exec-commit-push.md](references/13-pre-exec-commit-push.md) | STOP until pushed or ack |
| P14 | Execute swarm | [14-execute-swarm.md](references/14-execute-swarm.md) | Gate each subtask via [15](references/15-subtask-completion-gate.md) |

Supporting:

- [15-subtask-completion-gate.md](references/15-subtask-completion-gate.md) — re-verify before `passes=true`
- [16-skill-wiring.md](references/16-skill-wiring.md) — related skills / MCP
- [checklists/phase-gates.md](references/checklists/phase-gates.md)
- [checklists/subtask-done.md](references/checklists/subtask-done.md)

## Flow (summary)

```text
P0 AskEndState ──(empty)──► Vercel default
         │
         ▼
P1 Arch → P2 Review → P3 Swarm → P4 Agents → P5 Gap
         → P6 Remotes → P7 Git → P8 Research → P9 Decompose
         → P10 Docs → P11 Clarify → P12 MasterPlan
         ──["plan is set to go"]──► P13 Commit/Push → P14 Execute
         → Subtask gate (orchestrator verifies) → next / done
```

## Locked substitutes (this monorepo family)

| Expected | Substitute |
|----------|------------|
| eslint | `pnpm run typecheck` (and `pnpm run build` when build is in end-state) |
| test runner / TDD | N/A unless end-state adds a runner — document N/A in gate |
| Opsera architecture MCP | Auth once via `mcp_auth`; on failure → local fallback; tag `arch_source: local-fallback` |
| Run artifacts | `.agent/` only |

## Orchestrator duties

- Own phase sequencing and hard STOPs.
- Fan out research/clarification/implementation to subagents; never mark their work done without re-running the completion gate yourself.
- Never commit secrets. Never push force to main/master unless the user explicitly demands it (and warn).
- After P12 approval phrase, only then P13→P14.

## Install / sync

See [INSTALL.md](INSTALL.md). Source of truth is this folder. Sync outward with `scripts/sync-installs.ps1` or `scripts/sync-installs.sh`.
