# P9 — Task decomposition (SDD-shaped)

## Goal

Turn gaps into chronological main tasks and parallelizable subtasks suitable for swarm execution.

## Method

Follow subagent-driven-development principles:

1. Chronological **main tasks** (must mostly succeed in order).
2. Under each main, deepen into **independent subtasks** that can run in parallel where safe.
3. Each subtask: id, description, steps (immutable later), status, `passes`, priority, dependencies.
4. Prefer fresh implementer + reviewer per subtask at execution time (P14).

## Steps

1. Load gap analysis + research + end-state.
2. Write `.agent/tasks.json` (JSON only; later updates may change only `status` / `passes`).
3. Mirror human-readable progress in `.agent/progress.md`.
4. Do not mark any `passes=true` here.

## STOP / CONTINUE

- **STOP:** `tasks.json` missing or not chronological at the main-task level.
- **CONTINUE:** Ledger written; ready for docs + clarification.

## Outputs

- `.agent/tasks.json`
- `.agent/progress.md` update
