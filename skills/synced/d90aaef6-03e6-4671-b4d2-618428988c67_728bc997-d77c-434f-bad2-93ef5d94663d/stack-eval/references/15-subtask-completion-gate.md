# P15 — Subtask completion gate (orchestrator re-verifies)

## Goal

Prevent premature `passes=true`. The **orchestrator** re-runs this gate; worker self-claims are insufficient.

## Gate sequence (all required unless N/A documented)

1. **Commit** — meaningful commit for the subtask (or explicit N/A if user forbade commits).
2. **Deliverable + docs** — code/config deliverable exists; docs updated before/during/after as required by `rules.md` / `system.md`.
3. **Refactor / simplify** — obvious slop removed; no drive-by refactors outside scope.
4. **Typecheck** — run `pnpm run typecheck` (eslint N/A in this monorepo family → **do not** require eslint). Include `pnpm run build` when end-state requires build.
5. **Env checklist** — required env vars documented; no secrets committed.
6. **Security** — quick review of auth/crypto/input/SQL surfaces touched; no new secret leaks.
7. **claude-flow memory** — store/search pattern note if tooling available; else document N/A.
8. **TDD** — tests added/run **or** N/A documented (no test runner in repo today unless end-state added one).
9. **Browser automation** — if UI changed, smoke via browser skill/MCP; else N/A.
10. **verification-before-completion** — re-read verification-quality / project verify guidance; confirm claims match evidence.
11. Only then set **`passes=true`**.

## STOP / CONTINUE

- **STOP:** Any required item failed or skipped without N/A reason.
- **CONTINUE:** All items pass → update ledger → next subtask.

## Checklist

Use [checklists/subtask-done.md](checklists/subtask-done.md).
