# Making your skills + rules seamlessly available to Grok Build

This is the "seamless availability" half — so both Claude and Grok Build follow the same
rules and have the same skills, and the review handoff compares like with like.

Grok Build is explicitly compatible with Claude Code skills, plugins, and `CLAUDE.md`
files, and supports Bring-Your-Own-MCP. That means you mostly *configure*, not rebuild.

## 1. Shared rules via CLAUDE.md

Grok Build reads `CLAUDE.md`. Keep one canonical rules file per repo (your coding
standards, naming, citation rules, Baldor SOP pointers) and both tools obey it. Don't fork
it per tool — a single source of truth is what keeps the two agents' plans comparable
instead of diverging on style.

Keep it lean (the same discipline you already apply): every line loads on every prompt in
both tools.

## 2. Shared skills

Point Grok Build at the same skill directory your Claude setup uses. Skills packaged as
`.skill` / `.md` packs are portable across both. For a skill like this one (`grok-review`),
you'd typically only install it on the Claude side — it's the *initiator* of the handoff;
Grok is the reviewer and doesn't need it.

If a skill shells out to tools, make sure those tools resolve in both environments (PATH,
env vars), or the skill will trigger but fail mid-run in one of them.

## 3. Shared connectors via Bring-Your-Own-MCP

Rather than relying on Grok's still-young native connector catalog, point Grok Build's MCP
client at your **Composio** endpoint. One MCP connection gives Grok everything Composio
already brokers (Gmail, Linear, Supabase, Exa, and the rest), which is far more than Grok's
native list. This is the single highest-leverage move for closing the "connection items
aren't great" gap.

Verify parity after setup: ask each tool to list its available tools/connectors and diff
the two. Anything present in one but not the other is a gap to close before you trust a
cross-review on a task that depends on that connector.

## Other directions of the same pattern

The `grok-review` packet format (Goal + Artifact + Rubric) is symmetric, so it also
supports:
- **Reverse** (Grok proposes, Claude reviews): have Grok Build write its plan/diff to a
  file, then ask Claude to review that file against the same rubric.
- **Blind two-way ensemble**: each model writes its plan independently to
  `.agent/plans/plan-claude.md` and `.agent/plans/plan-grok.md` with no peeking, then each
  reviews the other's, then one synthesizes. Blindness matters — if either sees the other's
  plan first it anchors and you get agreement, not review.
