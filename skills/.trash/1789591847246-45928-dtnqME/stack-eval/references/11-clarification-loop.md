# P11 — Clarification loop

## Goal

Surface and resolve ambiguities before locking the master plan.

## Loop

1. Orchestrator aggregates: end-state, architecture, gaps, research, tasks, docs, available tools.
2. Fan out clarification asks to expert subagents (architect, deploy, security, product as needed).
3. Compile a **single** deduplicated question list for the human.
4. Pose questions; record answers in `.agent/clarifications.md`.
5. Repeat until the list is empty **or** remaining items are explicitly deferred by the user.

## STOP / CONTINUE

- **STOP:** Open blocking questions remain unanswered and not deferred.
- **CONTINUE:** No blocking questions left (all answered or deferred with owners).

## Outputs

- `.agent/clarifications.md`
