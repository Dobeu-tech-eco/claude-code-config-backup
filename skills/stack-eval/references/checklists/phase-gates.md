# Phase gates checklist

Use with `/stack-eval` SKILL.md. Mark each before advancing.

| Phase | Gate | Done |
|-------|------|------|
| P0 | End-state asked; recorded or vercel-default applied | [ ] |
| P1 | `.agent/architecture.md` with `arch_source` | [ ] |
| P2 | `.agent/code-review.md` (review or skip reason) | [ ] |
| P3 | Swarm init or degraded mode documented | [ ] |
| P4 | `.agent/agents-inventory.md` | [ ] |
| P5 | `.agent/gap-analysis.md` prioritized | [ ] |
| P6 | Remote cascade completed (declines OK) | [ ] |
| P7 | Branch + `.agent/` ledger ready | [ ] |
| P8 | Research notes (CI/CD + deploy + gates) | [ ] |
| P9 | `.agent/tasks.json` chronological mains | [ ] |
| P10 | `rules.md` + `system.md` + STRATEGY attempted | [ ] |
| P11 | Clarifications empty or deferred | [ ] |
| P12 | MASTER_PLAN written; **STOP** until "plan is set to go" | [ ] |
| P13 | Committed + pushed **or** push failure acknowledged | [ ] |
| P14 | Execution only after P12+P13; each subtask gated | [ ] |

## Hard STOPs (must remain true)

1. End-state ask not skipped (default only if no guidance).
2. No implementation before **plan is set to go**.
3. No P14 before push or explicit ack.
4. No `passes=true` without orchestrator completion gate.
