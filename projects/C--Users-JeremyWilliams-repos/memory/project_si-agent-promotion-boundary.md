---
name: si-agent-promotion-boundary
description: "si promote/rollback have no dry-run — without --confirm they just error, so a candidate verdict always costs a state write and needs explicit user approval"
metadata: 
  node_type: memory
  type: project
  originSessionId: c8c98d02-007d-48a0-8971-e28c90c20b63
  modified: 2026-09-23T20:17:36.778Z
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

### Why more/harder examples CANNOT fix it (corrected 2026-09-23)

An earlier note here recommended "add holdout examples the baseline fails." **That is impossible**
as the target is currently configured. Both hard checks in `readme_checks()` ignore their `example`
argument entirely:

- `required_sections.py` — `[s for s in self.sections if s not in output]`
- `no_placeholder_text.py` — `[m for m in PLACEHOLDER_MARKERS if m in output]`

Neither reads `expected_output` or `task_input`, so the gate never compares output to label. The
hard-pass rate is a property of the **instruction's output format**, not of the example. Verified:
a deliberately worthless README containing the 7 required headings scores `hard_passed=True` on
all four holdout rows, with identical verdicts across different examples.

So no example can make the baseline fail — only an instruction that stops emitting a heading would.
Adding rows changes nothing. Grader scores can't rescue it either; `decide()` never reads them.

**The only way to create headroom is a hard check that actually reads `example`** — e.g. a
grounding check failing when the output asserts a stack/deployment fact absent from `task_input`
(the canary's forbidden-claims idea generalised to regular splits). That one addition would also
give the optimizer real dev failures to reflect on, fixing the no-op optimizer and the ceiling
together.

## The optimizer is currently a no-op on this target

Verified 2026-09-23 against the real store: drafts v2, v3 and v4 are all **byte-identical to
baseline v1 apart from its trailing newline** (v1 961 chars, every draft 960; `v3 == v4` exactly).
The optimizer model echoes the instruction back verbatim and
`reflective_optimizer.py:24` `.strip()`s it — which also rules out the `proposal or current.body`
empty-proposal fallback, since that path would have preserved the newline.

Root cause: `si optimize` evaluates `validated.non_holdout("dev")` — only the **3 dev rows**, not
the 34 train rows — and dev currently passes 3/3, so `_format_failures` hands the reflection
prompt `"(no failures observed)"` and there is nothing to revise.

## The recorded `canary_leak` was false — root-caused 2026-09-23

v2's `canary_leak` (c1, c2) was **not** a real leak, and not optimizer drift. The canary rows in
`datasets/repo_readme_author.jsonl` carry no `forbidden_claims` metadata (c1 has no `metadata`
field; c2 has an unrelated `canary` key). `canary_forbidden_claims` returned `passed=True` on empty
claims, and `canary_failures()` reads a *passing* canary as a leak — so the detector accused the
candidate without ever inspecting its output. Any candidate would have "leaked".

An earlier note here claimed v1's own text leaked. **That was wrong** — the check never looked at
any output.

Fixed on branch `worktree-canary-metadata-fix` (pushed): the check now raises a named
configuration error, and `scripts/build_readme_dataset.py::_to_record` no longer drops `metadata`
on write (it had the same defect, so a regenerated dataset could never hold a usable canary).

**Resolved 2026-09-23:** the dataset was regenerated with the fixed script. The canary is now
`repo-empty-canary` carrying real `forbidden_claims`; train/dev/holdout membership and labels are
byte-identical, only the fingerprint changed (`dd919b47…` → `3c04eb31…`), which invalidated drafts
v2–v4.

### The working canary immediately caught a REAL defect

A live `promote v5 --confirm` returned `canary_leak: repo-empty-canary`, `delta +0.000`, baseline
4/4, candidate 4/4 — baseline stayed v1. This is **not** the old false positive: metadata is
present (no `ValueError`), so the check actually inspected the output and found forbidden claims.
v5 is textually identical to v1, so this is **baseline v1's own behaviour**: given an empty-scaffold
repo (no files, no `package.json`) it fabricates stack claims.

Note the distinction — the v2 leak was false (check never ran); this one is real (check ran and
found claims). Same-looking verdict, opposite meaning.

**Both defects addressed 2026-09-23** on branch `worktree-canary-metadata-fix` (commit `ea14fef`):

- `checks/grounded_claims.py` — a Check that reads `example.task_input` and fails when the output
  asserts a vocabulary claim the input does not support. Whole-token matching, so `i18next` cannot
  ground a `Next.js` claim. Its `reason` names the offending claims, because that string is the
  optimizer's entire signal (`reflective_optimizer.py:30`).
- `Target.checks_for_canaries()` now raises instead of falling back to `checks()`.

**Measured outcome — the ceiling broke.** Live dev hard-pass rate went **1.0 → 0.333**
(`grounded_claims` failed on `repo-ai-tutor` and `repo-ikram-meme-and-co`, both Next.js repos
claiming Vercel with no `vercel.json` or `@vercel/*` in the input). With real failures to reflect
on, `si optimize` produced **v6 = 1582 chars, genuinely different from v1** — the first divergent
draft ever (v2–v5 were all byte-identical to v1).

**v6 was PROMOTED 2026-09-23** — the first successful promotion for this target. Baseline v1 scored
3/4 on holdout (the grounded Check caught it fabricating on one row); v6 scored 4/4 with no canary
leak, giving `holdout_delta +0.250`, `reason_code: improved`. Baseline is now v6; v1 retained as
`promoted`.

The decision ledger reads as the whole diagnosis: v2 `canary_leak` (false — missing metadata),
v5 `canary_leak` (real — fabrication), v6 `improved` (+0.250).

**How to apply:** the two defects were coupled — fixing the check suite is what let the loop attack
the instruction. Don't hand-author an instruction fix when the gate has no signal; give the gate a
Check that reads its example first, and make its `reason` name the offending tokens.

**How to apply:** Do not re-run `si optimize` expecting a different draft while dev is clean — it
costs 4 model calls and reproduces the same no-op. Give dev failing examples first.

**Why:** The si-agent skill forbids inferring promotion approval from a request to review,
evaluate, or prepare a promotion, and the CLI gives no safe middle path — and here the attempt
would burn model calls on a mathematically certain failure.

**How to apply:** Never add `--confirm` without an explicit user request naming that specific
version. Present SI id, current baseline version, candidate version, dataset path, and the exact
command, then stop. See [[si-agent-core-runtime]] for getting the loop runnable at all.
