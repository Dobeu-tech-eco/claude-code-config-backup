# Continuous Improvement Review

<!-- review: cadence=self | last-reviewed=2026-07-17 -->

Systematic review loop for the ruflo harness and the rules themselves.
Industry basis: retrospectives (agile), blameless postmortems (SRE), and
kaizen — small, regular, evidence-driven corrections beat big rewrites.

## Learning Capture (continuous)

After any significant completed task:
1. What worked that wasn't obvious? → `memory_store` to `patterns`.
2. What failed or was corrected by the user? → `memory_store` to `patterns`
   with tag `anti-pattern`, including the why.
3. Decision made that future sessions must not re-litigate? → `decisions`.

One entry per insight. No insight, no entry.

## Weekly Light Review (~10 min, user-initiated: "run the weekly review")

1. `memory_stats` — entry growth, namespace balance, embedding coverage.
2. `session_list` — stale sessions to delete.
3. Cost check (`cost-tracking` namespace / cost report) — trend vs last week.
4. Scan `patterns` entries added this week — dedupe, sharpen, or delete weak ones.

## Monthly Deep Audit (~30 min, user-initiated: "run the rules audit")

For every file in `~/.claude/rules/` and each active project CLAUDE.md:
1. **Accuracy** — does each rule still match reality (tool names, paths,
   model lineup, plugin versions)? Fix or delete.
2. **Usage** — did any rule get violated repeatedly this month? Either the
   rule is wrong or it needs a hook to enforce it (see update-config skill).
3. **Cost** — is any rules file bloated? Rules are loaded every session;
   cut anything that hasn't influenced behavior.
4. **Conflicts** — global vs local contradictions; local tightens, never
   loosens. Resolve in favor of the more specific scope.
5. Update the `<!-- review: ... -->` header stamp in each audited file and
   sync the config backup on `G:\`.
6. Log one-line audit outcome to memory (`patterns`, key
   `rules-audit-YYYY-MM`): what changed and why.

## Horizon Tracking

The standing objective lives in ruflo memory (`horizons` namespace, key
`ruflo-rules-continuous-improvement`). Review its progress during the
monthly audit; update milestone/drift there, not in this file.

## Escalation

If the same class of failure appears in 3+ sessions, stop patching rules:
run a root-cause pass (systematic-debugging skill) and consider a hook,
a skill, or automation (Make/Composio) instead of more prose.
