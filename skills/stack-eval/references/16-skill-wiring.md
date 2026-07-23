# Skill wiring — related skills & MCP

## Related local skills (prefer project copies)

| Need | Skill / tool |
|------|----------------|
| Swarm coord | `v3-swarm-coordination`, `swarm-advanced`, `swarm-orchestration` |
| GitHub review | `github-code-review`, `github-workflow-automation` |
| Verification | `verification-quality` |
| Browser UI smoke | `browser` / browse MCP / Playwright MCP |
| Strategy doc | `ce-strategy` (compound-engineering) for `STRATEGY.md` |
| SDD execution | subagent-driven-development (superpowers) |
| Memory | claude-flow / agentdb skills as available |

## MCP

| Server | Use | Failure mode |
|--------|-----|--------------|
| Opsera DevSecOps | architecture-analyze, telemetry | Auth once → local fallback (`arch_source: local-fallback`) |
| GitHub | PR review, issues | Fall back to `gh`; skip with reason |
| Vercel | deploy/preview when end-state is Vercel | Document skip; do not block planning |
| Browse / Playwright | UI verification in gate | N/A if no UI |

## Install sync

Canonical SoT: repo `.claude/skills/stack-eval/`. Sync via `scripts/sync-installs.ps1` / `.sh`. See [../INSTALL.md](../INSTALL.md).

## STOP / CONTINUE

- **STOP:** Required wiring for the current phase is unknown and not documented here or in the phase reference (do not invent fake tools).
- **CONTINUE:** Use listed skills/MCP with documented failure modes; missing tools → substitute or skip with reason in `.agent/`.
