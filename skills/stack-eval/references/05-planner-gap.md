# P5 — Planner gap analysis

## Goal

Diff current architecture vs recorded end-state into a prioritized gap list.

## Steps

1. Load `.agent/end-state.md` and `.agent/architecture.md`.
2. Produce gaps by category: deploy, API, SPA, DB, env, CI/CD, docs, security, observability, quality gates.
3. Rank: P0 blocker → P1 needed for prod → P2 nice-to-have.
4. Write `.agent/gap-analysis.md` with acceptance hints per gap.
5. Do not start implementation.

## STOP / CONTINUE

- **STOP:** Gap analysis missing or not tied to end-state.
- **CONTINUE:** Prioritized gap doc written.

## Outputs

- `.agent/gap-analysis.md`
