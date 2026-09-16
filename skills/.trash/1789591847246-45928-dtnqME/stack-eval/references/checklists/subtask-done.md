# Subtask done checklist (orchestrator)

Subtask id: ________  Main task: ________

Re-run this list yourself. Worker claims do not count.

| # | Check | Result |
|---|--------|--------|
| 1 | Commit present (or N/A with reason) | [ ] pass / [ ] N/A: ___ |
| 2 | Deliverable + docs updated (before/during/after) | [ ] pass |
| 3 | Refactor/simplify within scope | [ ] pass |
| 4 | `pnpm run typecheck` (eslint N/A) | [ ] pass |
| 4b | `pnpm run build` if deploy surface touched | [ ] pass / [ ] N/A |
| 5 | Env checklist; no secrets committed | [ ] pass |
| 6 | Security spot-check on touched surfaces | [ ] pass |
| 7 | claude-flow memory note | [ ] pass / [ ] N/A |
| 8 | TDD / tests | [ ] pass / [ ] N/A (no runner) |
| 9 | Browser smoke if UI | [ ] pass / [ ] N/A |
| 10 | verification-before-completion evidence matches claims | [ ] pass |

**Only if all required rows pass:** set `passes=true` and `status=completed` in `.agent/tasks.json`.

Orchestrator initials / timestamp: ________
