# P13 — Pre-exec commit + push

## Goal

Persist plan artifacts to git and push before swarm execution.

## Commit set (typical)

- `.agent/**` plan artifacts (end-state, architecture, gaps, research, tasks, clarifications, MASTER_PLAN, state/progress)
- `rules.md`, `system.md`, `STRATEGY.md` if created/updated
- Do **not** commit secrets, `.env`, credentials

## Steps

1. Confirm P12 approval recorded.
2. Stage only plan/docs artifacts (no unrelated user WIP unless user asks).
3. Commit with a clear message (e.g. `[STACK-EVAL] Lock master plan for execution`).
4. Push to the working remote/branch.
5. If push fails → **STOP** Phase 14 until the user explicitly acknowledges proceeding without push (record ack in `.agent/state.json`).

## STOP / CONTINUE

- **STOP:** Not committed; or push failed without user acknowledgment.
- **CONTINUE:** Pushed successfully **or** user explicitly acknowledged push failure.

## Outputs

- Commit SHA in `.agent/state.json`
- Push result in `.agent/progress.md`
