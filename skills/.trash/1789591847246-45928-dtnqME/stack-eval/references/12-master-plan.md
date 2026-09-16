# P12 — Master plan

## Goal

Produce the human-approvable master plan. **No implementation until approval.**

## Steps

1. Assemble master plan from end-state, architecture, gaps, research, tasks, clarifications, docs contract.
2. Write using [doc-templates/MASTER_PLAN.md.template](doc-templates/MASTER_PLAN.md.template) → typically `.agent/MASTER_PLAN.md` (and optionally a short root pointer).
3. Ensure STRATEGY.md stays aligned (re-invoke `ce-strategy` if needed).
4. Present the plan to the user and ask for explicit approval.

## HARD STOP

**Do not execute implementation** until the user says **`plan is set to go`** (or equivalent explicit approval such as “approved — execute”, “go ahead with the plan”).

Ambiguous replies (“looks good”, “maybe”, “LGTM” without execute intent) → ask once to confirm with the approval phrase.

## STOP / CONTINUE

- **STOP:** Until explicit approval phrase.
- **CONTINUE:** Only after approval → proceed to P13.

## Outputs

- `.agent/MASTER_PLAN.md`
- Approval recorded in `.agent/progress.md` / `state.json`
