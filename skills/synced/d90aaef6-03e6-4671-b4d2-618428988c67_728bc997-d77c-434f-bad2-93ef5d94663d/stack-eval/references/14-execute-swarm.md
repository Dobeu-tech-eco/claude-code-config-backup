# P14 — Execute swarm

## Goal

Execute chronological main tasks with parallel subtasks under swarm coordination. Gate every subtask.

## Wiring

- Prefer `v3-swarm-coordination` + `swarm-advanced` + hive-mind consensus where available.
- Wire `task-orchestrate` / code-review-swarm for review passes.
- SDD: fresh implementer per subtask + task review; orchestrator owns completion gate.

## Steps

1. Confirm P13 complete (push OK or ack).
2. Walk main tasks in chronological order.
3. Within a main task, run independent subtasks in parallel when safe.
4. After each subtask claims done → orchestrator runs [15-subtask-completion-gate.md](15-subtask-completion-gate.md) (and [checklists/subtask-done.md](checklists/subtask-done.md)).
5. Set `passes=true` only when the gate fully passes.
6. Update `.agent/tasks.json` (`status` / `passes` only) and `.agent/progress.md`.
7. On blocker → record BLOCKED; do not silently skip gates.

## STOP / CONTINUE

- **STOP:** Attempting execution without P12 approval or without P13 push/ack.
- **CONTINUE:** Next subtask only after gate pass; run complete when all mains done or blocked with user notice.

## Outputs

- Updated `.agent/tasks.json` / `progress.md`
- Code/docs changes per plan
- Final summary for user
