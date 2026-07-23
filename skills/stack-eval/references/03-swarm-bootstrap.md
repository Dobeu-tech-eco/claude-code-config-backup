# P3 — Swarm bootstrap

## Goal

Initialize coordination topology for later research and execution phases.

## Steps

1. Prefer hierarchical (or hierarchical-mesh) topology for plan-then-execute work.
2. Init via available tooling, e.g.:
   - `npx @claude-flow/cli@latest swarm init --topology hierarchical --max-agents 8 --strategy specialized`
   - or project skills `v3-swarm-coordination` / `swarm-orchestration` / `swarm-advanced`
3. Record swarm id / topology in `.agent/state.json` and a short `.agent/swarm.md`.
4. Do **not** spawn full implementation workers yet — bootstrap only.

## STOP / CONTINUE

- **STOP:** Swarm init failed and no degraded “single-orchestrator” mode recorded.
- **CONTINUE:** Swarm ready **or** explicit degraded mode documented (orchestrator-only until P14).

## Outputs

- `.agent/swarm.md`
- `.agent/state.json` swarm fields
