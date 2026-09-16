# P0 — Ask production end-state

## Goal

Record the target production end-state for this `/stack-eval` run before any analysis or planning.

## Steps

1. Ask the user **once**, clearly, for the production end-state. Include prompts such as:
   - Hosting / deploy target (e.g. Vercel, other)
   - App shape (SPA + API, monorepo packages, preview vs prod)
   - Quality gates (typecheck, build, tests if any)
   - Env / secrets contract
   - Success criteria for “done”
2. If the user answers → write `.agent/end-state.md` (or equivalent ledger entry) with their answers verbatim plus a short normalized summary. Tag `end_state: user-specified`.
3. If the user gives **no guidance** (empty, skip, “default”, “you decide”) → load [vercel-default-endstate.md](vercel-default-endstate.md), copy/adapt into `.agent/end-state.md`, tag `end_state: vercel-default`.
4. Do **not** invent a third default. Do **not** proceed to P1 until end-state is recorded.

## STOP / CONTINUE

- **STOP:** End-state not asked.
- **CONTINUE:** End-state file/ledger entry exists with either `user-specified` or `vercel-default`.

## Outputs

- `.agent/end-state.md`
- Optional: `.agent/state.json` field `end_state`
