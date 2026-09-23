---
name: si-agent-promotion-boundary
description: "si promote/rollback have no dry-run — without --confirm they just error, so a candidate verdict always costs a state write and needs explicit user approval"
metadata: 
  node_type: memory
  type: project
  originSessionId: c8c98d02-007d-48a0-8971-e28c90c20b63
  modified: 2026-09-23T02:57:27.616Z
---

In `si-agent-core`, `si promote` and `si rollback` call `_require_confirmation(confirm)` as the
**first** statement in the command body (`src/si_agent/cli/app_factory.py`), before dataset
validation or any evaluation. Without `--confirm` they raise
`typer.BadParameter("state changes require --confirm")` and do nothing.

Consequence: **there is no non-mutating "prepare" or dry-run path to get a candidate's
holdout/canary verdict.** Even a run that fails the gate records a decision row
(the v2 attempt recorded `promoted: false`, `reason_code: canary_leak`). So asking
"is this candidate good?" cannot be answered without a state write.

`si eval` scores the **baseline** only, never a draft candidate — so it cannot stand in
as a candidate check.

## The `repo-readme-author` holdout gate is currently unpassable

`promotion/promoter.py` computes `delta = candidate.hard_pass_rate - baseline.hard_pass_rate`
and rejects with `no_improvement` when `delta <= HOLDOUT_MIN_IMPROVEMENT` (`constants.py` = `0.0`),
so improvement must be **strictly positive**. The recorded v2 decision shows the baseline already
scoring `4` hard passes out of `4` holdout examples — a hard-pass rate of 1.0.

Therefore `delta <= 0` for *every* possible candidate, and any promote attempt is a guaranteed
`no_improvement` failure. v2's `canary_leak` was only the first gate reached (canary is checked
before the delta comparison); a canary-clean candidate still falls through to `no_improvement`.

Unblocking this needs a dataset change, not another optimize run: add holdout examples the current
baseline actually fails, so there is headroom to improve. Grader scores cannot rescue it —
`decide()` deliberately never reads them.

**Why:** The si-agent skill forbids inferring promotion approval from a request to review,
evaluate, or prepare a promotion, and the CLI gives no safe middle path — and here the attempt
would burn model calls on a mathematically certain failure.

**How to apply:** Never add `--confirm` without an explicit user request naming that specific
version. Present SI id, current baseline version, candidate version, dataset path, and the exact
command, then stop. See [[si-agent-core-runtime]] for getting the loop runnable at all.
