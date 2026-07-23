# P7 — Git bootstrap

## Goal

Ready a branch and ledger so plan artifacts can be committed later (P13) without chaos.

## Steps

1. Confirm clean-enough working tree for planning (stash or note dirty files; do not destroy user work).
2. Prefer a dedicated branch for the eval run (e.g. `stack-eval/<date-or-slug>`) unless user specifies otherwise.
3. Ensure `.agent/` exists with `tasks.json`, `progress.md`, `state.json` stubs if missing.
4. Record branch name and HEAD SHA in `.agent/state.json`.
5. Do **not** commit plan docs yet — that is P13 after approval.

## STOP / CONTINUE

- **STOP:** Cannot determine git root / branch and user has not approved no-git mode.
- **CONTINUE:** Branch + `.agent/` ledger ready.

## Outputs

- Branch ready
- `.agent/state.json` git fields
- Stub ledger files if needed
