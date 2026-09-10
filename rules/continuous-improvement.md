# Continuous Improvement Review

<!-- review: cadence=self | last-reviewed=2026-09-09 -->

Systematic review loop for the harness and the rules themselves.
Industry basis: retrospectives (agile), blameless postmortems (SRE), and
kaizen — small, regular, evidence-driven corrections beat big rewrites.

## Learning Capture (continuous)

After any significant completed task, save a durable learning to native
file-memory (`~/.claude/projects/<project>/memory/`, indexed in `MEMORY.md`):
1. What worked that wasn't obvious? → a `patterns`-type memory file.
2. What failed or was corrected by the user? → a `feedback`-type memory
   file, including the why.
3. Decision made that future sessions must not re-litigate? → a `project`-
   type memory file.

One entry per insight. No insight, no entry. See the `memory-curator` agent
for dedup/prune/index hygiene on this store.

## Weekly Light Review (~10 min, user-initiated: "run the weekly review")

1. Scan `~/.claude/projects/<project>/memory/` for growth and staleness.
2. Review recent session/project files for anything that should be captured
   or retired.
3. Scan memory files added this week — dedupe, sharpen, or delete weak ones.

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
6. Log one-line audit outcome to a memory file (key `rules-audit-YYYY-MM`):
   what changed and why.

## Horizon Tracking

Standing objectives are tracked as `project`-type native memory files.
Review their progress during the monthly audit; update milestone/drift
there, not in this file.

## Escalation

If the same class of failure appears in 3+ sessions, stop patching rules:
run a root-cause pass (systematic-debugging skill) and consider a hook,
a skill, or automation (Make/Composio) instead of more prose.
